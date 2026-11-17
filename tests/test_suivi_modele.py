"""Suivi et adaptation du modèle : PSI, recalibration, réentraînement, règle de promotion.
Aucune connexion à la base : les données locales sont simulées ici."""
from datetime import date

import joblib
import numpy as np
import pandas as pd
import pytest

from app.explication import contributions
from app.scoring import charger_modele, profil_client
from src.champion_challenger import comparer, verdict
from src.donnees_locales import fin_observation
from src.modeling import COLONNES
from src.recalibration import Calibrateur, PipelineRecalibre, continuer_entrainement, recalibrer
from src.suggestion import construire_ligne
from src.surveillance import (bruit_psi, comparer as comparer_psi, construire_reference,
                              modalites_inconnues, niveau, psi)


@pytest.fixture(scope="module")
def modele():
    return charger_modele()


@pytest.fixture(scope="module")
def locaux(modele):
    """400 crédits fictifs : profils tirés au hasard, défaut tiré selon 1,5 × le risque du modèle
    (population plus risquée que Home Credit, ce qu'une recalibration doit corriger)."""
    rng = np.random.default_rng(0)
    lignes = []
    for i in range(400):
        profil = {"CNT_CHILDREN": int(rng.integers(0, 5)), "CNT_FAM_MEMBERS": int(rng.integers(1, 8)),
                  "age_ans": float(rng.uniform(20, 65)), "anciennete_emploi_ans": float(rng.uniform(0, 20)),
                  "sans_emploi": 0, "NAME_INCOME_TYPE": rng.choice(["Working", "Commercial associate"]),
                  "NAME_FAMILY_STATUS": "Married", "NAME_HOUSING_TYPE": "House / apartment",
                  "OCCUPATION_TYPE": rng.choice(["Sales staff", "Laborers", "Drivers"]),
                  "FLAG_OWN_REALTY": "N", "FLAG_OWN_CAR": "N"}
        ligne = construire_ligne(profil, int(rng.integers(1, 20)) * 50_000, 12, 150_000, COLONNES, 0.24)
        lignes.append(ligne.iloc[0].to_dict())
    df = pd.DataFrame(lignes)
    p = modele.predict_proba(df[COLONNES])[:, 1]
    df["defaut"] = (rng.random(len(df)) < np.clip(1.5 * p, 0, 1)).astype(int)
    df["sexe"] = rng.choice(["F", "M"], len(df))
    df["date_decaissement"] = pd.date_range("2025-01-01", periods=len(df), freq="D").date
    return df


# ---- PSI -------------------------------------------------------------------------------------

def test_psi_nul_pour_deux_repartitions_identiques():
    assert psi([0.2, 0.3, 0.5], [0.2, 0.3, 0.5]) == pytest.approx(0)
    assert psi([0.5, 0.5], [0.9, 0.1]) > 0.25


def test_niveaux_d_alerte():
    assert niveau(0.05, 0.10, 0.25) == "vert"
    assert niveau(0.12, 0.10, 0.25) == "orange"
    assert niveau(0.30, 0.10, 0.25) == "rouge"


def test_bruit_psi_diminue_avec_le_volume():
    assert bruit_psi(10, 500, 130) > 0.08 > bruit_psi(10, 5000, 5000)


def test_une_derive_d_age_est_detectee_et_pas_le_hasard(locaux, modele):
    p = modele.predict_proba(locaux[COLONNES])[:, 1]
    ref = construire_reference(locaux.iloc[:200], p[:200], "test")
    meme = comparer_psi(ref, locaux.iloc[200:], p[200:])
    assert meme["exces"]["age_ans"] < 0.10                     # même population : pas d'alerte
    vieillie = locaux.iloc[200:].copy()
    vieillie["age_ans"] += 15
    assert comparer_psi(ref, vieillie, p[200:])["exces"]["age_ans"] >= 0.25


def test_modalite_inconnue_comptee(locaux, modele):
    X = locaux[COLONNES].copy()
    X.loc[X.index[:40], "OCCUPATION_TYPE"] = "Vendeur de crédit téléphonique"
    res = modalites_inconnues(modele, X)
    assert res["part_dossiers"] == pytest.approx(0.10)
    assert "OCCUPATION_TYPE" in res["exemples"]


