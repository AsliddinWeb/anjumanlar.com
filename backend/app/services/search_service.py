"""Flatten ORM books into Meilisearch documents + translate sort strings.

Pure helpers — Celery tasks (``app.tasks.search_tasks``) own the I/O.
"""

from __future__ import annotations

from typing import Any

from app.models import Book

# Map our ``?sort=`` query keys onto Meili's ``attribute:direction`` syntax.
SORT_MAP: dict[str, list[str]] = {
    "-published_at": ["published_at_ts:desc"],
    "published_at": ["published_at_ts:asc"],
    "-created_at": ["created_at_ts:desc"],
    "created_at": ["created_at_ts:asc"],
    "price": ["price:asc"],
    "-price": ["price:desc"],
    "-average_rating": ["average_rating:desc"],
    "-sales_count": ["sales_count:desc"],
    "-views_count": ["views_count:desc"],
}
DEFAULT_SORT = "-published_at"


def book_to_document(book: Book) -> dict[str, Any]:
    """Flatten a Book ORM row into the dict Meilisearch wants.

    JSONB ``title`` / ``description`` are spread into per-locale top-level
    fields so the searchable-attributes list can target them directly.
    """
    title = book.title or {}
    desc = book.description or {}
    return {
        "id": str(book.id),
        "slug": book.slug,
        "title_uz": title.get("uz") or "",
        "title_ru": title.get("ru") or "",
        "title_en": title.get("en") or "",
        "description_uz": desc.get("uz") or "",
        "description_ru": desc.get("ru") or "",
        "description_en": desc.get("en") or "",
        "language": book.language.value if hasattr(book.language, "value") else book.language,
        "price": float(book.price),
        "is_free": bool(book.is_free),
        "featured": bool(book.featured),
        "category_ids": [str(c.id) for c in (book.categories or [])],
        "category_slugs": [c.slug for c in (book.categories or [])],
        "author_id": str(book.author_id),
        "author_slug": book.author.slug if book.author else "",
        "author_name": book.author.display_name if book.author else "",
        "publisher": book.publisher or "",
        "isbn": book.isbn or "",
        "cover_url": book.cover_url,
        "average_rating": float(book.average_rating),
        "reviews_count": int(book.reviews_count),
        "sales_count": int(book.sales_count),
        "views_count": int(book.views_count),
        "published_at_ts": int(book.published_at.timestamp()) if book.published_at else None,
        "created_at_ts": int(book.created_at.timestamp()) if book.created_at else None,
    }


def translate_sort(sort: str | None) -> list[str]:
    return SORT_MAP.get(sort or DEFAULT_SORT, SORT_MAP[DEFAULT_SORT])


def build_filters(
    *,
    category_slug: str | None = None,
    language: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    is_free: bool | None = None,
    featured: bool | None = None,
) -> list[str] | None:
    """Compose a Meilisearch filter expression list."""
    parts: list[str] = []
    if category_slug:
        # Array membership — Meili matches if the value is in ``category_slugs``.
        parts.append(f'category_slugs = "{category_slug}"')
    if language:
        parts.append(f'language = "{language}"')
    if min_price is not None:
        parts.append(f"price >= {min_price}")
    if max_price is not None:
        parts.append(f"price <= {max_price}")
    if is_free is not None:
        parts.append(f"is_free = {str(bool(is_free)).lower()}")
    if featured is not None:
        parts.append(f"featured = {str(bool(featured)).lower()}")
    return parts or None


__all__ = [
    "DEFAULT_SORT",
    "SORT_MAP",
    "book_to_document",
    "build_filters",
    "translate_sort",
]
