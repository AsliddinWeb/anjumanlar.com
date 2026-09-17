"""Pydantic schemas for /orders endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import OrderStatus
from app.schemas.book import BookPublic


class OrderCreate(BaseModel):
    """Client payload — just a list of book ids. Server computes prices,
    commission, and totals from authoritative DB rows so the client can't
    spoof a discount."""

    book_ids: list[UUID] = Field(..., min_length=1, max_length=20)
    payment_method: str | None = Field(default="payme", max_length=50)


class OrderItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book: BookPublic
    price: float
    commission_rate: float
    author_earning: float
    platform_fee: float


class OrderPublic(BaseModel):
    """Order detail visible to the owner."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    status: OrderStatus
    subtotal: float
    discount: float
    total: float
    currency: str
    payment_method: str | None = None
    paid_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime
    items: list[OrderItemPublic]


class OrderCheckout(BaseModel):
    """Response to POST /orders — order + Payme redirect URL."""

    order: OrderPublic
    payment_url: str | None = None


class OrderList(BaseModel):
    items: list[OrderPublic]
    total: int
    page: int
    page_size: int


class OrderBuyer(BaseModel):
    """Buyer identity as shown to admins — no auth-sensitive fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    preferred_locale: str


class OrderPaymentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    provider_id: str | None = None
    amount: float
    currency: str
    status: str
    state: int | None = None
    create_time: int | None = None
    perform_time: int | None = None
    cancel_time: int | None = None
    reason: int | None = None
    created_at: datetime


class OrderAdminPublic(OrderPublic):
    """Order row as shown in the admin orders table — adds the buyer."""

    user: OrderBuyer


class OrderAdminDetail(OrderAdminPublic):
    """Full admin detail — adds the payment-attempt history."""

    payments: list[OrderPaymentPublic]


class OrderAdminList(BaseModel):
    items: list[OrderAdminPublic]
    total: int
    page: int
    page_size: int
