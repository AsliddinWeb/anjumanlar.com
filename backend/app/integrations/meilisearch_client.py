"""Meilisearch SDK wrapper.

The SDK is sync — Celery tasks call it directly; FastAPI endpoints
wrap it in :func:`asyncio.to_thread` so we don't block the event loop
on a (typically <50 ms) round trip.

Index settings (searchable / filterable / sortable attributes) are
applied lazily on first use via :func:`ensure_books_index_settings`,
which is idempotent — running it twice is a no-op once Meili acks.
"""

from __future__ import annotations

import logging
from typing import Any

from meilisearch import Client

from app.config import settings

logger = logging.getLogger(__name__)

BOOKS_INDEX = "books"

_SEARCHABLE = [
    "title_uz",
    "title_ru",
    "title_en",
    "description_uz",
    "description_ru",
    "description_en",
    "author_name",
    "publisher",
    "isbn",
]
_FILTERABLE = [
    "language",
    "is_free",
    "featured",
    "price",
    "category_ids",
    "category_slugs",
    "author_id",
    "author_slug",
]
_SORTABLE = [
    "price",
    "average_rating",
    "sales_count",
    "views_count",
    "published_at_ts",
    "created_at_ts",
]

_settings_applied = False


def get_client() -> Client:
    return Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_MASTER_KEY)


def ensure_books_index_settings() -> None:
    """Apply searchable/filterable/sortable settings on the ``books`` index.

    Cached in-process to avoid re-issuing the same update every call —
    Meili dedupes silently but the wire chatter adds up across workers.
    """
    global _settings_applied
    if _settings_applied:
        return

    client = get_client()
    # Create the index if it doesn't exist yet (Meili auto-creates on first
    # write, but explicit creation is cheap and makes settings deterministic).
    try:
        client.create_index(BOOKS_INDEX, {"primaryKey": "id"})
    except Exception as exc:
        logger.debug("books index already exists or create skipped: %s", exc)

    index = client.index(BOOKS_INDEX)
    index.update_searchable_attributes(_SEARCHABLE)
    index.update_filterable_attributes(_FILTERABLE)
    index.update_sortable_attributes(_SORTABLE)
    _settings_applied = True


def upsert_book_document(doc: dict[str, Any]) -> None:
    ensure_books_index_settings()
    get_client().index(BOOKS_INDEX).add_documents([doc], primary_key="id")


def delete_book_document(book_id: str) -> None:
    """Idempotent — 404 from Meili just means the doc was already gone."""
    try:
        get_client().index(BOOKS_INDEX).delete_document(book_id)
    except Exception:
        logger.exception("delete_book_document failed for %s", book_id)


def search_books(
    q: str | None,
    *,
    filters: list[str] | None = None,
    sort: list[str] | None = None,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    ensure_books_index_settings()
    return (
        get_client()
        .index(BOOKS_INDEX)
        .search(
            q or "",
            {
                "limit": page_size,
                "offset": (page - 1) * page_size,
                "filter": filters,
                "sort": sort,
                "attributesToRetrieve": ["id"],
            },
        )
    )


__all__ = [
    "BOOKS_INDEX",
    "delete_book_document",
    "ensure_books_index_settings",
    "get_client",
    "search_books",
    "upsert_book_document",
]
