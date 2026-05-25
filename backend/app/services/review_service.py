"""Review lifecycle.

Workflow:

    user → POST review → pending → admin approve → approved
                                 └── admin reject → rejected

- One review per (user, book) — second POST returns 409.
- Authors edit their own review while it's pending (in-place); once it's
  approved, editing flips it back to pending so a moderator can re-check.
- Phase 4 will gate the create endpoint behind a successful purchase; for
  now any active user can write a review.
- ``book.average_rating`` and ``book.reviews_count`` are recomputed from
  the approved set whenever a review crosses into / out of ``approved``
  or when an approved review's rating changes.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models import (
    Book,
    BookStatus,
    Review,
    ReviewStatus,
    User,
    UserRole,
    UserStatus,
)
from app.schemas.review import ReviewCreate, ReviewUpdate

# ---------- helpers ----------


async def _get_loaded_review(db: AsyncSession, review_id: UUID) -> Review:
    row = (
        await db.execute(
            select(Review).options(selectinload(Review.user)).where(Review.id == review_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Review not found", details={"code": "review_not_found"})
    return row


async def _recompute_book_aggregate(db: AsyncSession, book_id: UUID) -> None:
    """Recalculate ``book.average_rating`` + ``reviews_count`` from approved rows.

    Uses a single SQL roll-up rather than re-reading each row; cheap even
    with thousands of reviews per book.
    """
    stmt = select(
        func.count(Review.id).label("n"),
        func.coalesce(func.avg(case((Review.rating > 0, Review.rating))), 0).label("avg"),
    ).where(Review.book_id == book_id, Review.status == ReviewStatus.approved)
    n, avg = (await db.execute(stmt)).one()
    await db.execute(
        Book.__table__.update()
        .where(Book.id == book_id)
        .values(reviews_count=int(n), average_rating=round(float(avg), 2))
    )


async def _get_approved_book(db: AsyncSession, book_id: UUID) -> Book:
    book = (
        await db.execute(
            select(Book).where(
                Book.id == book_id,
                Book.status == BookStatus.approved,
            )
        )
    ).scalar_one_or_none()
    if book is None:
        raise NotFoundError("Book not found", details={"code": "book_not_found"})
    return book


# ---------- user actions ----------


async def create_review(db: AsyncSession, user: User, book_id: UUID, data: ReviewCreate) -> Review:
    """Create a pending review; only one per (user, book)."""
    await _get_approved_book(db, book_id)  # ensures the book is approved + visible

    duplicate = (
        await db.execute(
            select(Review.id).where(Review.user_id == user.id, Review.book_id == book_id)
        )
    ).scalar_one_or_none()
    if duplicate is not None:
        raise ConflictError(
            "You've already reviewed this book",
            details={"code": "duplicate_review"},
        )

    review = Review(
        book_id=book_id,
        user_id=user.id,
        rating=data.rating,
        title=data.title,
        body=data.body,
        status=ReviewStatus.pending,
    )
    db.add(review)
    await db.flush()
    return await _get_loaded_review(db, review.id)


async def update_review(
    db: AsyncSession, user: User, review_id: UUID, data: ReviewUpdate
) -> Review:
    review = await _get_loaded_review(db, review_id)
    if review.user_id != user.id:
        raise ForbiddenError("Not your review", details={"code": "not_owner"})

    was_approved = review.status == ReviewStatus.approved
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(review, key, value)

    # Any edit flips the review back to pending so a moderator can re-check.
    review.status = ReviewStatus.pending
    await db.flush()

    if was_approved:
        # Removed from the approved set — recompute aggregate.
        await _recompute_book_aggregate(db, review.book_id)

    return await _get_loaded_review(db, review.id)


async def delete_review(db: AsyncSession, user: User, review_id: UUID) -> None:
    review = await _get_loaded_review(db, review_id)
    is_admin = user.role in {UserRole.admin, UserRole.superadmin}
    if not is_admin and review.user_id != user.id:
        raise ForbiddenError("Not your review", details={"code": "not_owner"})
    was_approved = review.status == ReviewStatus.approved
    book_id = review.book_id
    await db.delete(review)
    await db.flush()
    if was_approved:
        await _recompute_book_aggregate(db, book_id)


# ---------- admin actions ----------


async def approve_review(db: AsyncSession, admin: User, review_id: UUID) -> Review:
    review = await _get_loaded_review(db, review_id)
    if review.status == ReviewStatus.approved:
        return review
    review.status = ReviewStatus.approved
    review.moderated_by = admin.id
    await db.flush()
    await _recompute_book_aggregate(db, review.book_id)
    return await _get_loaded_review(db, review.id)


async def reject_review(db: AsyncSession, admin: User, review_id: UUID) -> Review:
    review = await _get_loaded_review(db, review_id)
    was_approved = review.status == ReviewStatus.approved
    review.status = ReviewStatus.rejected
    review.moderated_by = admin.id
    await db.flush()
    if was_approved:
        await _recompute_book_aggregate(db, review.book_id)
    return await _get_loaded_review(db, review.id)


# ---------- read paths ----------


async def list_for_book(
    db: AsyncSession,
    book_id: UUID,
    *,
    page: int,
    page_size: int,
) -> tuple[list[Review], int]:
    """Public list — only approved reviews from active users."""
    base = (
        select(Review)
        .options(selectinload(Review.user))
        .join(User, Review.user_id == User.id)
        .where(
            Review.book_id == book_id,
            Review.status == ReviewStatus.approved,
            User.status != UserStatus.blocked,
        )
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(Review.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows), total


async def list_pending(db: AsyncSession, *, page: int, page_size: int) -> tuple[list[Review], int]:
    return await admin_list(db, page=page, page_size=page_size, status=ReviewStatus.pending)


async def admin_list(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: ReviewStatus | None = None,
) -> tuple[list[Review], int]:
    """Admin list with optional status filter (None = all statuses).

    Sorted oldest-first when filtering by pending (so the moderation
    queue surfaces the oldest waiters first) and newest-first otherwise.
    """
    base = select(Review).options(selectinload(Review.user))
    if status is not None:
        base = base.where(Review.status == status)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    order = Review.created_at.asc() if status == ReviewStatus.pending else Review.created_at.desc()
    rows = (
        (
            await db.execute(
                base.order_by(order).offset((page - 1) * page_size).limit(page_size)
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows), total
