"""book_co_authors — free-text "additional authors" field on books

Lets the operator credit co-authors / contributors that don't have
their own AuthorProfile row. The main author still lives in
``books.author_id``; this column is metadata only.

Revision ID: d7e2f3a4b5c6
Revises: c4f1a2b3d5e6
Create Date: 2026-06-01 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7e2f3a4b5c6"
down_revision: Union[str, None] = "c4f1a2b3d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("books", sa.Column("co_authors", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("books", "co_authors")
