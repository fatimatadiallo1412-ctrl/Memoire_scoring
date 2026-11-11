import secrets
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.validation import valider_gmail
from app.db import get_session
from app.deps import exiger_roles, utilisateur_courant
from app.models import Agence, Client, Journal, Utilisateur
from app.models.enums import Role
from app.security import hasher_mot_de_passe, verifier_mot_de_passe

router = APIRouter(prefix="/comptes", tags=["comptes"])
router_mdp = APIRouter(prefix="/auth", tags=["authentification"])

# Sans caractères ambigus (0/O, 1/l/I) pour qu'on puisse le dicter ou le lire sans erreur.
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"


def _mot_de_passe_temporaire() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(10))


def _verifier_email(valeur: str) -> str:
    return valider_gmail(valeur)


class CompteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom_complet: str
    role: Role
    actif: bool
    agence_id: int | None
    client_id: int | None
    derniere_connexion: datetime | None
    cree_le: datetime
    doit_changer_mdp: bool


class CompteCreeOut(CompteOut):
    mot_de_passe_temporaire: str  # affiché une seule fois, jamais stocké en clair ni journalisé


class MotDePasseTemporaireOut(BaseModel):
    email: str
    mot_de_passe_temporaire: str


class CompteIn(BaseModel):
    email: str = Field(max_length=255)
    nom_complet: str = Field(min_length=2, max_length=150)
    role: Literal["agent_credit", "decideur"]  # jamais « administrateur » ni « client » ici
    agence_id: int | None = None

    _email = field_validator("email")(lambda cls, v: _verifier_email(v))

    @field_validator("nom_complet", mode="before")
    @classmethod
    def nettoyer(cls, valeur):
        return valeur.strip() if isinstance(valeur, str) else valeur


class CompteClientIn(BaseModel):
    client_id: int
    email: str = Field(max_length=255)

    _email = field_validator("email")(lambda cls, v: _verifier_email(v))


class ActivationIn(BaseModel):
    actif: bool


class MotDePasseIn(BaseModel):
    ancien: str
    nouveau: str = Field(min_length=8, max_length=128)


def _avec_mot_de_passe(compte: Utilisateur, mot_de_passe: str) -> CompteCreeOut:
    return CompteCreeOut(**CompteOut.model_validate(compte).model_dump(),
                         mot_de_passe_temporaire=mot_de_passe)


def _email_libre(session: Session, email: str) -> None:
    if session.scalar(select(Utilisateur).where(func.lower(Utilisateur.email) == email)):
        raise HTTPException(409, "Cet e-mail est déjà utilisé.")


@router.get("", response_model=list[CompteOut])
def lister_comptes(
        role: Role | None = None,
        q: str | None = Query(None, min_length=2, max_length=100),
        limite: int = Query(100, ge=1, le=300),
        session: Session = Depends(get_session),
        _=Depends(exiger_roles(Role.ADMINISTRATEUR))):
    requete = select(Utilisateur).order_by(Utilisateur.role, Utilisateur.nom_complet)
    if role is not None:
        requete = requete.where(Utilisateur.role == role)
    if q:
        motif = f"%{q.strip().lower()}%"
        requete = requete.where(func.lower(Utilisateur.nom_complet).like(motif)
                                | func.lower(Utilisateur.email).like(motif))
    return session.scalars(requete.limit(limite)).all()


@router.post("", response_model=CompteCreeOut, status_code=201)
def creer_compte_personnel(
        donnees: CompteIn,
        session: Session = Depends(get_session),
        admin: Utilisateur = Depends(exiger_roles(Role.ADMINISTRATEUR))):
    _email_libre(session, donnees.email)
    if donnees.role == "agent_credit" and donnees.agence_id is None:
        raise HTTPException(422, "Une agence est obligatoire pour un agent de crédit.")
    if donnees.agence_id is not None and session.get(Agence, donnees.agence_id) is None:
        raise HTTPException(404, "Agence introuvable.")
    mot_de_passe = _mot_de_passe_temporaire()
    compte = Utilisateur(
        email=donnees.email, nom_complet=donnees.nom_complet,
        mot_de_passe_hash=hasher_mot_de_passe(mot_de_passe),
        role=Role(donnees.role), agence_id=donnees.agence_id, doit_changer_mdp=True)
    session.add(compte)
    session.flush()
    session.add(Journal(utilisateur_id=admin.id, action="compte_cree", entite="utilisateur",
                        entite_id=compte.id, details={"role": donnees.role, "email": donnees.email}))
    session.commit()
    session.refresh(compte)
    return _avec_mot_de_passe(compte, mot_de_passe)


