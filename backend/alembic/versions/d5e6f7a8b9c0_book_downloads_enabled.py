"""books.downloads_enabled — per-book download kill switch

Admin toggle: when false, a buyer can still read the book via
/libraries/me/{id}/stream (inline, no save dialog) but the
/download endpoint (signed URL meant for saving to disk) refuses.
Defaults to true so every existing book keeps today's behaviour.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-09-18 09:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "books",
        sa.Column("downloads_enabled", sa.Boolean(), nullable=False,
                   server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("books", "downloads_enabled")
