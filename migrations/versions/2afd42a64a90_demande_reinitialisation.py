"""demande reinitialisation

Revision ID: 2afd42a64a90
Revises: 8a41a7f97962
Create Date: 2026-11-10 13:05:10.782847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2afd42a64a90'
down_revision: Union[str, Sequence[str], None] = '8a41a7f97962'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""CREATE TABLE ops.demande_reinitialisation (
        id serial PRIMARY KEY,
        utilisateur_id integer NOT NULL REFERENCES ops.utilisateur(id),
        email varchar(255) NOT NULL,
        contact varchar(100),
        statut varchar(20) NOT NULL DEFAULT 'en_attente' CHECK (statut IN ('en_attente','traitee','rejetee')),
        cree_le timestamptz NOT NULL DEFAULT now(),
        traitee_par integer REFERENCES ops.utilisateur(id),
        traitee_le timestamptz)""")
    op.execute("CREATE INDEX ix_demande_reinitialisation_statut ON ops.demande_reinitialisation (statut)")



def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE ops.demande_reinitialisation")

