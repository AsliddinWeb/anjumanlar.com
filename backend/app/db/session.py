"""Async SQLAlchemy engine + session factory + FastAPI dependency."""

import asyncio
from collections.abc import AsyncIterator, Coroutine
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a session and rolls back on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def run_db_task[T](coro: Coroutine[Any, Any, T]) -> T:
    """Entry point for a Celery task that needs this module's async engine.

    Celery's prefork workers call ``asyncio.run()`` fresh per task —
    each invocation spins up and tears down its own event loop — but
    ``engine``'s connection pool is a process-wide singleton shared by
    every task that fork ever runs. A pooled asyncpg connection opened
    under one event loop can't be reused once that loop closes
    (``RuntimeError: ... attached to a different loop`` /
    ``Event loop is closed``), so the pool must be dropped before this
    call returns, or the *next* task's fresh loop inherits poisoned
    connections. Route every Celery task's top-level async call through
    here instead of a bare ``asyncio.run()`` so none of them forget it.
    """

    async def _runner() -> T:
        try:
            return await coro
        finally:
            await engine.dispose()

    return asyncio.run(_runner())


__all__ = ["AsyncSessionLocal", "engine", "get_db", "run_db_task"]
