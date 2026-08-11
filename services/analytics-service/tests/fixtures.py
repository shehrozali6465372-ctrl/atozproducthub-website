"""Shared helpers for analytics-service tests.

Builds an in-memory SQLite app inside the caller's event loop (backend-core
test pattern): API tests run through httpx ASGITransport inside
``asyncio.run`` and never cross event-loop boundaries. The pipeline uses the
in-memory backbone + warehouse — no Kafka or ClickHouse required for tests.
"""

import json
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from atoz_analytics_service.config import Settings
from atoz_analytics_service.domain.pipeline import (
    InMemoryEventBackbone,
    InMemoryWarehouse,
    PipelineWorker,
)
from atoz_analytics_service.main import create_app
from atoz_analytics_service.services import AnalyticsService
from atoz_backend_core.auth import create_access_token
from atoz_backend_core.db.base import Base
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher

TEST_JWT_SECRET = "test-analytics-jwt-secret-0123456789abcdef0123456789abcdef"
TEST_EVENT_SECRET = "test-analytics-event-secret-0123456789abcdef0123456789abcdef"
TEST_READ_PERMISSIONS = ("analytics:read",)
TEST_WRITE_PERMISSIONS = ("analytics:read", "analytics:write")


def make_settings(**overrides: object) -> Settings:
    """Test settings: fixed secrets, in-memory-friendly defaults."""
    base: dict[str, object] = {
        "app_env": "test",
        "rate_limit_enabled": False,
        "jwt_secret": TEST_JWT_SECRET,
        "event_webhook_secret": TEST_EVENT_SECRET,
        "kafka_enabled": False,
        "warehouse_enabled": False,
        "rollup_window_days": 400,
        "collector_max_batch_size": 100,
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
    backbone: InMemoryEventBackbone | None = None,
    warehouse: InMemoryWarehouse | None = None,
) -> tuple[
    FastAPI,
    AsyncEngine,
    InMemoryEventBus,
    list[EventEnvelope],
    InMemoryEventBackbone,
    InMemoryWarehouse,
]:
    """Create an app with a fresh in-memory database + in-memory pipeline."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    bus = InMemoryEventBus()
    captured: list[EventEnvelope] = []

    async def capture(event: EventEnvelope) -> None:
        captured.append(event)

    if capture_events:
        await bus.subscribe("analytics:rollup-completed.v1", capture)

    backbone = backbone or InMemoryEventBackbone()
    warehouse = warehouse or InMemoryWarehouse()
    app = create_app(
        settings=settings or make_settings(),
        session_factory=session_factory,
        backbone=backbone,
        warehouse=warehouse,
    )
    return app, engine, bus, captured, backbone, warehouse


async def build_service(
    *,
    settings: Settings | None = None,
) -> tuple[async_sessionmaker, AnalyticsService, InMemoryEventBackbone, InMemoryWarehouse]:
    """In-memory SQLite session factory + service for service-level tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    backbone = InMemoryEventBackbone()
    warehouse = InMemoryWarehouse()
    service = AnalyticsService(
        uow_factory=lambda: AnalyticsService.build_uow(session_factory),
        event_publisher=EventPublisher(InMemoryEventBus(), publisher="analytics-service"),
        settings=settings or make_settings(),
        backbone=backbone,
        warehouse=warehouse,
        pipeline_worker=PipelineWorker(backbone, warehouse),
    )
    return session_factory, service, backbone, warehouse


async def api_client(app: FastAPI) -> httpx.AsyncClient:
    """Async test client for the given app (same event loop)."""
    from httpx import ASGITransport, AsyncClient

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def scenario(runner: Callable[[], Coroutine[Any, Any, None]]) -> None:
    """Run an async scenario helper through the event loop (no pytest-asyncio)."""
    import asyncio

    asyncio.run(runner())


def utc_dt(year: int, month: int, day: int, hour: int = 12) -> datetime:
    """Timezone-aware datetime helper for ledger events."""
    from datetime import datetime as _datetime

    return _datetime(year, month, day, hour, tzinfo=UTC)
