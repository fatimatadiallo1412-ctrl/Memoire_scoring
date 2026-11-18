"""motif communiqué au client

Décision : motif rédigé pour le client, distinct du commentaire interne du directeur.
Obligatoire quand le directeur refuse alors que le modèle recommandait un accord
(le modèle n'a alors aucun motif à donner au client).

Revision ID: d4b8e1f2a7c9
Revises: c7e2a9d41f03
Create Date: 2026-11-18 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4b8e1f2a7c9'
down_revision: Union[str, Sequence[str], None] = 'c7e2a9d41f03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('decision', sa.Column('motif_client', sa.Text(), nullable=True), schema='ops')
    # Les refus déjà enregistrés ne sont pas concernés (NOT VALID : contrôle des nouvelles lignes seulement).
    op.execute(
        "ALTER TABLE ops.decision ADD CONSTRAINT motif_client_si_refus_contre_modele CHECK ("
        "decision <> 'refuser' OR recommandation_modele IS NULL OR recommandation_modele = 'refus' "
        "OR (motif_client IS NOT NULL AND length(trim(motif_client)) > 0)) NOT VALID")


def downgrade() -> None:
    op.drop_constraint('motif_client_si_refus_contre_modele', 'decision', schema='ops', type_='check')
    op.drop_column('decision', 'motif_client', schema='ops')
