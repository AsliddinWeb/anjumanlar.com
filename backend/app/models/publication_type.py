"""Publication type — what KIND of book this is (textbook, monograph,
dictionary, ...), orthogonal to the subject `Category` tree.

Admin-manageable like `Category`, but flat (no parent tree) and a book
carries exactly one — a plain FK on `Book`, not a many-to-many join
table like `book_categories`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.book import Book


class PublicationType(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "publication_types"

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    books: Mapped[list[Book]] = relationship(back_populates="publication_type")

    if TYPE_CHECKING:
        # Not a DB column — set at read time by the service layer's live COUNT(*) query.
        book_count: int
