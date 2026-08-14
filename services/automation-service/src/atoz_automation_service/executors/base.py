"""Executor abstraction for the automation engine (Task 21 / M10 Step 2).

An executor performs ONE business workflow by calling an owning sibling
service over HTTP — automation-service never re-implements Pinterest, SEO,
affiliate, analytics, or AI OS logic (Website Contract §4). The durable
queue ledger drives execution: Celery tasks claim ``queue_items`` rows and
run the matching executor; the ledger is the retry source of truth.

The context carries the scoped identity (niche, job run, payload), the
sibling-service clients, and the settings; the result carries the outcome
for the workflow to persist and notify about.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from atoz_automation_service.config import Settings
from atoz_automation_service.executors.clients import SiblingClients


class ExecutorError(RuntimeError):
    """Raised by executors; the workflow converts it to a failed result."""


@dataclass(frozen=True)
class ExecutorContext:
    """Everything an executor needs for one execution."""

    executor_name: str
    queue_item_id: str
    job_run_id: str | None
    scheduled_job_id: str | None
    niche_id: str | None
    payload: dict[str, Any]
    settings: Settings
    siblings: SiblingClients


@dataclass
class ExecutorResult:
    """Outcome of one execution."""

    status: str = "failed"  # success | failed
    summary: str | None = None
    output_ref: str | None = None
    error: str | None = None
    retryable: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def success(
    *, summary: str | None = None, output_ref: str | None = None, **metadata: Any
) -> ExecutorResult:
    return ExecutorResult(
        status="success", summary=summary, output_ref=output_ref, metadata=metadata
    )


def failure(
    *, error: str, retryable: bool = True, summary: str | None = None, **metadata: Any
) -> ExecutorResult:
    return ExecutorResult(
        status="failed", error=error, retryable=retryable, summary=summary, metadata=metadata
    )


class Executor(ABC):
    """One registered business workflow."""

    #: Stable executor name used as the queue item's ``queue`` value and in
    #: Celery task routing (e.g. ``pinterest.publish_due``).
    name: str = ""
    #: Celery queue this executor's work routes to.
    queue: str = "default"

    @abstractmethod
    async def execute(self, ctx: ExecutorContext) -> ExecutorResult:
        """Run the workflow; must be idempotent-safe (late acks re-run)."""
