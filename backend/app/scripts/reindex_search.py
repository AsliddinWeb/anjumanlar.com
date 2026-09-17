"""Rebuild the Meilisearch ``books`` index from Postgres.

Per-book syncs only fire on approve/reject/delete (see
``app.tasks.search_tasks``), so a field added to
``search_service.book_to_document`` after books were already approved
never reaches Meili until something re-pushes those documents. Run
this once after such a change (e.g. the ``co_authors`` field) to
backfill every already-approved book in one pass.

Usage::

    docker compose exec backend python -m app.scripts.reindex_search
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.integrations.meilisearch_client import upsert_book_document
from app.models import Book, BookStatus
from app.services import search_service

logger = logging.getLogger("reindex_search")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [reindex] %(message)s")


async def _run() -> None:
    async with AsyncSessionLocal() as session:
        rows = (
            (
                await session.execute(
                    select(Book)
                    .options(
                        selectinload(Book.author),
                        selectinload(Book.categories),
                        selectinload(Book.publication_type),
                    )
                    .where(Book.status == BookStatus.approved)
                )
            )
            .scalars()
            .unique()
            .all()
        )

    for book in rows:
        upsert_book_document(search_service.book_to_document(book))
    logger.info("reindexed %d approved book(s)", len(rows))


if __name__ == "__main__":
    asyncio.run(_run())
