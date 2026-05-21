"""phase4_3_orders_seq

Revision ID: e378a40e7057
Revises: e7fbd9dd2a5e
Create Date: 2026-05-21 16:56:02.316278

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e378a40e7057"
down_revision: Union[str, None] = "e7fbd9dd2a5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Process-safe counter for order_number. The year prefix on the
    # rendered number is cosmetic, so the sequence itself never resets.
    op.execute("CREATE SEQUENCE IF NOT EXISTS orders_seq START 1 INCREMENT 1")


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS orders_seq")
