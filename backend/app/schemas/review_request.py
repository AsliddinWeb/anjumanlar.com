"""Pydantic schemas for the paid peer-review flow."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import ReviewRequestStatus

PriceField = Annotated[float, Field(ge=0, le=1_000_000_000)]


# ----- Write paths -----

class ReviewRequestCreate(BaseModel):
    """Reader creates a request — picks the author, optionally adds notes
    and a proposed price. The manuscript file lands via a separate
    upload endpoint after the row exists."""

    author_id: UUID
    notes: str | None = Field(default=None, max_length=4000)
    proposed_price: PriceField | None = None


class ReviewRequestQuote(BaseModel):
    """Author sets the final price."""

    final_price: PriceField


class ReviewRequestSubmit(BaseModel):
    """Author submits the review."""

    review_text: str = Field(..., min_length=1, max_length=20_000)


class ReviewRequestCancel(BaseModel):
    """Either side (or admin) cancels — optional reason."""

    reason: str | None = Field(default=None, max_length=2000)


# ----- Read paths -----

class ReviewRequestAuthorRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    display_name: str


class ReviewRequestRequesterRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str
    email: str


class ReviewRequestPublic(BaseModel):
    """Full row payload shared by both sides + admin."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester: ReviewRequestRequesterRef
    author: ReviewRequestAuthorRef
    manuscript_url: str | None
    manuscript_filename: str | None
    notes: str | None
    status: ReviewRequestStatus
    proposed_price: float | None
    final_price: float | None
    review_text: str | None
    review_file_url: str | None
    cancellation_reason: str | None
    created_at: datetime
    quoted_at: datetime | None
    paid_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None


class ReviewRequestList(BaseModel):
    items: list[ReviewRequestPublic]
    total: int
    page: int
    page_size: int
