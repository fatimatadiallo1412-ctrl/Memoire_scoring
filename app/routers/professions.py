from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from app import referentiels as R
from app.db import get_session
from app.deps import exiger_roles
from app.models import Client, DemandeCredit, Journal, Metier, Utilisateur
from app.models.enums import Role
from app.routers.clients import STATUTS_OUVERTS

router = APIRouter(prefix="/professions", tags=["professions"])

PERSONNEL = (Role.AGENT_CREDIT, Role.DECIDEUR, Role.ADMINISTRATEUR)
RESPONSABLES = (Role.DECIDEUR, Role.ADMINISTRATEUR)

# Catégories de métiers que le modèle connaît (celles déjà utilisées par le référentiel)
CATEGORIES = sorted(set(R.PROFESSION.values()))


class MetierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    libelle: str
    categorie_modele: str | None
    valide: bool


class AClasserOut(BaseModel):
    code: str
    libelle: str
    nb_clients: int


class ClassementIn(BaseModel):
    categorie_modele: str
    libelle: str | None = Field(default=None, min_length=2, max_length=100)


@router.get("", response_model=list[MetierOut])
def lister_metiers(session: Session = Depends(get_session),
                   utilisateur: Utilisateur = Depends(exiger_roles(*PERSONNEL))):
    """Suggestions pour le champ « profession » (un métier absent peut aussi être saisi librement)."""
    requete = select(Metier).where(Metier.actif.is_(True)).order_by(Metier.libelle)
    return session.scalars(requete).all()


@router.get("/categories", response_model=list[str])
def lister_categories(utilisateur: Utilisateur = Depends(exiger_roles(*RESPONSABLES))):
    return CATEGORIES


@router.get("/a-classer", response_model=list[AClasserOut])
def metiers_a_classer(session: Session = Depends(get_session),
                      utilisateur: Utilisateur = Depends(exiger_roles(*RESPONSABLES))):
    """Métiers saisis librement et pas encore rattachés à une catégorie du modèle."""
    lignes = session.execute(
        select(Metier, func.count(Client.id))
        .outerjoin(Client, Client.profession == Metier.code)
        .where(Metier.categorie_modele.is_(None), Metier.actif.is_(True))
        .group_by(Metier.id).order_by(Metier.libelle)).all()
    return [AClasserOut(code=m.code, libelle=m.libelle, nb_clients=n) for m, n in lignes]


@router.put("/{code}", response_model=MetierOut)
def classer_metier(code: str, donnees: ClassementIn, session: Session = Depends(get_session),
                   utilisateur: Utilisateur = Depends(exiger_roles(*RESPONSABLES))):
    """Rattache un métier à une catégorie du modèle et met à jour les clients concernés."""
    metier = session.scalar(select(Metier).where(Metier.code == code))
    if metier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Métier introuvable")
    if donnees.categorie_modele not in CATEGORIES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Catégorie inconnue. Choix possibles : " + ", ".join(CATEGORIES))

    ancienne = metier.categorie_modele
    metier.categorie_modele = donnees.categorie_modele
    metier.valide = True
    if donnees.libelle:
        metier.libelle = donnees.libelle.strip()

    session.execute(update(Client).where(Client.profession == code)
                    .values(categorie_profession=donnees.categorie_modele))
    if ancienne != donnees.categorie_modele:
        # Les scores des dossiers en cours de ces clients deviennent périmés
        concernes = select(Client.id).where(Client.profession == code)
        session.execute(
            update(DemandeCredit)
            .where(DemandeCredit.client_id.in_(concernes),
                   DemandeCredit.statut.in_(STATUTS_OUVERTS))
            .values(donnees_modifiees_le=text("now()")))

    session.add(Journal(utilisateur_id=utilisateur.id, action="metier_classe",
                        entite="metier", entite_id=metier.id,
                        details={"code": code, "ancienne": ancienne,
                                 "nouvelle": donnees.categorie_modele}))
    session.commit()
    session.refresh(metier)
    return metier
