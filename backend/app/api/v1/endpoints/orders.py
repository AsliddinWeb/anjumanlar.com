"""Order endpoints — create / list / read / cancel.

POST /orders kicks off the checkout flow: the service-layer locks in
prices and commission, the response carries a placeholder
``payment_url`` field that the Payme integration (Phase 4.4) will
populate.

``admin_router`` (mounted at /admin/orders) gives staff the full order
table — every buyer's orders, with buyer identity and the raw payment
attempts, for support and reconciliation.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_current_user, require_admin_scope
from app.integrations.payme.client import build_checkout_url
from app.models import OrderStatus, User
from app.schemas.order import (
    OrderAdminDetail,
    OrderAdminList,
    OrderAdminPublic,
    OrderCheckout,
    OrderCreate,
    OrderList,
    OrderPublic,
)
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])
admin_router = APIRouter(prefix="/admin/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderCheckout,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pending order from a cart of book ids",
)
async def create_order(
    data: OrderCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> OrderCheckout:
    order = await order_service.create_order(
        db, user, data.book_ids, payment_method=data.payment_method
    )
    await db.commit()

    payment_url: str | None = None
    if (
        data.payment_method == "payme"
        and float(order.total) > 0
        and settings.PAYME_MERCHANT_ID
    ):
        lang = (
            user.preferred_locale if user.preferred_locale in {"uz", "ru", "en"} else "uz"
        )
        payment_url = build_checkout_url(
            order_id=str(order.id),
            amount_uzs=float(order.total),
            return_url=(
                f"{settings.FRONTEND_URL.rstrip('/')}/{lang}/checkout/success?order={order.id}"
            ),
            language=lang,
        )
    return OrderCheckout(order=OrderPublic.model_validate(order), payment_url=payment_url)


@router.get(
    "/me",
    response_model=OrderList,
    summary="List the current user's orders",
)
async def list_my_orders(
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: OrderStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> OrderList:
    items, total = await order_service.list_for_user(
        db, user, page=page, page_size=page_size, status=status_filter
    )
    return OrderList(
        items=[OrderPublic.model_validate(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{order_id}",
    response_model=OrderPublic,
    summary="Read one order (owner or admin)",
)
async def read_order(
    order_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> OrderPublic:
    order = await order_service.get_for_user(db, user, order_id)
    return OrderPublic.model_validate(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderPublic,
    summary="Cancel a pending order (no-op once it's paid or expired)",
)
async def cancel_order(
    order_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> OrderPublic:
    order = await order_service.cancel(db, user, order_id)
    await db.commit()
    return OrderPublic.model_validate(order)


# ---------- admin ----------


@admin_router.get(
    "",
    response_model=OrderAdminList,
    summary="List every order in the system (admin)",
)
async def admin_list_orders(
    _: Annotated[User, Depends(require_admin_scope("orders"))],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: OrderStatus | None = Query(None, alias="status"),
    search: str | None = Query(None, max_length=255),
    sort: Literal["created_at", "-created_at", "total", "-total"] = "-created_at",
    db: AsyncSession = Depends(get_db),
) -> OrderAdminList:
    items, total = await order_service.admin_list(
        db,
        page=page,
        page_size=page_size,
        status=status_filter,
        search=search,
        sort=sort,
    )
    return OrderAdminList(
        items=[OrderAdminPublic.model_validate(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@admin_router.get(
    "/{order_id}",
    response_model=OrderAdminDetail,
    summary="Full order detail — items, buyer, payment attempts (admin)",
)
async def admin_read_order(
    order_id: UUID,
    _: Annotated[User, Depends(require_admin_scope("orders"))],
    db: AsyncSession = Depends(get_db),
) -> OrderAdminDetail:
    order = await order_service.admin_get(db, order_id)
    return OrderAdminDetail.model_validate(order)
