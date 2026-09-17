"""site_settings — contact person, phone, and social links

Admin-editable footer/contact info (previously hardcoded in
AppFooter.vue). Seeds the current real values as server defaults so
existing installs show correct contact details immediately, no
/admin/settings visit required before deploy.

Revision ID: a2b3c4d5e6f7
Revises: f6a7b8c9d0e1
Create Date: 2026-09-17 13:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "site_settings",
        sa.Column("contact_name", sa.String(255), nullable=True,
                   server_default="Ixtiyorbek Norov"),
    )
    op.add_column(
        "site_settings",
        sa.Column("contact_phone", sa.String(50), nullable=True,
                   server_default="+998 88 652 96 98"),
    )
    op.add_column(
        "site_settings",
        sa.Column("contact_email", sa.String(255), nullable=True,
                   server_default="info@monografiya.com"),
    )
    op.add_column(
        "site_settings",
        sa.Column("telegram_url", sa.String(255), nullable=True,
                   server_default="https://t.me/monografiya_uz"),
    )
    op.add_column(
        "site_settings",
        sa.Column("instagram_url", sa.String(255), nullable=True,
                   server_default="https://instagram.com/monografiya"),
    )
    op.add_column(
        "site_settings",
        sa.Column("facebook_url", sa.String(255), nullable=True),
    )
    op.add_column(
        "site_settings",
        sa.Column("youtube_url", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("site_settings", "youtube_url")
    op.drop_column("site_settings", "facebook_url")
    op.drop_column("site_settings", "instagram_url")
    op.drop_column("site_settings", "telegram_url")
    op.drop_column("site_settings", "contact_email")
    op.drop_column("site_settings", "contact_phone")
    op.drop_column("site_settings", "contact_name")
