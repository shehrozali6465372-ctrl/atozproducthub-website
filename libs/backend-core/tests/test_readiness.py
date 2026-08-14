"""Readiness failure-injection tests (M11 Phase G)."""

import asyncio

import httpx

from atoz_backend_core.config import BaseServiceSettings
from atoz_backend_core.db.redis import check_redis


def test_check_redis_down_returns_down() -> None:
    """Redis failure injects a 'down' component (never an exception)."""
    result = asyncio.run(check_redis("redis://127.0.0.1:1/0"))  # closed port
    assert result["name"] == "redis"
    assert result["status"] == "down"


def test_ready_returns_503_when_redis_down() -> None:
    from atoz_backend_core import __version__
    from atoz_backend_core.app import create_service_app

    async def scenario() -> None:
        settings = BaseServiceSettings(
            app_env="test",
            database_url=None,
            redis_url="redis://127.0.0.1:1/0",
            rate_limit_enabled=False,
        )
        app = create_service_app(
            service_name="backend-core-test",
            version=__version__,
            settings=settings,
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            ready = await client.get("/ready")
            assert ready.status_code == 503
            body = ready.json()
            assert body["status"] == "degraded"
            components = {c["name"]: c["status"] for c in body["components"]}
            assert components["redis"] == "down"

    asyncio.run(scenario())
