"""produits du site public

Ajoute les quatre produits présentés sur la page « Nos produits »
(frontend/src/vitrine.js), avec les mêmes montants et durées.
Les produits MICRO, PME et SALARIE restent actifs.

Revision ID: b3f1c2a4d5e6
Revises: d6996cc37621
Create Date: 2026-11-11 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3f1c2a4d5e6'
down_revision: Union[str, Sequence[str], None] = 'd6996cc37621'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# code, libellé, montant min, montant max (FCFA), durée min, durée max (mois), taux annuel (%)
PRODUITS = [
    ("COMMERCE", "Crédit commerce", 50_000, 1_000_000, 3, 12, 24.0),
    ("ARTISAN", "Crédit artisan", 100_000, 25_000_000, 24, 60, 22.0),
    ("AGRICOLE", "Crédit agricole", 100_000, 25_000_000, 6, 60, 20.0),
    ("EQUIPEMENT", "Crédit équipement et consommation", 50_000, 25_000_000, 3, 60, 18.0),
]


def upgrade() -> None:
    for code, libelle, mmin, mmax, dmin, dmax, taux in PRODUITS:
        op.execute(sa.text(
            "INSERT INTO ops.produit_credit "
            "(code, libelle, montant_min, montant_max, duree_min_mois, duree_max_mois, taux_annuel, actif) "
            "VALUES (:code, :libelle, :mmin, :mmax, :dmin, :dmax, :taux, true) "
            "ON CONFLICT (code) DO NOTHING"
        ).bindparams(code=code, libelle=libelle, mmin=mmin, mmax=mmax, dmin=dmin, dmax=dmax, taux=taux))


def downgrade() -> None:
    # On ne supprime que les produits qui n'ont encore servi à aucune demande.
    op.execute(sa.text(
        "DELETE FROM ops.produit_credit p WHERE p.code IN ('COMMERCE','ARTISAN','AGRICOLE','EQUIPEMENT') "
        "AND NOT EXISTS (SELECT 1 FROM ops.demande_credit d WHERE d.produit_id = p.id)"))
