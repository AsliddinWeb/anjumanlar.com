"""users.admin_scopes — granular admin panel access

Lets a superadmin restrict a given `admin` account to a subset of admin
sections (books, finance, withdrawals, ...) instead of the previous
all-or-nothing role. NULL keeps the legacy "sees everything" behaviour,
so every existing admin is unaffected.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-25 14:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("admin_scopes", postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "admin_scopes")
