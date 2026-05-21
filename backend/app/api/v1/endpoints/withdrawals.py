"""Withdrawal endpoints.

Two routers live here:

- ``author_router`` — mounted as part of ``/authors``. Lets the logged-in
  author check their balance, request a payout, list their own
  requests, and cancel a still-pending one.
- ``admin_router`` — mounted at ``/admin/withdrawals``. Admins move
  requests through the approval workflow (approve → processing →
  completed), or reject them outright.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models import User, WithdrawalStatus
from app.schemas.withdrawal import (
    AuthorBalance,
    WithdrawalCreate,
    WithdrawalDecision,
    WithdrawalList,
    WithdrawalPublic,
)
from app.services import withdrawal_service

author_router = APIRouter(prefix="/authors", tags=["withdrawals"])
admin_router = APIRouter(prefix="/admin/withdrawals", tags=["withdrawals"])


@author_router.get(
    "/me/balance",
    response_model=AuthorBalance,
    summary="Available / pending balance + commission rate for the current author",
)
async def read_my_balance(
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> AuthorBalance:
    profile = await withdrawal_service.get_author_profile_for_user(db, user)
    return AuthorBalance.model_validate(
        withdrawal_service.author_balance_snapshot(profile)
    )


@author_router.post(
    "/me/withdrawals",
    response_model=WithdrawalPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Request a payout from the available balance",
)
async def request_withdrawal(
    data: WithdrawalCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> WithdrawalPublic:
    row = await withdrawal_service.create_request(
        db,
        user,
        amount=data.amount,
        bank_details_override=data.bank_details,
    )
    await db.commit()
    return WithdrawalPublic.model_validate(row)


@author_router.get(
    "/me/withdrawals",
    response_model=WithdrawalList,
    summary="List the current author's withdrawal requests",
)
async def list_my_withdrawals(
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> WithdrawalList:
    items, total = await withdrawal_service.list_for_author(
        db, user, page=page, page_size=page_size
    )
    return WithdrawalList(
        items=[WithdrawalPublic.model_validate(w) for w in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@author_router.post(
    "/me/withdrawals/{withdrawal_id}/cancel",
    response_model=WithdrawalPublic,
    summary="Author cancels a still-pending withdrawal",
)
async def cancel_my_withdrawal(
    withdrawal_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> WithdrawalPublic:
    row = await withdrawal_service.cancel_by_author(db, user, withdrawal_id)
    await db.commit()
    return WithdrawalPublic.model_validate(row)


# ---------- admin ----------


@admin_router.get(
    "",
    response_model=WithdrawalList,
    summary="List withdrawal requests (admin)",
)
async def admin_list_withdrawals(
    _: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: WithdrawalStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> WithdrawalList:
    items, total = await withdrawal_service.admin_list(
        db, page=page, page_size=page_size, status=status_filter
    )
    return WithdrawalList(
        items=[WithdrawalPublic.model_validate(w) for w in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.post(
    "/{withdrawal_id}/approve",
    response_model=WithdrawalPublic,
    summary="Approve a requested withdrawal",
)
async def admin_approve_withdrawal(
    withdrawal_id: UUID,
    data: WithdrawalDecision,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> WithdrawalPublic:
    row = await withdrawal_service.admin_approve(
        db, admin, withdrawal_id, admin_notes=data.admin_notes
    )
    await db.commit()
    return WithdrawalPublic.model_validate(row)


@admin_router.post(
    "/{withdrawal_id}/processing",
    response_model=WithdrawalPublic,
    summary="Mark an approved withdrawal as processing (bank transfer in-flight)",
)
async def admin_mark_withdrawal_processing(
    withdrawal_id: UUID,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> WithdrawalPublic:
    row = await withdrawal_service.admin_mark_processing(db, admin, withdrawal_id)
    await db.commit()
    return WithdrawalPublic.model_validate(row)


@admin_router.post(
    "/{withdrawal_id}/complete",
    response_model=WithdrawalPublic,
    summary="Mark a processing withdrawal as completed (funds delivered)",
)
async def admin_complete_withdrawal(
    withdrawal_id: UUID,
    data: WithdrawalDecision,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> WithdrawalPublic:
    row = await withdrawal_service.admin_mark_completed(
        db, admin, withdrawal_id, transaction_ref=data.transaction_ref
    )
    await db.commit()
    return WithdrawalPublic.model_validate(row)


@admin_router.post(
    "/{withdrawal_id}/reject",
    response_model=WithdrawalPublic,
    summary="Reject a withdrawal and return the amount to available balance",
)
async def admin_reject_withdrawal(
    withdrawal_id: UUID,
    data: WithdrawalDecision,
    admin: Annotated[User, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
) -> WithdrawalPublic:
    row = await withdrawal_service.admin_reject(
        db, admin, withdrawal_id, admin_notes=data.admin_notes
    )
    await db.commit()
    return WithdrawalPublic.model_validate(row)
