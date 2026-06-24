"""Admin finance analytics.

Pulls revenue + commission rollups straight from ``orders`` /
``order_items`` so the dashboard never lies about historical sales — the
snapshot fields on ``OrderItem`` mean a refunded order keeps the
breakdown it shipped with at purchase time.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AuthorProfile,
    Book,
    Order,
    OrderItem,
    OrderStatus,
    User,
)


def _start_of_day(d: datetime) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)


async def _sum_revenue_between(
    db: AsyncSession, start: datetime | None, end: datetime | None
) -> tuple[float, float, int]:
    """Return (gross, platform_fee, paid_order_count) for paid orders in range."""
    base = select(Order.id, Order.total).where(Order.status == OrderStatus.paid)
    if start is not None:
        base = base.where(Order.paid_at >= start)
    if end is not None:
        base = base.where(Order.paid_at < end)
    orders = (await db.execute(base)).all()
    gross = sum(float(o.total) for o in orders)
    order_count = len(orders)

    fee_q = (
        select(func.coalesce(func.sum(OrderItem.platform_fee), 0))
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.status == OrderStatus.paid)
    )
    if start is not None:
        fee_q = fee_q.where(Order.paid_at >= start)
    if end is not None:
        fee_q = fee_q.where(Order.paid_at < end)
    fee = (await db.execute(fee_q)).scalar_one()
    return gross, float(fee), order_count


async def admin_overview(db: AsyncSession, *, days: int = 30) -> dict[str, Any]:
    """Bundle KPI cards + a 30-day revenue series + top-N tables."""
    now = datetime.now(UTC)
    today_start = _start_of_day(now)
    week_start = today_start - timedelta(days=7)
    month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
    if now.month == 1:
        prev_month_start = datetime(now.year - 1, 12, 1, tzinfo=UTC)
    else:
        prev_month_start = datetime(now.year, now.month - 1, 1, tzinfo=UTC)

    today_gross, today_fee, today_orders = await _sum_revenue_between(db, today_start, None)
    week_gross, week_fee, week_orders = await _sum_revenue_between(db, week_start, None)
    month_gross, month_fee, month_orders = await _sum_revenue_between(db, month_start, None)
    prev_month_gross, prev_month_fee, prev_month_orders = await _sum_revenue_between(
        db, prev_month_start, month_start
    )
    all_gross, all_fee, all_orders = await _sum_revenue_between(db, None, None)

    # ---- daily series (last N days, ascending) ----
    series_start = today_start - timedelta(days=days - 1)
    series_rows = (
        await db.execute(
            select(
                cast(Order.paid_at, Date).label("day"),
                func.coalesce(func.sum(Order.total), 0).label("gross"),
                func.count(Order.id).label("orders"),
            )
            .where(Order.status == OrderStatus.paid, Order.paid_at >= series_start)
            .group_by("day")
            .order_by("day")
        )
    ).all()
    by_day: dict[date, dict[str, float]] = {
        row.day: {"gross": float(row.gross), "orders": int(row.orders)} for row in series_rows
    }
    series = []
    cursor = series_start.date()
    end_day = today_start.date()
    while cursor <= end_day:
        bucket = by_day.get(cursor, {"gross": 0.0, "orders": 0})
        series.append({
            "date": cursor.isoformat(),
            "gross": bucket["gross"],
            "orders": bucket["orders"],
        })
        cursor += timedelta(days=1)

    # ---- top books by revenue ----
    top_books_rows = (
        await db.execute(
            select(
                Book.id,
                Book.slug,
                Book.title,
                func.coalesce(func.sum(OrderItem.price), 0).label("revenue"),
                func.count(OrderItem.id).label("units"),
            )
            .join(OrderItem, OrderItem.book_id == Book.id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.status == OrderStatus.paid)
            .group_by(Book.id, Book.slug, Book.title)
            .order_by(func.sum(OrderItem.price).desc())
            .limit(10)
        )
    ).all()
    top_books = [
        {
            "id": str(r.id),
            "slug": r.slug,
            "title": r.title,
            "revenue": float(r.revenue),
            "units": int(r.units),
        }
        for r in top_books_rows
    ]

    # ---- top authors by revenue ----
    top_authors_rows = (
        await db.execute(
            select(
                AuthorProfile.id,
                AuthorProfile.slug,
                AuthorProfile.display_name,
                func.coalesce(func.sum(OrderItem.author_earning), 0).label("earning"),
                func.count(OrderItem.id).label("units"),
            )
            .join(Book, Book.author_id == AuthorProfile.id)
            .join(OrderItem, OrderItem.book_id == Book.id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.status == OrderStatus.paid)
            .group_by(AuthorProfile.id, AuthorProfile.slug, AuthorProfile.display_name)
            .order_by(func.sum(OrderItem.author_earning).desc())
            .limit(10)
        )
    ).all()
    top_authors = [
        {
            "id": str(r.id),
            "slug": r.slug,
            "display_name": r.display_name,
            "earning": float(r.earning),
            "units": int(r.units),
        }
        for r in top_authors_rows
    ]

    # ---- status breakdown (last 30d) ----
    status_rows = (
        await db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.created_at >= series_start)
            .group_by(Order.status)
        )
    ).all()
    status_breakdown = {row[0].value: int(row[1]) for row in status_rows}

    return {
        "currency": "UZS",
        "generated_at": now.isoformat(),
        "kpi": {
            "today": {"gross": today_gross, "fee": today_fee, "orders": today_orders},
            "week": {"gross": week_gross, "fee": week_fee, "orders": week_orders},
            "month": {"gross": month_gross, "fee": month_fee, "orders": month_orders},
            "prev_month": {
                "gross": prev_month_gross,
                "fee": prev_month_fee,
                "orders": prev_month_orders,
            },
            "all_time": {"gross": all_gross, "fee": all_fee, "orders": all_orders},
        },
        "series": series,
        "top_books": top_books,
        "top_authors": top_authors,
        "status_breakdown": status_breakdown,
    }


async def author_overview(
    db: AsyncSession, author_user: User, *, days: int = 30
) -> dict[str, Any]:
    """Per-author sales/earning rollup for the author dashboard.

    Pulls the AuthorProfile from the user; returns an empty payload when
    the user has no profile (a brand-new author hasn't filled theirs in
    yet).
    """
    profile = (
        await db.execute(
            select(AuthorProfile).where(AuthorProfile.user_id == author_user.id)
        )
    ).scalar_one_or_none()
    if profile is None:
        return {
            "currency": "UZS",
            "series": [],
            "totals": {"gross": 0.0, "earning": 0.0, "units": 0},
            "top_books": [],
        }

    now = datetime.now(UTC)
    series_start = _start_of_day(now) - timedelta(days=days - 1)

    items_filter = (OrderItem.book_id.in_(
        select(Book.id).where(Book.author_id == profile.id)
    ))

    # ---- daily series ----
    series_rows = (
        await db.execute(
            select(
                cast(Order.paid_at, Date).label("day"),
                func.coalesce(func.sum(OrderItem.price), 0).label("gross"),
                func.coalesce(func.sum(OrderItem.author_earning), 0).label("earning"),
                func.count(OrderItem.id).label("units"),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                Order.status == OrderStatus.paid,
                Order.paid_at >= series_start,
                items_filter,
            )
            .group_by("day")
            .order_by("day")
        )
    ).all()
    by_day = {
        r.day: {
            "gross": float(r.gross),
            "earning": float(r.earning),
            "units": int(r.units),
        }
        for r in series_rows
    }
    series = []
    cursor = series_start.date()
    end_day = _start_of_day(now).date()
    while cursor <= end_day:
        bucket = by_day.get(cursor, {"gross": 0.0, "earning": 0.0, "units": 0})
        series.append({
            "date": cursor.isoformat(),
            "gross": bucket["gross"],
            "earning": bucket["earning"],
            "units": bucket["units"],
        })
        cursor += timedelta(days=1)

    # ---- lifetime totals ----
    totals_row = (
        await db.execute(
            select(
                func.coalesce(func.sum(OrderItem.price), 0),
                func.coalesce(func.sum(OrderItem.author_earning), 0),
                func.count(OrderItem.id),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.status == OrderStatus.paid, items_filter)
        )
    ).one()

    top_books_rows = (
        await db.execute(
            select(
                Book.id,
                Book.slug,
                Book.title,
                func.coalesce(func.sum(OrderItem.author_earning), 0).label("earning"),
                func.count(OrderItem.id).label("units"),
            )
            .join(OrderItem, OrderItem.book_id == Book.id)
            .join(Order, OrderItem.order_id == Order.id)
            .where(
                Order.status == OrderStatus.paid,
                Book.author_id == profile.id,
            )
            .group_by(Book.id, Book.slug, Book.title)
            .order_by(func.sum(OrderItem.author_earning).desc())
            .limit(5)
        )
    ).all()
    top_books = [
        {
            "id": str(r.id),
            "slug": r.slug,
            "title": r.title,
            "earning": float(r.earning),
            "units": int(r.units),
        }
        for r in top_books_rows
    ]

    return {
        "currency": "UZS",
        "series": series,
        "totals": {
            "gross": float(totals_row[0]),
            "earning": float(totals_row[1]),
            "units": int(totals_row[2]),
        },
        "top_books": top_books,
    }
