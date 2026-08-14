"""Execution workflow tests (M10 Step 2): claim → execute → persist → notify.

Runs the ledger-driven state machine against an in-memory database with a
mocked sibling transport. Verifies success, retryable/terminal failures,
AI OS correlation advancement, late-ack redelivery safety, timeouts, and
tenancy forwarding.
"""

import asyncio
import json
from datetime import UTC

import httpx

from atoz_automation_service.domain.entities import PlatformBase
from atoz_automation_service.executors import build_default_registry
from atoz_automation_service.executors.base import (
    Executor,
    ExecutorContext,
    ExecutorResult,
    success,
)
from atoz_automation_service.executors.clients import SiblingClients
from atoz_automation_service.repositories import AutomationUnitOfWork
from atoz_automation_service.workflow import ExecutionWorkflow
from atoz_backend_core.db.base import Base
from atoz_backend_core.events.bus import InMemoryEventBus
from atoz_backend_core.events.publisher import EventPublisher

from .fixtures import make_settings, scenario


async def build_world(*, settings=None, transport=None):
    """In-memory DB + service + workflow with a mocked sibling transport."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from atoz_automation_service.services import AutomationService

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(PlatformBase.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = settings or make_settings()
    bus = InMemoryEventBus()
    captured: list = []

    async def capture(event) -> None:
        captured.append(event)

    for event_type in (
        "automation:job-enqueued.v1",
        "automation:job-queued.v1",
        "automation:job-started.v1",
        "automation:job-succeeded.v1",
        "automation:job-failed.v1",
        "automation:job-retry-scheduled.v1",
        "automation:aios-job-created.v1",
        "automation:aios-job-succeeded.v1",
        "automation:aios-job-failed.v1",
    ):
        await bus.subscribe(event_type, capture)
    publisher = EventPublisher(bus, publisher="automation-test")
    service = AutomationService(
        uow_factory=lambda: AutomationUnitOfWork.build(session_factory),
        event_publisher=publisher,
        settings=settings,
    )
    siblings = SiblingClients(
        settings, transport=transport or httpx.MockTransport(lambda r: httpx.Response(200, json={}))
    )
    workflow = ExecutionWorkflow(
        uow_factory=lambda: AutomationUnitOfWork.build(session_factory),
        event_publisher=publisher,
        settings=settings,
        registry=build_default_registry(),
        siblings=siblings,
    )
    return engine, session_factory, service, workflow, captured, siblings


async def make_enabled_job(
    service, *, niche_id=None, queue="seo", handler="seo.sitemap_rebuild", config=None
):
    job = await service.create_scheduled_job(
        niche_id=niche_id,
        job_key=f"job-{queue}-{handler}",
        cron_expr="0 6 * * *",
        queue=queue,
        handler=handler,
        config=config,
    )
    return job


def test_workflow_success_completes_queue_and_run() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"shard_count": 2})

        engine, _, service, workflow, captured, siblings = await build_world(
            transport=httpx.MockTransport(handler)
        )
        try:
            niche = await service.create_niche(name="A", slug="wf-a", status="active")
            job = await make_enabled_job(service, niche_id=niche.id)
            run_row, item = await service.enqueue_job(job.id, niche.id)

            outcome = await workflow.run(item.id)
            assert outcome["status"] == "success"

            runs = await service.list_job_runs(niche.id)
            assert runs[0].status == "success"
            assert runs[0].attempts == 1
            items = await service.list_queue(niche.id)
            assert items[0].state == "done"
            types = {e.type for e in captured}
            assert "automation:job-started.v1" in types
            assert "automation:job-succeeded.v1" in types
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)


def test_workflow_retryable_failure_requeues_with_backoff() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"detail": "busy"})

        engine, _, service, workflow, captured, siblings = await build_world(
            transport=httpx.MockTransport(handler)
        )
        try:
            niche = await service.create_niche(name="A", slug="wf-b", status="active")
            job = await make_enabled_job(service, niche_id=niche.id)
            _run_row, item = await service.enqueue_job(job.id, niche.id)
            original_run_at = item.run_at

            outcome = await workflow.run(item.id)
            assert outcome["status"] == "retry_scheduled"
            assert outcome["attempts"] == 1

            items = await service.list_queue(niche.id)
            assert items[0].state == "queued"
            requeued_at = items[0].run_at
            if requeued_at.tzinfo is None:
                requeued_at = requeued_at.replace(tzinfo=UTC)
            assert requeued_at > original_run_at  # backoff pushed it forward
            runs = await service.list_job_runs(niche.id)
            assert runs[0].status == "pending"
            assert runs[0].started_at is None
            types = {e.type for e in captured}
            assert "automation:job-retry-scheduled.v1" in types
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)


def test_workflow_terminal_failure_marks_failed() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"detail": "permanent"})

        settings = make_settings(queue_max_attempts=1)
        engine, _, service, workflow, captured, siblings = await build_world(
            settings=settings, transport=httpx.MockTransport(handler)
        )
        try:
            niche = await service.create_niche(name="A", slug="wf-c", status="active")
            job = await make_enabled_job(service, niche_id=niche.id)
            _run_row, item = await service.enqueue_job(job.id, niche.id)

            outcome = await workflow.run(item.id)
            assert outcome["status"] == "failed"

            items = await service.list_queue(niche.id)
            assert items[0].state == "failed"
            assert items[0].error
            runs = await service.list_job_runs(niche.id)
            assert runs[0].status == "failed"
            types = {e.type for e in captured}
            assert "automation:job-failed.v1" in types
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)


def test_workflow_unknown_executor_is_terminal() -> None:
    async def run() -> None:
        engine, _, service, workflow, _captured, siblings = await build_world()
        try:
            niche = await service.create_niche(name="A", slug="wf-d", status="active")
            item, _created = await service.enqueue(
                niche_id=niche.id, queue="does-not-exist", payload_ref="x:1"
            )
            outcome = await workflow.run(item.id)
            assert outcome["status"] == "failed"
            assert "unknown executor" in outcome["error"]
            items = await service.list_queue(niche.id)
            assert items[0].state == "failed"
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)


def test_workflow_aios_correlation_advances() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"job_id": "aios-job-9"})

        engine, _, service, workflow, captured, siblings = await build_world(
            transport=httpx.MockTransport(handler)
        )
        try:
            niche = await service.create_niche(name="A", slug="wf-aios", status="active")
            job = await make_enabled_job(
                service,
                niche_id=niche.id,
                queue="aios",
                handler="aios.dispatch",
                config={
                    "job_id": "a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
                    "contract": "seo-metadata",
                    "request": {"article_id": "art-1"},
                },
            )
            _run_row, item = await service.enqueue_job(job.id, niche.id)
            aios = await service.create_aios_job(
                niche_id=niche.id,
                job_id="a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
                contract="seo-metadata",
            )
            assert aios[0].status == "pending"

            outcome = await workflow.run(item.id)
            assert outcome["status"] == "success"

            rows = await service.list_aios_jobs(niche.id)
            assert rows[0].status == "succeeded"
            types = {e.type for e in captured}
            assert "automation:aios-job-succeeded.v1" in types
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)


def test_workflow_aios_failure_advances_to_failed() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={"detail": "AI OS busy"})

        settings = make_settings(queue_max_attempts=1)
        engine, _, service, workflow, captured, siblings = await build_world(
            settings=settings, transport=httpx.MockTransport(handler)
        )
        try:
            niche = await service.create_niche(name="A", slug="wf-aios-f", status="active")
            job = await make_enabled_job(
                service,
                niche_id=niche.id,
                queue="aios",
                handler="aios.dispatch",
                config={
                    "job_id": "a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
                    "contract": "analytics-insights",
                    "request": {},
                },
            )
            _run_row, item = await service.enqueue_job(job.id, niche.id)
            await service.create_aios_job(
                niche_id=niche.id,
                job_id="a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
                contract="analytics-insights",
            )

            outcome = await workflow.run(item.id)
            assert outcome["status"] == "failed"

            rows = await service.list_aios_jobs(niche.id)
            assert rows[0].status == "failed"
            assert rows[0].attempts == 1
            types = {e.type for e in captured}
            assert "automation:aios-job-failed.v1" in types
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)


def test_workflow_late_ack_redelivery_is_idempotent() -> None:
    """A re-delivered claimed item re-executes safely (idempotent-safe)."""

    async def run() -> None:
        calls = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            calls["n"] += 1
            return httpx.Response(200, json={"shard_count": 1})

        engine, _, service, workflow, captured, siblings = await build_world(
            transport=httpx.MockTransport(handler)
        )
        try:
            niche = await service.create_niche(name="A", slug="wf-late", status="active")
            job = await make_enabled_job(service, niche_id=niche.id)
            _run_row, item = await service.enqueue_job(job.id, niche.id)
            # Simulate a worker crash after claim: the row is already claimed.
            await service.claim_queue_item(item.id, niche.id)

            first = await workflow.run(item.id)  # late-ack redelivery
            assert first["status"] == "success"
            # A second redelivery finds the terminal row → no-op, no re-execution.
            second = await workflow.run(item.id)
            assert second["status"] == "noop"
            assert calls["n"] == 1
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)


def test_workflow_timeout_is_retryable_failure() -> None:
    async def run() -> None:
        class SlowExecutor(Executor):
            name = "slow.executor"
            queue = "slow"

            async def execute(self, ctx: ExecutorContext) -> ExecutorResult:
                await asyncio.sleep(5)
                return success(summary="never")

        settings = make_settings(executor_timeout_seconds=0.05, queue_max_attempts=1)
        engine, _, service, workflow, _captured, siblings = await build_world(settings=settings)
        try:
            workflow._registry.register(SlowExecutor())  # noqa: SLF001
            niche = await service.create_niche(name="A", slug="wf-timeout", status="active")
            item, _created = await service.enqueue(
                niche_id=niche.id, queue="slow", payload_ref="x:1"
            )
            outcome = await workflow.run(item.id)
            assert outcome["status"] == "failed"
            assert "timed out" in outcome["error"]
            items = await service.list_queue(niche.id)
            assert items[0].state == "failed"
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)


def test_workflow_override_config_payload_ref() -> None:
    """enqueue_job_with_config stores the override on the queue item."""

    async def run() -> None:
        captured: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["path"] = request.url.path
            return httpx.Response(200, json={"shard_count": 4})

        engine, _, service, workflow, _captured, siblings = await build_world(
            transport=httpx.MockTransport(handler)
        )
        try:
            niche = await service.create_niche(name="A", slug="wf-cfg", status="active")
            job = await make_enabled_job(service, niche_id=niche.id, config={"group": "articles"})
            run_row, item = await service.enqueue_job_with_config(
                job.id, niche.id, config={"group": "products"}
            )
            parsed = json.loads(item.payload_ref)
            assert parsed["job_run_id"] == run_row.id
            assert parsed["config"] == {"group": "products"}

            outcome = await workflow.run(item.id)
            assert outcome["status"] == "success"
            assert captured["path"] == "/api/v1/admin/sitemaps/products/rebuild"
        finally:
            await siblings.aclose()
            await engine.dispose()

    scenario(run)
