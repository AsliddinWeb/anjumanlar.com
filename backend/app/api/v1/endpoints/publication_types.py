"""Publication type endpoints — public reads, admin writes.

Same shape as /categories: flat list + slug lookup are open, mutations
sit behind `require_admin_scope("categories")` since this is the same
"catalog taxonomy management" bucket as subject categories.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin_scope
from app.models import User
from app.schemas.publication_type import (
    PublicationTypeCreate,
    PublicationTypeList,
    PublicationTypePublic,
    PublicationTypeUpdate,
)
from app.services import publication_type_service

router = APIRouter(prefix="/publication-types", tags=["publication-types"])


@router.get(
    "",
    response_model=PublicationTypeList,
    summary="Flat publication-type list (sorted)",
)
async def list_publication_types(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> PublicationTypeList:
    rows = await publication_type_service.list_all(db, active_only=active_only)
    return PublicationTypeList(
        items=[PublicationTypePublic.model_validate(r) for r in rows],
        total=len(rows),
    )


@router.get(
    "/{slug}",
    response_model=PublicationTypePublic,
    summary="Get one publication type by slug",
)
async def read_publication_type(
    slug: str, db: AsyncSession = Depends(get_db)
) -> PublicationTypePublic:
    return PublicationTypePublic.model_validate(
        await publication_type_service.get_by_slug(db, slug)
    )


@router.post(
    "",
    response_model=PublicationTypePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a publication type (admin+)",
)
async def create_publication_type(
    data: PublicationTypeCreate,
    _: Annotated[User, Depends(require_admin_scope("categories"))],
    db: AsyncSession = Depends(get_db),
) -> PublicationTypePublic:
    row = await publication_type_service.create(db, data)
    await db.commit()
    return PublicationTypePublic.model_validate(row)


@router.patch(
    "/{publication_type_id}",
    response_model=PublicationTypePublic,
    summary="Update a publication type (admin+)",
)
async def update_publication_type(
    publication_type_id: UUID,
    data: PublicationTypeUpdate,
    _: Annotated[User, Depends(require_admin_scope("categories"))],
    db: AsyncSession = Depends(get_db),
) -> PublicationTypePublic:
    row = await publication_type_service.update(db, publication_type_id, data)
    await db.commit()
    return PublicationTypePublic.model_validate(row)


@router.delete(
    "/{publication_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a publication type (admin+); books' publication_type_id becomes NULL",
)
async def delete_publication_type(
    publication_type_id: UUID,
    _: Annotated[User, Depends(require_admin_scope("categories"))],
    db: AsyncSession = Depends(get_db),
) -> None:
    await publication_type_service.delete(db, publication_type_id)
    await db.commit()
