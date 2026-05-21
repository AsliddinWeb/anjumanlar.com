"""Public book search backed by Meilisearch.

Meili gives us back ranked ID's; Postgres supplies the full Book rows so
the response payload matches what the catalogue endpoint produces.
"""

from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.integrations.meilisearch_client import search_books as meili_search
from app.models import Book, BookStatus
from app.schemas.book import BookList, BookPublic
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=BookList,
    summary="Full-text search across approved books (Meilisearch-backed)",
)
async def search(
    q: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    category: str | None = Query(None, description="Category slug"),
    language: str | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    is_free: bool | None = None,
    featured: bool | None = None,
    sort: str = Query("-published_at"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> BookList:
    filters = search_service.build_filters(
        category_slug=category,
        language=language,
        min_price=min_price,
        max_price=max_price,
        is_free=is_free,
        featured=featured,
    )
    sort_clauses = search_service.translate_sort(sort)

    # Meili SDK is sync — run it off the event loop.
    raw = await asyncio.to_thread(
        meili_search,
        q,
        filters=filters,
        sort=sort_clauses,
        page=page,
        page_size=page_size,
    )
    hit_ids = [UUID(hit["id"]) for hit in raw.get("hits", [])]
    if not hit_ids:
        return BookList(
            items=[],
            total=int(raw.get("estimatedTotalHits") or 0),
            page=page,
            page_size=page_size,
        )

    rows = (
        (
            await db.execute(
                select(Book)
                .options(selectinload(Book.author), selectinload(Book.categories))
                .where(
                    Book.id.in_(hit_ids),
                    Book.status == BookStatus.approved,
                    Book.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .unique()
        .all()
    )
    rows_by_id: dict[UUID, Book] = {r.id: r for r in rows}
    # Preserve Meili's ranking order; drop hits whose Postgres row is gone.
    ordered = [rows_by_id[i] for i in hit_ids if i in rows_by_id]

    return BookList(
        items=[BookPublic.model_validate(b) for b in ordered],
        total=int(raw.get("estimatedTotalHits") or 0),
        page=page,
        page_size=page_size,
    )
