"""book_language enum — add Karakalpak (kaa)

Follow-up to b3c4d5e6f7a8: kaa was already professionally translated
in the frontend's `languages` i18n namespace, so it's worth the extra
enum value to reuse that translation instead of introducing a
regional language with no vetted label.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-09-18 09:05:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE book_language ADD VALUE IF NOT EXISTS 'kaa'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums — leaving the type as-is.
    pass
