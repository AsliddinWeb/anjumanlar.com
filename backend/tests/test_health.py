import pytest


@pytest.mark.asyncio
async def test_health(client) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "anjumanlar"


@pytest.mark.asyncio
async def test_ping(client) -> None:
    resp = await client.get("/api/v1/ping")
    assert resp.status_code == 200
    assert resp.json() == {"pong": "ok"}
