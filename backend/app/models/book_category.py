"""Bridge table for the many-to-many between books and categories.

We use an explicit Core ``Table`` instead of a mapped class because the
relationship is junction-only — there's no extra data on the edge.
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base

book_categories = Table(
    "book_categories",
    Base.metadata,
    Column(
        "book_id",
        PG_UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "category_id",
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)
