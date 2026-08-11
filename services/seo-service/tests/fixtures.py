"""Shared helpers for seo-service tests.

Builds an in-memory SQLite app inside the caller's event loop (backend-core
test pattern): API tests run through httpx ASGITransport inside
``asyncio.run`` and never cross event-loop boundaries. Search uses the
in-memory index — no Typesense required for tests.
"""

import json
from collections.abc import Callable, Coroutine
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from atoz_backend_core.auth import create_access_token
from atoz_backend_core.db.base import Base
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher
from atoz_seo_service.config import Settings
from atoz_seo_service.domain.search import InMemorySearchIndex
from atoz_seo_service.main import create_app
from atoz_seo_service.services import SeoService

TEST_JWT_SECRET = "test-seo-jwt-secret-0123456789abcdef0123456789abcdef"
TEST_EVENT_SECRET = "test-seo-event-secret-0123456789abcdef0123456789abcdef"
TEST_READ_PERMISSIONS = ("seo:read",)
TEST_WRITE_PERMISSIONS = ("seo:read", "seo:write")


def make_settings(**overrides: object) -> Settings:
    """Test settings: fixed secrets, in-memory-friendly defaults."""
    base: dict[str, object] = {
        "app_env": "test",
        "rate_limit_enabled": False,
        "jwt_secret": TEST_JWT_SECRET,
        "event_webhook_secret": TEST_EVENT_SECRET,
        "public_base_url": "https://atozproducthub.dev",
        "typesense_api_base": "http://typesense.test:8108",
        "typesense_api_key": "test-key",
        "sitemap_max_urls": 3,
        "sitemap_group_chunk_urls": 100,
        "search_page_size_default": 20,
        "search_page_size_max": 50,
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


def event_signature(secret: str, payload: dict[str, Any]) -> str:
    """Compute the HMAC-SHA256 webhook signature for a JSON payload."""
    import hashlib
    import hmac

    raw = json.dumps(payload, separators=(",", ":")).encode()
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


async def build_app(
    *,
    capture_events: bool = True,
    settings: Settings | None = None,
) -> tuple[FastAPI, AsyncEngine, InMemoryEventBus, list[EventEnvelope]]:
    """Create an app with a fresh in-memory database + in-memory search."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    bus = InMemoryEventBus()
    captured: list[EventEnvelope] = []

    async def capture(event: EventEnvelope) -> None:
        captured.append(event)

    if capture_events:
        for event_type in (
            "seo:sitemap-rebuilt.v1",
            "search:indexed.v1",
            "search:removed.v1",
        ):
            await bus.subscribe(event_type, capture)

    app = create_app(
        settings=settings or make_settings(),
        session_factory=session_factory,
        search_index=InMemorySearchIndex(),
    )
    return app, engine, bus, captured


async def build_service(
    *,
    search_index: InMemorySearchIndex | None = None,
    settings: Settings | None = None,
) -> tuple[async_sessionmaker, SeoService]:
    """In-memory SQLite session factory + service for service-level tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    service = SeoService(
        uow_factory=lambda: SeoService.build_uow(session_factory),
        event_publisher=EventPublisher(InMemoryEventBus(), publisher="seo-service"),
        settings=settings or make_settings(),
        search_index=search_index or InMemorySearchIndex(),
    )
    return session_factory, service


async def api_client(app: FastAPI) -> httpx.AsyncClient:
    """Async test client for the given app (same event loop)."""
    from httpx import ASGITransport, AsyncClient

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def scenario(runner: Callable[[], Coroutine[Any, Any, None]]) -> None:
    """Run an async scenario helper through the event loop (no pytest-asyncio)."""
    import asyncio

    asyncio.run(runner())
