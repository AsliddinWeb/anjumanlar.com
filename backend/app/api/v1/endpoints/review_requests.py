"""Paid peer-review endpoints.

Three routers because the role gating differs per group:

- ``/review-requests``        — authenticated reader (create + own list +
                                 manuscript upload + mark-paid + cancel).
- ``/review-requests/incoming`` — authenticated author (quote +
                                   submit review).
- ``/admin/review-requests``  — admin oversight (list + force cancel).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models import ReviewRequestStatus, User
from app.schemas.review_request import (
    ReviewRequestCancel,
    ReviewRequestCreate,
    ReviewRequestList,
    ReviewRequestPublic,
    ReviewRequestQuote,
    ReviewRequestSubmit,
)
from app.services import review_request_service

router = APIRouter(prefix="/review-requests", tags=["review-requests"])
admin_router = APIRouter(prefix="/admin/review-requests", tags=["review-requests"])


# ---------- Requester ----------


@router.post(
    "",
    response_model=ReviewRequestPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a peer-review request (reader)",
)
async def create_request(
    data: ReviewRequestCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestPublic:
    row = await review_request_service.create(db, user, data)
    await db.commit()
    return ReviewRequestPublic.model_validate(row)


@router.post(
    "/{request_id}/manuscript",
    response_model=ReviewRequestPublic,
    summary="Upload the manuscript PDF for a review request",
)
async def upload_manuscript(
    request_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestPublic:
    raw = await file.read()
    row = await review_request_service.upload_manuscript(
        db, user, request_id, raw, file.content_type or "application/pdf", file.filename
    )
    await db.commit()
    return ReviewRequestPublic.model_validate(row)


@router.get(
    "/me",
    response_model=ReviewRequestList,
    summary="My outgoing review requests (as requester)",
)
async def list_my_requests(
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ReviewRequestStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestList:
    items, total = await review_request_service.list_for_requester(
        db, user, page=page, page_size=page_size, status=status_filter
    )
    return ReviewRequestList(
        items=[ReviewRequestPublic.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/incoming",
    response_model=ReviewRequestList,
    summary="Incoming review requests (as the target author)",
)
async def list_incoming(
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ReviewRequestStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestList:
    items, total = await review_request_service.list_incoming_for_author(
        db, user, page=page, page_size=page_size, status=status_filter
    )
    return ReviewRequestList(
        items=[ReviewRequestPublic.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{request_id}",
    response_model=ReviewRequestPublic,
    summary="Get a single request (requester / author / admin)",
)
async def read_request(
    request_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestPublic:
    row = await review_request_service.get_for_user(db, user, request_id)
    return ReviewRequestPublic.model_validate(row)


@router.post(
    "/{request_id}/pay",
    response_model=ReviewRequestPublic,
    summary="Mark a quoted request as paid (Phase G stub — Payme wires later)",
)
async def mark_paid(
    request_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestPublic:
    row = await review_request_service.mark_paid(db, user, request_id)
    await db.commit()
    return ReviewRequestPublic.model_validate(row)


@router.post(
    "/{request_id}/cancel",
    response_model=ReviewRequestPublic,
    summary="Cancel a request (either side or admin)",
)
async def cancel_request(
    request_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    data: ReviewRequestCancel = Body(default_factory=ReviewRequestCancel),
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestPublic:
    row = await review_request_service.cancel(db, user, request_id, data.reason)
    await db.commit()
    return ReviewRequestPublic.model_validate(row)


# ---------- Author (within /review-requests/{id}/...) ----------


@router.post(
    "/{request_id}/quote",
    response_model=ReviewRequestPublic,
    summary="Author sets the final price (moves status to quoted)",
)
async def quote_request(
    request_id: UUID,
    data: ReviewRequestQuote,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestPublic:
    row = await review_request_service.quote(db, user, request_id, data)
    await db.commit()
    return ReviewRequestPublic.model_validate(row)


@router.post(
    "/{request_id}/submit-review",
    response_model=ReviewRequestPublic,
    summary="Author submits the review (text + optional file). Status → completed.",
)
async def submit_review(
    request_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    review_text: str = Form(..., min_length=1, max_length=20_000),
    file: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestPublic:
    payload = ReviewRequestSubmit(review_text=review_text)
    file_tuple: tuple[bytes, str] | None = None
    if file is not None:
        raw = await file.read()
        file_tuple = (raw, file.content_type or "application/pdf")
    row = await review_request_service.submit_review(db, user, request_id, payload, file_tuple)
    await db.commit()
    return ReviewRequestPublic.model_validate(row)


# ---------- Admin ----------


@admin_router.get(
    "",
    response_model=ReviewRequestList,
    summary="Full review-request catalogue (admin+)",
)
async def admin_list_requests(
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ReviewRequestStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> ReviewRequestList:
    items, total = await review_request_service.admin_list(
        db, page=page, page_size=page_size, status=status_filter
    )
    return ReviewRequestList(
        items=[ReviewRequestPublic.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )
