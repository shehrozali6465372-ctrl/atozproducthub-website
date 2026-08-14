"""Celery Beat tick: enqueue due scheduled jobs (M10 Step 2).

Celery docs recommend a single scheduler owner to avoid duplicate periodic
triggers. The tick therefore acquires a Redis lock (``SET NX EX``) before
scanning the durable ``scheduled_jobs`` table for enabled jobs whose
``next_run_at`` has passed, enqueues one execution each, and advances
``next_run_at`` via croniter (the schedule is DB-driven; Beat simply wakes
the tick).

Lock acquisition is best-effort: if Redis is unavailable the tick returns
``unavailable`` and the next beat cycle retries naturally — a missed tick
never enqueues duplicate work because ``UNIQUE (niche_id, job_key)`` and
the queue-ledger dedupe protect the database.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from croniter import croniter

from atoz_automation_service.config import Settings
from atoz_automation_service.services import AutomationService

logger = logging.getLogger("atoz.automation.beat")

LOCK_KEY = "atoz:automation:beat:lock"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class BeatLock:
    """Redis single-scheduler lock (SET NX EX); no-op when Redis is absent."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._redis: Any = None

    async def acquire(self) -> bool:
        if not self._settings.celery_broker_url.startswith("redis"):
            return True  # dev/CI without broker: allow the local tick
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(self._settings.celery_broker_url)
            acquired = await self._redis.set(
                LOCK_KEY,
                "1",
                nx=True,
                ex=self._settings.beat_lock_ttl_seconds,
            )
            return bool(acquired)
        except Exception as exc:  # noqa: BLE001 — best-effort lock
            logger.warning("beat lock unavailable: %s", exc)
            self._redis = None
            return False

    async def release(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.delete(LOCK_KEY)
            except Exception:  # noqa: BLE001
                pass
            finally:
                try:
                    await self._redis.aclose()
                except Exception:  # noqa: BLE001
                    pass
                self._redis = None


def next_cron_run(cron_expr: str, *, base: datetime | None = None) -> datetime | None:
    """Compute the next occurrence of a cron expression (UTC)."""
    try:
        iterator = croniter(cron_expr, base or _utcnow())
        return iterator.get_next(datetime)
    except (ValueError, KeyError):
        return None


async def run_beat_tick(
    service: AutomationService,
    settings: Settings,
    *,
    lock: BeatLock | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Enqueue every due scheduled job; returns a tick summary."""
    lock = lock or BeatLock(settings)
    if not await lock.acquire():
        return {"status": "locked", "enqueued": 0}
    try:
        current = now or _utcnow()
        due_jobs = await service.list_due_scheduled_jobs(current)
        enqueued: list[dict[str, str]] = []
        for job in due_jobs:
            run_row, _item = await service.enqueue_job(job.id, job.niche_id)
            next_run = next_cron_run(job.cron_expr, base=current)
            if next_run is not None:
                await service.update_scheduled_job_next_run(
                    job.id, job.niche_id, next_run_at=next_run
                )
            enqueued.append(
                {
                    "job_id": job.id,
                    "job_key": job.job_key,
                    "run_id": run_row.id,
                }
            )
        return {"status": "ok", "enqueued": len(enqueued), "jobs": enqueued}
    finally:
        await lock.release()
