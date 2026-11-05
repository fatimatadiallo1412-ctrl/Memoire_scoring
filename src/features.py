import numpy as np
import pandas as pd

PLAFOND_REVENU = 574_438      # 99,5e percentile observé (EDA)
PLAFOND_RATIO_CREDIT = 15     # 99,5e percentile de credit_sur_revenu (EDA)
PLAFOND_ENFANTS = 5
PLAFOND_FAMILLE = 8
SEUIL_RARE = 100              # modalités avec moins de 100 lignes -> "Autre"

CATEGORIELLES = [
    "NAME_INCOME_TYPE", "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE", "OCCUPATION_TYPE", "FLAG_OWN_REALTY", "FLAG_OWN_CAR",
]


def regrouper_rares(serie, seuil=SEUIL_RARE):
    effectifs = serie.value_counts()
    rares = effectifs[effectifs < seuil].index
    return serie.where(~serie.isin(rares), "Autre")


def construire_variables(df):
    df = df.copy()
    # 1. Plafonnement (aucune ligne supprimée)
    df["AMT_INCOME_TOTAL"] = df["AMT_INCOME_TOTAL"].clip(upper=PLAFOND_REVENU)
    df["CNT_CHILDREN"] = df["CNT_CHILDREN"].clip(upper=PLAFOND_ENFANTS)
    df["CNT_FAM_MEMBERS"] = df["CNT_FAM_MEMBERS"].clip(upper=PLAFOND_FAMILLE)
    # 2. Manquants structurels
    df["anciennete_emploi_ans"] = df["anciennete_emploi_ans"].fillna(0)
    df["OCCUPATION_TYPE"] = df["OCCUPATION_TYPE"].fillna("Non renseigné")
    # 3. Catégories rares
    for col in CATEGORIELLES:
        df[col] = regrouper_rares(df[col])
    # 4. Ratios sans unité (calculés APRÈS le plafonnement du revenu)
    df["credit_sur_revenu"] = (df["AMT_CREDIT"] / df["AMT_INCOME_TOTAL"]).clip(upper=PLAFOND_RATIO_CREDIT)
    df["annuite_sur_revenu"] = (df["AMT_ANNUITY"] / df["AMT_INCOME_TOTAL"]).clip(upper=1)
    df["duree_implicite"] = df["AMT_CREDIT"] / df["AMT_ANNUITY"]
    return df