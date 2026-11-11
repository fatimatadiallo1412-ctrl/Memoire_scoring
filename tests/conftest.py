"""Configuration commune des tests.

Les tests de règles métier n'ouvrent aucune connexion à la base de données.
Une clé de signature propre aux tests est imposée avant tout import de l'application :
la clé réelle du fichier .env n'est jamais utilisée (load_dotenv ne remplace pas une variable déjà définie).
"""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import date

import pytest
from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

os.environ["SECRET_KEY"] = "cle-de-test-uniquement-" + "x" * 40

# ---- Garde-fou : les tests ne doivent JAMAIS se connecter à la base de développement ----------
# Le nom de la base est remplacé AVANT tout import de l'application (app.db lit POSTGRES_DB).
load_dotenv(RACINE / ".env")
BASE_REELLE = os.environ.get("POSTGRES_DB")
BASE_TEST = os.environ.get("TEST_POSTGRES_DB")
BASE_TEST_VALIDE = bool(BASE_TEST) and BASE_TEST != BASE_REELLE and "test" in BASE_TEST.lower()
os.environ["POSTGRES_DB"] = BASE_TEST if BASE_TEST_VALIDE else "aucune_base_de_test_configuree"


@pytest.fixture
def client_type():
    """Une commerçante indépendante : profil de référence pour le modèle."""
    return SimpleNamespace(
        nb_enfants=3, taille_menage=6, date_naissance=date(1985, 5, 1), anciennete_activite_mois=60,
        type_revenu="independant", situation_familiale="marie", type_logement="locataire",
        profession="commercant", categorie_profession=None, possede_bien_immobilier=False,
        possede_vehicule=False, revenu_mensuel=150_000)


@pytest.fixture
def parametres():
    return {"seuil_defaut": 0.12, "facteur_prudence_antecedent": 0.8, "endettement_max": 0.40,
            "pas_montant": 50_000, "ratio_min": 0.5}
