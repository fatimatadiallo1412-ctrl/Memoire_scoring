import os
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    return _hasher.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, empreinte: str) -> bool:
    try:
        return _hasher.verify(empreinte, mot_de_passe)
    except VerifyMismatchError:
        return False

load_dotenv()

CLE_SECRETE = os.environ["SECRET_KEY"]
ALGORITHME = "HS256"
DUREE_JETON_MINUTES = 480


def creer_jeton(utilisateur_id: int, role: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=DUREE_JETON_MINUTES)
    charge = {"sub": str(utilisateur_id), "role": role, "exp": expiration}
    return jwt.encode(charge, CLE_SECRETE, algorithm=ALGORITHME)


def decoder_jeton(jeton: str) -> dict:
    return jwt.decode(jeton, CLE_SECRETE, algorithms=[ALGORITHME])    