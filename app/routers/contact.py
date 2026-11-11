import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.validation import valider_gmail
from app.db import get_session
from app.deps import exiger_roles
from app.models.contact import MessageContact
from app.models.enums import Role

router = APIRouter(prefix="/contact", tags=["contact"])

# Limite simple, en mémoire : au plus 5 messages par heure et par adresse.
# Elle repart de zéro au redémarrage du serveur (limite assumée, voir le mémoire).
FENETRE_SECONDES = 3600
MAX_MESSAGES = 5
_ENVOIS: dict[str, deque] = defaultdict(deque)



def _verifier_limite(adresse: str) -> None:
    maintenant = time.monotonic()
    file = _ENVOIS[adresse]
    while file and maintenant - file[0] > FENETRE_SECONDES:
        file.popleft()
    if len(file) >= MAX_MESSAGES:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de messages envoyés. Réessayez dans une heure.",
        )
    file.append(maintenant)


class ContactIn(BaseModel):
    nom: str = Field(min_length=2, max_length=100)
    email: str = Field(max_length=200)
    objet: str | None = Field(default=None, max_length=150)
    message: str = Field(min_length=10, max_length=2000)
    site_web: str = Field(default="", max_length=200)  # piège anti-robots : doit rester vide

    @field_validator("nom", "objet", "message", mode="before")
    @classmethod
    def nettoyer(cls, valeur):
        return valeur.strip() if isinstance(valeur, str) else valeur

    @field_validator("email")
    @classmethod
    def verifier_email(cls, valeur: str) -> str:
        return valider_gmail(valeur)


class ConfirmationOut(BaseModel):
    message: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    email: str
    objet: str | None
    message: str
    cree_le: datetime
    traite: bool
    traite_le: datetime | None


@router.post("", response_model=ConfirmationOut, status_code=status.HTTP_201_CREATED)
def envoyer_message(
    donnees: ContactIn,
    requete: Request,
    session: Session = Depends(get_session),
):
    """Route publique (sans connexion) du formulaire « Contactez-nous »."""
    confirmation = ConfirmationOut(message="Merci, votre message a bien été transmis.")
    if donnees.site_web:
        return confirmation  # un robot a rempli le champ caché : on ignore sans le dire
    _verifier_limite(requete.client.host if requete.client else "inconnu")
    session.add(MessageContact(
        nom=donnees.nom,
        email=donnees.email,
        objet=donnees.objet or None,
        message=donnees.message,
    ))
    session.commit()
    return confirmation


@router.get("/messages", response_model=list[MessageOut])
def lister_messages(
    traite: bool | None = None,
    limite: int = Query(50, ge=1, le=200),
    decalage: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    _=Depends(exiger_roles(Role.ADMINISTRATEUR)),
):
    requete = select(MessageContact).order_by(MessageContact.id.desc())
    if traite is not None:
        requete = requete.where(MessageContact.traite.is_(traite))
    return session.scalars(requete.limit(limite).offset(decalage)).all()


@router.post("/messages/{message_id}/traite", response_model=MessageOut)
def marquer_traite(
    message_id: int,
    session: Session = Depends(get_session),
    utilisateur=Depends(exiger_roles(Role.ADMINISTRATEUR)),
):
    message = session.get(MessageContact, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message introuvable.")
    if not message.traite:
        message.traite = True
        message.traite_par = utilisateur.id
        message.traite_le = datetime.now(timezone.utc)
        session.commit()
        session.refresh(message)
    return message
