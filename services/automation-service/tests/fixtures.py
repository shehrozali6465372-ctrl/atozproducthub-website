"""Shared helpers for automation-service tests.

Builds an in-memory SQLite app inside the caller's event loop (backend-core
test pattern): API tests run through httpx ASGITransport inside
``asyncio.run`` and never cross event-loop boundaries. Tables are created
from the automation metadata (including the Platform table mappings for
scheduled_jobs / job_runs / queue_items, which admin-service owns in
production — ADR-0010).
"""

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from atoz_automation_service.config import Settings
from atoz_automation_service.domain.entities import PlatformBase
from atoz_automation_service.main import create_app
from atoz_automation_service.services import AutomationService
from atoz_backend_core.auth import create_access_token
from atoz_backend_core.db.base import Base
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher

TEST_JWT_SECRET = "test-automation-jwt-secret-0123456789abcdef0123456789abcdef"
TEST_READ_PERMISSIONS = ("automation:read",)
TEST_WRITE_PERMISSIONS = ("automation:read", "automation:write")


def make_settings(**overrides: object) -> Settings:
    """Test settings: fixed secrets, deterministic retry schedule."""
    base: dict[str, object] = {
        "app_env": "test",
        "rate_limit_enabled": False,
        "jwt_secret": TEST_JWT_SECRET,
        "queue_max_attempts": 5,
        "queue_retry_base_delay_seconds": 1.0,
        "queue_retry_max_delay_seconds": 4.0,
        "queue_retry_jitter": 0.0,
        "job_max_attempts": 3,
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
) -> tuple[FastAPI, AsyncEngine, InMemoryEventBus, list[EventEnvelope]]:
    """Create an app with a fresh in-memory database + captured events."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(PlatformBase.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    bus = InMemoryEventBus()
    captured: list[EventEnvelope] = []

    async def capture(event: EventEnvelope) -> None:
        captured.append(event)

    if capture_events:
        await bus.subscribe("automation:rule-enabled.v1", capture)
        await bus.subscribe("automation:rule-disabled.v1", capture)
        await bus.subscribe("automation:run-started.v1", capture)
        await bus.subscribe("automation:run-succeeded.v1", capture)
        await bus.subscribe("automation:run-failed.v1", capture)
        await bus.subscribe("automation:job-enqueued.v1", capture)
        await bus.subscribe("automation:job-queued.v1", capture)
        await bus.subscribe("automation:aios-job-created.v1", capture)

    app = create_app(
        settings=settings or make_settings(), session_factory=session_factory, event_bus=bus
    )
    app.state.event_bus = bus
    app.state.captured_events = captured
    return app, engine, bus, captured


async def build_service(
    *,
    settings: Settings | None = None,
) -> tuple[async_sessionmaker, AutomationService, InMemoryEventBus, list[EventEnvelope]]:
    """In-memory SQLite session factory + service for service-level tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(PlatformBase.metadata.create_all)
    session_factory: async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    bus = InMemoryEventBus()
    captured: list[EventEnvelope] = []

    async def capture(event: EventEnvelope) -> None:
        captured.append(event)

    for event_type in (
        "automation:rule-enabled.v1",
        "automation:rule-disabled.v1",
        "automation:run-started.v1",
        "automation:run-succeeded.v1",
        "automation:run-failed.v1",
        "automation:job-enqueued.v1",
        "automation:job-queued.v1",
        "automation:aios-job-created.v1",
    ):
        await bus.subscribe(event_type, capture)
    publisher = EventPublisher(bus, publisher="automation-service")
    service = AutomationService(
        uow_factory=lambda: AutomationService.build_uow(session_factory),
        event_publisher=publisher,
        settings=settings or make_settings(),
    )
    return session_factory, service, bus, captured


async def api_client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {access_token()}"},
    )


def scenario(runner: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
    """Run an async scenario inside its own event loop."""
    return asyncio.run(runner())


def utc_dt(year: int, month: int, day: int, hour: int = 12) -> datetime:
    """Timezone-aware datetime helper."""
    return datetime(year, month, day, hour, tzinfo=UTC)
