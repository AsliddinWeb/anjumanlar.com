"""Fixed catalog of admin panel scopes.

Each entry maps 1:1 to a sidebar section in the admin frontend. A `User`
with role `admin` and a non-null `admin_scopes` list is restricted to
exactly these sections; `admin_scopes = None` (the default) keeps the
legacy "every admin sees everything" behaviour. `superadmin` always
bypasses scope checks — see `require_admin_scope` in app/dependencies.py.
"""

from __future__ import annotations

ADMIN_SCOPES: list[str] = [
    "books",
    "reviews",
    "review_requests",
    "review_categories",
    "blog",
    "categories",
    "users",
    "withdrawals",
    "finance",
    "audit",
    "settings",
]
