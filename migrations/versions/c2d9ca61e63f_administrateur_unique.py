"""administrateur unique

Revision ID: c2d9ca61e63f
Revises: 75c30910fac0
Create Date: 2026-11-10 11:50:48.668902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d9ca61e63f'
down_revision: Union[str, Sequence[str], None] = '75c30910fac0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE UNIQUE INDEX ix_utilisateur_administrateur_unique ON ops.utilisateur (role) WHERE role = 'administrateur'")



def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX ops.ix_utilisateur_administrateur_unique")

