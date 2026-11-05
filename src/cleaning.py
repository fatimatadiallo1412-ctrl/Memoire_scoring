import numpy as np
import pandas as pd

HC_COLONNES = [
    "SK_ID_CURR", "TARGET", "CODE_GENDER", "CNT_CHILDREN", "CNT_FAM_MEMBERS",
    "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY",
    "NAME_INCOME_TYPE", "NAME_EDUCATION_TYPE", "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE", "FLAG_OWN_REALTY", "FLAG_OWN_CAR", "OCCUPATION_TYPE",
    "age_ans", "anciennete_emploi_ans", "sans_emploi",
]


def nettoyer_home_credit(df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)
    df = df[df["NAME_CONTRACT_TYPE"] == "Cash loans"].copy()
    print(f"HC : {n0 - len(df)} lignes hors 'Cash loans' retirées")

    df["sans_emploi"] = (df["DAYS_EMPLOYED"] == 365243).astype(int)
    print(f"HC : {df['sans_emploi'].sum()} lignes avec DAYS_EMPLOYED = 365243")
    df["DAYS_EMPLOYED"] = df["DAYS_EMPLOYED"].replace(365243, np.nan)

    df["age_ans"] = -df["DAYS_BIRTH"] / 365.25
    df["anciennete_emploi_ans"] = -df["DAYS_EMPLOYED"] / 365.25
    return df[HC_COLONNES].reset_index(drop=True)


def nettoyer_credit_risk(df: pd.DataFrame) -> pd.DataFrame:
    n0 = len(df)
    df = df.drop_duplicates()
    print(f"CR : {n0 - len(df)} doublons retirés")

    n1 = len(df)
    df = df[df["person_age"] <= 100]
    print(f"CR : {n1 - len(df)} lignes avec âge > 100 retirées")

    n2 = len(df)
    emploi_possible = df["person_emp_length"].isna() | (
        df["person_emp_length"] <= df["person_age"] - 14
    )
    df = df[emploi_possible]
    print(f"CR : {n2 - len(df)} lignes avec ancienneté impossible retirées")

    return df.drop(columns=["loan_grade", "loan_int_rate"]).reset_index(drop=True)