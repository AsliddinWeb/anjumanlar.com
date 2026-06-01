"""site_settings — singleton config table

Holds the active theme name (and any future site-wide toggles). Single
row enforced by a unique TRUE-only boolean column plus a CHECK.

Revision ID: e8f3c4d5a6b7
Revises: d7e2f3a4b5c6
Create Date: 2026-06-01 12:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e8f3c4d5a6b7"
down_revision: Union[str, None] = "d7e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_settings",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "singleton",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "theme_name",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'classic'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("singleton", name="uq_site_settings_singleton"),
        sa.CheckConstraint("singleton = TRUE", name="site_settings_singleton_check"),
    )

    # Seed the singleton row so the API doesn't need to do a "create
    # if missing" dance on first read.
    op.execute(
        "INSERT INTO site_settings (id, singleton, theme_name) "
        "VALUES (gen_random_uuid(), TRUE, 'classic')"
    )


def downgrade() -> None:
    op.drop_table("site_settings")
