"""Payment endpoints.

- ``POST /payments/payme/callback`` — Paycom Merchant API JSON-RPC.
  Authenticated with HTTP Basic (``Paycom:<PAYME_SECRET_KEY>``).
  Auth failures must return the JSON-RPC error envelope rather than an
  HTTP 401 so the Paycom side can ingest the response per spec.

- ``POST /payments/payme/checkout/{order_id}`` — owner-only helper
  that returns the redirect URL for a pending order. Lets the frontend
  reissue the URL if the user lost the original tab.
"""

from __future__ import annotations

import base64
import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_current_user
from app.integrations.payme.client import build_checkout_url
from app.integrations.payme.errors import PAYME_ERRORS
from app.models import OrderStatus, User
from app.services import order_service
from app.services.payme_service import PaymeMerchant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


def _jsonrpc_error(code: int, *, req_id: Any = None) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": code,
            "message": PAYME_ERRORS.get(code, "Unknown error"),
            "data": None,
        },
    }


def _basic_auth_ok(authorization: str | None) -> bool:
    if not authorization or not authorization.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(authorization[len("Basic "):]).decode("utf-8")
    except Exception:  # noqa: BLE001 — base64 raises a wide family
        return False
    if ":" not in decoded:
        return False
    user, _, password = decoded.partition(":")
    expected_user = "Paycom"
    expected_password = settings.PAYME_SECRET_KEY
    if not expected_password:
        logger.warning("payme.webhook called with no PAYME_SECRET_KEY configured")
        return False
    return user == expected_user and password == expected_password


@router.post(
    "/payme/callback",
    summary="Paycom Merchant API JSON-RPC endpoint",
    include_in_schema=False,
)
async def payme_webhook(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse(_jsonrpc_error(-32700))

    req_id = payload.get("id") if isinstance(payload, dict) else None

    if not _basic_auth_ok(authorization):
        return JSONResponse(_jsonrpc_error(-32504, req_id=req_id))

    if not isinstance(payload, dict) or "method" not in payload:
        return JSONResponse(_jsonrpc_error(-32600, req_id=req_id))

    handler = PaymeMerchant(db)
    result = await handler.dispatch(payload)
    # Successful handlers flush; commit so any state changes (Payment
    # rows, Order status) persist before the response leaves.
    await db.commit()
    return JSONResponse(result)


@router.post(
    "/payme/checkout/{order_id}",
    summary="Build a Payme checkout URL for a pending order",
)
async def payme_checkout(
    order_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    order = await order_service.get_for_user(db, user, order_id)
    if order.status != OrderStatus.pending:
        from app.core.exceptions import ConflictError

        raise ConflictError(
            "Order is not awaiting payment",
            details={"code": "invalid_state", "current_status": order.status.value},
        )
    lang = user.preferred_locale if user.preferred_locale in {"uz", "ru", "en"} else "uz"
    url = build_checkout_url(
        order_id=str(order.id),
        amount_uzs=float(order.total),
        return_url=f"{settings.FRONTEND_URL.rstrip('/')}/{lang}/checkout/success?order={order.id}",
        language=lang,
    )
    return {"url": url}
