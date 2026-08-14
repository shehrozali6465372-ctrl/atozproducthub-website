"""Execution workflow: ledger-driven runner for the Celery worker (M10 Step 2).

One queue-item execution is a bounded state machine:

1. **Claim** — the durable ``queue_items`` ledger row transitions
   ``queued → claimed`` (attempts + 1). A re-delivered task (Celery late
   ack after a worker crash) finds the row already ``claimed`` and proceeds
   — executors are idempotent-safe, so re-execution is safe.
2. **Resolve** — the executor payload comes from the linked scheduled-job
   config (``job_run:{id}`` references) or from the payload reference
   itself (JSON object or plain business reference).
3. **Execute** — the registered executor calls the owning sibling service
   with the item's ``niche_id`` scope (server-side tenancy forwarding);
   bounded by ``executor_timeout_seconds`` (timeout/cancellation).
4. **Persist** — success completes the queue item + linked job run;
   failure re-queues with exponential backoff while attempts remain
   (retryable) or marks the item terminal ``failed``. AI OS correlation
   records are advanced in lockstep.
5. **Notify** — at most once per outcome (best-effort; never blocks).

The worker is trusted infrastructure: it resolves queue items by UUID
(global), but every sibling call carries the item's ``niche_id`` so
niche isolation is enforced end-to-end.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from atoz_automation_service.config import Settings
from atoz_automation_service.domain.entities import QueueItem
from atoz_automation_service.domain.events import (
    aios_job_failed_event,
    aios_job_succeeded_event,
    job_failed_event,
    job_retry_scheduled_event,
    job_started_event,
    job_succeeded_event,
)
from atoz_automation_service.domain.retry import next_retry_at
from atoz_automation_service.executors.base import ExecutorContext, ExecutorResult
from atoz_automation_service.executors.clients import SiblingClients, send_notification
from atoz_automation_service.executors.registry import ExecutorRegistry
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher

logger = logging.getLogger("atoz.automation.workflow")

TERMINAL_STATES = ("done", "failed")


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ExecutionWorkflow:
    """Orchestrates one queue-item execution."""

    def __init__(
        self,
        *,
        uow_factory,
        event_publisher: EventPublisher,
        settings: Settings,
        registry: ExecutorRegistry,
        siblings: SiblingClients,
    ) -> None:
        self._uow_factory = uow_factory
        self._event_publisher = event_publisher
        self._settings = settings
        self._registry = registry
        self._siblings = siblings

    async def publish(self, event: EventEnvelope) -> None:
        await self._event_publisher.publish(event)

    async def run(self, queue_item_id: str, executor_name: str | None = None) -> dict[str, Any]:
        """Execute one queue item; returns an outcome summary dict."""
        claimed = await self._claim(queue_item_id)
        if claimed is None:
            return claimed_outcome
        item, newly_claimed, niche_id = claimed

        payload, job_run_id, scheduled_job_id, handler = await self._resolve_payload(item)
        executor = self._registry.get(executor_name or item.queue)
        if executor is None and handler:
            executor = self._registry.get(handler)
        if executor is None:
            executor = self._registry.by_queue(item.queue)
        if executor is None:
            return await self._terminal_failure(
                item,
                payload,
                niche_id=niche_id,
                job_run_id=job_run_id,
                error=f"unknown executor: {executor_name or item.queue or handler}",
                retryable=False,
            )

        ctx = ExecutorContext(
            executor_name=executor.name,
            queue_item_id=item.id,
            job_run_id=job_run_id,
            scheduled_job_id=scheduled_job_id,
            niche_id=niche_id,
            payload=payload,
            settings=self._settings,
            siblings=self._siblings,
        )

        # AI OS correlation: mark in-progress before dispatch.
        if niche_id and payload.get("job_id") and payload.get("contract"):
            await self._set_aios_status(
                niche_id, payload["job_id"], payload["contract"], "in_progress"
            )
        if newly_claimed:
            await self._notify(
                "job.started",
                "Automation job started",
                f"Executor {executor.name} started for queue item {item.id}.",
                niche_id,
                item.id,
            )
            if job_run_id:
                await self._transition_job_run(job_run_id, "start")
                await self.publish(
                    job_started_event(
                        niche_id=niche_id,
                        run_id=job_run_id,
                        job_id=str(payload.get("scheduled_job_id") or scheduled_job_id or ""),
                    )
                )

        try:
            result = await asyncio.wait_for(
                executor.execute(ctx),
                timeout=self._settings.executor_timeout_seconds,
            )
        except TimeoutError:
            result = ExecutorResult(
                status="failed",
                error=(f"executor timed out after {self._settings.executor_timeout_seconds}s"),
                retryable=True,
            )
        except Exception as exc:  # noqa: BLE001 — worker never dies on one item
            logger.exception(
                "executor_unhandled",
                extra={"executor": executor.name, "queue_item_id": item.id},
            )
            result = ExecutorResult(status="failed", error=str(exc), retryable=True)

        if result.status == "success":
            return await self._complete(
                item, payload, niche_id=niche_id, job_run_id=job_run_id, result=result
            )
        return await self._handle_failure(
            item, payload, niche_id=niche_id, job_run_id=job_run_id, result=result
        )

    # ------------------------------------------------------------ steps
    async def _claim(self, queue_item_id: str) -> tuple[QueueItem, bool, str | None] | None:
        async with self._uow_factory().transaction() as unit:
            item = await unit.queue.get(queue_item_id)
            if item is None:
                return None
            if item.state in TERMINAL_STATES:
                return None
            if item.state == "queued":
                item.state = "claimed"
                item.attempts += 1
                return item, True, item.niche_id
            # claimed: late-ack redelivery — proceed idempotently.
            return item, False, item.niche_id

    async def _resolve_payload(
        self, item: QueueItem
    ) -> tuple[dict[str, Any], str | None, str | None, str | None]:
        """Resolve the executor payload (+ handler) from the queue item's reference."""
        job_run_id: str | None = None
        scheduled_job_id: str | None = None
        handler: str | None = None
        if item.payload_ref.startswith("job_run:"):
            run_id = item.payload_ref.split(":", 1)[1]
            async with self._uow_factory().transaction() as unit:
                run = await unit.job_runs.get(run_id)
                if run is not None:
                    job_run_id = run.id
                    scheduled_job_id = run.scheduled_job_id
                    job = await unit.scheduled_jobs.get(run.scheduled_job_id)
                    if job is not None:
                        handler = job.handler
                        try:
                            return (
                                json.loads(job.config_json or "{}"),
                                job_run_id,
                                scheduled_job_id,
                                handler,
                            )
                        except ValueError:
                            return (
                                {"config_json": job.config_json},
                                job_run_id,
                                scheduled_job_id,
                                handler,
                            )
            return {}, job_run_id, scheduled_job_id, handler
        try:
            parsed = json.loads(item.payload_ref)
            if isinstance(parsed, dict):
                # Override-config executions (enqueue_job_with_config) carry
                # {job_run_id, scheduled_job_id, config} on the queue item.
                if isinstance(parsed.get("config"), dict) and parsed.get("job_run_id"):
                    run_id = str(parsed["job_run_id"])
                    handler = None
                    async with self._uow_factory().transaction() as unit:
                        run = await unit.job_runs.get(run_id)
                        if run is not None:
                            job = await unit.scheduled_jobs.get(run.scheduled_job_id)
                            if job is not None:
                                handler = job.handler
                    return (
                        parsed["config"],
                        run_id,
                        str(parsed.get("scheduled_job_id") or ""),
                        handler,
                    )
                return parsed, None, None, None
        except ValueError:
            pass
        return {"payload_ref": item.payload_ref}, None, None, None

    async def _complete(
        self,
        item: QueueItem,
        payload: dict[str, Any],
        *,
        niche_id: str | None,
        job_run_id: str | None,
        result: ExecutorResult,
    ) -> dict[str, Any]:
        async with self._uow_factory().transaction() as unit:
            current = await unit.queue.get(item.id)
            if current is not None and current.state == "claimed":
                current.state = "done"
                current.completed_at = _utcnow()
                current.error = None
            if job_run_id:
                run = await unit.job_runs.get(job_run_id)
                if run is not None and run.status == "running":
                    run.status = "success"
                    run.finished_at = _utcnow()
                    run.output_ref = result.output_ref
        if job_run_id:
            await self.publish(
                job_succeeded_event(
                    niche_id=niche_id,
                    run_id=job_run_id,
                    job_id=str(payload.get("scheduled_job_id", "")),
                    output_ref=result.output_ref,
                )
            )
        if niche_id and payload.get("job_id") and payload.get("contract"):
            await self._set_aios_status(
                niche_id, payload["job_id"], payload["contract"], "succeeded"
            )
        await self._notify(
            "job.succeeded",
            "Automation job succeeded",
            result.summary or f"Queue item {item.id} completed.",
            niche_id,
            item.id,
        )
        return {
            "status": "success",
            "queue_item_id": item.id,
            "summary": result.summary,
        }

    async def _handle_failure(
        self,
        item: QueueItem,
        payload: dict[str, Any],
        *,
        niche_id: str | None,
        job_run_id: str | None,
        result: ExecutorResult,
    ) -> dict[str, Any]:
        next_run = next_retry_at(
            attempts=item.attempts,
            max_attempts=item.max_attempts,
            base_delay_seconds=self._settings.queue_retry_base_delay_seconds,
            max_delay_seconds=self._settings.queue_retry_max_delay_seconds,
            jitter=self._settings.queue_retry_jitter,
        )
        if result.retryable and next_run is not None:
            return await self._requeue_failure(
                item,
                payload,
                niche_id=niche_id,
                job_run_id=job_run_id,
                result=result,
                next_run=next_run,
            )
        return await self._terminal_failure(
            item,
            payload,
            niche_id=niche_id,
            job_run_id=job_run_id,
            error=result.error or "executor failed",
            retryable=False,
        )

    async def _requeue_failure(
        self,
        item: QueueItem,
        payload: dict[str, Any],
        *,
        niche_id: str | None,
        job_run_id: str | None,
        result: ExecutorResult,
        next_run: datetime,
    ) -> dict[str, Any]:
        async with self._uow_factory().transaction() as unit:
            current = await unit.queue.get(item.id)
            if current is not None and current.state == "claimed":
                current.state = "queued"
                current.run_at = next_run
                current.error = result.error
            if job_run_id:
                run = await unit.job_runs.get(job_run_id)
                if run is not None and run.status == "running":
                    run.status = "pending"
                    run.started_at = None
                    run.error = result.error
        if job_run_id:
            await self.publish(
                job_retry_scheduled_event(
                    niche_id=niche_id,
                    run_id=job_run_id,
                    job_id=str(payload.get("scheduled_job_id", "")),
                    next_run_at=next_run.isoformat(),
                    attempts=item.attempts,
                )
            )
        if niche_id and payload.get("job_id") and payload.get("contract"):
            # Correlation record stays in-progress while retries remain.
            pass
        await self._notify(
            "job.retry_scheduled",
            "Automation job retry scheduled",
            f"{result.error} — next attempt at {next_run.isoformat()}.",
            niche_id,
            item.id,
        )
        return {
            "status": "retry_scheduled",
            "queue_item_id": item.id,
            "next_run_at": next_run.isoformat(),
            "attempts": item.attempts,
            "error": result.error,
        }

    async def _terminal_failure(
        self,
        item: QueueItem,
        payload: dict[str, Any],
        *,
        niche_id: str | None,
        job_run_id: str | None,
        error: str,
        retryable: bool,
    ) -> dict[str, Any]:
        async with self._uow_factory().transaction() as unit:
            current = await unit.queue.get(item.id)
            if current is not None and current.state == "claimed":
                current.state = "failed"
                current.completed_at = _utcnow()
                current.error = error
            if job_run_id:
                run = await unit.job_runs.get(job_run_id)
                if run is not None and run.status == "running":
                    run.status = "failed"
                    run.finished_at = _utcnow()
                    run.error = error
        if job_run_id:
            await self.publish(
                job_failed_event(
                    niche_id=niche_id,
                    run_id=job_run_id,
                    job_id=str(payload.get("scheduled_job_id", "")),
                    error=error,
                )
            )
        if niche_id and payload.get("job_id") and payload.get("contract"):
            await self._set_aios_status(
                niche_id, payload["job_id"], payload["contract"], "failed", error=error
            )
        await self._notify(
            "job.failed",
            "Automation job failed",
            error,
            niche_id,
            item.id,
        )
        return {
            "status": "failed",
            "queue_item_id": item.id,
            "error": error,
            "retryable": retryable,
        }

    async def _transition_job_run(self, run_id: str, action: str) -> None:
        async with self._uow_factory().transaction() as unit:
            run = await unit.job_runs.get(run_id)
            if run is None:
                return
            if action == "start" and run.status == "pending":
                run.status = "running"
                run.started_at = _utcnow()
                run.attempts += 1

    async def _set_aios_status(
        self, niche_id: str, job_id: str, contract: str, status: str, error: str | None = None
    ) -> None:
        async with self._uow_factory().transaction() as unit:
            row = await unit.aios_jobs.get_by_job_contract(job_id, contract)
            if row is None:
                return
            if status == "in_progress" and row.status == "pending":
                row.status = "in_progress"
            elif status == "succeeded" and row.status == "in_progress":
                row.status = "succeeded"
                row.completed_at = _utcnow()
            elif status == "failed" and row.status == "in_progress":
                row.status = "failed"
                row.completed_at = _utcnow()
                row.error = error
                row.attempts += 1
        if status == "succeeded":
            await self.publish(
                aios_job_succeeded_event(niche_id=niche_id, job_id=job_id, contract=contract)
            )
        elif status == "failed":
            await self.publish(
                aios_job_failed_event(
                    niche_id=niche_id, job_id=job_id, contract=contract, error=error
                )
            )

    async def _notify(
        self, kind: str, title: str, body: str, niche_id: str | None, action_ref: str | None
    ) -> None:
        await send_notification(
            self._siblings,
            self._settings,
            kind=kind,
            title=title,
            body=body,
            niche_id=niche_id,
            action_ref=action_ref,
        )


claimed_outcome: dict[str, Any] = {"status": "noop", "reason": "terminal or missing"}
