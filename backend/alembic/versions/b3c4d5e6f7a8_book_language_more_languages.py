"""book_language enum — add 12 more languages

Was uz/ru/en/mixed only. Adds kk, tr, ky, tg, tk, az, ar, fa, zh, de,
fr, es so authors publishing in other Central Asian / regional
languages don't get forced into "mixed".

Postgres enums only support adding values, never removing — downgrade
is a no-op (existing rows using a new value would otherwise have no
valid enum member to fall back to).

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-09-18 09:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_VALUES = ["kk", "tr", "ky", "tg", "tk", "az", "ar", "fa", "zh", "de", "fr", "es"]


def upgrade() -> None:
    for value in NEW_VALUES:
        op.execute(f"ALTER TYPE book_language ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums — leaving the type as-is.
    pass
