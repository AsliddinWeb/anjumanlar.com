"""Shared pytest fixtures.

For now we keep this minimal — full async DB fixtures will be added in Phase 1
when the first models land.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
