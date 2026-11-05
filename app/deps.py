import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Utilisateur
from app.models.enums import Role
from app.security import decoder_jeton

schema_oauth = OAuth2PasswordBearer(tokenUrl="/auth/login")


def utilisateur_courant(
    jeton: str = Depends(schema_oauth),
    session: Session = Depends(get_session),
) -> Utilisateur:
    erreur = HTTPException(status.HTTP_401_UNAUTHORIZED, "Jeton invalide ou expiré",
                           headers={"WWW-Authenticate": "Bearer"})
    try:
        utilisateur_id = int(decoder_jeton(jeton)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise erreur
    utilisateur = session.get(Utilisateur, utilisateur_id)
    if utilisateur is None or not utilisateur.actif:
        raise erreur
    return utilisateur


def exiger_roles(*roles: Role):
    """Fabrique une dépendance qui n'accepte que les rôles indiqués."""
    def verification(utilisateur: Utilisateur = Depends(utilisateur_courant)) -> Utilisateur:
        if utilisateur.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé pour ce rôle")
        return utilisateur
    return verification