@router.post("/client", response_model=CompteCreeOut, status_code=201)
def creer_compte_client(
        donnees: CompteClientIn,
        session: Session = Depends(get_session),
        agent: Utilisateur = Depends(exiger_roles(Role.AGENT_CREDIT))):
    """L'agent ouvre l'accès « espace client » d'un client de SON portefeuille."""
    client = session.get(Client, donnees.client_id)
    if client is None or client.gestionnaire_id != agent.id:
        raise HTTPException(404, "Client introuvable.")
    if session.scalar(select(Utilisateur).where(Utilisateur.client_id == client.id)):
        raise HTTPException(409, "Ce client a déjà un compte.")
    _email_libre(session, donnees.email)
    mot_de_passe = _mot_de_passe_temporaire()
    compte = Utilisateur(
        email=donnees.email, nom_complet=f"{client.prenom} {client.nom}",
        mot_de_passe_hash=hasher_mot_de_passe(mot_de_passe),
        role=Role.CLIENT, client_id=client.id, doit_changer_mdp=True)
    session.add(compte)
    session.flush()
    session.add(Journal(utilisateur_id=agent.id, action="compte_client_cree", entite="utilisateur",
                        entite_id=compte.id, details={"client_id": client.id}))
    session.commit()
    session.refresh(compte)
    return _avec_mot_de_passe(compte, mot_de_passe)


@router.put("/{compte_id}/activation", response_model=CompteOut)
def changer_activation(
        compte_id: int, donnees: ActivationIn,
        session: Session = Depends(get_session),
        admin: Utilisateur = Depends(exiger_roles(Role.ADMINISTRATEUR))):
    cible = session.get(Utilisateur, compte_id)
    if cible is None:
        raise HTTPException(404, "Compte introuvable.")
    if cible.id == admin.id:
        raise HTTPException(400, "Vous ne pouvez pas modifier l'état de votre propre compte.")
    if cible.role == Role.ADMINISTRATEUR:
        raise HTTPException(400, "Le compte administrateur se remplace avec le script prévu à cet effet.")
    if cible.actif != donnees.actif:
        cible.actif = donnees.actif
        session.add(Journal(utilisateur_id=admin.id,
                            action="compte_active" if donnees.actif else "compte_desactive",
                            entite="utilisateur", entite_id=cible.id, details={}))
        session.commit()
        session.refresh(cible)
    return cible


@router.post("/{compte_id}/reinitialiser", response_model=MotDePasseTemporaireOut)
def reinitialiser_mot_de_passe(
        compte_id: int,
        session: Session = Depends(get_session),
        admin: Utilisateur = Depends(exiger_roles(Role.ADMINISTRATEUR))):
    """Nouveau mot de passe temporaire, à communiquer à la personne après vérification de son identité."""
    cible = session.get(Utilisateur, compte_id)
    if cible is None:
        raise HTTPException(404, "Compte introuvable.")
    if cible.id == admin.id:
        raise HTTPException(400, "Utilisez « Changer mon mot de passe » pour votre propre compte.")
    mot_de_passe = _mot_de_passe_temporaire()
    cible.mot_de_passe_hash = hasher_mot_de_passe(mot_de_passe)
    cible.doit_changer_mdp = True
    cible.echecs_connexion = 0
    cible.verrouille_jusqua = None
    session.add(Journal(utilisateur_id=admin.id, action="mot_de_passe_reinitialise",
                        entite="utilisateur", entite_id=cible.id, details={}))
    session.commit()
    return MotDePasseTemporaireOut(email=cible.email, mot_de_passe_temporaire=mot_de_passe)


@router_mdp.post("/mot-de-passe", status_code=204, response_class=Response)
def changer_mon_mot_de_passe(
        donnees: MotDePasseIn,
        session: Session = Depends(get_session),
        utilisateur: Utilisateur = Depends(utilisateur_courant)):
    if not verifier_mot_de_passe(donnees.ancien, utilisateur.mot_de_passe_hash):
        raise HTTPException(400, "Le mot de passe actuel est incorrect.")
    if donnees.nouveau == donnees.ancien:
        raise HTTPException(400, "Le nouveau mot de passe doit être différent de l'ancien.")
    utilisateur.mot_de_passe_hash = hasher_mot_de_passe(donnees.nouveau)
    utilisateur.doit_changer_mdp = False
    session.add(Journal(utilisateur_id=utilisateur.id, action="mot_de_passe_change",
                        entite="utilisateur", entite_id=utilisateur.id, details={}))
    session.commit()
    return Response(status_code=204)
