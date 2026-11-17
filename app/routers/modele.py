"""Santé du modèle : rapports de suivi (stabilité, décisions, performance), réservés à l'administrateur."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.deps import exiger_roles
from app.models import Journal, RapportSuivi, Utilisateur
from app.models.enums import Role
from app.scoring import VERSION_MODELE
from src.registre import lire_fiche
from src.surveillance import (BAISSE_AUC_ORANGE, BAISSE_AUC_ROUGE, CALIBRATION_ORANGE,
                              CALIBRATION_ROUGE, DEROGATION_ORANGE, DEROGATION_ROUGE,
                              INCONNUES_ORANGE, INCONNUES_ROUGE, MIN_DEFAUTS_PERFORMANCE,
                              PSI_ORANGE, PSI_ROUGE, enregistrer_en_base, produire_rapport,
                              trimestre_ecoule)

router = APIRouter(prefix="/modele", tags=["modèle"])
ADMIN = exiger_roles(Role.ADMINISTRATEUR)

SEUILS = {
    "psi": [PSI_ORANGE, PSI_ROUGE], "modalites_inconnues": [INCONNUES_ORANGE, INCONNUES_ROUGE],
    "derogations": [DEROGATION_ORANGE, DEROGATION_ROUGE],
    "baisse_auc": [BAISSE_AUC_ORANGE, BAISSE_AUC_ROUGE],
    "calibration": [CALIBRATION_ORANGE, CALIBRATION_ROUGE],
    "min_defauts": MIN_DEFAUTS_PERFORMANCE,
}


def etat(session: Session) -> dict:
    rapports = session.scalars(select(RapportSuivi)
                               .order_by(RapportSuivi.produit_le.desc()).limit(12)).all()
    dernier = rapports[0] if rapports else None
    return {
        "version_en_service": VERSION_MODELE,
        "fiche": lire_fiche(VERSION_MODELE),
        "seuils": SEUILS,
        "dernier": None if dernier is None else {
            "id": dernier.id, "produit_le": dernier.produit_le,
            "automatique": dernier.produit_par is None, "contenu": dernier.contenu},
        "historique": [{"id": r.id, "debut": r.debut, "fin": r.fin, "niveau_global": r.niveau_global,
                        "version_modele": r.version_modele, "produit_le": r.produit_le}
                       for r in rapports],
    }


@router.get("/sante")
def lire_sante(session: Session = Depends(get_session), _: Utilisateur = Depends(ADMIN)):
    """Dernier rapport de suivi, historique des 12 derniers et fiche du modèle en service."""
    return etat(session)


@router.post("/sante", status_code=status.HTTP_201_CREATED)
def produire_sante(session: Session = Depends(get_session), utilisateur: Utilisateur = Depends(ADMIN)):
    """Produit tout de suite le rapport des trois derniers mois complets (sinon : le 1er du mois)."""
    debut, fin = trimestre_ecoule(date.today())
    try:
        rapport = produire_rapport(session, debut, fin)
    except Exception as erreur:          # données inattendues : message lisible pour l'administrateur
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            f"Le rapport n'a pas pu être produit : {erreur}")
    enregistre = enregistrer_en_base(session, rapport, utilisateur.id)
    session.add(Journal(utilisateur_id=utilisateur.id, action="suivi_modele_produit",
                        entite="rapport_suivi", entite_id=enregistre.id,
                        details={"niveau": rapport["niveau_global"]}))
    session.commit()
    return etat(session)
