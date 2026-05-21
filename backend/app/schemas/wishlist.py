"""Pydantic schemas for /users/me/wishlist."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.book import BookPublic


class WishlistItem(BaseModel):
    """One wishlist entry. We embed the full book payload so the frontend
    can render the list without a second round-trip per item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    book: BookPublic


class WishlistList(BaseModel):
    items: list[WishlistItem]
    total: int
