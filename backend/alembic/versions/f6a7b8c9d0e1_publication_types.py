"""publication_types table + books.publication_type_id

Adds an admin-managed lookup table for what KIND of publication a book
is (textbook, monograph, study guide, lecture notes, dictionary,
conference proceedings) — orthogonal to the subject `categories` tree.
A book carries at most one, via a plain nullable FK (existing books
predate this column and need a one-time admin classification pass).

Seeds the six types the client asked for so the picker isn't empty
after the migration runs.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-27 12:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED_TYPES = [
    {
        "slug": "textbook",
        "name": {"uz": "Darslik", "ru": "Учебник", "en": "Textbook"},
        "sort_order": 10,
    },
    {
        "slug": "monograph",
        "name": {"uz": "Monografiya", "ru": "Монография", "en": "Monograph"},
        "sort_order": 20,
    },
    {
        "slug": "study-guide",
        "name": {"uz": "O'quv qo'llanma", "ru": "Учебное пособие", "en": "Study guide"},
        "sort_order": 30,
    },
    {
        "slug": "lecture-notes",
        "name": {"uz": "Ma'ruzalar matni", "ru": "Курс лекций", "en": "Lecture notes"},
        "sort_order": 40,
    },
    {
        "slug": "dictionary",
        "name": {"uz": "Lug'at", "ru": "Словарь", "en": "Dictionary"},
        "sort_order": 50,
    },
    {
        "slug": "conference-proceedings",
        "name": {
            "uz": "Konferensiya materiallari",
            "ru": "Материалы конференции",
            "en": "Conference proceedings",
        },
        "sort_order": 60,
    },
]


def upgrade() -> None:
    op.create_table(
        "publication_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "name",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_publication_types_slug"),
    )
    op.create_index(
        "ix_publication_types_slug", "publication_types", ["slug"], unique=False
    )

    op.add_column(
        "books",
        sa.Column("publication_type_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_books_publication_type_id",
        "books",
        "publication_types",
        ["publication_type_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_books_publication_type_id", "books", ["publication_type_id"], unique=False
    )

    publication_types = sa.table(
        "publication_types",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String),
        sa.column("name", postgresql.JSONB),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        publication_types,
        [
            {
                "id": uuid4(),
                "slug": t["slug"],
                "name": t["name"],
                "sort_order": t["sort_order"],
                "is_active": True,
            }
            for t in SEED_TYPES
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_books_publication_type_id", table_name="books")
    op.drop_constraint("fk_books_publication_type_id", "books", type_="foreignkey")
    op.drop_column("books", "publication_type_id")

    op.drop_index("ix_publication_types_slug", table_name="publication_types")
    op.drop_table("publication_types")
