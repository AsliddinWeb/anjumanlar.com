"""Periodic review-reminder fan-out.

Runs once a day from Celery beat. Picks orders paid REMINDER_DELAY_DAYS
days ago that don't yet have a review for the purchased book, and
enqueues a single ``review_reminder`` email per (user, book) pair so a
reader who bought five books in one order gets five reminders — each
linking back to the right book page.

Idempotency: we look at orders paid on EXACTLY the cutoff date (UTC
day), so a reader who already received a reminder yesterday won't be
hit again today. Combined with the "skip if a review already exists"
filter, double-sends are not possible under steady-state load.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, exists, not_, select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models import (
    Book,
    Order,
    OrderItem,
    OrderStatus,
    Review,
    User,
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

REMINDER_DELAY_DAYS = 3


def _pick_title(title_map: dict[str, str] | None, locale: str | None) -> str:
    if not title_map:
        return ""
    for key in (locale or "uz", "uz", "en", "ru"):
        v = title_map.get(key)
        if v and v.strip():
            return v
    return next(iter(title_map.values()), "")


async def _send_reminders() -> int:
    """Find eligible (user, book) pairs and queue one email each."""
    from app.tasks.email_tasks import send_template_email

    async with AsyncSessionLocal() as session:
        today_utc = datetime.now(UTC)
        day_start = datetime(today_utc.year, today_utc.month, today_utc.day, tzinfo=UTC) \
            - timedelta(days=REMINDER_DELAY_DAYS)
        day_end = day_start + timedelta(days=1)

        review_exists = exists(
            select(Review.id).where(
                Review.user_id == Order.user_id,
                Review.book_id == OrderItem.book_id,
            )
        )

        stmt = (
            select(Order, OrderItem, Book, User)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Book, Book.id == OrderItem.book_id)
            .join(User, User.id == Order.user_id)
            .where(
                and_(
                    Order.status == OrderStatus.paid,
                    Order.paid_at >= day_start,
                    Order.paid_at < day_end,
                    not_(review_exists),
                )
            )
            .options(selectinload(Book.author))
        )
        rows = (await session.execute(stmt)).all()

    sent = 0
    seen_pairs: set[tuple[str, str]] = set()
    for _order, item, book, user in rows:
        pair = (str(user.id), str(item.book_id))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        try:
            send_template_email.delay(
                to=user.email,
                template_name="review_reminder",
                locale=user.preferred_locale or "uz",
                context={
                    "full_name": user.full_name,
                    "book_title": _pick_title(book.title, user.preferred_locale),
                    "book_slug": book.slug,
                },
            )
            sent += 1
        except Exception:  # noqa: BLE001 — broker may be down; skip + log
            logger.exception("review_reminder enqueue failed user=%s book=%s", user.id, book.id)

    return sent


@celery_app.task(name="reviews.send_reminders", bind=True)
def send_review_reminders(self) -> int:  # noqa: ARG001 — bind for retry compat
    """Public entry point for beat. Returns the number of emails queued."""
    sent = asyncio.run(_send_reminders())
    logger.info("reviews.send_reminders queued=%s", sent)
    return sent


__all__ = ["send_review_reminders"]
