"""Review-request service — state transitions + listing.

Most endpoints translate directly to one of these functions. The state
guards live here so the HTTP layer stays a thin wrapper.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models import (
    AuthorProfile,
    ReviewCategory,
    ReviewRequest,
    ReviewRequestStatus,
    User,
    UserRole,
)
from app.schemas.review_request import (
    ReviewRequestCreate,
    ReviewRequestQuote,
    ReviewRequestSubmit,
)
from app.services import storage_service


def _load_options():
    return (
        selectinload(ReviewRequest.requester),
        selectinload(ReviewRequest.author),
        selectinload(ReviewRequest.category),
    )


async def _get(db: AsyncSession, request_id: UUID) -> ReviewRequest:
    row = (
        await db.execute(
            select(ReviewRequest).options(*_load_options()).where(ReviewRequest.id == request_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "Review request not found", details={"code": "review_request_not_found"}
        )
    return row


def _is_admin(user: User) -> bool:
    return user.role in {UserRole.admin, UserRole.superadmin}


async def _assert_visible(db: AsyncSession, request: ReviewRequest, user: User) -> None:
    """Requester + assigned author + admin can read; everyone else is rejected."""
    if _is_admin(user):
        return
    if request.requester_id == user.id:
        return
    if request.author_id is not None:
        author = request.author
        if author is None:
            author = (
                await db.execute(
                    select(AuthorProfile).where(AuthorProfile.id == request.author_id)
                )
            ).scalar_one_or_none()
        if author is not None and author.user_id == user.id:
            return
    raise ForbiddenError("Not your review request", details={"code": "not_visible"})


# ---------- Requester actions ----------


async def create(
    db: AsyncSession, requester: User, data: ReviewRequestCreate
) -> ReviewRequest:
    category = (
        await db.execute(
            select(ReviewCategory).where(ReviewCategory.id == data.category_id)
        )
    ).scalar_one_or_none()
    if category is None or not category.is_active:
        raise ValidationError(
            "Review category not found", details={"code": "review_category_not_found"}
        )

    row = ReviewRequest(
        requester_id=requester.id,
        author_id=None,
        category_id=category.id,
        is_international=data.is_international,
        notes=data.notes,
        status=ReviewRequestStatus.pending,
    )
    db.add(row)
    await db.flush()
    return await _get(db, row.id)


async def upload_manuscript(
    db: AsyncSession,
    user: User,
    request_id: UUID,
    raw: bytes,
    content_type: str,
    filename: str | None,
) -> ReviewRequest:
    request = await _get(db, request_id)
    if request.requester_id != user.id and not _is_admin(user):
        raise ForbiddenError("Not your request", details={"code": "not_owner"})
    if request.status not in {ReviewRequestStatus.pending, ReviewRequestStatus.quoted}:
        raise ConflictError(
            "Manuscript can only be (re-)uploaded before payment",
            details={"code": "wrong_status", "status": request.status.value},
        )
    url, safe_name = storage_service.upload_review_manuscript(
        request.id, raw, content_type, filename
    )
    request.manuscript_url = url
    request.manuscript_filename = safe_name
    await db.flush()
    return await _get(db, request.id)


# ---------- Quote / submit (admin or assigned author) ----------


def _can_quote_or_submit(user: User, request: ReviewRequest) -> bool:
    """Admin always can; an assigned author can only if they're the target."""
    if _is_admin(user):
        return True
    return (
        request.author is not None
        and request.author.user_id == user.id
    )


async def quote(
    db: AsyncSession, user: User, request_id: UUID, data: ReviewRequestQuote
) -> ReviewRequest:
    request = await _get(db, request_id)
    if not _can_quote_or_submit(user, request):
        raise ForbiddenError("Not your request to quote", details={"code": "not_target"})
    if request.status not in {ReviewRequestStatus.pending, ReviewRequestStatus.quoted}:
        raise ConflictError(
            "Can only quote a request that's still awaiting payment",
            details={"code": "wrong_status", "status": request.status.value},
        )
    if request.manuscript_url is None:
        raise ConflictError(
            "Manuscript is not uploaded yet",
            details={"code": "manuscript_missing"},
        )

    request.final_price = data.final_price
    request.status = ReviewRequestStatus.quoted
    request.quoted_at = datetime.now(UTC)
    await db.flush()
    return await _get(db, request.id)


