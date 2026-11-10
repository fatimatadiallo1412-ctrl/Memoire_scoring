"""mode decaissement

Revision ID: d6996cc37621
Revises: 9f0854ef0258
Create Date: 2026-11-10 15:39:42.932204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6996cc37621'
down_revision: Union[str, Sequence[str], None] = '9f0854ef0258'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE ops.credit ADD COLUMN mode_decaissement VARCHAR(20), "
               "ADD COLUMN reference_decaissement VARCHAR(60)")
    op.execute("ALTER TABLE ops.credit ADD CONSTRAINT ck_credit_mode CHECK "
               "(mode_decaissement IN ('especes','mobile_money','virement'))")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE ops.credit DROP CONSTRAINT ck_credit_mode")
    op.execute("ALTER TABLE ops.credit DROP COLUMN mode_decaissement, "
               "DROP COLUMN reference_decaissement")
