"""Order — a user's purchase basket-turned-invoice.

Lifecycle:

    pending ──pay──> paid ──refund──> refunded
        │
        ├── expires_at hit ──> expired
        └── user cancel ─────> cancelled

A pending order holds a 30-minute reservation; the Celery beat job marks
stale ones as ``expired`` so book stock (free) and analytics stay honest.

The platform fee is locked at order-item time using
``AuthorProfile.commission_rate`` so retroactive rate changes don't
reshuffle past payouts.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.book import Book
    from app.models.payment import Payment
    from app.models.user import User


class OrderStatus(enum.StrEnum):
    pending = "pending"
    paid = "paid"
    expired = "expired"
    cancelled = "cancelled"
    failed = "failed"
    refunded = "refunded"


class Order(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    order_number: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.pending,
        server_default=OrderStatus.pending.value,
        index=True,
    )

    subtotal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    discount: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False, default=0, server_default="0"
    )
    total: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="UZS", server_default="UZS"
    )

    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[User] = relationship()
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list[Payment]] = relationship(back_populates="order")


class OrderItem(UUIDMixin, Base):
    """A line item — snapshot of price + commission at purchase time.

    Keeping the snapshot fields here (instead of recomputing from the
    book row) is what lets us answer "how much did this exact sale earn
    the author?" months later, even after the book price changes.
    """

    __tablename__ = "order_items"

    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("books.id"),
        nullable=False,
        index=True,
    )

    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    commission_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    author_earning: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    order: Mapped[Order] = relationship(back_populates="items")
    book: Mapped[Book] = relationship()
