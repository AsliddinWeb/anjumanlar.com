"""Aggregated counters for the admin dashboard.

Single ``snapshot`` call so the dashboard does one round-trip instead
of fanning out per card. Each query is a count or sum so the cost is
dominated by index lookups; on a non-trivial dataset we can revisit
this with a materialised view, but for now plain queries are fine.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Book,
    BookStatus,
    Order,
    OrderItem,
    OrderStatus,
    Review,
    ReviewStatus,
    User,
    UserRole,
    UserStatus,
    Withdrawal,
    WithdrawalStatus,
)


async def snapshot(db: AsyncSession) -> dict[str, Any]:
    """Return every KPI the admin dashboard currently renders."""

    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    month_start = datetime(now.year, now.month, 1, tzinfo=UTC)

    # ---- users ----
    users_total = (
        await db.execute(
            select(func.count()).select_from(User).where(User.status != UserStatus.deleted)
        )
    ).scalar_one()
    users_last_7d = (
        await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.status != UserStatus.deleted, User.created_at >= week_ago)
        )
    ).scalar_one()
    authors = (
        await db.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.author)
        )
    ).scalar_one()
    admins = (
        await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.role.in_((UserRole.admin, UserRole.superadmin)))
        )
    ).scalar_one()

    # ---- books ----
    books_total = (
        await db.execute(
            select(func.count())
            .select_from(Book)
            .where(Book.status == BookStatus.approved, Book.deleted_at.is_(None))
        )
    ).scalar_one()
    books_pending = (
        await db.execute(
            select(func.count())
            .select_from(Book)
            .where(Book.status == BookStatus.pending, Book.deleted_at.is_(None))
        )
    ).scalar_one()

    # ---- reviews ----
    reviews_pending = (
        await db.execute(
            select(func.count())
            .select_from(Review)
            .where(Review.status == ReviewStatus.pending)
        )
    ).scalar_one()

    # ---- orders + revenue ----
    orders_paid_total = (
        await db.execute(
            select(func.count()).select_from(Order).where(Order.status == OrderStatus.paid)
        )
    ).scalar_one()
    orders_paid_this_month = (
        await db.execute(
            select(func.count())
            .select_from(Order)
            .where(
                Order.status == OrderStatus.paid,
                Order.paid_at >= month_start,
            )
        )
    ).scalar_one()

    revenue_total = (
        await db.execute(
            select(func.coalesce(func.sum(Order.total), 0))
            .where(Order.status == OrderStatus.paid)
        )
    ).scalar_one()
    platform_fee_total = (
        await db.execute(
            select(func.coalesce(func.sum(OrderItem.platform_fee), 0))
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.status == OrderStatus.paid)
        )
    ).scalar_one()

    # ---- withdrawals ----
    withdrawals_open = (
        await db.execute(
            select(func.count())
            .select_from(Withdrawal)
            .where(
                Withdrawal.status.in_(
                    (
                        WithdrawalStatus.requested,
                        WithdrawalStatus.approved,
                        WithdrawalStatus.processing,
                    )
                )
            )
        )
    ).scalar_one()
    withdrawals_pending_amount = (
        await db.execute(
            select(func.coalesce(func.sum(Withdrawal.amount), 0))
            .where(
                Withdrawal.status.in_(
                    (
                        WithdrawalStatus.requested,
                        WithdrawalStatus.approved,
                        WithdrawalStatus.processing,
                    )
                )
            )
        )
    ).scalar_one()

    return {
        "users": {
            "total": int(users_total),
            "last_7d": int(users_last_7d),
            "authors": int(authors),
            "admins": int(admins),
        },
        "books": {
            "approved": int(books_total),
            "pending": int(books_pending),
        },
        "reviews": {
            "pending": int(reviews_pending),
        },
        "orders": {
            "paid_total": int(orders_paid_total),
            "paid_this_month": int(orders_paid_this_month),
        },
        "revenue": {
            "gross": float(revenue_total),
            "platform_fee": float(platform_fee_total),
            "currency": "UZS",
        },
        "withdrawals": {
            "open": int(withdrawals_open),
            "open_amount": float(withdrawals_pending_amount),
        },
        "generated_at": now.isoformat(),
    }
