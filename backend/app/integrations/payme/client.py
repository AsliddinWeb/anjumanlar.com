"""Payme Checkout URL builder.

Paycom's checkout API takes a base64-encoded query string of the form
``m=<merchant_id>;ac.order_id=<id>;a=<tiyin>;l=<lang>;c=<return_url>``
and serves the payment page at ``{CHECKOUT_URL}/{base64}``.

Tiyin is the smallest UZS unit: 1 so'm = 100 tiyin. We round the order
total to whole so'm at creation time, then multiply by 100 here so the
amount Payme bills always matches what's in the order row.
"""

from __future__ import annotations

import base64
from typing import Literal

from app.config import settings


def uzs_to_tiyin(amount_uzs: float) -> int:
    """Convert UZS so'm to tiyin (rounded to the nearest tiyin)."""
    return int(round(amount_uzs * 100))


def build_checkout_url(
    *,
    order_id: str,
    amount_uzs: float,
    return_url: str,
    language: Literal["uz", "ru", "en"] = "uz",
    callback_timeout_ms: int = 15000,
) -> str:
    """Compose the Payme checkout URL for an order.

    Returns the full URL the frontend should redirect to.
    """
    params = {
        "m": settings.PAYME_MERCHANT_ID,
        "ac.order_id": order_id,
        "a": uzs_to_tiyin(amount_uzs),
        "l": language,
        "c": return_url,
        "ct": callback_timeout_ms,
    }
    param_str = ";".join(f"{k}={v}" for k, v in params.items())
    encoded = base64.b64encode(param_str.encode("utf-8")).decode("ascii")
    base = settings.PAYME_CHECKOUT_URL.rstrip("/")
    return f"{base}/{encoded}"
