"""ORM entities for the automation module (automation_db).

Table shapes follow Database Blueprint §5.21–§5.23 and §5.29, and the
Platform table shapes owned by admin-service (ADR-0009). Ownership split
(ADR-0010):

- automation-service **creates** ``automation_niches`` (local tenancy
  mirror), ``automation_rules``, ``automation_runs`` (with an
  ``idempotency_key`` extension column for trigger dedupe), and
  ``aios_job_records`` (Bridge correlation metadata only).
- The Platform tables ``scheduled_jobs``, ``job_runs``, and ``queue_items``
  are **created by the admin-service migration stream** (ADR-0009); the
  automation service maps its ORM entities to those exact physical tables
  (identical names/columns) and never creates a competing migration.

Every scoped record carries ``niche_id`` (nullable for global rules/jobs,
Blueprint §4). ``aios_job_records`` stores correlation metadata only — no
prompts, no generated-content internals, no learning data (§5.29 boundary
statement).
"""

from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from atoz_backend_core.db.base import Base

UUID_LEN = 36


class PlatformBase(DeclarativeBase):
    """Declarative base for the Platform-table mappings (ADR-0010).

    admin-service already maps the same physical tables (scheduled_jobs /
    job_runs / queue_items) onto the shared backend-core ``Base`` in the
    admin package. Each service runs in its own process in production, so
    the mappings never clash there; the single-process test suite imports
    both packages, so the automation-side mappings use this separate
    metadata to coexist.
    """

    metadata = MetaData()


def _utcnow() -> datetime:
    """Python-side ``updated_at`` value (no post-flush expiry)."""
    return datetime.now(UTC)


class AutomationNiche(Base):
    """Local tenant-registry mirror (ADR-0010 mirror policy).

    ``niches`` is owned by content-service in ``content_db``; cross-database
    foreign keys are impossible, so automation_db keeps this minimal
    read-only-style mirror for local tenancy lookups.
    """

    __tablename__ = "automation_niches"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class AutomationRule(Base):
    """Configured business automation (Blueprint §5.21).

    Business rules only — never AI logic. ``niche_id`` is nullable for
    global rules; ``code`` is unique per niche (service-enforced when
    ``niche_id`` is NULL because NULLs are distinct in unique indexes).
    """

    __tablename__ = "automation_rules"
    __table_args__ = (
        UniqueConstraint("niche_id", "code", name="uq_automation_rules_niche_code"),
        Index("ix_automation_rules_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="disabled")
    run_as_user_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class AutomationRun(Base):
    """Execution history of automation rules (Blueprint §5.21), append-only.

    ``idempotency_key`` is an M10 extension (ADR-0010): a client-supplied
    key that makes ``trigger`` replay-safe — the first accepted key creates
    the run; every later replay returns the same run instead of duplicating
    history. Rows are never updated after ``finished_at`` is written and
    never deleted; the repository exposes no update/delete paths.
    """

    __tablename__ = "automation_runs"
    __table_args__ = (
        Index("ix_automation_runs_rule_started", "automation_rule_id", "started_at"),
        Index("ix_automation_runs_niche_status", "niche_id", "status"),
        Index("uq_automation_runs_idempotency", "idempotency_key", unique=True),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    automation_rule_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("automation_rules.id"), nullable=False
    )
    triggered_by: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ScheduledJob(PlatformBase):
    """Persistent scheduled job definition (Platform table, §5.22).

    Table is owned/created by admin-service (ADR-0009); automation-service
    integrates through the identical physical table. Mapped on
    ``platform_metadata`` so the single-process test suite can import both
    admin and automation packages (ADR-0010). ``niche_id`` is
    nullable for global jobs.
    """

    __tablename__ = "scheduled_jobs"
    __table_args__ = (
        UniqueConstraint("niche_id", "job_key", name="uq_scheduled_job_key"),
        Index("ix_scheduled_jobs_status_next", "status", "next_run_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    job_key: Mapped[str] = mapped_column(String(120), nullable=False)
    cron_expr: Mapped[str] = mapped_column(String(100), nullable=False)
    queue: Mapped[str] = mapped_column(String(80), nullable=False, default="default")
    handler: Mapped[str] = mapped_column(String(200), nullable=False)
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="enabled")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobRun(PlatformBase):
    """Execution record for a scheduled job (Platform table, §5.22).

    Owned/created by admin-service; automation-service writes execution
    records through this mapping. ``PENDING`` is the durable "queued" state.
    """

    __tablename__ = "job_runs"
    __table_args__ = (
        Index("ix_job_runs_job_time", "scheduled_job_id", "run_at"),
        Index("ix_job_runs_status_time", "status", "run_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    scheduled_job_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("scheduled_jobs.id"), nullable=False
    )
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    output_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class QueueItem(PlatformBase):
    """Durable queue ledger (Platform table, §5.23).

    Owned/created by admin-service; automation-service enqueues and
    transitions ledger rows through this mapping. Redis holds only the live
    working set; this table is the rebuildable source of truth.
    """

    __tablename__ = "queue_items"
    __table_args__ = (
        Index("ix_queue_queue_state_run", "queue", "state", "run_at"),
        Index("ix_queue_niche_state", "niche_id", "state"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    queue: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_ref: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class AiosJobRecord(Base):
    """AI OS Bridge correlation metadata (Blueprint §5.29).

    Stores only: job_id (AI OS correlation), contract, direction,
    payload_ref, status, attempts, timestamps, error. It stores **no
    prompts, no generated-content internals, no model outputs, no learning
    data** — the AI OS keeps its own data in its own systems. ``UNIQUE
    (job_id, contract)`` makes webhook/replay delivery idempotent.
    """

    __tablename__ = "aios_job_records"
    __table_args__ = (
        UniqueConstraint("job_id", "contract", name="uq_aios_job_record_job_contract"),
        Index("ix_aios_job_records_niche_status_created", "niche_id", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    job_id: Mapped[str] = mapped_column(String(128), nullable=False)
    contract: Mapped[str] = mapped_column(String(100), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    payload_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
