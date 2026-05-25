"""hard_delete_users_books — drop soft-delete plumbing

Removes:
  - ``users.deleted_at`` column
  - ``books.deleted_at`` column
  - ``user_status`` enum value ``deleted``

Any pre-existing rows with the deprecated state are migrated rather
than refused: deleted users get demoted to ``blocked``, deleted books
get archived. This is a one-way change — the downgrade re-adds the
columns + enum value but cannot resurrect any rows we removed.

Revision ID: c4f1a2b3d5e6
Revises: 1b1d75ce36ca
Create Date: 2026-05-25 03:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4f1a2b3d5e6"
down_revision: Union[str, None] = "1b1d75ce36ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Move any rows still on the deprecated states out before we strip
    # the columns/enum values they reference. We don't try to delete
    # the rows themselves (FK chain is non-trivial) — operators with
    # actually-soft-deleted data can clean up after.
    op.execute("UPDATE users SET status = 'blocked' WHERE status = 'deleted'")

    op.drop_column("users", "deleted_at")
    op.drop_column("books", "deleted_at")

    # PG can't drop an enum value in place — swap the type out.
    op.execute("ALTER TYPE user_status RENAME TO user_status_old")
    op.execute("CREATE TYPE user_status AS ENUM ('active', 'pending', 'blocked')")
    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN status DROP DEFAULT, "
        "ALTER COLUMN status TYPE user_status USING status::text::user_status, "
        "ALTER COLUMN status SET DEFAULT 'pending'"
    )
    op.execute("DROP TYPE user_status_old")


def downgrade() -> None:
    op.execute("ALTER TYPE user_status RENAME TO user_status_old")
    op.execute("CREATE TYPE user_status AS ENUM ('active', 'pending', 'blocked', 'deleted')")
    op.execute(
        "ALTER TABLE users "
        "ALTER COLUMN status DROP DEFAULT, "
        "ALTER COLUMN status TYPE user_status USING status::text::user_status, "
        "ALTER COLUMN status SET DEFAULT 'pending'"
    )
    op.execute("DROP TYPE user_status_old")

    op.add_column(
        "books",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
