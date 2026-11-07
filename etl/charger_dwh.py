"""ETL : reconstruit l'entrepôt `dwh` à partir des schémas `ops` et `ml`.

    python -m etl.charger_dwh
"""
from datetime import date
from pathlib import Path

from sqlalchemy import text

from app.db import engine
from etl.credits import charger_credits

DOSSIER = Path(__file__).parent
TABLES = ["dim_temps", "dim_agence", "dim_produit", "dim_agent", "dim_client",
          "fait_demande", "fait_credit", "fait_echeance", "fait_paiement",
          "fait_portefeuille_mensuel"]


def executer_fichier(connexion, nom: str) -> None:
    """Exécute chaque instruction du fichier SQL (séparées par des points-virgules)."""
    for instruction in (DOSSIER / nom).read_text(encoding="utf-8").split(";"):
        if instruction.strip():
            connexion.execute(text(instruction))


def main() -> None:
    with engine.begin() as connexion:          # tout ou rien : une seule transaction
        executer_fichier(connexion, "schema_dwh.sql")
        executer_fichier(connexion, "chargement_dwh.sql")
        charger_credits(connexion, date.today())
        print("Lignes chargées :")
        for table in TABLES:
            n = connexion.execute(text(f"SELECT count(*) FROM dwh.{table}")).scalar()
            print(f"  dwh.{table:<27} {n:>7}")


if __name__ == "__main__":
    main()