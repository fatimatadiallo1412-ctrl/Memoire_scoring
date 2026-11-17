"""variables microfinance et rapports de suivi du modèle

Client : épargne mensuelle, appartenance à un groupement (tontine, GIE), usage du mobile money,
activité saisonnière. Demande : garantie proposée. Ces variables ne sont pas utilisées par le
modèle v4 ; elles sont collectées pour les modèles appris sur les données de l'institution.
ml.rapport_suivi : rapports de stabilité et de performance du modèle (page « Santé du modèle »).

Revision ID: c7e2a9d41f03
Revises: b3f1c2a4d5e6
Create Date: 2026-11-17 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'c7e2a9d41f03'
down_revision: Union[str, Sequence[str], None] = 'b3f1c2a4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('client', sa.Column('epargne_mensuelle', sa.BigInteger(), nullable=True), schema='ops')
    op.add_column('client', sa.Column('membre_groupement', sa.Boolean(), nullable=True), schema='ops')
    op.add_column('client', sa.Column('usage_mobile_money', sa.String(length=20), nullable=True), schema='ops')
    op.add_column('client', sa.Column('activite_saisonniere', sa.Boolean(), nullable=True), schema='ops')
    op.create_check_constraint('epargne_positive', 'client', 'epargne_mensuelle >= 0', schema='ops')
    op.create_check_constraint(
        'usage_mobile_money_connu', 'client',
        "usage_mobile_money IN ('jamais', 'occasionnel', 'regulier')", schema='ops')
    op.add_column('demande_credit', sa.Column('garantie', sa.String(length=30), nullable=True), schema='ops')
    op.create_check_constraint(
        'garantie_connue', 'demande_credit',
        "garantie IN ('aucune', 'caution_solidaire', 'garant', 'epargne_nantie')", schema='ops')

    op.create_table(
        'rapport_suivi',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_modele', sa.String(length=80), nullable=False),
        sa.Column('debut', sa.Date(), nullable=False),
        sa.Column('fin', sa.Date(), nullable=False),
        sa.Column('niveau_global', sa.String(length=10), nullable=False),
        sa.Column('contenu', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('produit_par', sa.Integer(), nullable=True),
        sa.Column('produit_le', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['produit_par'], ['ops.utilisateur.id']),
        sa.PrimaryKeyConstraint('id'),
        schema='ml')


def downgrade() -> None:
    op.drop_table('rapport_suivi', schema='ml')
    op.drop_constraint('garantie_connue', 'demande_credit', schema='ops')
    op.drop_column('demande_credit', 'garantie', schema='ops')
    op.drop_constraint('usage_mobile_money_connu', 'client', schema='ops')
    op.drop_constraint('epargne_positive', 'client', schema='ops')
    for colonne in ('activite_saisonniere', 'usage_mobile_money', 'membre_groupement', 'epargne_mensuelle'):
        op.drop_column('client', colonne, schema='ops')
