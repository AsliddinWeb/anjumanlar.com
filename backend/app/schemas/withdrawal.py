"""Pydantic schemas for /authors/me/withdrawals + admin moderation."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import WithdrawalStatus


class WithdrawalCreate(BaseModel):
    """Author requests a payout. ``bank_details`` overrides the snapshot
    taken from the author profile — most users will skip it and use the
    profile defaults."""

    amount: float = Field(..., gt=0, le=1_000_000_000)
    bank_details: dict[str, Any] | None = None


class WithdrawalDecision(BaseModel):
    """Admin payload for approve/reject."""

    admin_notes: str | None = Field(default=None, max_length=2000)
    transaction_ref: str | None = Field(default=None, max_length=255)


class WithdrawalPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: float
    currency: str
    status: WithdrawalStatus
    bank_details: dict[str, Any]
    admin_notes: str | None = None
    transaction_ref: str | None = None
    processed_at: datetime | None = None
    created_at: datetime


class WithdrawalList(BaseModel):
    items: list[WithdrawalPublic]
    total: int
    page: int
    page_size: int


class AuthorBalance(BaseModel):
    """Snapshot of an author's earnings."""

    available_balance: float
    pending_balance: float
    total_revenue: float
    total_sales: int
    commission_rate: float
    currency: str = "UZS"
