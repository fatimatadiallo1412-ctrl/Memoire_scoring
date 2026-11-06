import pandas as pd
from sqlalchemy import text

from src.db import get_engine
from src.modeling import DONNEES


def charger_home_credit():
    df = pd.read_parquet(DONNEES)
    df.columns = [c.lower() for c in df.columns]   # noms en minuscules : pas de guillemets en SQL

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))

    df.to_sql("home_credit_features", engine, schema="staging",
              if_exists="replace", index=False, chunksize=2000, method="multi")
    print(f"{len(df)} lignes chargées dans staging.home_credit_features")


if __name__ == "__main__":
    charger_home_credit()