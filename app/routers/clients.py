from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, text, update
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models import Agence, Client, DemandeCredit, Journal, Utilisateur
from app.models.enums import Role, StatutDossier
from app.schemas import ClientIn, ClientOut

router = APIRouter(prefix="/clients", tags=["clients"])

SAISIE = (Role.AGENT_CREDIT, Role.ADMINISTRATEUR)
LECTURE = (Role.AGENT_CREDIT, Role.DECIDEUR, Role.ADMINISTRATEUR)
STATUTS_OUVERTS = [StatutDossier.BROUILLON, StatutDossier.COMPLET, StatutDossier.SCORE,
                   StatutDossier.INSTRUIT, StatutDossier.SOUMIS]


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def creer_client(donnees: ClientIn, session: Session = Depends(get_session),
                 utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    if session.get(Agence, donnees.agence_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Agence inconnue")

    # On réserve le numéro d'identifiant pour en déduire le code client (CL000123)
    prochain_id = session.scalar(text("SELECT nextval(pg_get_serial_sequence('ops.client', 'id'))"))
    client = Client(id=prochain_id, code_client=f"CL{prochain_id:06d}", **donnees.model_dump())
    session.add(client)
    session.add(Journal(utilisateur_id=utilisateur.id, action="client_cree",
                        entite="client", entite_id=prochain_id))
    session.commit()
    session.refresh(client)
    return client


@router.get("", response_model=list[ClientOut])
def rechercher_clients(
    q: str | None = Query(default=None, min_length=2, description="Nom, prénom, téléphone ou code client"),
    limite: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE)),
):
    requete = select(Client).order_by(Client.nom, Client.prenom).limit(limite)
    if q:
        for mot in q.split():
            motif = f"%{mot}%"
            requete = requete.where(or_(Client.nom.ilike(motif), Client.prenom.ilike(motif),
                                        Client.telephone.ilike(motif), Client.code_client.ilike(motif)))
    return session.scalars(requete).all()


@router.get("/{client_id}", response_model=ClientOut)
def lire_client(client_id: int, session: Session = Depends(get_session),
                utilisateur: Utilisateur = Depends(exiger_roles(*LECTURE))):
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")
    return client


@router.put("/{client_id}", response_model=ClientOut)
def modifier_client(client_id: int, donnees: ClientIn, session: Session = Depends(get_session),
                    utilisateur: Utilisateur = Depends(exiger_roles(*SAISIE))):
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")
    if session.get(Agence, donnees.agence_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Agence inconnue")

    for champ, valeur in donnees.model_dump().items():
        setattr(client, champ, valeur)

    # Les données du client ont changé : les scores des dossiers en cours deviennent périmés
    session.execute(
        update(DemandeCredit)
        .where(DemandeCredit.client_id == client_id, DemandeCredit.statut.in_(STATUTS_OUVERTS))
        .values(donnees_modifiees_le=text("now()")))
    session.add(Journal(utilisateur_id=utilisateur.id, action="client_modifie",
                        entite="client", entite_id=client_id))
    session.commit()
    session.refresh(client)
    return client