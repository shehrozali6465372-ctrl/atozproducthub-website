"""Automation enums: rule/run/job/queue/AI OS bridge states (Task 20 / M10).

Frozen values follow Database Blueprint §5.21–§5.23 and §5.29, and the
Platform table shapes owned by admin-service (ADR-0009). The M10 job state
machine ``scheduled → queued → running → succeeded/failed/cancelled`` maps
to the Platform tables as: definition ``enabled`` (scheduled_jobs),
execution created as ``pending`` (job_runs = queued), then ``running`` →
``success/failed/cancelled``. Business layer only — no AI concepts exist.
"""

from enum import StrEnum


class RuleStatus(StrEnum):
    """Automation rule definition state (Blueprint §5.21)."""

    DISABLED = "disabled"
    ENABLED = "enabled"


class RuleTriggerType(StrEnum):
    """How an automation rule starts (Blueprint §5.21)."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    WEBHOOK = "webhook"


class RunStatus(StrEnum):
    """Automation run execution state (Blueprint §5.21)."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ScheduledJobStatus(StrEnum):
    """Scheduled job definition state (Platform table, §5.22)."""

    ENABLED = "enabled"
    DISABLED = "disabled"


class JobRunStatus(StrEnum):
    """Job execution state (Platform table, §5.22).

    ``PENDING`` is the durable "queued" state (admin-service ADR-0009 froze
    this value); the M10 machine documents it as ``queued``.
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueState(StrEnum):
    """Durable queue ledger state (Platform table, §5.23)."""

    QUEUED = "queued"
    CLAIMED = "claimed"
    DONE = "done"
    FAILED = "failed"


class AiosJobStatus(StrEnum):
    """AI OS Bridge correlation record state (Blueprint §5.29)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AiosDirection(StrEnum):
    """Which side initiated the Bridge job (Blueprint §5.29)."""

    OUTBOUND = "outbound"  # website requests AI OS work
    INBOUND = "inbound"  # AI OS delivers assets/status to the website
