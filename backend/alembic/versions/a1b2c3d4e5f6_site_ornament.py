"""site_settings.ornament_name — selectable national-motif variant

Adds a second admin-controlled palette toggle alongside theme_name:
which SVG ornament pattern to use across the site.

Revision ID: a1b2c3d4e5f6
Revises: f9a4d5b6c7e8
Create Date: 2026-06-02 09:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f9a4d5b6c7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_settings",
        sa.Column(
            "ornament_name",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'classic'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("site_settings", "ornament_name")
