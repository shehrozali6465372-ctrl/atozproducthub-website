"""Automation business layer (Task 20 / M10 foundation).

Facade over the automation_db repositories implementing the durable
automation engine foundation:

- Rule lifecycle: create (unique ``(niche_id, code)``), ``disabled →
  enabled`` / ``enabled → disabled`` transitions, manual trigger.
- Run history: append-only ``automation_runs`` with idempotent triggers
  (client-supplied ``Idempotency-Key``), status transitions, events.
- Scheduler: Platform ``scheduled_jobs`` + ``job_runs`` definitions and
  execution records; enqueue creates the run and a durable ``queue_items``
  ledger row (Redis working set rebuildable from the ledger).
- Queue ledger: explicit ``queued → claimed → done/failed`` transitions
  with audited retries (exponential backoff + jitter) and idempotent
  enqueue (open item with the same payload is reused).
- AI OS Bridge correlation: ``aios_job_records`` with ``UNIQUE (job_id,
  contract)`` dedupe — correlation metadata only, never AI internals.
- Celery is scaffolded separately (``celery_app.py``); no business tasks
  exist yet (Step 2 wires executors).

The service performs zero AI work; AI OS jobs are recorded for correlation
only and executed by the Bridge (Website Contract §4).
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from atoz_automation_service.config import Settings
from atoz_automation_service.domain.entities import (
    AiosJobRecord,
    AutomationNiche,
    AutomationRule,
    AutomationRun,
    JobRun,
    QueueItem,
    ScheduledJob,
)
from atoz_automation_service.domain.enums import (
    AiosDirection,
    AiosJobStatus,
    JobRunStatus,
    QueueState,
    RuleStatus,
    RuleTriggerType,
    RunStatus,
)
from atoz_automation_service.domain.events import (
    aios_job_created_event,
    job_enqueued_event,
    job_queued_event,
    rule_disabled_event,
    rule_enabled_event,
    run_failed_event,
    run_started_event,
    run_succeeded_event,
)
from atoz_automation_service.domain.retry import next_retry_at
from atoz_automation_service.errors import (
    DuplicateError,
    NotFoundError,
    ValidationError,
)
from atoz_automation_service.repositories import AutomationUnitOfWork
from atoz_automation_service.uuids import uuid7
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher

logger = logging.getLogger("atoz.automation.service")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _json_default(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True)


class AutomationService:
    """Facade for the automation business layer (niche/global scoped)."""

    def __init__(
        self,
        *,
        uow_factory,
        event_publisher: EventPublisher,
        settings: Settings,
    ) -> None:
        self._uow_factory = uow_factory
        self._event_publisher = event_publisher
        self._settings = settings

    @property
    def uow_factory(self):
        """Unit-of-work factory used by the observability refresh task."""
        return self._uow_factory

    @staticmethod
    def build_uow(session_factory) -> AutomationUnitOfWork:
        return AutomationUnitOfWork.build(session_factory)

    async def publish(self, event: EventEnvelope) -> None:
        await self._event_publisher.publish(event)

    # ----------------------------------------------------------- niches
    async def create_niche(self, *, name: str, slug: str, status: str = "draft") -> AutomationNiche:
        async with self._uow_factory().transaction() as unit:
            if await unit.niches.slug_exists(slug):
                raise DuplicateError("A niche with this slug already exists.")
            row = AutomationNiche(id=uuid7(), slug=slug, name=name, status=status)
            await unit.niches.add(row)
            return row

    async def get_niche(self, niche_id: str) -> AutomationNiche | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.get(niche_id)

    async def get_niche_by_slug(self, slug: str) -> AutomationNiche | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.get_by_slug(slug)

    async def list_niches(self) -> Sequence[AutomationNiche]:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.list_by_status()

    async def _require_niche(self, niche_id: str) -> AutomationNiche:
        niche = await self.get_niche(niche_id)
        if niche is None:
            raise ValidationError("The requested niche is not registered.")
        return niche

    # ----------------------------------------------------------- rules
    async def create_rule(
        self,
        *,
        niche_id: str | None,
        code: str,
        trigger_type: str,
        config: dict[str, Any] | None = None,
        run_as_user_id: str | None = None,
    ) -> AutomationRule:
        if not code.strip() or len(code) > 120:
            raise ValidationError("Rule code is required (max 120 chars).")
        try:
            trigger = RuleTriggerType(trigger_type)
        except ValueError as exc:
            raise ValidationError(f"Unsupported trigger_type: {trigger_type!r}.") from exc
        if niche_id is not None:
            await self._require_niche(niche_id)
        async with self._uow_factory().transaction() as unit:
            if await unit.rules.get_by_code(niche_id, code) is not None:
                raise DuplicateError("An automation rule with this code already exists.")
            row = AutomationRule(
                id=uuid7(),
                niche_id=niche_id,
                code=code,
                trigger_type=trigger.value,
                config_json=_json_default(config or {}),
                status=RuleStatus.DISABLED.value,
                run_as_user_id=run_as_user_id,
            )
            await unit.rules.add(row)
            return row

    async def get_rule(self, rule_id: str, niche_id: str | None) -> AutomationRule | None:
        async with self._uow_factory().transaction() as unit:
            return await self._scoped_get(unit.rules, rule_id, niche_id)

    async def list_rules(self, niche_id: str | None) -> Sequence[AutomationRule]:
        async with self._uow_factory().transaction() as unit:
            return await unit.rules.list_scoped(niche_id)

    async def enable_rule(self, rule_id: str, niche_id: str | None) -> AutomationRule:
        async with self._uow_factory().transaction() as unit:
            rule = await self._scoped_get(unit.rules, rule_id, niche_id)
            if rule is None:
                raise NotFoundError("Automation rule not found.")
            if rule.status != RuleStatus.DISABLED.value:
                raise ValidationError("Only disabled rules can be enabled.")
            rule.status = RuleStatus.ENABLED.value
            await self.publish(
                rule_enabled_event(niche_id=rule.niche_id, rule_id=rule.id, code=rule.code)
            )
            return rule

    async def disable_rule(self, rule_id: str, niche_id: str | None) -> AutomationRule:
        async with self._uow_factory().transaction() as unit:
            rule = await self._scoped_get(unit.rules, rule_id, niche_id)
            if rule is None:
                raise NotFoundError("Automation rule not found.")
            if rule.status != RuleStatus.ENABLED.value:
                raise ValidationError("Only enabled rules can be disabled.")
            rule.status = RuleStatus.DISABLED.value
            await self.publish(
                rule_disabled_event(niche_id=rule.niche_id, rule_id=rule.id, code=rule.code)
            )
            return rule

    # ----------------------------------------------------------- runs
    async def trigger_rule(
        self,
        *,
        rule_id: str,
        niche_id: str | None,
        triggered_by: str | None = None,
        idempotency_key: str | None = None,
    ) -> tuple[AutomationRun, bool]:
        """Start a rule run; ``(run, created)`` with idempotent replay.

        A previously accepted ``idempotency_key`` returns the existing run
        with ``created=False`` (the key is globally unique per
        ADR-0010) — replays never duplicate execution history.
        """
        if idempotency_key and len(idempotency_key) > 128:
            raise ValidationError("Idempotency-Key exceeds 128 chars.")
        if idempotency_key:
            async with self._uow_factory().transaction() as unit:
                existing = await unit.runs.get_by_idempotency_key(idempotency_key)
                if existing is not None:
                    return existing, False
        async with self._uow_factory().transaction() as unit:
            rule = await self._scoped_get(unit.rules, rule_id, niche_id)
            if rule is None:
                raise NotFoundError("Automation rule not found.")
            if rule.status != RuleStatus.ENABLED.value:
                raise ValidationError("Only enabled rules can be triggered.")
            run = AutomationRun(
                id=uuid7(),
                niche_id=rule.niche_id,
                automation_rule_id=rule.id,
                triggered_by=triggered_by,
                idempotency_key=idempotency_key,
                status=RunStatus.RUNNING.value,
                started_at=_utcnow(),
            )
            await unit.runs.add(run)
            await self.publish(
                run_started_event(
                    niche_id=rule.niche_id,
                    rule_id=rule.id,
                    run_id=run.id,
                    triggered_by=triggered_by,
                )
            )
            return run, True

    async def complete_run(
        self, run_id: str, niche_id: str | None, *, summary: str | None = None
    ) -> AutomationRun:
        async with self._uow_factory().transaction() as unit:
            run = await self._scoped_get(unit.runs, run_id, niche_id)
            if run is None:
                raise NotFoundError("Automation run not found.")
            if run.status != RunStatus.RUNNING.value:
                raise ValidationError("Only running runs can complete.")
            run.status = RunStatus.SUCCESS.value
            run.finished_at = _utcnow()
            run.result_summary = summary
            await self.publish(
                run_succeeded_event(niche_id=run.niche_id, run_id=run.id, summary=summary)
            )
            return run

    async def fail_run(
        self, run_id: str, niche_id: str | None, *, error: str | None = None
    ) -> AutomationRun:
        async with self._uow_factory().transaction() as unit:
            run = await self._scoped_get(unit.runs, run_id, niche_id)
            if run is None:
                raise NotFoundError("Automation run not found.")
            if run.status != RunStatus.RUNNING.value:
                raise ValidationError("Only running runs can fail.")
            run.status = RunStatus.FAILED.value
            run.finished_at = _utcnow()
            run.error = error
            await self.publish(run_failed_event(niche_id=run.niche_id, run_id=run.id, error=error))
            return run

    async def list_runs(
        self,
        niche_id: str | None,
        *,
        rule_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AutomationRun]:
        async with self._uow_factory().transaction() as unit:
            return await unit.runs.list_scoped(
                niche_id, rule_id=rule_id, status=status, limit=limit, offset=offset
            )

    async def run_count_by_status(self, niche_id: str | None, status: str) -> int:
        async with self._uow_factory().transaction() as unit:
            return await unit.runs.count_by_status(niche_id, status)

    # ------------------------------------------------------- scheduler
    async def create_scheduled_job(
        self,
        *,
        niche_id: str | None,
        job_key: str,
        cron_expr: str,
        queue: str,
        handler: str,
        config: dict[str, Any] | None = None,
        next_run_at: datetime | None = None,
    ) -> ScheduledJob:
        if not job_key.strip() or len(job_key) > 120:
            raise ValidationError("job_key is required (max 120 chars).")
        if not cron_expr.strip() or len(cron_expr) > 100:
            raise ValidationError("cron_expr is required (max 100 chars).")
        if not handler.strip() or len(handler) > 200:
            raise ValidationError("handler is required (max 200 chars).")
        if niche_id is not None:
            await self._require_niche(niche_id)
        async with self._uow_factory().transaction() as unit:
            if await unit.scheduled_jobs.get_by_key(niche_id, job_key) is not None:
                raise DuplicateError("A scheduled job with this key already exists.")
            row = ScheduledJob(
                id=uuid7(),
                niche_id=niche_id,
                job_key=job_key,
                cron_expr=cron_expr,
                queue=queue or "default",
                handler=handler,
                config_json=_json_default(config or {}),
                status="enabled",
                next_run_at=next_run_at,
            )
            await unit.scheduled_jobs.add(row)
            return row

    async def get_scheduled_job(self, job_id: str, niche_id: str | None) -> ScheduledJob | None:
        async with self._uow_factory().transaction() as unit:
            return await self._scoped_get(unit.scheduled_jobs, job_id, niche_id)

    async def list_scheduled_jobs(self, niche_id: str | None) -> Sequence[ScheduledJob]:
        async with self._uow_factory().transaction() as unit:
            return await unit.scheduled_jobs.list_scoped(niche_id)

    async def list_due_scheduled_jobs(self, now: datetime) -> Sequence[ScheduledJob]:
        """Internal scheduler scan: enabled jobs whose ``next_run_at`` passed.

        Runs across every scope (single-scheduler Beat). Each returned job
        is enqueued with its own ``niche_id``; sibling calls then carry that
        scope server-side, so no cross-niche work can ever be produced.
        """
        async with self._uow_factory().transaction() as unit:
            return await unit.scheduled_jobs.list_due(now)

    async def update_scheduled_job_next_run(
        self,
        job_id: str,
        niche_id: str | None,
        *,
        next_run_at: datetime,
    ) -> ScheduledJob:
        """Advance ``next_run_at`` after a Beat enqueue (croniter next)."""
        async with self._uow_factory().transaction() as unit:
            job = await self._scoped_get(unit.scheduled_jobs, job_id, niche_id)
            if job is None:
                raise NotFoundError("Scheduled job not found.")
            job.next_run_at = next_run_at
            return job

    async def set_scheduled_job_status(
        self, job_id: str, niche_id: str | None, *, enabled: bool
    ) -> ScheduledJob:
        async with self._uow_factory().transaction() as unit:
            job = await self._scoped_get(unit.scheduled_jobs, job_id, niche_id)
            if job is None:
                raise NotFoundError("Scheduled job not found.")
            desired = "enabled" if enabled else "disabled"
            if job.status == desired:
                raise ValidationError(f"Scheduled job is already {desired}.")
            job.status = desired
            return job

    async def enqueue_job(
        self,
        job_id: str,
        niche_id: str | None,
        *,
        run_at: datetime | None = None,
    ) -> tuple[JobRun, QueueItem]:
        """Queue one execution of a scheduled job.

        Creates the ``job_runs`` record (queued/pending state) and a durable
        ``queue_items`` ledger row whose payload references the run
        (``job_run:{run_id}``) so the Redis working set stays rebuildable
        from the ledger (Blueprint §5.23). Each enqueue is a distinct
        execution instance; duplicate prevention for the same work item is
        enforced by the queue-ledger dedupe on
        ``(niche_id, queue, payload_ref)`` and by ``UNIQUE (niche_id,
        job_key)`` at definition time.
        """
        async with self._uow_factory().transaction() as unit:
            job = await self._scoped_get(unit.scheduled_jobs, job_id, niche_id)
            if job is None:
                raise NotFoundError("Scheduled job not found.")
            if job.status != "enabled":
                raise ValidationError("Only enabled scheduled jobs can be enqueued.")
            run_row = JobRun(
                id=uuid7(),
                niche_id=job.niche_id,
                scheduled_job_id=job.id,
                run_at=run_at or _utcnow(),
                status=JobRunStatus.PENDING.value,
                attempts=0,
            )
            await unit.job_runs.add(run_row)
            item = QueueItem(
                id=uuid7(),
                niche_id=job.niche_id,
                queue=job.queue,
                payload_ref=f"job_run:{run_row.id}",
                state=QueueState.QUEUED.value,
                attempts=0,
                max_attempts=self._settings.queue_max_attempts,
                run_at=run_at or _utcnow(),
            )
            await unit.queue.add(item)
            job.last_run_at = _utcnow()
            await self.publish(
                job_enqueued_event(
                    niche_id=job.niche_id,
                    job_id=job.id,
                    run_id=run_row.id,
                    queue=job.queue,
                    run_at=run_row.run_at.isoformat(),
                )
            )
            await self.publish(
                job_queued_event(
                    niche_id=job.niche_id,
                    queue_item_id=item.id,
                    payload_ref=item.payload_ref,
                    queue=item.queue,
                )
            )
            return run_row, item

    async def enqueue_job_with_config(
        self,
        job_id: str,
        niche_id: str | None,
        *,
        run_at: datetime | None = None,
        config: dict[str, Any] | None = None,
    ) -> tuple[JobRun, QueueItem]:
        """Queue one execution of a scheduled job with an override config.

        The override config is stored **on the queue item** (JSON payload
        reference), never merged into the scheduled job definition, so the
        frozen ``config_json`` stays intact for future scheduled runs. The
        execution workflow unwraps the ``{job_run_id, scheduled_job_id,
        config}`` reference and runs the executor with the override.
        """
        async with self._uow_factory().transaction() as unit:
            job = await self._scoped_get(unit.scheduled_jobs, job_id, niche_id)
            if job is None:
                raise NotFoundError("Scheduled job not found.")
            if job.status != "enabled":
                raise ValidationError("Only enabled scheduled jobs can be enqueued.")
            run_row = JobRun(
                id=uuid7(),
                niche_id=job.niche_id,
                scheduled_job_id=job.id,
                run_at=run_at or _utcnow(),
                status=JobRunStatus.PENDING.value,
                attempts=0,
            )
            await unit.job_runs.add(run_row)
            payload_ref = json.dumps(
                {
                    "job_run_id": run_row.id,
                    "scheduled_job_id": job.id,
                    "config": config or {},
                },
                sort_keys=True,
            )
            item = QueueItem(
                id=uuid7(),
                niche_id=job.niche_id,
                queue=job.queue,
                payload_ref=payload_ref,
                state=QueueState.QUEUED.value,
                attempts=0,
                max_attempts=self._settings.queue_max_attempts,
                run_at=run_at or _utcnow(),
            )
            await unit.queue.add(item)
            job.last_run_at = _utcnow()
            await self.publish(
                job_enqueued_event(
                    niche_id=job.niche_id,
                    job_id=job.id,
                    run_id=run_row.id,
                    queue=job.queue,
                    run_at=run_row.run_at.isoformat(),
                )
            )
            await self.publish(
                job_queued_event(
                    niche_id=job.niche_id,
                    queue_item_id=item.id,
                    payload_ref=item.payload_ref,
                    queue=item.queue,
                )
            )
            return run_row, item

    async def start_job_run(self, run_id: str, niche_id: str | None) -> JobRun:
        async with self._uow_factory().transaction() as unit:
            run = await self._scoped_get(unit.job_runs, run_id, niche_id)
            if run is None:
                raise NotFoundError("Job run not found.")
            if run.status != JobRunStatus.PENDING.value:
                raise ValidationError("Only pending job runs can start.")
            run.status = JobRunStatus.RUNNING.value
            run.started_at = _utcnow()
            run.attempts += 1
            return run

    async def complete_job_run(
        self, run_id: str, niche_id: str | None, *, output_ref: str | None = None
    ) -> JobRun:
        async with self._uow_factory().transaction() as unit:
            run = await self._scoped_get(unit.job_runs, run_id, niche_id)
            if run is None:
                raise NotFoundError("Job run not found.")
            if run.status != JobRunStatus.RUNNING.value:
                raise ValidationError("Only running job runs can complete.")
            run.status = JobRunStatus.SUCCESS.value
            run.finished_at = _utcnow()
            run.output_ref = output_ref
            return run

    async def fail_job_run(
        self,
        run_id: str,
        niche_id: str | None,
        *,
        error: str | None = None,
        retry: bool = True,
    ) -> JobRun:
        async with self._uow_factory().transaction() as unit:
            run = await self._scoped_get(unit.job_runs, run_id, niche_id)
            if run is None:
                raise NotFoundError("Job run not found.")
            if run.status != JobRunStatus.RUNNING.value:
                raise ValidationError("Only running job runs can fail.")
            if retry and run.attempts < self._settings.job_max_attempts:
                run.status = JobRunStatus.PENDING.value
                run.started_at = None
                run.error = error
                return run
            run.status = JobRunStatus.FAILED.value
            run.finished_at = _utcnow()
            run.error = error
            return run

    async def cancel_job_run(self, run_id: str, niche_id: str | None) -> JobRun:
        async with self._uow_factory().transaction() as unit:
            run = await self._scoped_get(unit.job_runs, run_id, niche_id)
            if run is None:
                raise NotFoundError("Job run not found.")
            if run.status not in (JobRunStatus.PENDING.value, JobRunStatus.RUNNING.value):
                raise ValidationError("Only pending/running job runs can be cancelled.")
            run.status = JobRunStatus.CANCELLED.value
            run.finished_at = _utcnow()
            return run

    async def list_job_runs(
        self,
        niche_id: str | None,
        *,
        job_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[JobRun]:
        async with self._uow_factory().transaction() as unit:
            return await unit.job_runs.list_scoped(
                niche_id, job_id=job_id, status=status, limit=limit, offset=offset
            )

    # ------------------------------------------------------------ queue
    async def enqueue(
        self,
        *,
        niche_id: str | None,
        queue: str,
        payload_ref: str,
        run_at: datetime | None = None,
        max_attempts: int | None = None,
    ) -> tuple[QueueItem, bool]:
        """Idempotent enqueue: an open item with the same payload is reused."""
        if not queue.strip() or len(queue) > 80:
            raise ValidationError("queue is required (max 80 chars).")
        if not payload_ref.strip() or len(payload_ref) > 500:
            raise ValidationError("payload_ref is required (max 500 chars).")
        if niche_id is not None:
            await self._require_niche(niche_id)
        async with self._uow_factory().transaction() as unit:
            existing = await unit.queue.get_open_by_payload(niche_id, queue, payload_ref)
            if existing is not None:
                return existing, False
            item = QueueItem(
                id=uuid7(),
                niche_id=niche_id,
                queue=queue,
                payload_ref=payload_ref,
                state=QueueState.QUEUED.value,
                attempts=0,
                max_attempts=max_attempts or self._settings.queue_max_attempts,
                run_at=run_at or _utcnow(),
            )
            await unit.queue.add(item)
            return item, True

    async def claim_queue_item(self, item_id: str, niche_id: str | None) -> QueueItem:
        async with self._uow_factory().transaction() as unit:
            item = await unit.queue.get_scoped(item_id, niche_id)
            if item is None:
                raise NotFoundError("Queue item not found.")
            if item.state != QueueState.QUEUED.value:
                raise ValidationError("Only queued items can be claimed.")
            item.state = QueueState.CLAIMED.value
            item.attempts += 1
            return item

    async def complete_queue_item(self, item_id: str, niche_id: str | None) -> QueueItem:
        async with self._uow_factory().transaction() as unit:
            item = await unit.queue.get_scoped(item_id, niche_id)
            if item is None:
                raise NotFoundError("Queue item not found.")
            if item.state != QueueState.CLAIMED.value:
                raise ValidationError("Only claimed items can complete.")
            item.state = QueueState.DONE.value
            item.completed_at = _utcnow()
            return item

    async def fail_queue_item(
        self, item_id: str, niche_id: str | None, *, error: str | None = None, retry: bool = True
    ) -> QueueItem:
        async with self._uow_factory().transaction() as unit:
            item = await unit.queue.get_scoped(item_id, niche_id)
            if item is None:
                raise NotFoundError("Queue item not found.")
            if item.state != QueueState.CLAIMED.value:
                raise ValidationError("Only claimed items can fail.")
            if retry:
                scheduled = next_retry_at(
                    attempts=item.attempts,
                    max_attempts=item.max_attempts,
                    base_delay_seconds=self._settings.queue_retry_base_delay_seconds,
                    max_delay_seconds=self._settings.queue_retry_max_delay_seconds,
                    jitter=self._settings.queue_retry_jitter,
                )
                if scheduled is not None:
                    item.state = QueueState.QUEUED.value
                    item.run_at = scheduled
                    item.error = error
                    return item
            item.state = QueueState.FAILED.value
            item.completed_at = _utcnow()
            item.error = error
            return item

    async def list_queue(
        self,
        niche_id: str | None,
        *,
        queue: str | None = None,
        state: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[QueueItem]:
        async with self._uow_factory().transaction() as unit:
            return await unit.queue.list_scoped(
                niche_id, queue=queue, state=state, limit=limit, offset=offset
            )

    async def list_queue_aggregate(
        self,
        niche_id: str | None,
        *,
        queue: str | None = None,
        state: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Queue ledger rows with the niche slug attached (admin dashboard)."""
        async with self._uow_factory().transaction() as unit:
            items = await unit.queue.list_scoped(
                niche_id, queue=queue, state=state, limit=limit, offset=offset
            )
            slugs = await self._niche_slug_map(unit, items)
            rows: list[dict[str, Any]] = []
            for item in items:
                row = {
                    "id": item.id,
                    "niche_id": item.niche_id,
                    "niche_slug": slugs.get(item.niche_id),
                    "queue": item.queue,
                    "payload_ref": item.payload_ref,
                    "state": item.state,
                    "attempts": item.attempts,
                    "max_attempts": item.max_attempts,
                    "run_at": item.run_at.isoformat(),
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                    "error": item.error,
                }
                rows.append(row)
            return rows

    async def list_job_runs_detailed(
        self,
        niche_id: str | None,
        *,
        job_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Job runs with the job key + niche slug attached (admin dashboard)."""
        async with self._uow_factory().transaction() as unit:
            runs = await unit.job_runs.list_scoped(
                niche_id, job_id=job_id, status=status, limit=limit, offset=offset
            )
            job_keys: dict[str, str] = {}
            for run in runs:
                if run.scheduled_job_id not in job_keys:
                    job = await unit.scheduled_jobs.get(run.scheduled_job_id)
                    job_keys[run.scheduled_job_id] = job.job_key if job else ""
            slugs = await self._niche_slug_map(unit, runs)
            rows: list[dict[str, Any]] = []
            for run in runs:
                rows.append(
                    {
                        "id": run.id,
                        "niche_id": run.niche_id,
                        "niche_slug": slugs.get(run.niche_id),
                        "scheduled_job_id": run.scheduled_job_id,
                        "job_key": job_keys.get(run.scheduled_job_id, ""),
                        "run_at": run.run_at.isoformat(),
                        "status": run.status,
                        "attempts": run.attempts,
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                        "output_ref": run.output_ref,
                        "error": run.error,
                    }
                )
            return rows

    async def retry_job_run(self, run_id: str, niche_id: str | None) -> tuple[JobRun, QueueItem]:
        """Retry a terminal job run: create a fresh execution for its job.

        The old run stays terminal (audit history is immutable); the new
        run carries the job's current config. A pending/running run cannot
        be retried (cancel it first).
        """
        async with self._uow_factory().transaction() as unit:
            run = await self._scoped_get(unit.job_runs, run_id, niche_id)
            if run is None:
                raise NotFoundError("Job run not found.")
            if run.status not in (JobRunStatus.FAILED.value, JobRunStatus.CANCELLED.value):
                raise ValidationError("Only failed/cancelled job runs can be retried.")
        return await self.enqueue_job(run.scheduled_job_id, niche_id)

    async def cancel_queue_item(self, item_id: str, niche_id: str | None) -> QueueItem:
        """Cancel a queued/claimed queue item by operator action.

        The item is marked terminal ``failed`` with the operator-cancelled
        error (no new states are introduced to the frozen ledger). A linked
        pending/running job run is cancelled in the same transaction.
        """
        async with self._uow_factory().transaction() as unit:
            item = await unit.queue.get_scoped(item_id, niche_id)
            if item is None:
                raise NotFoundError("Queue item not found.")
            if item.state not in (QueueState.QUEUED.value, QueueState.CLAIMED.value):
                raise ValidationError("Only queued/claimed items can be cancelled.")
            item.state = QueueState.FAILED.value
            item.completed_at = _utcnow()
            item.error = "cancelled by operator"
            if item.payload_ref.startswith("job_run:"):
                run_id = item.payload_ref.split(":", 1)[1]
                run = await unit.job_runs.get(run_id)
                if run is not None and run.status in (
                    JobRunStatus.PENDING.value,
                    JobRunStatus.RUNNING.value,
                ):
                    run.status = JobRunStatus.CANCELLED.value
                    run.finished_at = _utcnow()
            return item

    async def retry_queue_item(self, item_id: str, niche_id: str | None) -> QueueItem:
        """Requeue a terminal (failed) queue item for a new attempt.

        Attempts are kept for audit transparency; the item is re-queued
        immediately (``run_at = now``) and the next claim/execution decides
        the outcome. Pending work cannot be retried (cancel first).
        """
        async with self._uow_factory().transaction() as unit:
            item = await unit.queue.get_scoped(item_id, niche_id)
            if item is None:
                raise NotFoundError("Queue item not found.")
            if item.state != QueueState.FAILED.value:
                raise ValidationError("Only failed queue items can be retried.")
            item.state = QueueState.QUEUED.value
            item.run_at = _utcnow()
            item.completed_at = None
            item.error = None
            return item

    async def _niche_slug_map(self, unit, rows) -> dict[str | None, str | None]:
        """Resolve niche slugs for a row set (one lookup per niche)."""
        slugs: dict[str | None, str | None] = {}
        seen: set[str] = set()
        for row in rows:
            niche_id = getattr(row, "niche_id", None)
            if niche_id and niche_id not in seen:
                niche = await unit.niches.get(niche_id)
                slugs[niche_id] = niche.slug if niche else None
                seen.add(niche_id)
        return slugs

    # -------------------------------------------------------- AI OS jobs
    async def create_aios_job(
        self,
        *,
        niche_id: str,
        job_id: str,
        contract: str,
        direction: str = AiosDirection.OUTBOUND.value,
        payload_ref: str | None = None,
    ) -> tuple[AiosJobRecord, bool]:
        """Create a Bridge correlation record; ``(row, created)`` dedupe.

        ``UNIQUE (job_id, contract)`` plus the service check make replay
        deliveries idempotent. Only correlation metadata is stored.
        """
        if not niche_id:
            raise ValidationError("niche_id is required for AI OS Bridge records.")
        await self._require_niche(niche_id)
        try:
            direction_enum = AiosDirection(direction)
        except ValueError as exc:
            raise ValidationError(f"Unsupported direction: {direction!r}.") from exc
        if not job_id.strip() or len(job_id) > 128:
            raise ValidationError("job_id is required (max 128 chars).")
        if not contract.strip() or len(contract) > 100:
            raise ValidationError("contract is required (max 100 chars).")
        async with self._uow_factory().transaction() as unit:
            existing = await unit.aios_jobs.get_by_job_contract(job_id, contract)
            if existing is not None:
                return existing, False
            row = AiosJobRecord(
                id=uuid7(),
                niche_id=niche_id,
                job_id=job_id,
                contract=contract,
                direction=direction_enum.value,
                payload_ref=payload_ref,
                status=AiosJobStatus.PENDING.value,
                attempts=0,
            )
            await unit.aios_jobs.add(row)
            await self.publish(
                aios_job_created_event(
                    niche_id=niche_id,
                    job_id=job_id,
                    contract=contract,
                    direction=direction_enum.value,
                )
            )
            return row, True

    async def set_aios_job_status(
        self,
        *,
        niche_id: str,
        job_id: str,
        contract: str,
        status: str,
        error: str | None = None,
    ) -> AiosJobRecord:
        """Advance the Bridge job status with lifecycle validation.

        ``pending → in_progress → succeeded/failed/cancelled``; failures may
        increment ``attempts`` for observability. Never stores AI internals.
        """
        try:
            desired = AiosJobStatus(status)
        except ValueError as exc:
            raise ValidationError(f"Unsupported aios job status: {status!r}.") from exc
        async with self._uow_factory().transaction() as unit:
            row = await unit.aios_jobs.get_by_job_contract(job_id, contract)
            if row is None:
                raise NotFoundError("AI OS job record not found.")
            if row.niche_id != niche_id:
                raise NotFoundError("AI OS job record not found.")
            current = AiosJobStatus(row.status)
            if current == desired:
                return row
            if current == AiosJobStatus.PENDING and desired == AiosJobStatus.IN_PROGRESS:
                row.status = desired.value
                return row
            if current == AiosJobStatus.IN_PROGRESS and desired in (
                AiosJobStatus.SUCCEEDED,
                AiosJobStatus.FAILED,
                AiosJobStatus.CANCELLED,
            ):
                row.status = desired.value
                row.completed_at = _utcnow()
                row.error = error
                if desired == AiosJobStatus.FAILED:
                    row.attempts += 1
                return row
            raise ValidationError(
                f"Invalid AI OS job transition: {current.value} → {desired.value}."
            )

    async def list_aios_jobs(
        self,
        niche_id: str,
        *,
        status: str | None = None,
        contract: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AiosJobRecord]:
        async with self._uow_factory().transaction() as unit:
            return await unit.aios_jobs.list_scoped(
                niche_id, status=status, contract=contract, limit=limit, offset=offset
            )

    # ------------------------------------------------------- tenancy
    async def _scoped_get(self, repository, entity_id: str, niche_id: str | None):
        """Fetch a record and enforce scope: global records need no header,
        niche records need the exact matching header (never leaks across
        niches — a mismatch returns None)."""
        row = await repository.get(entity_id)
        if row is None:
            return None
        row_niche: str | None = getattr(row, "niche_id", None)
        if row_niche != niche_id:
            return None
        return row
