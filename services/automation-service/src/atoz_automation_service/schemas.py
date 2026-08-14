"""Pydantic schemas for the automation admin API (Task 20 / M10).

Tenancy is enforced server-side from the ``X-Niche-Id`` header — request
bodies never carry ``niche_id`` (no client spoofing surface). Response
schemas expose read-only business state; no AI fields exist.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=120)
    trigger_type: str = Field(pattern="^(manual|schedule|event|webhook)$")
    config: dict[str, Any] = Field(default_factory=dict)
    run_as_user_id: str | None = Field(default=None, max_length=36)


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str | None
    code: str
    trigger_type: str
    status: str
    run_as_user_id: str | None
    created_at: datetime
    updated_at: datetime


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str | None
    automation_rule_id: str
    triggered_by: str | None
    status: str
    started_at: datetime
    finished_at: datetime | None
    result_summary: str | None
    error: str | None


class ScheduledJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_key: str = Field(min_length=1, max_length=120)
    cron_expr: str = Field(min_length=1, max_length=100)
    queue: str = Field(default="default", max_length=80)
    handler: str = Field(min_length=1, max_length=200)
    config: dict[str, Any] = Field(default_factory=dict)
    next_run_at: datetime | None = None


class ScheduledJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str | None
    job_key: str
    cron_expr: str
    queue: str
    handler: str
    status: str
    last_run_at: datetime | None
    next_run_at: datetime | None


class JobRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str | None
    scheduled_job_id: str
    run_at: datetime
    status: str
    attempts: int
    started_at: datetime | None
    finished_at: datetime | None
    output_ref: str | None
    error: str | None


class QueueItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str | None
    queue: str
    payload_ref: str
    state: str
    attempts: int
    max_attempts: int
    run_at: datetime
    completed_at: datetime | None
    error: str | None


class QueueEnqueueIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    queue: str = Field(min_length=1, max_length=80)
    payload_ref: str = Field(min_length=1, max_length=500)
    run_at: datetime | None = None
    max_attempts: int | None = Field(default=None, ge=1, le=50)


class RunJobRequest(BaseModel):
    """Optional per-execution config for a manual scheduled-job run.

    The override is stored on the queue item and never merged into the
    scheduled job definition (frozen ``config_json`` stays intact).
    """

    model_config = ConfigDict(extra="forbid")

    config: dict[str, Any] = Field(default_factory=dict)


class JobRunDetailOut(BaseModel):
    """Job run with the owning job key + niche slug (admin dashboard)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    niche_id: str | None
    niche_slug: str | None
    scheduled_job_id: str
    job_key: str
    run_at: datetime
    status: str
    attempts: int
    started_at: datetime | None
    finished_at: datetime | None
    output_ref: str | None
    error: str | None


class QueueItemDetailOut(BaseModel):
    """Queue ledger row with the niche slug (admin dashboard)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    niche_id: str | None
    niche_slug: str | None
    queue: str
    payload_ref: str
    state: str
    attempts: int
    max_attempts: int
    run_at: datetime
    completed_at: datetime | None
    error: str | None


class ExecutorOut(BaseModel):
    """Registered executor descriptor (read-only, no business payload)."""

    name: str
    queue: str


class AiosJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1, max_length=128)
    contract: str = Field(min_length=1, max_length=100)
    direction: str = Field(default="outbound", pattern="^(outbound|inbound)$")
    payload_ref: str | None = Field(default=None, max_length=500)


class AiosJobStatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1, max_length=128)
    contract: str = Field(min_length=1, max_length=100)
    status: str = Field(pattern="^(pending|in_progress|succeeded|failed|cancelled)$")
    error: str | None = Field(default=None, max_length=500)


class AiosJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    job_id: str
    contract: str
    direction: str
    payload_ref: str | None
    status: str
    attempts: int
    created_at: datetime
    completed_at: datetime | None
    error: str | None


class NicheMirrorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    status: str = Field(default="draft", pattern="^(draft|active|disabled)$")


class NicheMirrorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    slug: str
    name: str
    status: str
