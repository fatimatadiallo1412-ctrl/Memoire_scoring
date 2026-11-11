"""Propriétés du modèle réellement utilisé par l'application (v4) et de son explication."""
from datetime import date
from types import SimpleNamespace

import numpy as np
import pytest
import xgboost as xgb

from app.explication import contributions
from app.scoring import charger_modele, evaluer_montant, profil_client, seuil_applicable
from src.modeling import COLONNES
from src.suggestion import construire_ligne, probabilite_defaut

DEMANDE = SimpleNamespace(date_demande=date(2026, 11, 1), duree_mois=12, montant_demande=500_000)
PRODUIT = SimpleNamespace(taux_annuel=24.0)


@pytest.fixture(scope="module")
def modele():
    return charger_modele()


# ---- Règles de politique, sans modèle -------------------------------------------------------

def test_seuil_resserre_apres_un_incident_regularise(parametres):
    assert seuil_applicable(parametres) == 0.12
    assert seuil_applicable(parametres, "regularise") == pytest.approx(0.096)


def test_profil_retraite_sans_activite(client_type):
    client_type.type_revenu = "retraite"
    profil = profil_client(client_type, date(2026, 11, 1))
    assert profil["sans_emploi"] == 1 and profil["anciennete_emploi_ans"] == 0
    assert profil["NAME_INCOME_TYPE"] == "Pensioner"


def test_profil_plafonne_et_traduit(client_type):
    client_type.nb_enfants, client_type.taille_menage = 12, 20
    profil = profil_client(client_type, date(2026, 11, 1))
    assert profil["CNT_CHILDREN"] == 5 and profil["CNT_FAM_MEMBERS"] == 8
    assert profil["anciennete_emploi_ans"] == 5
    assert profil["OCCUPATION_TYPE"] == "Sales staff"
    assert 41 < profil["age_ans"] < 42


# ---- Propriétés du modèle --------------------------------------------------------------------

def test_le_risque_croit_avec_le_montant(modele, client_type):
    """Contrainte de monotonie : à durée fixe, emprunter plus ne peut pas réduire le risque."""
    profil = profil_client(client_type, DEMANDE.date_demande)
    risques = [probabilite_defaut(modele, profil, m, 12, 150_000, COLONNES, 0.24)
               for m in range(100_000, 3_000_001, 100_000)]
    assert all(b >= a - 1e-9 for a, b in zip(risques, risques[1:]))


def test_a_mensualite_egale_le_risque_croit_avec_la_duree(modele, client_type):
    """Correction v4 : plus de profil en dents de scie selon la durée."""
    profil = profil_client(client_type, DEMANDE.date_demande)
    r, risques = 0.24 / 12, []
    for d in [3, 6, 9, 12, 18, 24, 36, 60]:
        montant = 30_000 * (1 - (1 + r) ** -d) / r       # mensualité fixée à 30 000 FCFA
        risques.append(probabilite_defaut(modele, profil, montant, d, 150_000, COLONNES, 0.24))
    assert all(b >= a - 1e-9 for a, b in zip(risques, risques[1:]))


def test_probabilites_dans_une_plage_realiste(modele, client_type):
    profil = profil_client(client_type, DEMANDE.date_demande)
    p = probabilite_defaut(modele, profil, 500_000, 12, 150_000, COLONNES, 0.24)
    assert 0.01 < p < 0.5


# ---- Évaluation d'un accord modifié -----------------------------------------------------------

def test_evaluer_montant_dans_la_politique(client_type, parametres):
    r = evaluer_montant(client_type, DEMANDE, PRODUIT, parametres, 100_000, 12)
    assert r["mensualite"] == 9_456
    assert r["endettement"] == pytest.approx(9_456 / 150_000, abs=1e-3)
    assert r["dans_politique"] == (r["p_defaut"] <= parametres["seuil_defaut"])


def test_evaluer_montant_hors_politique(client_type, parametres):
    r = evaluer_montant(client_type, DEMANDE, PRODUIT, parametres, 3_000_000, 12)
    assert not r["dans_politique"] and "endettement" in r["motifs"]


def test_antecedent_en_cours_toujours_hors_politique(client_type, parametres):
    r = evaluer_montant(client_type, DEMANDE, PRODUIT, parametres, 50_000, 12, antecedent="en_cours")
    assert "antecedent_en_cours" in r["motifs"] and not r["dans_politique"]


# ---- Explication (valeurs de Shapley) --------------------------------------------------------

def test_explication_additive(modele, client_type):
    """Somme des contributions + valeur de base = score du modèle (en log-odds)."""
    profil = profil_client(client_type, DEMANDE.date_demande)
    ligne = construire_ligne(profil, 500_000, 12, 150_000, COLONNES, 0.24)
    toutes = contributions(modele, ligne, DEMANDE, nombre=1000)
    base = modele.named_steps["clf"].get_booster().predict(
        xgb.DMatrix(modele.named_steps["prep"].transform(ligne)), pred_contribs=True)[0][-1]
    p = modele.predict_proba(ligne)[0, 1]
    assert sum(c["contribution"] for c in toutes) + base == pytest.approx(np.log(p / (1 - p)), abs=1e-2)


def test_explication_regroupee_et_lisible(modele, client_type):
    profil = profil_client(client_type, DEMANDE.date_demande)
    ligne = construire_ligne(profil, 500_000, 12, 150_000, COLONNES, 0.24)
    top = contributions(modele, ligne, DEMANDE)
    assert len(top) == 6
    variables = [c["variable"] for c in top]
    assert len(set(variables)) == 6 and all(v in COLONNES for v in variables)    # une ligne par variable
    forces = [abs(c["contribution"]) for c in top]
    assert forces == sorted(forces, reverse=True)
    assert all(c["libelle"] != c["variable"] for c in top)                        # libellés en français


def test_seuil_par_defaut_de_l_application():
    """Seuil de démonstration retenu : 12 % (voir le rapport d'audit, section 11)."""
    from app.parametres import PARAMETRES_DEFAUT
    from src.suggestion import SEUIL_DEFAUT
    assert PARAMETRES_DEFAUT["seuil_defaut"][0] == SEUIL_DEFAUT == 0.12
