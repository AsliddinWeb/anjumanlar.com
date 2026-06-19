"""Pydantic schemas for the paid peer-review flow."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import ReviewRequestStatus

PriceField = Annotated[float, Field(ge=0, le=1_000_000_000)]


# ----- Write paths -----

class ReviewRequestCreate(BaseModel):
    """Reader creates a request.

    Author is no longer chosen by the requester — admin sees the request,
    picks the price, optionally assigns a reviewer. The requester supplies
    a category (kind of work) and flags whether the review should be
    international. Notes are optional.
    """

    category_id: UUID
    is_international: bool = False
    notes: str | None = Field(default=None, max_length=4000)


class ReviewRequestQuote(BaseModel):
    """Admin sets the final price."""

    final_price: PriceField


class ReviewRequestSubmit(BaseModel):
    """Admin submits the review."""

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


class ReviewRequestCategoryRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    name: dict[str, Any]


class ReviewRequestPublic(BaseModel):
    """Full row payload shared by both sides + admin."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester: ReviewRequestRequesterRef
    author: ReviewRequestAuthorRef | None = None
    category: ReviewRequestCategoryRef | None = None
    is_international: bool = False
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
