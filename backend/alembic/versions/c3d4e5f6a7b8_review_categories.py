"""review_categories table + review_requests.category_id / is_international

Adds an admin-managed lookup table for review-request categories
("article", "dissertation", "study guide", "textbook", …) and wires
review_requests to it. ``author_id`` becomes nullable in the same step
because the redesigned flow no longer asks the requester to pick an
author — admin handles the request end-to-end.

Seeds the four starter categories so the picker isn't empty after the
migration runs.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-19 10:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED_CATEGORIES = [
    {
        "slug": "article",
        "name": {
            "uz": "Maqolaga taqriz",
            "ru": "Рецензия на статью",
            "en": "Article review",
        },
        "sort_order": 10,
    },
    {
        "slug": "dissertation",
        "name": {
            "uz": "Dissertatsiyaga taqriz",
            "ru": "Рецензия на диссертацию",
            "en": "Dissertation review",
        },
        "sort_order": 20,
    },
    {
        "slug": "study-guide",
        "name": {
            "uz": "O'quv qo'llanmaga taqriz",
            "ru": "Рецензия на учебное пособие",
            "en": "Study guide review",
        },
        "sort_order": 30,
    },
    {
        "slug": "textbook",
        "name": {
            "uz": "Darslikka taqriz",
            "ru": "Рецензия на учебник",
            "en": "Textbook review",
        },
        "sort_order": 40,
    },
]


def upgrade() -> None:
    op.create_table(
        "review_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column(
            "name",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "description",
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
        sa.UniqueConstraint("slug", name="uq_review_categories_slug"),
    )
    op.create_index(
        "ix_review_categories_slug", "review_categories", ["slug"], unique=False
    )
    op.create_index(
        "ix_review_categories_is_active", "review_categories", ["is_active"], unique=False
    )

    # review_requests: nullable author_id, new category_id, is_international.
    op.alter_column("review_requests", "author_id", existing_type=postgresql.UUID(), nullable=True)
    op.add_column(
        "review_requests",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "review_requests",
        sa.Column(
            "is_international",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_foreign_key(
        "fk_review_requests_category_id",
        "review_requests",
        "review_categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_review_requests_category_id", "review_requests", ["category_id"], unique=False
    )

    # Seed the four starter categories.
    review_categories = sa.table(
        "review_categories",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String),
        sa.column("name", postgresql.JSONB),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        review_categories,
        [
            {
                "id": uuid4(),
                "slug": c["slug"],
                "name": c["name"],
                "sort_order": c["sort_order"],
                "is_active": True,
            }
            for c in SEED_CATEGORIES
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_review_requests_category_id", table_name="review_requests")
    op.drop_constraint(
        "fk_review_requests_category_id", "review_requests", type_="foreignkey"
    )
    op.drop_column("review_requests", "is_international")
    op.drop_column("review_requests", "category_id")
    op.alter_column(
        "review_requests", "author_id", existing_type=postgresql.UUID(), nullable=False
    )

    op.drop_index("ix_review_categories_is_active", table_name="review_categories")
    op.drop_index("ix_review_categories_slug", table_name="review_categories")
    op.drop_table("review_categories")
