"""Bootstrap a superadmin from the CLI.

The ``register`` API endpoint always creates ``reader`` accounts on
purpose — there's no admin-creation UI. Use this script after the
first deploy::

    docker compose -f docker-compose.prod.yml exec backend \
        python -m app.scripts.create_admin \
        --email you@monografiya.com \
        --password 'StrongPass!2026' \
        --name 'Site Admin'

Idempotent:

- If a user with that email already exists, the script promotes them
  to ``superadmin`` (status → active, email_verified → true) instead
  of creating a duplicate. Existing password stays untouched unless
  ``--reset-password`` is passed.
- If the user does not exist, a fresh row is inserted with the
  password hashed via ``bcrypt`` (same hasher the auth flow uses).

The first run gives you a ``superadmin``; from inside the admin panel
that account can promote others to ``admin`` without superadmin
powers.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import NoReturn

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import User, UserRole, UserStatus

logger = logging.getLogger("create_admin")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [admin] %(message)s")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote (or create) a user as superadmin."
    )
    parser.add_argument("--email", required=True, help="login email")
    parser.add_argument(
        "--password",
        required=False,
        default=None,
        help="password (required only when creating a new account)",
    )
    parser.add_argument(
        "--name",
        required=False,
        default=None,
        help="display name (defaults to the email's local-part)",
    )
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help=(
            "if the user exists, overwrite their password with --password "
            "(otherwise the existing hash is left alone)"
        ),
    )
    return parser.parse_args(argv)


def _fail(msg: str) -> NoReturn:
    logger.error(msg)
    sys.exit(1)


async def _run(args: argparse.Namespace) -> None:
    async with AsyncSessionLocal() as db:
        existing = await _find_by_email(db, args.email)

        if existing is None:
            if not args.password:
                _fail("Creating a new admin requires --password")
            display_name = args.name or args.email.split("@", 1)[0]
            user = User(
                email=args.email,
                password_hash=hash_password(args.password),
                full_name=display_name,
                role=UserRole.superadmin,
                status=UserStatus.active,
                email_verified=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info("created superadmin %s (id=%s)", user.email, user.id)
            return

        # Existing user — promote in place.
        existing.role = UserRole.superadmin
        existing.status = UserStatus.active
        existing.email_verified = True
        if args.name:
            existing.full_name = args.name
        if args.reset_password:
            if not args.password:
                _fail("--reset-password requires --password")
            existing.password_hash = hash_password(args.password)
            logger.info("password reset for %s", existing.email)

        await db.commit()
        logger.info("promoted %s to superadmin (id=%s)", existing.email, existing.id)


async def _find_by_email(db: AsyncSession, email: str) -> User | None:
    # email is CITEXT, so case is already collapsed at the column level.
    return (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
