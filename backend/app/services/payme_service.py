"""Payme Merchant API JSON-RPC handler.

Six methods land on ``POST /api/v1/payments/payme/callback`` and we route
them via a dispatch table to keep the per-method logic small.

Idempotency is the trickiest piece: Paycom retries on network blips,
so every state-changing handler has to be a no-op when called with
the same transaction id twice. We do that by checking the stored
``state`` before applying any change, and returning the existing
record verbatim if it's already in the target state.

Amounts on the wire are in tiyin (1 so'm = 100 tiyin); we convert to
so'm for the ``Payment.amount`` column so downstream balance maths
match the order rows.

Once a payment hits ``state = 2`` we flip the order to ``paid`` and
hand off to ``library_service`` (Phase 4.5) — that part is wired here
behind an explicit import so this module stays load-order-friendly.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.integrations.payme.errors import PaymeError
from app.models import (
    Order,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentProvider,
    PaymentStatus,
)

logger = logging.getLogger(__name__)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _uzs_to_tiyin(amount_uzs: float) -> int:
    return int(round(amount_uzs * 100))


class PaymeMerchant:
    """JSON-RPC dispatcher for the Paycom Merchant API.

    Instantiated per-request — the AsyncSession is bound at construction
    time so individual methods can stay sync-shaped readers of state.
    The caller (endpoint) commits the transaction once dispatch returns
    successfully; we ``flush`` inside handlers so subsequent queries
    in the same request see the changes.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        req_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params") or {}

        handler_map = {
            "CheckPerformTransaction": self._check_perform,
            "CreateTransaction": self._create,
            "PerformTransaction": self._perform,
            "CancelTransaction": self._cancel,
            "CheckTransaction": self._check,
            "GetStatement": self._statement,
        }

        try:
            handler = handler_map.get(str(method) if method else "")
            if handler is None:
                raise PaymeError(-32601)
            result = await handler(params, raw=payload)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except PaymeError as err:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": err.code,
                    "message": err.message,
                    "data": err.data or None,
                },
            }
        except Exception:
            logger.exception("payme.webhook unexpected error method=%s", method)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": "Internal error", "data": None},
            }

    # ---------- helpers ----------

    async def _get_order(self, account: dict[str, Any]) -> Order:
        raw_id = (account or {}).get("order_id")
        if not raw_id:
            raise PaymeError(-31050, data={"field": "order_id"})
        try:
            order_uuid = UUID(str(raw_id))
        except (TypeError, ValueError) as exc:
            raise PaymeError(-31050, data={"field": "order_id"}) from exc
        order = (
            await self.db.execute(
                select(Order)
                .options(selectinload(Order.items).selectinload(OrderItem.book))
                .where(Order.id == order_uuid)
            )
        ).scalar_one_or_none()
        if order is None:
            raise PaymeError(-31050, data={"field": "order_id"})
        return order

    async def _get_payment(self, transaction_id: str) -> Payment:
        payment = (
            await self.db.execute(
                select(Payment).where(
                    Payment.provider == PaymentProvider.payme,
                    Payment.provider_id == transaction_id,
                )
            )
        ).scalar_one_or_none()
        if payment is None:
            raise PaymeError(-31003)
        return payment

    @staticmethod
    def _assert_amount(order: Order, amount_tiyin: int | None) -> None:
        if amount_tiyin is None:
            raise PaymeError(-31001)
        expected = _uzs_to_tiyin(float(order.total))
        if int(amount_tiyin) != expected:
            raise PaymeError(-31001)

    # ---------- handlers ----------

    async def _check_perform(self, params: dict[str, Any], **_: Any) -> dict[str, Any]:
        order = await self._get_order(params.get("account", {}))
        self._assert_amount(order, params.get("amount"))

        if order.status == OrderStatus.paid:
            raise PaymeError(-31054)
        if order.status in (OrderStatus.cancelled, OrderStatus.refunded, OrderStatus.expired):
            raise PaymeError(-31055)
        if order.status != OrderStatus.pending:
            raise PaymeError(-31051)

        return {"allow": True}

    async def _create(
        self, params: dict[str, Any], raw: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        transaction_id = str(params.get("id") or "")
        request_time = int(params.get("time") or 0)
        amount = params.get("amount")

        if not transaction_id or not request_time:
            raise PaymeError(-32602)

        # Idempotency: re-issued create for the same transaction id.
        existing = (
            await self.db.execute(
                select(Payment).where(
                    Payment.provider == PaymentProvider.payme,
                    Payment.provider_id == transaction_id,
                )
            )
        ).scalar_one_or_none()

        if existing is not None:
            if existing.state == 1:
                return {
                    "create_time": existing.create_time or request_time,
                    "transaction": str(existing.id),
                    "state": 1,
                }
            raise PaymeError(-31008)

        order = await self._get_order(params.get("account", {}))
        self._assert_amount(order, amount)

        if order.status != OrderStatus.pending:
            raise PaymeError(-31051)

        # Only one open payment per order — Paycom won't double-charge
        # an order, but our own client could trigger two checkouts.
        other_open = (
            await self.db.execute(
                select(Payment).where(
                    Payment.order_id == order.id,
                    Payment.state == 1,
                )
            )
        ).scalar_one_or_none()
        if other_open is not None:
            raise PaymeError(-31008)

        payment = Payment(
            order_id=order.id,
            provider=PaymentProvider.payme,
            provider_id=transaction_id,
            amount=float(order.total),
            currency=order.currency,
            status=PaymentStatus.pending,
            state=1,
            create_time=request_time,
            raw_response=raw,
        )
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment)

        return {
            "create_time": request_time,
            "transaction": str(payment.id),
            "state": 1,
        }

    async def _perform(
        self, params: dict[str, Any], raw: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        transaction_id = str(params.get("id") or "")
        if not transaction_id:
            raise PaymeError(-32602)

        payment = await self._get_payment(transaction_id)

        if payment.state == 2:
            # Idempotent — return the cached result.
            return {
                "transaction": str(payment.id),
                "perform_time": payment.perform_time or 0,
                "state": 2,
            }
        if payment.state != 1:
            raise PaymeError(-31008)

        perform_time = _now_ms()
        payment.state = 2
        payment.status = PaymentStatus.paid
        payment.perform_time = perform_time
        payment.raw_response = raw

        order = (
            await self.db.execute(
                select(Order)
                .options(selectinload(Order.items))
                .where(Order.id == payment.order_id)
            )
        ).scalar_one()
        order.status = OrderStatus.paid
        order.paid_at = datetime.now(UTC)
        await self.db.flush()

        # Phase 4.5 will plug library + watermark here. Importing inline
        # so the order tests don't drag in the (yet-to-land) library
        # service.
        try:
            from app.services import library_service  # type: ignore[attr-defined]

            await library_service.grant_order(self.db, order)
        except (ImportError, AttributeError):
            logger.debug("library_service not wired yet — skipping grant for %s", order.id)

        return {
            "transaction": str(payment.id),
            "perform_time": perform_time,
            "state": 2,
        }

    async def _cancel(
        self, params: dict[str, Any], raw: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        transaction_id = str(params.get("id") or "")
        reason = params.get("reason")
        if not transaction_id:
            raise PaymeError(-32602)

        payment = await self._get_payment(transaction_id)

        # Idempotent — already cancelled.
        if payment.state in (-1, -2):
            return {
                "transaction": str(payment.id),
                "cancel_time": payment.cancel_time or 0,
                "state": payment.state,
            }

        cancel_time = _now_ms()
        if payment.state == 1:
            payment.state = -1
            order = await self.db.get(Order, payment.order_id)
            if order is not None and order.status == OrderStatus.pending:
                order.status = OrderStatus.cancelled
        elif payment.state == 2:
            payment.state = -2
            order = await self.db.get(Order, payment.order_id)
            if order is not None:
                order.status = OrderStatus.refunded
        else:
            raise PaymeError(-31007)

        payment.status = PaymentStatus.cancelled
        payment.cancel_time = cancel_time
        if reason is not None:
            payment.reason = int(reason)
        payment.raw_response = raw
        await self.db.flush()

        return {
            "transaction": str(payment.id),
            "cancel_time": cancel_time,
            "state": payment.state,
        }

    async def _check(self, params: dict[str, Any], **_: Any) -> dict[str, Any]:
        transaction_id = str(params.get("id") or "")
        if not transaction_id:
            raise PaymeError(-32602)
        payment = await self._get_payment(transaction_id)
        return {
            "create_time": payment.create_time or 0,
            "perform_time": payment.perform_time or 0,
            "cancel_time": payment.cancel_time or 0,
            "transaction": str(payment.id),
            "state": payment.state or 0,
            "reason": payment.reason,
        }

    async def _statement(self, params: dict[str, Any], **_: Any) -> dict[str, Any]:
        from_ms = int(params.get("from") or 0)
        to_ms = int(params.get("to") or 0)
        if from_ms <= 0 or to_ms <= 0 or to_ms < from_ms:
            raise PaymeError(-32602)

        from_dt = datetime.fromtimestamp(from_ms / 1000, tz=UTC)
        to_dt = datetime.fromtimestamp(to_ms / 1000, tz=UTC)

        rows = (
            (
                await self.db.execute(
                    select(Payment).where(
                        Payment.provider == PaymentProvider.payme,
                        Payment.created_at >= from_dt,
                        Payment.created_at <= to_dt,
                    )
                )
            )
            .scalars()
            .all()
        )

        transactions = []
        for p in rows:
            transactions.append(
                {
                    "id": p.provider_id or "",
                    "time": p.create_time or 0,
                    "amount": _uzs_to_tiyin(float(p.amount)),
                    "account": {"order_id": str(p.order_id)},
                    "create_time": p.create_time or 0,
                    "perform_time": p.perform_time or 0,
                    "cancel_time": p.cancel_time or 0,
                    "transaction": str(p.id),
                    "state": p.state or 0,
                    "reason": p.reason,
                }
            )
        return {"transactions": transactions}