async def submit_review(
    db: AsyncSession,
    user: User,
    request_id: UUID,
    data: ReviewRequestSubmit,
    review_file: tuple[bytes, str] | None = None,
) -> ReviewRequest:
    request = await _get(db, request_id)
    if not _can_quote_or_submit(user, request):
        raise ForbiddenError("Not your request to submit", details={"code": "not_target"})
    if request.status != ReviewRequestStatus.paid:
        raise ConflictError(
            "Can only submit a review after payment",
            details={"code": "wrong_status", "status": request.status.value},
        )

    request.review_text = data.review_text
    if review_file is not None:
        raw, content_type = review_file
        request.review_file_url = storage_service.upload_review_response_file(
            request.id, raw, content_type
        )
    request.status = ReviewRequestStatus.completed
    request.completed_at = datetime.now(UTC)
    await db.flush()
    return await _get(db, request.id)


# ---------- Payment (mark-as-paid for now; Phase J adds Payme webhook) ----------


async def mark_paid(db: AsyncSession, user: User, request_id: UUID) -> ReviewRequest:
    """Move a quoted request to paid.

    Phase G uses a manual action (requester button after they "pay")
    instead of a Payme webhook — we'll wire the real flow in Phase J.
    Admin can also flip this from the panel.
    """
    request = await _get(db, request_id)
    if not _is_admin(user) and request.requester_id != user.id:
        raise ForbiddenError("Not your request", details={"code": "not_owner"})
    if request.status != ReviewRequestStatus.quoted:
        raise ConflictError(
            "Only quoted requests can be paid",
            details={"code": "wrong_status", "status": request.status.value},
        )
    if request.final_price is None:
        raise ConflictError(
            "Author hasn't set a price yet",
            details={"code": "missing_quote"},
        )
    request.status = ReviewRequestStatus.paid
    request.paid_at = datetime.now(UTC)
    await db.flush()
    return await _get(db, request.id)


# ---------- Cancel ----------


async def cancel(
    db: AsyncSession, user: User, request_id: UUID, reason: str | None
) -> ReviewRequest:
    request = await _get(db, request_id)

    # Visibility check: requester, target author, or admin.
    if not _is_admin(user):
        if request.requester_id != user.id and (
            request.author is None or request.author.user_id != user.id
        ):
            raise ForbiddenError("Not your request", details={"code": "not_visible"})

    if request.status in {ReviewRequestStatus.completed, ReviewRequestStatus.cancelled}:
        raise ConflictError(
            "Cannot cancel a request in this state",
            details={"code": "wrong_status", "status": request.status.value},
        )

    request.status = ReviewRequestStatus.cancelled
    request.cancelled_at = datetime.now(UTC)
    if reason:
        request.cancellation_reason = reason
    await db.flush()
    return await _get(db, request.id)


# ---------- Listing ----------


async def list_for_requester(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    page_size: int,
    status: ReviewRequestStatus | None = None,
) -> tuple[list[ReviewRequest], int]:
    base = (
        select(ReviewRequest)
        .options(*_load_options())
        .where(ReviewRequest.requester_id == user.id)
    )
    if status is not None:
        base = base.where(ReviewRequest.status == status)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(ReviewRequest.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows), total


async def list_incoming_for_author(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    page_size: int,
    status: ReviewRequestStatus | None = None,
) -> tuple[list[ReviewRequest], int]:
    profile = (
        await db.execute(select(AuthorProfile).where(AuthorProfile.user_id == user.id))
    ).scalar_one_or_none()
    if profile is None:
        return [], 0

    base = (
        select(ReviewRequest)
        .options(*_load_options())
        .where(ReviewRequest.author_id == profile.id)
    )
    if status is not None:
        base = base.where(ReviewRequest.status == status)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(ReviewRequest.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows), total


async def admin_list(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: ReviewRequestStatus | None = None,
) -> tuple[list[ReviewRequest], int]:
    base = select(ReviewRequest).options(*_load_options())
    if status is not None:
        base = base.where(ReviewRequest.status == status)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(ReviewRequest.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows), total


async def get_for_user(
    db: AsyncSession, user: User, request_id: UUID
) -> ReviewRequest:
    request = await _get(db, request_id)
    await _assert_visible(db, request, user)
    return request
