import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import utilisateur_courant
from app.models import Utilisateur
from app.schemas import Jeton, UtilisateurOut
from app.security import creer_jeton, verifier_mot_de_passe

router = APIRouter(prefix="/auth", tags=["authentification"])

MAX_ECHECS = 5
DUREE_VERROUILLAGE = timedelta(minutes=15)
MESSAGE_VERROUILLE = ("Trop de tentatives échouées. Réessayez dans 15 minutes "
                      "ou demandez la réinitialisation de votre mot de passe.")

# Comptes inexistants : même comportement que les vrais comptes (pour ne pas révéler lesquels existent).
# Compteur en mémoire, remis à zéro au redémarrage du serveur.
_INCONNUS: dict[str, deque] = defaultdict(deque)


def _inconnu_bloque(cle: str) -> bool:
    maintenant = time.monotonic()
    file = _INCONNUS[cle]
    while file and maintenant - file[0] > DUREE_VERROUILLAGE.total_seconds():
        file.popleft()
    return len(file) >= MAX_ECHECS


@router.post("/login", response_model=Jeton)
def connexion(formulaire: OAuth2PasswordRequestForm = Depends(),
              session: Session = Depends(get_session)):
    cle = formulaire.username.strip().lower()
    maintenant = datetime.now(timezone.utc)
    utilisateur = session.scalar(select(Utilisateur).where(func.lower(Utilisateur.email) == cle))

    if utilisateur is not None:
        if utilisateur.verrouille_jusqua and utilisateur.verrouille_jusqua > maintenant:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, MESSAGE_VERROUILLE)
    elif _inconnu_bloque(cle):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, MESSAGE_VERROUILLE)

    valide = (utilisateur is not None and utilisateur.actif
              and verifier_mot_de_passe(formulaire.password, utilisateur.mot_de_passe_hash))
    if not valide:
        if utilisateur is not None:
            utilisateur.echecs_connexion += 1
            if utilisateur.echecs_connexion >= MAX_ECHECS:
                utilisateur.verrouille_jusqua = maintenant + DUREE_VERROUILLAGE
                utilisateur.echecs_connexion = 0
            session.commit()
        else:
            _INCONNUS[cle].append(time.monotonic())
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants incorrects")

    utilisateur.echecs_connexion = 0
    utilisateur.verrouille_jusqua = None
    utilisateur.derniere_connexion = maintenant
    session.commit()
    return Jeton(access_token=creer_jeton(utilisateur.id, utilisateur.role.value))


@router.get("/me", response_model=UtilisateurOut)
def moi(utilisateur: Utilisateur = Depends(utilisateur_courant)):
    return utilisateur
