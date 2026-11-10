"""mode decaissement

Revision ID: 9f0854ef0258
Revises: 2afd42a64a90
Create Date: 2026-11-10 15:33:29.110001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f0854ef0258'
down_revision: Union[str, Sequence[str], None] = '2afd42a64a90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
