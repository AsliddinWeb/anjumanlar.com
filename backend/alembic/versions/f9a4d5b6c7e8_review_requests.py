"""review_requests — paid peer-review flow

Reader → uploads manuscript → picks author → author quotes →
reader pays → author submits review.

Revision ID: f9a4d5b6c7e8
Revises: e8f3c4d5a6b7
Create Date: 2026-06-01 18:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f9a4d5b6c7e8"
down_revision: Union[str, None] = "e8f3c4d5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_requests",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "requester_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("author_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("manuscript_url", sa.String(length=500), nullable=True),
        sa.Column("manuscript_filename", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "quoted", "paid", "completed", "cancelled",
                name="review_request_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("proposed_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("final_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("review_file_url", sa.String(length=500), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("quoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index("ix_review_requests_requester_id", "review_requests", ["requester_id"])
    op.create_index("ix_review_requests_author_id", "review_requests", ["author_id"])
    op.create_index("ix_review_requests_status", "review_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_review_requests_status", "review_requests")
    op.drop_index("ix_review_requests_author_id", "review_requests")
    op.drop_index("ix_review_requests_requester_id", "review_requests")
    op.drop_table("review_requests")
    op.execute("DROP TYPE IF EXISTS review_request_status")
