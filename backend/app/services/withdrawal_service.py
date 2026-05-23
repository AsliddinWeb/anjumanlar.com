"""Author payout requests.

State machine (mirrors :class:`app.models.WithdrawalStatus`):

    requested ──admin approve──> approved ──> processing ──> completed
        │                              │
        ├── admin reject ──────────────┴────> rejected
        └── author cancel (only while requested) ────────> cancelled

The dance with the author's balance: when a request is *created* we
move ``amount`` from ``available_balance`` to ``pending_balance``
optimistically. Approve + complete is a no-op on the totals (the money
stays under "pending" until the off-platform bank transfer happens and
the admin marks it complete). Reject + cancel return the funds to
``available_balance``.

Idempotency: the admin actions all check the current status before
mutating, so re-clicking "approve" doesn't double-deduct anything.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.models import AuthorProfile, User, UserRole, Withdrawal, WithdrawalStatus

logger = logging.getLogger(__name__)


# Smallest withdrawal we accept — anything below this is most likely a
# typo. 50 000 so'm covers the bank transfer fee on common Uzbek banks
# with room to spare.
MIN_WITHDRAWAL_UZS = 50_000


def author_balance_snapshot(profile: AuthorProfile) -> dict[str, Any]:
    return {
        "available_balance": float(profile.available_balance),
        "pending_balance": float(profile.pending_balance),
        "total_revenue": float(profile.total_revenue),
        "total_sales": profile.total_sales,
        "commission_rate": float(profile.commission_rate),
        "currency": "UZS",
    }


async def get_author_profile_for_user(db: AsyncSession, user: User) -> AuthorProfile:
    profile = (
        await db.execute(
            select(AuthorProfile).where(AuthorProfile.user_id == user.id)
        )
    ).scalar_one_or_none()
    if profile is None:
        raise NotFoundError(
            "You don't have an author profile yet",
            details={"code": "author_profile_missing"},
        )
    return profile


async def create_request(
    db: AsyncSession,
    user: User,
    *,
    amount: float,
    bank_details_override: dict[str, Any] | None = None,
) -> Withdrawal:
    profile = await get_author_profile_for_user(db, user)

    if amount < MIN_WITHDRAWAL_UZS:
        raise ValidationError(
            f"Minimum withdrawal is {MIN_WITHDRAWAL_UZS} UZS",
            details={"code": "amount_too_small", "min_uzs": MIN_WITHDRAWAL_UZS},
        )

    available = float(profile.available_balance)
    if amount > available:
        raise ConflictError(
            "Insufficient available balance",
            details={
                "code": "insufficient_balance",
                "available": available,
                "requested": amount,
            },
        )

    bank_details = bank_details_override or dict(profile.bank_details or {})
    if not bank_details:
        raise ValidationError(
            "Bank details required — fill them in your author profile first",
            details={"code": "bank_details_missing"},
        )

    profile.available_balance = round(available - amount, 2)
    profile.pending_balance = round(float(profile.pending_balance) + amount, 2)

    row = Withdrawal(
        author_id=profile.id,
        amount=amount,
        currency="UZS",
        bank_details=bank_details,
        status=WithdrawalStatus.requested,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    logger.info(
        "withdrawal.request author=%s amount=%s id=%s", profile.id, amount, row.id
    )
    _enqueue_withdrawal_email(user, row, template="withdrawal_requested")
    return row


async def list_for_author(
    db: AsyncSession,
    user: User,
    *,
    page: int,
    page_size: int,
) -> tuple[list[Withdrawal], int]:
    profile = await get_author_profile_for_user(db, user)
    base = select(Withdrawal).where(Withdrawal.author_id == profile.id)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(Withdrawal.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total


async def cancel_by_author(
    db: AsyncSession, user: User, withdrawal_id: UUID
) -> Withdrawal:
    """Author may pull back a request that's still ``requested``."""
    profile = await get_author_profile_for_user(db, user)
    row = await _get_for_author(db, profile, withdrawal_id)

    if row.status != WithdrawalStatus.requested:
        raise ConflictError(
            "Only requested withdrawals can be cancelled by the author",
            details={"code": "invalid_state", "current_status": row.status.value},
        )

    row.status = WithdrawalStatus.cancelled
    _return_funds(profile, float(row.amount))
    await db.flush()
    return row


# ---------- admin ----------