# ---- Recalibration ---------------------------------------------------------------------------

@pytest.mark.parametrize("methode", ["decalage", "platt", "isotonique"])
def test_recalibration_croissante_et_au_bon_niveau(locaux, modele, methode):
    y = locaux["defaut"]
    m = recalibrer(modele, locaux, y, methode)
    brut = modele.predict_proba(locaux[COLONNES])[:, 1]
    p = m.predict_proba(locaux[COLONNES])[:, 1]
    ordre = np.argsort(brut)
    assert np.all(np.diff(p[ordre]) >= -1e-12)                   # le classement est conservé
    assert abs(p.mean() - y.mean()) < abs(brut.mean() - y.mean())  # niveau corrigé


def test_choix_automatique_de_la_methode():
    rng = np.random.default_rng(1)
    p = rng.uniform(0.01, 0.3, 3000)
    for n_defauts, attendu in [(10, "decalage"), (80, "platt"), (300, "isotonique")]:
        y = np.zeros(3000, dtype=int)
        y[np.argsort(-p)[:n_defauts]] = 1
        assert Calibrateur().fit(p, y).methode_ == attendu


def test_modele_recalibre_sauvegardable_et_explicable(locaux, modele, tmp_path, client_type):
    m = recalibrer(modele, locaux, locaux["defaut"])
    joblib.dump(m, tmp_path / "m.joblib")
    recharge = joblib.load(tmp_path / "m.joblib")
    assert isinstance(recharge, PipelineRecalibre)
    ligne = construire_ligne(profil_client(client_type, date(2026, 11, 1)),
                             500_000, 12, 150_000, COLONNES, 0.24)
    assert recharge.predict_proba(ligne)[0, 1] == pytest.approx(m.predict_proba(ligne)[0, 1])
    assert len(contributions(recharge, ligne)) == 6               # SHAP fonctionne toujours


def test_reentrainement_ajoute_des_arbres_et_garde_la_monotonie(locaux, modele, client_type):
    m = continuer_entrainement(modele, locaux, locaux["defaut"], n_arbres=20)
    avant = modele.named_steps["clf"].get_booster().num_boosted_rounds()
    assert m.named_steps["clf"].get_booster().num_boosted_rounds() == avant + 20
    profil = profil_client(client_type, date(2026, 11, 1))
    risques = [m.predict_proba(construire_ligne(profil, mt, 12, 150_000, COLONNES, 0.24))[0, 1]
               for mt in range(100_000, 2_000_001, 100_000)]
    assert all(b >= a - 1e-9 for a, b in zip(risques, risques[1:]))


# ---- Champion / challenger -------------------------------------------------------------------

def test_pas_de_promotion_sans_assez_de_defauts():
    champion = {"brier": 0.08, "auc": 0.65, "ecart_equite": 0.05, "n_defauts": 10}
    ok, raisons = verdict(champion, champion | {"brier": 0.05})
    assert not ok and "nécessaires" in raisons[0]


def test_promotion_bloquee_par_l_equite():
    champion = {"brier": 0.08, "auc": 0.65, "ecart_equite": 0.05, "n_defauts": 50}
    assert verdict(champion, champion | {"brier": 0.07})[0]
    assert not verdict(champion, champion | {"brier": 0.07, "ecart_equite": 0.10})[0]
    assert not verdict(champion, champion | {"brier": 0.07, "auc": 0.62})[0]


def test_comparaison_hors_periode(locaux, modele):
    c = comparer(locaux, modele, seuil=0.12)
    assert c["n_apprentissage"] + c["n_evaluation"] == len(locaux)
    assert {"champion", "recalibre"} <= set(c["resultats"])
    # Population 1,5 fois plus risquée : la recalibration rapproche le prévu de l'observé
    r, ch = c["resultats"]["recalibre"], c["resultats"]["champion"]
    assert abs(r["taux_prevu"] - r["taux_observe"]) < abs(ch["taux_prevu"] - ch["taux_observe"])


def test_fenetre_d_observation():
    assert fin_observation(date(2025, 1, 10), 6) == date(2025, 10, 8)     # 6 mois + 90 jours
    assert fin_observation(date(2025, 1, 10), 24) == date(2026, 4, 10)    # plafonnée à 12 mois
