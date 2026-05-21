"""Celery tasks that produce derived PDFs.

Two tasks live here:

- ``pdf.generate_demo`` — downloads the canonical PDF for a book,
  extracts the first N pages, uploads the result to the public ``demos``
  bucket, and writes ``book.demo_url`` back to the DB.
- ``pdf.watermark`` — Phase 4 will fire this on a successful purchase to
  build a per-buyer copy stamped with their email + the purchase date.
  The task lands now so the surface is stable; Phase 4 will wire the
  call from the payment-success handler.

Each task opens its own SQLAlchemy session because Celery workers run
outside any FastAPI request context.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations.minio_client import get_bytes, put_bytes
from app.models import Book
from app.services import pdf_service
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

DEMO_PAGE_COUNT = 10


async def _set_book_field(book_id: UUID, **fields: object) -> None:
    """Open a fresh async session, update the named columns, commit."""
    async with AsyncSessionLocal() as session:
        book = (await session.execute(select(Book).where(Book.id == book_id))).scalar_one_or_none()
        if book is None:
            logger.warning("pdf task: book %s vanished before update", book_id)
            return
        for key, value in fields.items():
            setattr(book, key, value)
        await session.commit()


@celery_app.task(
    name="pdf.generate_demo",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(OSError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
)
def generate_demo_pdf(self, book_id: str) -> str:
    """Pull the original PDF, extract a demo, upload it, set ``book.demo_url``.

    Returns the demo URL on success; raises (and retries) on transient
    MinIO failures.
    """
    object_key = f"{book_id}.pdf"
    raw = get_bytes(settings.MINIO_BUCKET_BOOKS, object_key)
    demo_bytes = pdf_service.extract_first_n_pages(raw, n=DEMO_PAGE_COUNT)
    demo_url = put_bytes(
        settings.MINIO_BUCKET_DEMOS,
        object_key,
        demo_bytes,
        "application/pdf",
    )
    asyncio.run(_set_book_field(UUID(book_id), demo_url=demo_url))
    logger.info("pdf.generate_demo OK book=%s url=%s", book_id, demo_url)
    return demo_url


@celery_app.task(
    name="pdf.watermark",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(OSError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
)
def watermark_pdf(self, book_id: str, user_id: str, watermark_text: str) -> str:
    """Build a per-buyer watermarked copy and store it in the private
    ``books-watermarked`` bucket, keyed by ``<user_id>/<book_id>.pdf``.

    Phase 4 will invoke this after a successful Payme payment. The
    returned URL is private — only signed downloads through the API can
    serve it.
    """
    raw = get_bytes(settings.MINIO_BUCKET_BOOKS, f"{book_id}.pdf")
    stamped = pdf_service.apply_watermark(raw, watermark_text)
    key = f"{user_id}/{book_id}.pdf"
    url = put_bytes(
        settings.MINIO_BUCKET_BOOKS_WM,
        key,
        stamped,
        "application/pdf",
    )
    logger.info("pdf.watermark OK book=%s user=%s key=%s", book_id, user_id, key)
    return url


__all__ = ["generate_demo_pdf", "watermark_pdf"]