async def admin_list(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    status: WithdrawalStatus | None = None,
) -> tuple[list[Withdrawal], int]:
    base = select(Withdrawal)
    if status is not None:
        base = base.where(Withdrawal.status == status)
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        (
            await db.execute(
                base.order_by(Withdrawal.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total


async def admin_approve(
    db: AsyncSession,
    admin: User,
    withdrawal_id: UUID,
    *,
    admin_notes: str | None = None,
) -> Withdrawal:
    _require_admin(admin)
    row = await _get(db, withdrawal_id)
    _assert_status(row, WithdrawalStatus.requested)
    row.status = WithdrawalStatus.approved
    if admin_notes:
        row.admin_notes = admin_notes
    row.processed_by = admin.id
    row.processed_at = datetime.now(UTC)
    await db.flush()
    return row


async def admin_mark_processing(
    db: AsyncSession, admin: User, withdrawal_id: UUID
) -> Withdrawal:
    _require_admin(admin)
    row = await _get(db, withdrawal_id)
    _assert_status(row, WithdrawalStatus.approved)
    row.status = WithdrawalStatus.processing
    row.processed_by = admin.id
    row.processed_at = datetime.now(UTC)
    await db.flush()
    return row


async def admin_mark_completed(
    db: AsyncSession,
    admin: User,
    withdrawal_id: UUID,
    *,
    transaction_ref: str | None = None,
) -> Withdrawal:
    _require_admin(admin)
    row = await _get(db, withdrawal_id)
    if row.status not in (WithdrawalStatus.approved, WithdrawalStatus.processing):
        raise ConflictError(
            "Only approved or processing withdrawals can be completed",
            details={"code": "invalid_state", "current_status": row.status.value},
        )
    row.status = WithdrawalStatus.completed
    if transaction_ref:
        row.transaction_ref = transaction_ref
    row.processed_by = admin.id
    row.processed_at = datetime.now(UTC)

    # Money has now physically left the platform — clear the matching
    # amount from the author's pending bucket.
    profile = await db.get(AuthorProfile, row.author_id)
    if profile is not None:
        profile.pending_balance = max(
            0.0, round(float(profile.pending_balance) - float(row.amount), 2)
        )
    await db.flush()
    await _enqueue_withdrawal_email_for_row(db, row, template="withdrawal_completed")
    return row


async def admin_reject(
    db: AsyncSession,
    admin: User,
    withdrawal_id: UUID,
    *,
    admin_notes: str | None = None,
) -> Withdrawal:
    _require_admin(admin)
    row = await _get(db, withdrawal_id)
    if row.status not in (WithdrawalStatus.requested, WithdrawalStatus.approved):
        raise ConflictError(
            "Only requested or approved withdrawals can be rejected",
            details={"code": "invalid_state", "current_status": row.status.value},
        )

    profile = await db.get(AuthorProfile, row.author_id)
    if profile is not None:
        _return_funds(profile, float(row.amount))

    row.status = WithdrawalStatus.rejected
    if admin_notes:
        row.admin_notes = admin_notes
    row.processed_by = admin.id
    row.processed_at = datetime.now(UTC)
    await db.flush()
    await _enqueue_withdrawal_email_for_row(db, row, template="withdrawal_rejected")
    return row


# ---------- notification helpers ----------


def _enqueue_withdrawal_email(
    user: User, row: Withdrawal, *, template: str
) -> None:
    """Fire the email through Celery — silent on enqueue failure."""
    try:
        from app.tasks.email_tasks import send_template_email

        send_template_email.delay(
            to=user.email,
            template_name=template,
            locale=user.preferred_locale or "uz",
            context={
                "full_name": user.full_name,
                "email": user.email,
                "amount": float(row.amount),
                "transaction_ref": row.transaction_ref,
                "admin_notes": row.admin_notes,
            },
        )
    except Exception:
        logger.exception(
            "withdrawal email enqueue failed (withdrawal=%s template=%s)", row.id, template
        )


async def _enqueue_withdrawal_email_for_row(
    db: AsyncSession, row: Withdrawal, *, template: str
) -> None:
    """Look up the author's user record from the withdrawal row, then send."""
    profile = await db.get(AuthorProfile, row.author_id)
    if profile is None:
        return
    user = (
        await db.execute(select(User).where(User.id == profile.user_id))
    ).scalar_one_or_none()
    if user is None:
        return
    _enqueue_withdrawal_email(user, row, template=template)


# ---------- internals ----------


def _return_funds(profile: AuthorProfile, amount: float) -> None:
    """Move ``amount`` from pending back to available."""
    profile.pending_balance = max(
        0.0, round(float(profile.pending_balance) - amount, 2)
    )
    profile.available_balance = round(float(profile.available_balance) + amount, 2)


async def _get(db: AsyncSession, withdrawal_id: UUID) -> Withdrawal:
    row = (
        await db.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError(
            "Withdrawal not found", details={"code": "withdrawal_not_found"}
        )
    return row


async def _get_for_author(
    db: AsyncSession, profile: AuthorProfile, withdrawal_id: UUID
) -> Withdrawal:
    row = await _get(db, withdrawal_id)
    if row.author_id != profile.id:
        raise ForbiddenError(
            "This withdrawal doesn't belong to you",
            details={"code": "withdrawal_forbidden"},
        )
    return row


def _assert_status(row: Withdrawal, expected: WithdrawalStatus) -> None:
    if row.status != expected:
        raise ConflictError(
            f"Withdrawal is not in {expected.value} status",
            details={"code": "invalid_state", "current_status": row.status.value},
        )


def _require_admin(user: User) -> None:
    if user.role not in (UserRole.admin, UserRole.superadmin):
        raise ForbiddenError("Admin role required", details={"code": "admin_required"})
