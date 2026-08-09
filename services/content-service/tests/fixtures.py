"""Shared helpers for content-service tests.

Not a conftest module — the root conftest owns shared pytest fixtures.
These helpers build an in-memory SQLite app inside the caller's event loop
(backend-core test pattern), so API tests run through httpx ASGITransport
inside ``asyncio.run`` and never cross event-loop boundaries.
"""

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from atoz_backend_core.auth import create_access_token
from atoz_backend_core.db.base import Base
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_content_service.config import Settings
from atoz_content_service.main import create_app
from atoz_content_service.storage import InMemoryContentStore

TEST_JWT_SECRET = "test-content-jwt-secret-0123456789abcdef0123456789abcdef"
TEST_READ_PERMISSIONS = ("content:read",)
TEST_WRITE_PERMISSIONS = ("content:read", "content:write")


def make_settings(**overrides: object) -> Settings:
    """Test settings: no rate limits, fixed JWT secret, in-memory storage."""
    base: dict[str, object] = {
        "app_env": "test",
        "rate_limit_enabled": False,
        "jwt_secret": TEST_JWT_SECRET,
        "public_base_url": "https://atozproducthub.dev",
    }
    base.update(overrides)
    return Settings(**base)


def access_token(
    *,
    subject: str = "tester",
    permissions: tuple[str, ...] = TEST_WRITE_PERMISSIONS,
    secret: str = TEST_JWT_SECRET,
) -> str:
    """Mint a JWT access token for admin API tests (RBAC claims)."""
    return create_access_token(
        secret=secret,
        subject=subject,
        session_id="test-session",
        permissions=permissions,
    )


async def build_app(
    *,
    capture_events: bool = True,
    settings: Settings | None = None,
) -> tuple[FastAPI, AsyncEngine, InMemoryContentStore, InMemoryEventBus, list[EventEnvelope]]:
    """Create an app with a fresh in-memory database and content store.

    Returns (app, engine, store, bus, captured_events). Call inside the
    same event loop that will drive the scenario.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    store = InMemoryContentStore()
    bus = InMemoryEventBus()
    captured: list[EventEnvelope] = []

    async def capture(event: EventEnvelope) -> None:
        captured.append(event)

    if capture_events:
        for event_type in (
            "content:published.v1",
            "content:updated.v1",
            "content:unpublished.v1",
        ):
            await bus.subscribe(event_type, capture)

    app = create_app(
        settings=settings or make_settings(),
        session_factory=session_factory,
        content_store=store,
    )
    return app, engine, store, bus, captured


async def api_client(app: FastAPI) -> AsyncClient:
    """Async test client for the given app (same event loop)."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def scenario(runner: Callable[[], Coroutine[Any, Any, None]]) -> None:
    """Run an async scenario helper through the event loop (no pytest-asyncio)."""
    import asyncio

    asyncio.run(runner())
