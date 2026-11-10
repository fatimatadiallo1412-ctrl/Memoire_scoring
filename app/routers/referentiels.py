from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models.enums import Role
from app.models.ops import Agence, ProduitCredit

router = APIRouter(tags=["référentiels"])

PERSONNEL = (Role.AGENT_CREDIT, Role.DECIDEUR, Role.ADMINISTRATEUR)
COMMERCIAL = (Role.AGENT_CREDIT, Role.DECIDEUR)


class AgenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    nom: str
    zone: str


class ProduitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    libelle: str
    montant_min: int
    montant_max: int
    duree_min_mois: int
    duree_max_mois: int
    taux_annuel: float | None = None


@router.get("/agences", response_model=list[AgenceOut])
def lister_agences(
    session: Session = Depends(get_session),
    _=Depends(exiger_roles(*PERSONNEL)),
):
    """Agences actives, pour les listes déroulantes de l'interface."""
    requete = select(Agence).where(Agence.actif.is_(True)).order_by(Agence.nom)
    return session.scalars(requete).all()


@router.get("/produits", response_model=list[ProduitOut])
def lister_produits(
    session: Session = Depends(get_session),
    _=Depends(exiger_roles(*COMMERCIAL)),
):
    """Produits de crédit (montants et durées autorisés), pour le formulaire de demande."""
    requete = select(ProduitCredit).order_by(ProduitCredit.libelle)
    if hasattr(ProduitCredit, "actif"):
        requete = requete.where(ProduitCredit.actif.is_(True))
    return session.scalars(requete).all()
