"""Author profile endpoints.

Two halves:

- ``/authors/me`` — managed by the logged-in user (create + read + update).
- ``/authors/...`` — public read-only listings + slug lookup.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.author import (
    AuthorList,
    AuthorPrivate,
    AuthorProfileUpdate,
    AuthorPublic,
    BecomeAuthorRequest,
)
from app.services import author_service

router = APIRouter(prefix="/authors", tags=["authors"])


@router.post(
    "/me",
    response_model=AuthorPrivate,
    status_code=status.HTTP_201_CREATED,
    summary="Become an author (creates the profile, upgrades role to author)",
)
async def create_my_author_profile(
    data: BecomeAuthorRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> AuthorPrivate:
    profile = await author_service.become_author(db, user, data)
    await db.commit()
    return AuthorPrivate.model_validate(profile)


@router.get(
    "/me",
    response_model=AuthorPrivate,
    summary="Get the logged-in user's author profile",
)
async def read_my_author_profile(
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> AuthorPrivate:
    profile = await author_service.get_me(db, user)
    return AuthorPrivate.model_validate(profile)


@router.patch(
    "/me",
    response_model=AuthorPrivate,
    summary="Update editable fields on the logged-in user's author profile",
)
async def update_my_author_profile(
    data: AuthorProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> AuthorPrivate:
    profile = await author_service.update_profile(db, user, data)
    await db.commit()
    return AuthorPrivate.model_validate(profile)


@router.get(
    "",
    response_model=AuthorList,
    summary="Public author directory — paginated, optional search + featured filter",
)
async def list_authors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=100),
    featured: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> AuthorList:
    items, total = await author_service.list_public(
        db, page=page, page_size=page_size, search=search, featured=featured
    )
    return AuthorList(
        items=[AuthorPublic.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{slug}",
    response_model=AuthorPublic,
    summary="Public author profile by slug",
)
async def read_author_by_slug(slug: str, db: AsyncSession = Depends(get_db)) -> AuthorPublic:
    profile = await author_service.get_public_by_slug(db, slug)
    return AuthorPublic.model_validate(profile)
