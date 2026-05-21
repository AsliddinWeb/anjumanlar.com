"""Celery tasks for order lifecycle housekeeping.

Currently a single periodic task: walk every ``pending`` order whose
``expires_at`` has passed and flip its status to ``expired``. Runs
every minute via celery beat (see :mod:`app.tasks.celery_app`) — at
that rate the worst-case lag between TTL expiry and state change is
a minute, which is fine for a 30-minute checkout window.
"""

from __future__ import annotations

import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services import order_service
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _expire_async() -> int:
    async with AsyncSessionLocal() as session:
        count = await order_service.expire_stale(session)
        if count:
            await session.commit()
        return count


@celery_app.task(name="orders.expire_pending")
def expire_pending_orders() -> int:
    """Periodic sweep — returns the number of orders moved to expired."""
    count = asyncio.run(_expire_async())
    if count:
        logger.info("orders.expire_pending moved %s order(s) to expired", count)
    return count


__all__ = ["expire_pending_orders"]
