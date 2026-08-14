"""Queue/worker Prometheus metrics tests (M11 Phase D)."""

import asyncio
from datetime import UTC, datetime

from prometheus_client import generate_latest
from sqlalchemy.ext.asyncio import async_sessionmaker

from atoz_automation_service import observability
from atoz_automation_service.domain.entities import JobRun, QueueItem, ScheduledJob
from atoz_automation_service.observability import refresh_queue_metrics
from atoz_automation_service.services import AutomationService

from .fixtures import build_app


def _metric_value(samples: bytes, name: str, label: str) -> int:
    text = samples.decode()
    needle = f'{name}{{state="{label}"}}'
    if needle not in text:
        needle = f'{name}{{status="{label}"}}'
    for line in text.splitlines():
        if line.startswith(needle):
            return int(float(line.split()[-1]))
    return -1


def test_refresh_queue_metrics() -> None:
    async def scenario() -> None:
        app, engine, _bus, _events = await build_app()
        service: AutomationService = app.state.automation_service
        now = datetime.now(UTC)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            job = ScheduledJob(
                id="job-1",
                niche_id=None,
                job_key="seo.sitemap_rebuild",
                cron_expr="0 * * * *",
                queue="seo",
                handler="seo.sitemap_rebuild",
                status="enabled",
                next_run_at=now,
            )
            session.add(job)
            await session.flush()
            session.add_all(
                [
                    QueueItem(
                        id=f"q-{i}",
                        niche_id=None,
                        queue="seo",
                        payload_ref=f"ref-{i}",
                        state=state,
                        run_at=now,
                    )
                    for i, state in enumerate(["queued", "claimed", "done", "failed"])
                ]
            )
            session.add_all(
                [
                    JobRun(
                        id=f"r-{i}",
                        niche_id=None,
                        scheduled_job_id="job-1",
                        status=status,
                        run_at=now,
                    )
                    for i, status in enumerate(["running", "success", "failed"])
                ]
            )
            await session.commit()

        await refresh_queue_metrics(service.uow_factory)
        samples = generate_latest()
        assert _metric_value(samples, "atoz_queue_items", "queued") == 1
        assert _metric_value(samples, "atoz_queue_items", "claimed") == 1
        assert _metric_value(samples, "atoz_queue_items", "done") == 1
        assert _metric_value(samples, "atoz_queue_items", "failed") == 1
        assert _metric_value(samples, "atoz_queue_items", "cancelled") == 0
        assert _metric_value(samples, "atoz_job_runs", "running") == 1
        assert _metric_value(samples, "atoz_job_runs", "success") == 1
        assert _metric_value(samples, "atoz_job_runs", "failed") == 1
        assert "atoz_scheduled_jobs_due 1" in samples.decode()

    asyncio.run(scenario())


def test_metrics_loop_survives_failures() -> None:
    """A broken UoW must degrade to a warning, not crash the worker."""

    def broken_factory():
        raise RuntimeError("boom")

    async def scenario() -> None:
        loop = asyncio.get_running_loop()
        task = loop.create_task(observability.metrics_loop(broken_factory, interval_seconds=0.01))
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    asyncio.run(scenario())
