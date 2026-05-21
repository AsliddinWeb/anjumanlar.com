"""Service-layer business logic.

Conventions:

- Services accept an :class:`AsyncSession` and never commit; the caller
  (usually the endpoint) owns the transaction. ``audit_service`` is the
  one exception — it opens its own session by design.
- Side-effects (email, search index sync, …) are enqueued as Celery tasks.
- Domain errors come from ``app.core.exceptions`` so the global handler can
  map them to JSON responses.

Submodules are imported lazily by callers (``from app.services import
auth_service``); this file stays empty to avoid circular-import traps
between auth_service ↔ email_tasks.
"""
