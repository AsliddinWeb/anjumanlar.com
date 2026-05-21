"""Celery tasks that keep Meilisearch in sync with Postgres.

Three triggers fire :func:`sync_book_to_meilisearch`:

- admin ``approve`` → book becomes searchable.
- admin ``reject`` → book is removed (it never should have been there).
- ``soft_delete`` → ditto.

The remove path is idempotent so re-firing on a missing doc is fine.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.integrations.meilisearch_client import (
    delete_book_document,
    upsert_book_document,
)
from app.models import Book
from app.services import search_service
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _load_book(book_id: UUID) -> Book | None:
    """Fetch + eager-load relationships we need to build the doc."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Book)
            .options(selectinload(Book.author), selectinload(Book.categories))
            .where(Book.id == book_id)
        )
        return result.scalar_one_or_none()


@celery_app.task(
    name="search.sync_book",
    bind=True,
    max_retries=5,
    default_retry_delay=15,
    autoretry_for=(OSError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
)
def sync_book_to_meilisearch(self, book_id: str) -> str:
    """Push the book's document to Meilisearch. Returns the doc id on success."""
    book = asyncio.run(_load_book(UUID(book_id)))
    if book is None:
        logger.warning("search.sync_book: book %s vanished", book_id)
        return book_id
    doc = search_service.book_to_document(book)
    upsert_book_document(doc)
    logger.info("search.sync_book OK book=%s", book_id)
    return book_id


@celery_app.task(
    name="search.remove_book",
    bind=True,
    max_retries=5,
    default_retry_delay=15,
    autoretry_for=(OSError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
)
def remove_book_from_meilisearch(self, book_id: str) -> str:
    delete_book_document(book_id)
    logger.info("search.remove_book OK book=%s", book_id)
    return book_id


__all__ = ["remove_book_from_meilisearch", "sync_book_to_meilisearch"]
