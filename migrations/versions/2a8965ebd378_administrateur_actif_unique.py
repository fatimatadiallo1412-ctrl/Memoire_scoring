"""administrateur actif unique

Revision ID: 2a8965ebd378
Revises: c2d9ca61e63f
Create Date: 2026-11-10 11:56:54.091821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a8965ebd378'
down_revision: Union[str, Sequence[str], None] = 'c2d9ca61e63f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP INDEX ops.ix_utilisateur_administrateur_unique")
    op.execute("CREATE UNIQUE INDEX ix_utilisateur_administrateur_unique ON ops.utilisateur (role) WHERE role = 'administrateur' AND actif")



def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX ops.ix_utilisateur_administrateur_unique")
    op.execute("CREATE UNIQUE INDEX ix_utilisateur_administrateur_unique ON ops.utilisateur (role) WHERE role = 'administrateur'")

