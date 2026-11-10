"""comptes securite

Revision ID: 8a41a7f97962
Revises: 2a8965ebd378
Create Date: 2026-11-10 12:47:39.202382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a41a7f97962'
down_revision: Union[str, Sequence[str], None] = '2a8965ebd378'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE ops.utilisateur ADD COLUMN doit_changer_mdp boolean NOT NULL DEFAULT false, ADD COLUMN echecs_connexion integer NOT NULL DEFAULT 0, ADD COLUMN verrouille_jusqua timestamptz")



def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE ops.utilisateur DROP COLUMN doit_changer_mdp, DROP COLUMN echecs_connexion, DROP COLUMN verrouille_jusqua")

