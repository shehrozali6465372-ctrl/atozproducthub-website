"""Queue/worker Prometheus metrics for automation-service (M11 Phase D).

Exposes durable-queue depth, job-run state counts, and due-scheduler load on
the shared ``/metrics`` endpoint so Prometheus can alert on queue
starvation, stuck runs, and failure spikes. Metrics are business data only —
no AI, no intelligence (Website Contract §4).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from prometheus_client import Gauge

logger = logging.getLogger("atoz.automation.metrics")

QUEUE_STATES = ("queued", "claimed", "done", "failed", "cancelled")
JOB_RUN_STATUSES = ("pending", "running", "success", "failed", "cancelled")

queue_items_gauge = Gauge("atoz_queue_items", "Durable queue ledger items by state", ["state"])
job_runs_gauge = Gauge("atoz_job_runs", "Platform job runs by status", ["status"])
scheduled_jobs_due_gauge = Gauge(
    "atoz_scheduled_jobs_due", "Enabled scheduled jobs whose next run is due", []
)


async def refresh_queue_metrics(uow_factory) -> None:
    """Refresh gauges from the durable ledgers (global compartment).

    The global compartment intentionally aggregates every niche: alerting
    cares about total starvation, while niche-level detail stays in the
    admin API where tenancy is enforced per request.
    """
    async with uow_factory().transaction() as unit:
        for state in QUEUE_STATES:
            queue_items_gauge.labels(state=state).set(
                await unit.queue.count_scoped(None, state=state)
            )
        for status in JOB_RUN_STATUSES:
            job_runs_gauge.labels(status=status).set(
                await unit.job_runs.count_by_status(None, status)
            )
        scheduled_jobs_due_gauge.set(await unit.scheduled_jobs.count_due(datetime.now(UTC)))


async def metrics_loop(uow_factory, *, interval_seconds: float) -> None:
    """Background refresh loop; failures degrade to warnings, never crash."""
    while True:
        try:
            await refresh_queue_metrics(uow_factory)
        except Exception as exc:  # noqa: BLE001
            logger.warning("queue metrics refresh failed: %s", exc)
        await asyncio.sleep(interval_seconds)


def start_metrics_task(app, *, uow_factory, interval_seconds: float) -> None:
    """Start the metrics refresh task and cancel it on shutdown."""
    task = asyncio.create_task(metrics_loop(uow_factory, interval_seconds=interval_seconds))
    app.state.metrics_task = task
    app.add_event_handler("shutdown", lambda: task.cancel())
