from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import utilisateur_courant
from app.models import Utilisateur
from app.schemas import Jeton, UtilisateurOut
from app.security import creer_jeton, verifier_mot_de_passe

router = APIRouter(prefix="/auth", tags=["authentification"])


@router.post("/login", response_model=Jeton)
def connexion(formulaire: OAuth2PasswordRequestForm = Depends(),
              session: Session = Depends(get_session)):
    utilisateur = session.scalar(
        select(Utilisateur).where(Utilisateur.email == formulaire.username))
    if (utilisateur is None or not utilisateur.actif
            or not verifier_mot_de_passe(formulaire.password, utilisateur.mot_de_passe_hash)):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants incorrects")
    utilisateur.derniere_connexion = datetime.now(timezone.utc)
    session.commit()
    return Jeton(access_token=creer_jeton(utilisateur.id, utilisateur.role.value))


@router.get("/me", response_model=UtilisateurOut)
def moi(utilisateur: Utilisateur = Depends(utilisateur_courant)):
    return utilisateur