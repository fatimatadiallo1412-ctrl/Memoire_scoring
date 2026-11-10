import base64
import hashlib
import hmac
import json
import os
import time

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.deps import exiger_roles, get_session
from app.models import Journal, Utilisateur
from app.models.enums import Role

load_dotenv()

router = APIRouter(prefix="/tableau-de-bord", tags=["tableau de bord"])

DIRECTION = (Role.DECIDEUR, Role.ADMINISTRATEUR)
DUREE_LIEN_SECONDES = 600  # le lien signé expire après 10 minutes


class LienOut(BaseModel):
    url: str
    expire_dans_secondes: int


def _b64(donnees: bytes) -> str:
    return base64.urlsafe_b64encode(donnees).rstrip(b"=").decode()


def _signer(charge: dict, cle: str) -> str:
    """Jeton signé HS256 attendu par Metabase pour l'intégration « invités »."""
    entete = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    corps = _b64(json.dumps(charge, separators=(",", ":")).encode())
    signature = hmac.new(cle.encode(), f"{entete}.{corps}".encode(), hashlib.sha256).digest()
    return f"{entete}.{corps}.{_b64(signature)}"


@router.get("/lien", response_model=LienOut)
def lien_tableau_de_bord(
        session: Session = Depends(get_session),
        utilisateur: Utilisateur = Depends(exiger_roles(*DIRECTION))):
    """Adresse temporaire et signée du tableau de bord Metabase (direction uniquement)."""
    site = os.environ.get("METABASE_SITE_URL", "").rstrip("/")
    cle = os.environ.get("METABASE_SECRET_KEY", "")
    identifiant = os.environ.get("METABASE_DASHBOARD_ID", "")
    if not (site and cle and identifiant.isdigit()):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Le tableau de bord n'est pas encore configuré.")

    jeton = _signer({
        "resource": {"dashboard": int(identifiant)},
        "params": {},
        "exp": int(time.time()) + DUREE_LIEN_SECONDES,
    }, cle)

    session.add(Journal(utilisateur_id=utilisateur.id, action="tableau_bord_ouvert",
                        entite="tableau_de_bord", entite_id=int(identifiant), details={}))
    session.commit()
    return LienOut(url=f"{site}/embed/dashboard/{jeton}#bordered=false&titled=false",
                   expire_dans_secondes=DUREE_LIEN_SECONDES)
