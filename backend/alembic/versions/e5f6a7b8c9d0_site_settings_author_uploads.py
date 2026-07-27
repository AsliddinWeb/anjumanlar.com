"""site_settings.author_uploads_enabled — temporary author-upload kill switch

Lets an admin pause self-service book creation (POST /books) from
/admin/settings without a deploy. Defaults to TRUE so existing installs
keep the current behaviour.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-27 10:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_settings",
        sa.Column(
            "author_uploads_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("site_settings", "author_uploads_enabled")
