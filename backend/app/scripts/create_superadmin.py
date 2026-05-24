"""CLI: bootstrap a SuperAdmin account.

Usage (run inside the backend container):

    docker compose exec backend python -m app.scripts.create_superadmin \\
        --email founder@monografiya.com \\
        --password "Hunter22!" \\
        --full-name "Founder"

If a user with that email already exists, their role is upgraded to
``superadmin`` and the account is force-activated (status=active,
email_verified=true). The password is rotated to the value passed in.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models import User, UserRole, UserStatus


async def _upsert(email: str, password: str, full_name: str) -> User:
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if existing is not None:
            existing.role = UserRole.superadmin
            existing.status = UserStatus.active
            existing.email_verified = True
            existing.password_hash = hash_password(password)
            existing.full_name = full_name
            await session.commit()
            return existing

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.superadmin,
            status=UserStatus.active,
            email_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", required=True)
    args = parser.parse_args(argv)

    if len(args.password) < 8:
        print("ERROR: password must be at least 8 characters", file=sys.stderr)
        return 2

    user = asyncio.run(_upsert(args.email, args.password, args.full_name))
    print(f"SuperAdmin ready: id={user.id} email={user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
