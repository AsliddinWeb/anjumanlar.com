"""Payment — a payment-provider attempt against an order.

Currently only Payme writes here, but the ``provider`` column leaves room
for Click/Uzum/etc. without another table. ``state`` mirrors the Payme
integer state machine verbatim (1 = created, 2 = paid, -1/-2 = cancelled)
so the JSON-RPC webhook handler can store the raw value and the rest of
the app can read ``status`` for a normalised view.

``raw_response`` keeps the last webhook payload for forensics — handy
when reconciling disputed transactions later.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.order import Order


class PaymentStatus(enum.StrEnum):
    created = "created"
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"
    failed = "failed"


class PaymentProvider(enum.StrEnum):
    payme = "payme"
    click = "click"
    manual = "manual"


class Payment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_provider_id", "provider", "provider_id"),
    )

    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    provider: Mapped[PaymentProvider] = mapped_column(
        SAEnum(PaymentProvider, name="payment_provider"),
        nullable=False,
        default=PaymentProvider.payme,
        server_default=PaymentProvider.payme.value,
    )
    # External transaction id, e.g. Payme's ``id`` field.
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="UZS", server_default="UZS"
    )

    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.created,
        server_default=PaymentStatus.created.value,
        index=True,
    )

    # Raw Payme integer state. -2/-1 = cancelled, 1 = created, 2 = paid.
    state: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Payme timestamps are in milliseconds since epoch.
    create_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    perform_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cancel_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[int | None] = mapped_column(Integer, nullable=True)

    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    order: Mapped[Order] = relationship(back_populates="payments")
