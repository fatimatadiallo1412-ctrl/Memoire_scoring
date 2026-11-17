"""Expérience d'optimisation sur Home Credit : validation croisée et recherche d'hyperparamètres.

Le modèle v4 a été réglé sur UNE séparation validation ; ici, chaque configuration est jugée par
validation croisée stratifiée à 5 blocs sur apprentissage + validation (80 % des données), ce qui
donne une moyenne ET un écart-type d'AUC. Le test (20 %, même graine que src/modeling.py) n'est
consulté qu'à la fin, pour la meilleure configuration de chaque variante.

Variantes comparées (même recherche d'hyperparamètres) :
  v4         contraintes croissantes sur les deux ratios et la durée (modèle en production)
  sans_duree durée retirée du modèle (variante A du notebook 03)
  libre      durée présente sans contrainte (comportement v3, en dents de scie)

Le modèle de production n'est PAS remplacé : le script écrit un rapport, la décision reste humaine.

    python -m src.experiences --essais 15        # ~30 min, à lancer en arrière-plan
"""
import argparse
import json
import time

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.modeling import CAT, CROISSANTES, DONNEES, NUM, PARAMS, RACINE, separer

ESPACE = {
    "max_depth": [3, 4, 5, 6],
    "min_child_weight": [1, 5, 10, 20, 50],
    "subsample": [0.6, 0.7, 0.8, 0.9, 1.0],
    "colsample_bytree": [0.5, 0.6, 0.7, 0.8, 1.0],
    "gamma": [0, 0.5, 1, 2],
    "reg_lambda": [1, 5, 10],
    "reg_alpha": [0, 0.5, 1],
}
VARIANTES = {
    "v4": (NUM, CROISSANTES),
    "sans_duree": ([c for c in NUM if c != "duree_implicite"],
                   [c for c in CROISSANTES if c != "duree_implicite"]),
    "libre": (NUM, [c for c in CROISSANTES if c != "duree_implicite"]),
}
TAUX = 0.05
MAX_ARBRES = 2000


def preparer(num, train):
    prep = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
    ])
    prep.fit(train[num + CAT])
    return prep


def contraintes(prep, croissantes):
    return "(" + ",".join(
        "1" if n.startswith("num__") and n[5:] in croissantes else "0"
        for n in prep.get_feature_names_out()) + ")"


def evaluer_cv(dtrain, params, graine=42) -> dict:
    res = xgb.cv(params, dtrain, num_boost_round=MAX_ARBRES, nfold=5, stratified=True,
                 early_stopping_rounds=50, metrics="auc", seed=graine, verbose_eval=False)
    return {"auc": float(res["test-auc-mean"].iloc[-1]),
            "ecart_type": float(res["test-auc-std"].iloc[-1]), "arbres": int(len(res))}


def tirer(rng) -> dict:
    return {k: v[int(rng.integers(len(v)))] for k, v in ESPACE.items()}


def main():
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--essais", type=int, default=15)
    args = parseur.parse_args()

    df = pd.read_parquet(DONNEES)
    train, val, test = separer(df)
    dev = pd.concat([train, val])
    rng = np.random.default_rng(42)

    # Configurations : celle de v4 (référence), puis des tirages aléatoires
    base = {k: PARAMS[k] for k in ("max_depth", "min_child_weight", "subsample", "colsample_bytree")}
    configs = [base | {"gamma": 0, "reg_lambda": 1, "reg_alpha": 0}]
    configs += [tirer(rng) for _ in range(args.essais)]

    journal = {"variantes": {}, "configs": configs}
    for nom, (num, croissantes) in VARIANTES.items():
        prep = preparer(num, dev)
        dtrain = xgb.DMatrix(prep.transform(dev[num + CAT]), label=dev["TARGET"])
        mono = contraintes(prep, croissantes)
        # Recherche complète pour v4 ; les autres variantes reprennent ses 5 meilleures configs
        essais = configs if nom == "v4" else [
            configs[i] for i in journal["variantes"]["v4"]["classement"][:5]]
        resultats = []
        for i, cfg in enumerate(essais):
            t = time.time()
            params = {"objective": "binary:logistic", "eta": TAUX, "tree_method": "hist",
                      "nthread": -1, "monotone_constraints": mono, **cfg}
            r = evaluer_cv(dtrain, params) | {"config": cfg}
            resultats.append(r)
            print(f"[{nom}] {i + 1}/{len(essais)} AUC {r['auc']:.4f} ± {r['ecart_type']:.4f} "
                  f"({r['arbres']} arbres, {time.time() - t:.0f} s) {cfg}", flush=True)
        ordre = sorted(range(len(resultats)), key=lambda i: -resultats[i]["auc"])
        meilleur = resultats[ordre[0]]

        # Test : une seule fois, meilleure configuration de la variante
        params = {"objective": "binary:logistic", "eta": TAUX, "tree_method": "hist",
                  "nthread": -1, "monotone_constraints": mono, **meilleur["config"]}
        booster = xgb.train(params, dtrain, num_boost_round=meilleur["arbres"])
        p = booster.predict(xgb.DMatrix(prep.transform(test[num + CAT])))
        journal["variantes"][nom] = {
            "resultats": resultats,
            "classement": [configs.index(resultats[i]["config"]) for i in ordre],
            "meilleure": meilleur, "auc_test": float(roc_auc_score(test["TARGET"], p)),
            "reference_v4_cv": resultats[0] if nom == "v4" else None,
        }
        print(f"[{nom}] meilleure CV {meilleur['auc']:.4f} · test {journal['variantes'][nom]['auc_test']:.4f}",
              flush=True)

    sortie = RACINE / "docs" / "suivi_modele" / "experience_hyperparametres.json"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(journal, indent=2, default=str), encoding="utf-8")
    print("Journal :", sortie)


if __name__ == "__main__":
    main()
