import re
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.validation import valider_telephone
from app.db import get_session
from app.deps import exiger_roles
from app.models import Client, DemandeReinitialisation, Journal, Utilisateur
from app.models.enums import Role
from app.routers.comptes import MotDePasseTemporaireOut, _mot_de_passe_temporaire
from app.security import hasher_mot_de_passe

router = APIRouter(prefix="/reinitialisations", tags=["réinitialisation"])

MOTIF_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MESSAGE_PUBLIC = ("Votre demande a été transmise. L'administrateur la traitera après vérification de votre "
                  "identité : présentez-vous à votre agence ou contactez l'institution.")

# Limite simple en mémoire : 5 demandes par heure et par adresse (remise à zéro au redémarrage).
_ENVOIS: dict[str, deque] = defaultdict(deque)


def _limiter(adresse: str) -> None:
    maintenant = time.monotonic()
    file = _ENVOIS[adresse]
    while file and maintenant - file[0] > 3600:
        file.popleft()
    if len(file) >= 5:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Trop de demandes. Réessayez dans une heure.")
    file.append(maintenant)


class DemandeIn(BaseModel):
    email: str = Field(max_length=255)
    contact: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def verifier_email(cls, valeur: str) -> str:
        valeur = valeur.strip().lower()
        if not MOTIF_EMAIL.match(valeur):
            raise ValueError("adresse e-mail invalide")
        return valeur

    @field_validator("contact", mode="before")
    @classmethod
    def nettoyer(cls, valeur):
        return valider_telephone(valeur) if isinstance(valeur, str) else valeur


class ConfirmationOut(BaseModel):
    message: str


class DemandeOut(BaseModel):
    id: int
    email: str
    nom_complet: str
    role: Role
    gestionnaire: str | None
    contact: str | None
    statut: str
    cree_le: datetime


@router.post("", response_model=ConfirmationOut, status_code=201)
def demander(donnees: DemandeIn, requete: Request, session: Session = Depends(get_session)):
    """Route publique. La réponse est identique que le compte existe ou non."""
    _limiter(requete.client.host if requete.client else "inconnu")
    compte = session.scalar(select(Utilisateur).where(func.lower(Utilisateur.email) == donnees.email))
    if compte is not None and compte.actif and compte.role != Role.ADMINISTRATEUR:
        deja = session.scalar(select(DemandeReinitialisation).where(
            DemandeReinitialisation.utilisateur_id == compte.id,
            DemandeReinitialisation.statut == "en_attente"))
        if deja is None:
            session.add(DemandeReinitialisation(
                utilisateur_id=compte.id, email=donnees.email, contact=donnees.contact or None))
            session.commit()
    return ConfirmationOut(message=MESSAGE_PUBLIC)


@router.get("", response_model=list[DemandeOut])
def lister(
        statut: Literal["en_attente", "traitee", "rejetee", "tous"] = "en_attente",
        session: Session = Depends(get_session),
        _=Depends(exiger_roles(Role.ADMINISTRATEUR))):
    requete = select(DemandeReinitialisation).order_by(DemandeReinitialisation.id.desc()).limit(100)
    if statut != "tous":
        requete = requete.where(DemandeReinitialisation.statut == statut)
    resultat = []
    for d in session.scalars(requete):
        compte = session.get(Utilisateur, d.utilisateur_id)
        gestionnaire = None
        # Pour un client : on montre seulement le NOM de son gestionnaire (pour confirmer l'identité par téléphone).
        if compte.role == Role.CLIENT and compte.client_id:
            client = session.get(Client, compte.client_id)
            if client is not None and client.gestionnaire_id:
                g = session.get(Utilisateur, client.gestionnaire_id)
                gestionnaire = g.nom_complet if g else None
        resultat.append(DemandeOut(
            id=d.id, email=d.email, nom_complet=compte.nom_complet, role=compte.role,
            gestionnaire=gestionnaire, contact=d.contact, statut=d.statut, cree_le=d.cree_le))
    return resultat


def _demande_en_attente(session: Session, demande_id: int) -> DemandeReinitialisation:
    d = session.get(DemandeReinitialisation, demande_id)
    if d is None:
        raise HTTPException(404, "Demande introuvable.")
    if d.statut != "en_attente":
        raise HTTPException(409, "Cette demande a déjà été traitée.")
    return d


@router.post("/{demande_id}/traiter", response_model=MotDePasseTemporaireOut)
def traiter(demande_id: int, session: Session = Depends(get_session),
            admin: Utilisateur = Depends(exiger_roles(Role.ADMINISTRATEUR))):
    """À faire APRÈS avoir vérifié l'identité de la personne hors application."""
    d = _demande_en_attente(session, demande_id)
    cible = session.get(Utilisateur, d.utilisateur_id)
    mot_de_passe = _mot_de_passe_temporaire()
    cible.mot_de_passe_hash = hasher_mot_de_passe(mot_de_passe)
    cible.doit_changer_mdp = True
    cible.echecs_connexion = 0
    cible.verrouille_jusqua = None
    d.statut = "traitee"
    d.traitee_par = admin.id
    d.traitee_le = datetime.now(timezone.utc)
    session.add(Journal(utilisateur_id=admin.id, action="mot_de_passe_reinitialise", entite="utilisateur",
                        entite_id=cible.id, details={"demande_id": d.id}))
    session.commit()
    return MotDePasseTemporaireOut(email=cible.email, mot_de_passe_temporaire=mot_de_passe)


@router.post("/{demande_id}/rejeter", response_model=ConfirmationOut)
def rejeter(demande_id: int, session: Session = Depends(get_session),
            admin: Utilisateur = Depends(exiger_roles(Role.ADMINISTRATEUR))):
    d = _demande_en_attente(session, demande_id)
    d.statut = "rejetee"
    d.traitee_par = admin.id
    d.traitee_le = datetime.now(timezone.utc)
    session.add(Journal(utilisateur_id=admin.id, action="reinitialisation_rejetee", entite="utilisateur",
                        entite_id=d.utilisateur_id, details={"demande_id": d.id}))
    session.commit()
    return ConfirmationOut(message="Demande rejetée.")
