"""SlowAPI limiter, Redis-backed.

Per-endpoint limits attach via ``@limiter.limit("N/period")``. Tests disable
the limiter in ``conftest.py`` so they don't accidentally trip on each other —
the dedicated rate-limit test flips it back on for the duration.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.config import settings


def _client_ip_key(request: Request) -> str:
    """Best-effort IP key. Honours ``X-Forwarded-For`` first (Nginx in prod
    will set it), falls back to the raw socket peer."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(
    key_func=_client_ip_key,
    storage_uri=settings.REDIS_URL,
    strategy="fixed-window",
    # ``headers_enabled`` would inject X-RateLimit-* but requires every
    # decorated endpoint to accept ``response: Response``. Phase 1 doesn't
    # need that polish — re-enable in Phase 6 alongside the security
    # hardening pass.
    headers_enabled=False,
)


async def rate_limit_exceeded_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return our standard ``{"error": {...}}`` envelope instead of slowapi's
    default detail-only response."""
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "rate_limited",
                "message": "Too many requests — please slow down",
                "details": {"limit": str(exc.detail)},
            }
        },
    )
