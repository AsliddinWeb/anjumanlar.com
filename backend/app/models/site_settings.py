"""Site-wide settings — a singleton row.

The row is created on first access via ``site_settings_service.get`` so
the admin panel can read+write a stable id without a separate seed
step. The ``CHECK (singleton = TRUE)`` + unique index combo guarantees
there's at most one row ever.

Today this holds just the active theme name; future toggles (logo URL,
SEO defaults, footer text) plug in here without another migration.
"""

from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class SiteSettings(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "site_settings"

    # Singleton guard: one row only. The column itself is meaningless —
    # we just need a NOT NULL boolean with a uniqueness constraint pinned
    # to TRUE so PostgreSQL refuses a second row.
    singleton: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true", unique=True
    )

    theme_name: Mapped[str] = mapped_column(
        String(64), nullable=False, default="classic", server_default="classic"
    )

    __table_args__ = (
        CheckConstraint("singleton = TRUE", name="site_settings_singleton_check"),
    )

    def __repr__(self) -> str:
        return f"<SiteSettings theme={self.theme_name!r}>"
