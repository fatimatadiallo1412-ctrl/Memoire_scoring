"""Compléments d'évaluation et d'équité du modèle en service, calculés sur la VALIDATION.

Le jeu de test n'est jamais ouvert ici. Sortie : docs/suivi_modele/audit_complements_validation.json

    python -m src.audit_complements

1. Mesures de validation du modèle en service (AUC, Gini, KS, Brier, PR-AUC).
2. Comparaison sur les 14 variables du modèle : régression logistique (par défaut, puis réglée sur C),
   XGBoost non réglé, XGBoost réglé (en service).
3. Équité aux seuils 12 % et 15 %, par sexe et par tranche d'âge : défaut observé et prévu,
   acceptation, égalité des chances (bons payeurs acceptés), acceptation des défaillants (FPR), AUC.
   IC bootstrap de l'écart d'AUC entre sexes.
4. Modèles sans âge et sans profession (mêmes réglages que v4) : AUC et équité.
5. Retrait de l'éducation (v2 -> v3) mesuré sur la validation.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from src.modeling import CAT, COLONNES, CROISSANTES, DONNEES, NUM, PARAMS, RACINE, separer

SORTIE = RACINE / "docs" / "suivi_modele" / "audit_complements_validation.json"
SEUILS = (0.12, 0.15)
B = 1000
RNG = np.random.default_rng(42)
TRANCHES = [0, 30, 40, 50, 60, 200]
NOMS_TRANCHES = ["< 30 ans", "30-39 ans", "40-49 ans", "50-59 ans", "60 ans et +"]


def mesures(y, p):
    fpr, tpr, _ = roc_curve(y, p)
    auc = roc_auc_score(y, p)
    return {"AUC": round(auc, 4), "Gini": round(2 * auc - 1, 4), "KS": round(float((tpr - fpr).max()), 4),
            "Brier": round(brier_score_loss(y, p), 5), "PR_AUC": round(average_precision_score(y, p), 4)}


def pipeline(num, cat, clf):
    prep = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat)])
    return Pipeline([("prep", prep), ("clf", clf)])


def xgb_contraint(train, num, cat, **params):
    prep = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat)])
    noms = prep.fit(train[num + cat]).get_feature_names_out()
    contraintes = tuple(1 if n.startswith("num__") and n[5:] in CROISSANTES else 0 for n in noms)
    m = Pipeline([("prep", prep), ("clf", XGBClassifier(monotone_constraints=contraintes, **params))])
    return m.fit(train[num + cat], train["TARGET"])


def wilson(k, n, z=1.96):
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h), 2), round(100 * (c + h), 2)


def taux(masque):
    k, n = int(masque.sum()), len(masque)
    return {"pct": round(100 * k / n, 2) if n else None, "IC95": wilson(k, n), "n": n}


def equite(d, groupe, seuils=SEUILS):
    """d : colonnes TARGET, p, et la colonne de groupe."""
    res = {}
    for g, x in d.groupby(groupe, observed=True):
        bloc = {"n": len(x), "defaut_observe_pct": round(100 * x.TARGET.mean(), 2),
                "defaut_prevu_pct": round(100 * x.p.mean(), 2),
                "AUC": round(roc_auc_score(x.TARGET, x.p), 4) if x.TARGET.nunique() == 2 else None}
        for s in seuils:
            bons, mauvais = x[x.TARGET == 0], x[x.TARGET == 1]
            bloc[f"seuil_{s:.2f}"] = {
                "acceptation": taux(x.p <= s),
                "egalite_chances_TPR": taux(bons.p <= s),       # bons payeurs acceptés
                "defaillants_acceptes_FPR": taux(mauvais.p <= s),
                "defaut_chez_acceptes_pct": round(100 * x.loc[x.p <= s, "TARGET"].mean(), 2)}
        res[str(g)] = bloc
    # Rapports au groupe le plus favorisé (le moins favorisé au numérateur)
    for s in seuils:
        cle = f"seuil_{s:.2f}"
        for indic in ("acceptation", "egalite_chances_TPR", "defaillants_acceptes_FPR"):
            # Groupes de moins de 100 dossiers (ex. « Academic degree ») : rapport non calculé
            valides = [g for g in res if res[g][cle][indic]["n"] >= 100]
            ref = max(valides, key=lambda g: res[g][cle][indic]["pct"])
            for g in res:
                res[g][cle][indic]["rapport_au_meilleur"] = (round(
                    res[g][cle][indic]["pct"] / res[ref][cle][indic]["pct"], 3) if g in valides else None)
                res[g][cle][indic]["groupe_reference"] = ref
    return res


def ecart_auc_sexes(d):
    f, m = d[d.CODE_GENDER == "F"], d[d.CODE_GENDER == "M"]
    obs = roc_auc_score(f.TARGET, f.p) - roc_auc_score(m.TARGET, m.p)
    fy, fp, my, mp = f.TARGET.to_numpy(), f.p.to_numpy(), m.TARGET.to_numpy(), m.p.to_numpy()
    ecarts = []
    for _ in range(B):
        i, j = RNG.integers(0, len(f), len(f)), RNG.integers(0, len(m), len(m))
        ecarts.append(roc_auc_score(fy[i], fp[i]) - roc_auc_score(my[j], mp[j]))
    lo, hi = np.percentile(ecarts, [2.5, 97.5])
    return {"AUC_F_moins_AUC_M": round(obs, 4), "IC95_bootstrap": [round(lo, 4), round(hi, 4)], "B": B}


def preparer(val, p):
    d = val[["TARGET", "CODE_GENDER", "age_ans"]].copy()
    d["p"] = p
    d["tranche_age"] = pd.cut(d.age_ans, TRANCHES, labels=NOMS_TRANCHES, right=False)
    return d


def bloc_equite(val, p):
    d = preparer(val, p)
    ds = d[d.CODE_GENDER.isin(["F", "M"])]
    return {"sexe": equite(ds, "CODE_GENDER"), "age": equite(d, "tranche_age"),
            "ecart_auc_sexes": ecart_auc_sexes(ds)}


def main():
    df = pd.read_parquet(DONNEES)
    train, val, _ = separer(df)                 # le test n'est jamais utilisé ici
    y_val = val["TARGET"]
    sortie = {"jeu": "validation Home Credit (55 647 dossiers, 20 %, graine 42)", "test_ouvert": False}

    # ---- 1. Modèle en service ----------------------------------------------------------------
    v4 = joblib.load(RACINE / "models" / "xgb_home_credit_v4.joblib")
    p_v4 = v4.predict_proba(val[COLONNES])[:, 1]
    sortie["modele_en_service"] = {"fichier": "models/xgb_home_credit_v4.joblib", **mesures(y_val, p_v4)}
    print("v4 validation", sortie["modele_en_service"])

    # ---- 2. Comparaison sur les 14 variables du modèle -------------------------------------------
    comp = {}
    lr = pipeline(NUM, CAT, LogisticRegression(max_iter=2000)).fit(train[COLONNES], train.TARGET)
    comp["Régression logistique (C = 1, par défaut)"] = mesures(y_val, lr.predict_proba(val[COLONNES])[:, 1])
    grille = {}
    for c in [1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100]:
        for poids in [None, "balanced"]:
            m = pipeline(NUM, CAT, LogisticRegression(C=c, class_weight=poids, max_iter=2000))
            m.fit(train[COLONNES], train.TARGET)
            grille[f"C={c:g}, class_weight={poids}"] = round(
                roc_auc_score(y_val, m.predict_proba(val[COLONNES])[:, 1]), 4)
    meilleur = max(grille, key=grille.get)
    comp["Régression logistique réglée"] = {"AUC": grille[meilleur], "reglage": meilleur, "grille_AUC": grille}
    # Régression avec âge et ancienneté découpés en classes (pour capter le non-linéaire)
    num_lin = [c for c in NUM if c not in ("age_ans", "anciennete_emploi_ans")]
    val_b, train_b = val.copy(), train.copy()
    for d in (train_b, val_b):
        d["age_classe"] = pd.cut(d.age_ans, [0, 25, 30, 35, 40, 45, 50, 55, 60, 200], right=False).astype(str)
        d["anc_classe"] = pd.cut(d.anciennete_emploi_ans, [-1, 0.5, 1, 2, 3, 5, 8, 12, 100]).astype(str)
    cols_b = num_lin + CAT + ["age_classe", "anc_classe"]
    lr_b = pipeline(num_lin, CAT + ["age_classe", "anc_classe"],
                    LogisticRegression(max_iter=2000, C=float(meilleur.split(",")[0][2:])))
    lr_b.fit(train_b[cols_b], train_b.TARGET)
    comp["Régression logistique réglée + âge et ancienneté en classes"] = mesures(
        y_val, lr_b.predict_proba(val_b[cols_b])[:, 1])
    xgb_base = xgb_contraint(train, NUM, CAT, n_estimators=300, learning_rate=0.05, max_depth=3,
                             subsample=0.8, colsample_bytree=0.8, tree_method="hist", n_jobs=-1,
                             random_state=42)
    comp["XGBoost non réglé (300 arbres, profondeur 3, contraintes v4)"] = mesures(
        y_val, xgb_base.predict_proba(val[COLONNES])[:, 1])
    comp["XGBoost réglé (v4 en service : 551 arbres, profondeur 3, taux 0,03)"] = mesures(y_val, p_v4)
    sortie["comparaison_validation"] = comp
    for k, v in comp.items():
        print(k, v.get("AUC"))

    # ---- 3. Équité du modèle en service --------------------------------------------------------
    sortie["equite_v4"] = bloc_equite(val, p_v4)

    # ---- 4. Modèles sans âge, sans profession ----------------------------------------------------
    variantes = {}
    for nom, retire in [("sans âge", "age_ans"), ("sans profession", "OCCUPATION_TYPE")]:
        num = [c for c in NUM if c != retire]
        cat = [c for c in CAT if c != retire]
        m = xgb_contraint(train, num, cat, **PARAMS)
        p = m.predict_proba(val[num + cat])[:, 1]
        variantes[nom] = {"variable_retiree": retire, **mesures(y_val, p), "equite": bloc_equite(val, p)}
        print(nom, variantes[nom]["AUC"])
    sortie["variantes"] = variantes

    # ---- 5. Retrait de l'éducation : v2 (avec) contre v3 (sans), sur la validation ---------------
    edu = {}
    for v in (2, 3):
        m = joblib.load(RACINE / "models" / f"xgb_home_credit_v{v}.joblib")
        cols = list(m.named_steps["prep"].feature_names_in_)
        p = m.predict_proba(val[cols])[:, 1]
        d = val[["TARGET", "CODE_GENDER", "NAME_EDUCATION_TYPE"]].copy()
        d["p"] = p
        ds = d[d.CODE_GENDER.isin(["F", "M"])]
        edu[f"v{v}"] = {"AUC": round(roc_auc_score(y_val, p), 4),
                        "sexe": equite(ds, "CODE_GENDER"), "education": equite(d, "NAME_EDUCATION_TYPE")}
    sortie["retrait_education"] = edu

    SORTIE.write_text(json.dumps(sortie, ensure_ascii=False, indent=1, default=float))
    print("Écrit :", SORTIE)


if __name__ == "__main__":
    main()
