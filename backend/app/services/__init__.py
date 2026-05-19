"""Service-layer business logic.

Conventions:

- Services accept an :class:`AsyncSession` and never commit; the caller
  (usually the endpoint) owns the transaction. ``audit_service`` is the
  one exception — it opens its own session by design.
- Side-effects (email, search index sync, …) are enqueued as Celery tasks.
- Domain errors come from ``app.core.exceptions`` so the global handler can
  map them to JSON responses.
"""

from app.services import (
    audit_service,
    auth_service,
    email_service,
    storage_service,
    user_service,
)

__all__ = [
    "audit_service",
    "auth_service",
    "email_service",
    "storage_service",
    "user_service",
]
