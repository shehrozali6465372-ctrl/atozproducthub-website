"""Repository layer for the automation module.

Every repository extends ``atoz_backend_core.repositories`` and enforces
Database Blueprint §4 tenancy server-side: all queries are niche-scoped so
one niche can never read or mutate another niche's automation state
(nullable ``niche_id`` = global records, visible only in global scope).

- ``automation_runs`` is append-only: no update/delete surface (the service
  transitions rows in-place, history is never removed).
- ``aios_job_records`` is deduped on ``UNIQUE (job_id, contract)``.
- Platform tables (scheduled_jobs, job_runs, queue_items) are mapped with
  explicit state-transition helpers; records are never deleted here.
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select

from atoz_automation_service.domain.entities import (
    AiosJobRecord,
    AutomationNiche,
    AutomationRule,
    AutomationRun,
    JobRun,
    QueueItem,
    ScheduledJob,
)
from atoz_automation_service.errors import ValidationError
from atoz_backend_core.repositories import SqlAlchemyRepository, SqlAlchemyUnitOfWork


class AutomationNicheRepository(SqlAlchemyRepository[AutomationNiche, str]):
    """Niches are a tenant-registry mirror — not niche-scoped themselves."""

    model = AutomationNiche

    async def get_by_slug(self, slug: str) -> AutomationNiche | None:
        result = await self._session.scalars(
            select(AutomationNiche).where(AutomationNiche.slug == slug)
        )
        return result.first()

    async def slug_exists(self, slug: str, *, exclude_id: str | None = None) -> bool:
        stmt = select(AutomationNiche.id).where(AutomationNiche.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(AutomationNiche.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None


class AutomationRuleRepository(SqlAlchemyRepository[AutomationRule, str]):
    """Rule definitions; ``(niche_id, code)`` is the natural key."""

    model = AutomationRule

    async def get_by_code(self, niche_id: str | None, code: str) -> AutomationRule | None:
        stmt = select(AutomationRule).where(AutomationRule.code == code)
        if niche_id is None:
            stmt = stmt.where(AutomationRule.niche_id.is_(None))
        else:
            stmt = stmt.where(AutomationRule.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def list_scoped(
        self, niche_id: str | None, *, limit: int = 100, offset: int = 0
    ) -> Sequence[AutomationRule]:
        stmt = select(AutomationRule).order_by(AutomationRule.code)
        if niche_id is None:
            stmt = stmt.where(AutomationRule.niche_id.is_(None))
        else:
            stmt = stmt.where(AutomationRule.niche_id == niche_id)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_scoped(self, niche_id: str | None) -> int:
        stmt = select(func.count(AutomationRule.id))
        if niche_id is None:
            stmt = stmt.where(AutomationRule.niche_id.is_(None))
        else:
            stmt = stmt.where(AutomationRule.niche_id == niche_id)
        return int((await self._session.execute(stmt)).scalar_one())


class AutomationRunRepository(SqlAlchemyRepository[AutomationRun, str]):
    """Append-only execution history (Blueprint §5.21).

    ``update`` and ``delete`` are intentionally unsupported: runs are
    immutable business records; the service only transitions status fields.
    """

    model = AutomationRun

    async def get_by_idempotency_key(self, key: str) -> AutomationRun | None:
        stmt = select(AutomationRun).where(AutomationRun.idempotency_key == key)
        return (await self._session.scalars(stmt)).first()

    async def list_scoped(
        self,
        niche_id: str | None,
        *,
        rule_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AutomationRun]:
        stmt = (
            select(AutomationRun)
            .where(
                AutomationRun.niche_id.is_(None)
                if niche_id is None
                else AutomationRun.niche_id == niche_id
            )
            .order_by(AutomationRun.started_at.desc())
        )
        if rule_id is not None:
            stmt = stmt.where(AutomationRun.automation_rule_id == rule_id)
        if status is not None:
            stmt = stmt.where(AutomationRun.status == status)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_by_status(self, niche_id: str | None, status: str) -> int:
        stmt = select(func.count(AutomationRun.id)).where(AutomationRun.status == status)
        if niche_id is None:
            stmt = stmt.where(AutomationRun.niche_id.is_(None))
        else:
            stmt = stmt.where(AutomationRun.niche_id == niche_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def update(self, entity: AutomationRun) -> AutomationRun:
        raise ValidationError("Automation runs are append-only history; rows cannot be replaced.")

    async def delete(self, entity_id: str) -> bool:
        raise ValidationError("Automation runs are append-only history; rows cannot be deleted.")


class ScheduledJobRepository(SqlAlchemyRepository[ScheduledJob, str]):
    """Platform ``scheduled_jobs`` (admin-owned table, §5.22)."""

    model = ScheduledJob

    async def get_by_key(self, niche_id: str | None, job_key: str) -> ScheduledJob | None:
        stmt = select(ScheduledJob).where(ScheduledJob.job_key == job_key)
        if niche_id is None:
            stmt = stmt.where(ScheduledJob.niche_id.is_(None))
        else:
            stmt = stmt.where(ScheduledJob.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def list_scoped(
        self, niche_id: str | None, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ScheduledJob]:
        stmt = select(ScheduledJob).order_by(ScheduledJob.job_key)
        if niche_id is None:
            stmt = stmt.where(ScheduledJob.niche_id.is_(None))
        else:
            stmt = stmt.where(ScheduledJob.niche_id == niche_id)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def list_due(self, now: datetime, *, limit: int = 200) -> Sequence[ScheduledJob]:
        """Enabled jobs whose ``next_run_at`` has passed (single-scheduler tick).

        Only jobs with an explicit schedule are due; jobs with a NULL
        ``next_run_at`` never fire automatically (they require a manual
        enqueue) so a misconfigured row can never create a runaway loop.

        This is the **internal scheduler** path (not an API path): it scans
        every scope so the single-scheduler Beat can enqueue due work for
        all niches. Tenancy is preserved downstream — each enqueue resolves
        the job through its own ``niche_id`` and every queue item carries
        its niche scope for sibling calls.
        """
        stmt = (
            select(ScheduledJob)
            .where(
                ScheduledJob.status == "enabled",
                ScheduledJob.next_run_at.is_not(None),
                ScheduledJob.next_run_at <= now,
            )
            .order_by(ScheduledJob.next_run_at)
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def count_scoped(self, niche_id: str | None) -> int:
        stmt = select(func.count(ScheduledJob.id))
        if niche_id is None:
            stmt = stmt.where(ScheduledJob.niche_id.is_(None))
        else:
            stmt = stmt.where(ScheduledJob.niche_id == niche_id)
        return int((await self._session.execute(stmt)).scalar_one())


class JobRunRepository(SqlAlchemyRepository[JobRun, str]):
    """Platform ``job_runs`` (admin-owned table, §5.22)."""

    model = JobRun

    async def list_scoped(
        self,
        niche_id: str | None,
        *,
        job_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[JobRun]:
        stmt = (
            select(JobRun)
            .where(JobRun.niche_id.is_(None) if niche_id is None else JobRun.niche_id == niche_id)
            .order_by(JobRun.run_at.desc())
        )
        if job_id is not None:
            stmt = stmt.where(JobRun.scheduled_job_id == job_id)
        if status is not None:
            stmt = stmt.where(JobRun.status == status)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_by_status(self, niche_id: str | None, status: str) -> int:
        stmt = select(func.count(JobRun.id)).where(JobRun.status == status)
        if niche_id is None:
            stmt = stmt.where(JobRun.niche_id.is_(None))
        else:
            stmt = stmt.where(JobRun.niche_id == niche_id)
        return int((await self._session.execute(stmt)).scalar_one())


class QueueItemRepository(SqlAlchemyRepository[QueueItem, str]):
    """Platform ``queue_items`` (admin-owned table, §5.23).

    Idempotent enqueue: an open (queued/claimed) item with the same
    ``(niche_id, queue, payload_ref)`` is reused instead of duplicated.
    """

    model = QueueItem

    async def get_open_by_payload(
        self, niche_id: str | None, queue: str, payload_ref: str
    ) -> QueueItem | None:
        stmt = (
            select(QueueItem)
            .where(
                QueueItem.queue == queue,
                QueueItem.payload_ref == payload_ref,
                QueueItem.state.in_(("queued", "claimed")),
            )
            .order_by(QueueItem.run_at)
        )
        if niche_id is None:
            stmt = stmt.where(QueueItem.niche_id.is_(None))
        else:
            stmt = stmt.where(QueueItem.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def get_scoped(self, item_id: str, niche_id: str | None) -> QueueItem | None:
        stmt = select(QueueItem).where(QueueItem.id == item_id)
        if niche_id is None:
            stmt = stmt.where(QueueItem.niche_id.is_(None))
        else:
            stmt = stmt.where(QueueItem.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def list_scoped(
        self,
        niche_id: str | None,
        *,
        queue: str | None = None,
        state: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[QueueItem]:
        stmt = (
            select(QueueItem)
            .where(
                QueueItem.niche_id.is_(None) if niche_id is None else QueueItem.niche_id == niche_id
            )
            .order_by(QueueItem.run_at)
        )
        if queue is not None:
            stmt = stmt.where(QueueItem.queue == queue)
        if state is not None:
            stmt = stmt.where(QueueItem.state == state)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_scoped(self, niche_id: str | None, state: str | None = None) -> int:
        stmt = select(func.count(QueueItem.id))
        if niche_id is None:
            stmt = stmt.where(QueueItem.niche_id.is_(None))
        else:
            stmt = stmt.where(QueueItem.niche_id == niche_id)
        if state is not None:
            stmt = stmt.where(QueueItem.state == state)
        return int((await self._session.execute(stmt)).scalar_one())


class AiosJobRecordRepository(SqlAlchemyRepository[AiosJobRecord, str]):
    """Bridge correlation records; ``UNIQUE (job_id, contract)`` dedupe."""

    model = AiosJobRecord

    async def get_by_job_contract(self, job_id: str, contract: str) -> AiosJobRecord | None:
        stmt = select(AiosJobRecord).where(
            AiosJobRecord.job_id == job_id, AiosJobRecord.contract == contract
        )
        return (await self._session.scalars(stmt)).first()

    async def list_scoped(
        self,
        niche_id: str,
        *,
        status: str | None = None,
        contract: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AiosJobRecord]:
        stmt = (
            select(AiosJobRecord)
            .where(AiosJobRecord.niche_id == niche_id)
            .order_by(AiosJobRecord.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(AiosJobRecord.status == status)
        if contract is not None:
            stmt = stmt.where(AiosJobRecord.contract == contract)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_scoped(self, niche_id: str, status: str | None = None) -> int:
        stmt = select(func.count(AiosJobRecord.id)).where(AiosJobRecord.niche_id == niche_id)
        if status is not None:
            stmt = stmt.where(AiosJobRecord.status == status)
        return int((await self._session.execute(stmt)).scalar_one())


class AutomationUnitOfWork(SqlAlchemyUnitOfWork):
    """Transaction boundary exposing all automation repositories."""

    niches: AutomationNicheRepository
    rules: AutomationRuleRepository
    runs: AutomationRunRepository
    scheduled_jobs: ScheduledJobRepository
    job_runs: JobRunRepository
    queue: QueueItemRepository
    aios_jobs: AiosJobRecordRepository

    @classmethod
    def build(cls, session_factory) -> "AutomationUnitOfWork":
        return cls(
            session_factory,
            repositories={
                "niches": AutomationNicheRepository,
                "rules": AutomationRuleRepository,
                "runs": AutomationRunRepository,
                "scheduled_jobs": ScheduledJobRepository,
                "job_runs": JobRunRepository,
                "queue": QueueItemRepository,
                "aios_jobs": AiosJobRecordRepository,
            },
        )
