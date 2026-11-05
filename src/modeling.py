from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "data" / "processed" / "home_credit_features.parquet"
SORTIE = RACINE / "models" / "xgb_home_credit_v3.joblib"

NUM = ["CNT_CHILDREN", "CNT_FAM_MEMBERS", "age_ans", "anciennete_emploi_ans",
       "sans_emploi", "credit_sur_revenu", "annuite_sur_revenu", "duree_implicite"]
CAT = ["NAME_INCOME_TYPE", "NAME_FAMILY_STATUS", "NAME_HOUSING_TYPE",
       "OCCUPATION_TYPE", "FLAG_OWN_REALTY", "FLAG_OWN_CAR"]
COLONNES = NUM + CAT
CROISSANTES = ["credit_sur_revenu", "annuite_sur_revenu"]

PARAMS = dict(
    n_estimators=965, learning_rate=0.03, max_depth=5, min_child_weight=10,
    subsample=0.8, colsample_bytree=0.8, tree_method="hist",
    n_jobs=-1, random_state=42)


def separer(df):
    """Séparation stratifiée 60 / 20 / 20 (apprentissage, validation, test)."""
    reste, test = train_test_split(df, test_size=0.20, stratify=df["TARGET"], random_state=42)
    train, val = train_test_split(reste, test_size=0.25, stratify=reste["TARGET"], random_state=42)
    return train, val, test


def construire_pipeline(X_train):
    prep = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                          ("sc", StandardScaler())]), NUM),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
    ])
    noms = prep.fit(X_train[COLONNES]).get_feature_names_out()
    contraintes = tuple(
        1 if n.startswith("num__") and n[5:] in CROISSANTES else 0 for n in noms)
    return Pipeline([
        ("prep", prep),
        ("clf", XGBClassifier(monotone_constraints=contraintes, **PARAMS)),
    ])


def entrainer_et_sauver():
    df = pd.read_parquet(DONNEES)
    train, val, test = separer(df)

    modele = construire_pipeline(train)
    modele.fit(train[COLONNES], train["TARGET"])

    for nom, d in [("validation", val), ("test", test)]:
        p = modele.predict_proba(d[COLONNES])[:, 1]
        print(f"AUC {nom} : {roc_auc_score(d['TARGET'], p):.4f}")

    SORTIE.parent.mkdir(exist_ok=True)
    joblib.dump(modele, SORTIE)
    print("Modèle sauvegardé :", SORTIE)


if __name__ == "__main__":
    entrainer_et_sauver()