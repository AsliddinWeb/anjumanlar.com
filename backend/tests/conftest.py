"""Shared pytest fixtures.

The suite talks to the real Postgres + Redis containers in the dev stack —
we do not mock them. Each DB-touching test runs inside an outer transaction
that is rolled back at teardown so tests stay isolated without truncate.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.limiter import limiter
from app.db.session import engine, get_db
from app.main import app

# Tests hammer login/register repeatedly and would otherwise trip the rate
# limiter on themselves. The dedicated rate-limit test re-enables it locally.
limiter.enabled = False


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Bare ASGI client — no DB override; suitable for /health, /api/v1/ping."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Session bound to an outer transaction that's rolled back at teardown."""
    async with engine.connect() as conn:
        outer_tx = await conn.begin()
        session_factory = async_sessionmaker(bind=conn, expire_on_commit=False, autoflush=False)
        async with session_factory() as session:
            try:
                yield session
            finally:
                await outer_tx.rollback()


@pytest.fixture
async def api_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """ASGI client that reuses the test's rolled-back session for every request.

    Pair with the ``captured_emails`` fixture when the code under test enqueues
    Celery jobs you don't actually want to fire."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
