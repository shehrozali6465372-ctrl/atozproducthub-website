"""Celery worker tasks: durable-ledger execution (M10 Step 2).

The worker is deliberately thin: Celery provides delivery only (``acks_late``
+ ``prefetch 1`` + time limits so a crashed worker never loses claimed work),
while every business decision lives in the workflow/executors and the durable
``queue_items`` ledger is the retry source of truth. The worker never
auto-retries forever (``max_retries=0``): a failed execution is persisted as
a retryable ledger state with exponential backoff, or as a terminal failure
that the admin dashboard can requeue.

The Beat task wakes the DB-driven scheduler tick (single-scheduler Redis
lock, croniter next-run computation) — Celery Beat is only a wake-up timer.

Both tasks build their dependencies at call time (never at import), so the
module imports cleanly in tests and the worker can reload configuration.
"""

from __future__ import annotations

import asyncio
from typing import Any

from atoz_automation_service.beat import run_beat_tick
from atoz_automation_service.celery_app import celery_app
from atoz_automation_service.config import Settings, get_settings
from atoz_automation_service.executors import build_default_registry
from atoz_automation_service.executors.clients import SiblingClients
from atoz_automation_service.repositories import AutomationUnitOfWork
from atoz_automation_service.services import AutomationService
from atoz_automation_service.workflow import ExecutionWorkflow
from atoz_backend_core.events.bus import EventBus, InMemoryEventBus, RedisEventBus
from atoz_backend_core.events.publisher import EventPublisher


def build_session_factory(database_url: str):
    """Async session factory for the worker's database (automation_db)."""
    from atoz_backend_core.db.postgres import create_engine, create_session_factory

    return create_session_factory(create_engine(database_url))


def build_event_publisher(settings: Settings) -> tuple[EventPublisher, EventBus]:
    """Outbound domain-event publisher (Redis pub/sub in production)."""
    if settings.celery_backend_url.startswith("redis"):
        bus: EventBus = RedisEventBus(settings.celery_backend_url)
    else:
        bus = InMemoryEventBus()
    return EventPublisher(bus, publisher="automation-worker"), bus


def _require_database(settings: Settings):
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured for the automation worker.")
    return build_session_factory(settings.database_url)


def run_executor_sync(
    queue_item_id: str,
    *,
    settings: Settings | None = None,
    session_factory=None,
    event_bus: EventBus | None = None,
) -> dict[str, Any]:
    """Execute one durable queue item inside a fresh event loop.

    ``session_factory`` and ``event_bus`` are injectable for tests; in
    production both are built from settings (PostgreSQL + Redis).
    """
    settings = settings or get_settings()
    session_factory = session_factory or _require_database(settings)
    if event_bus is None:
        publisher, event_bus = build_event_publisher(settings)
    else:
        publisher = EventPublisher(event_bus, publisher="automation-worker")

    async def _run() -> dict[str, Any]:
        siblings = SiblingClients(settings)
        try:
            workflow = ExecutionWorkflow(
                uow_factory=lambda: AutomationUnitOfWork.build(session_factory),
                event_publisher=publisher,
                settings=settings,
                registry=build_default_registry(),
                siblings=siblings,
            )
            return await workflow.run(queue_item_id)
        finally:
            await siblings.aclose()

    return asyncio.run(_run())


def beat_tick_sync(
    *,
    settings: Settings | None = None,
    session_factory=None,
    event_bus: EventBus | None = None,
) -> dict[str, Any]:
    """Wake the DB-driven scheduler tick (single-scheduler Beat lock)."""
    settings = settings or get_settings()
    session_factory = session_factory or _require_database(settings)
    if event_bus is None:
        publisher, event_bus = build_event_publisher(settings)
    else:
        publisher = EventPublisher(event_bus, publisher="automation-beat")
    service = AutomationService(
        uow_factory=lambda: AutomationUnitOfWork.build(session_factory),
        event_publisher=publisher,
        settings=settings,
    )

    async def _run() -> dict[str, Any]:
        return await run_beat_tick(service, settings)

    return asyncio.run(_run())


@celery_app.task(
    name="automation.run_executor",
    bind=True,
    acks_late=True,
    max_retries=0,  # retries are owned by the durable ledger, never Celery
    time_limit=3600,
    soft_time_limit=3300,
)
def run_executor(self, queue_item_id: str) -> dict[str, Any]:
    """Execute one durable queue item (idempotent-safe re-delivery)."""
    return run_executor_sync(queue_item_id)


@celery_app.task(
    name="automation.beat_tick",
    acks_late=True,
    max_retries=0,
    time_limit=600,
    soft_time_limit=540,
)
def beat_tick() -> dict[str, Any]:
    """Wake the DB-driven scheduler tick (single-scheduler lock)."""
    return beat_tick_sync()


__all__ = [
    "beat_tick",
    "beat_tick_sync",
    "run_executor",
    "run_executor_sync",
]
