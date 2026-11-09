import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, or_, select, text, update
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models import Agence, Client, DemandeCredit, Journal, Utilisateur
from app.models.enums import Role, StatutDossier
from app.portefeuille import exiger_client, filtrer_clients
from app.schemas import ClientIn, ClientMaj, ClientOut

router = APIRouter(prefix="/clients", tags=["clients"])

SAISIE = (Role.AGENT_CREDIT, Role.ADMINISTRATEUR)
LECTURE = (Role.AGENT_CREDIT, Role.DECIDEUR, Role.ADMINISTRATEUR)
AFFECTATION = (Role.DECIDEUR, Role.ADMINISTRATEUR)
STATUTS_OUVERTS = [StatutDossier.BROUILLON, StatutDossier.COMPLET, StatutDossier.SCORE,
                   StatutDossier.INSTRUIT, StatutDossier.SOUMIS]

# Corriger une de ces informations n'a aucun effet sur le score : on n'invalide pas les scores.
IDENTITE = {"nom", "prenom", "telephone", "adresse", "sexe"}

ACCENTS = "àâäéèêëîïôöùûüç"
SANS_ACCENTS = "aaaeeeeiioouuuc"


def sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def colonne_sans_accents(colonne):
    """Minuscules et sans accents côté base, pour comparer avec la saisie normalisée."""
    return func.translate(func.lower(colonne), ACCENTS, SANS_ACCENTS)


class AffectationIn(BaseModel):
    gestionnaire_id: int


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def creer_client(donnees: ClientIn, session: Session = Depends(get_session),
                 utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    if session.get(Agence, donnees.agence_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Agence inconnue")

    # Un agent qui crée un client en devient le gestionnaire ; sinon il reste à affecter.
    gestionnaire = utilisateur.id if utilisateur.role == Role.AGENT_CREDIT else None

    # On réserve le numéro d'identifiant pour en déduire le code client (CL000123)
    prochain_id = session.scalar(text("SELECT nextval(pg_get_serial_sequence('ops.client', 'id'))"))
    client = Client(id=prochain_id, code_client=f"CL{prochain_id:06d}",
                    gestionnaire_id=gestionnaire, **donnees.model_dump())
    session.add(client)
    session.add(Journal(utilisateur_id=utilisateur.id, action="client_cree",
                        entite="client", entite_id=prochain_id,
                        details={"gestionnaire_id": gestionnaire}))
    session.commit()
    session.refresh(client)
    return client


@router.get("", response_model=list[ClientOut])
def rechercher_clients(
    q: str | None = Query(default=None, min_length=2,
                          description="Nom, prénom, téléphone ou code client (accents ignorés)"),
    limite: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE)),
):
    """Liste tous les clients correspondants (homonymes compris) dans le portefeuille de l'utilisateur."""
    requete = filtrer_clients(select(Client), utilisateur)
    requete = requete.order_by(Client.nom, Client.prenom, Client.date_naissance,
                               Client.id).limit(limite)
    if q:
        for mot in sans_accents(q).split():
            motif = f"%{mot}%"
            requete = requete.where(or_(
                colonne_sans_accents(Client.nom).like(motif),
                colonne_sans_accents(Client.prenom).like(motif),
                Client.telephone.ilike(motif),
                Client.code_client.ilike(motif)))
    return session.scalars(requete).all()


@router.get("/{client_id}", response_model=ClientOut)
def lire_client(client_id: int, session: Session = Depends(get_session),
                utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    return exiger_client(session, client_id, utilisateur)


@router.patch("/{client_id}", response_model=ClientOut)
def modifier_client(client_id: int, donnees: ClientMaj, session: Session = Depends(get_session),
                    utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    """Modification partielle : on n'envoie que les champs à changer."""
    client = exiger_client(session, client_id, utilisateur)
    envoyes = donnees.model_dump(exclude_unset=True)
    if not envoyes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Aucun champ à modifier")
    if "agence_id" in envoyes and session.get(Agence, envoyes["agence_id"]) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Agence inconnue")

    # Les règles de ClientIn (majorité, profession connue...) sont revérifiées sur la fiche
    # fusionnée ; on ne retient que les erreurs portant sur les champs envoyés.
    actuel = {champ: getattr(client, champ) for champ in ClientIn.model_fields}
    try:
        ClientIn(**{**actuel, **envoyes})
    except ValidationError as erreur:
        problemes = [{"champ": e["loc"][0], "message": e["msg"]}
                     for e in erreur.errors() if e["loc"] and e["loc"][0] in envoyes]
        if problemes:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, problemes)

    changes = {champ: valeur for champ, valeur in envoyes.items()
               if getattr(client, champ) != valeur}
    if not changes:
        return client                      # rien à changer

    for champ, valeur in changes.items():
        setattr(client, champ, valeur)

    # Si une donnée utile au scoring change, les scores des dossiers en cours deviennent périmés
    if not set(changes) <= IDENTITE:
        session.execute(
            update(DemandeCredit)
            .where(DemandeCredit.client_id == client_id,
                   DemandeCredit.statut.in_(STATUTS_OUVERTS))
            .values(donnees_modifiees_le=text("now()")))
    # Minimisation : on journalise les noms des champs modifiés, pas leurs valeurs
    session.add(Journal(utilisateur_id=utilisateur.id, action="client_modifie",
                        entite="client", entite_id=client_id,
                        details={"champs": sorted(changes)}))
    session.commit()
    session.refresh(client)
    return client


@router.put("/{client_id}/gestionnaire", response_model=ClientOut)
def affecter_client(client_id: int, donnees: AffectationIn,
                    session: Session = Depends(get_session),
                    utilisateur: Utilisateur = Depends(exiger_roles(*AFFECTATION))):
    """Rattache (ou réaffecte) un client à un gestionnaire."""
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")
    gestionnaire = session.get(Utilisateur, donnees.gestionnaire_id)
    if gestionnaire is None or gestionnaire.role != Role.AGENT_CREDIT or not gestionnaire.actif:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Gestionnaire inconnu, inactif ou qui n'est pas un agent de crédit")

    ancien = client.gestionnaire_id
    client.gestionnaire_id = gestionnaire.id
    session.add(Journal(utilisateur_id=utilisateur.id, action="client_affecte",
                        entite="client", entite_id=client_id,
                        details={"ancien": ancien, "nouveau": gestionnaire.id}))
    session.commit()
    session.refresh(client)
    return client