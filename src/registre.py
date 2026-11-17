"""Registre des modèles : chaque version a son fichier .joblib et sa fiche .json dans models/.

La fiche documente la version : données, période, performances de référence, équité, validation.
Elle sert de référence au suivi (une baisse d'AUC se mesure par rapport à la fiche) et de
dossier pour l'autorité de supervision.
"""
import json
from datetime import date
from pathlib import Path

import joblib

from src.modeling import RACINE

DOSSIER = RACINE / "models"

# Fiche de la version en production, reprise de notebooks/03_modelisation.ipynb (échantillon de test)
FICHE_V4 = {
    "version": "xgb_home_credit_v4",
    "parent": None,
    "type": "XGBoost monotone (pipeline scikit-learn)",
    "donnees": "Home Credit Default Risk, 278 232 dossiers ; séparation stratifiée 60/20/20",
    "periode": None,
    "performances": {"AUC": 0.6423, "PR-AUC": 0.1389, "KS": 0.2032, "Brier": 0.0749,
                     "taux_defaut": 0.0835, "echantillon": "test Home Credit (55 647)"},
    "equite": {"au_dessus_15pc": {"F": 0.0532, "M": 0.1116}},
    "validation": "Choix sur la validation, test consulté une fois (notebook 03).",
    "cree_le": "2026-11-11",
}


def chemin_fiche(version: str) -> Path:
    return DOSSIER / f"{version}.json"


def lire_fiche(version: str) -> dict:
    chemin = chemin_fiche(version)
    if chemin.exists():
        return json.loads(chemin.read_text(encoding="utf-8"))
    if version == FICHE_V4["version"]:
        return FICHE_V4
    return {"version": version, "performances": {}}


def enregistrer(modele, fiche: dict) -> Path:
    """Enregistre le modèle et sa fiche. Refuse d'écraser une version existante."""
    version = fiche["version"]
    chemin = DOSSIER / f"{version}.joblib"
    if chemin.exists():
        raise FileExistsError(f"La version {version} existe déjà : choisir un autre nom.")
    fiche = {"cree_le": date.today().isoformat(), **fiche}
    joblib.dump(modele, chemin)
    chemin_fiche(version).write_text(json.dumps(fiche, ensure_ascii=False, indent=2, default=str),
                                     encoding="utf-8")
    return chemin


def charger(version: str):
    return joblib.load(DOSSIER / f"{version}.joblib")
