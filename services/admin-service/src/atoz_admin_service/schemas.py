"""Pydantic schemas for the admin-service (RBAC, audit, ops, notifications)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------- niches/users
class NicheMirrorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=200, pattern=r"^[a-z0-9-]+$")
    status: str = Field(default="active", pattern="^(active|draft|archived)$")


class RoleAssignIn(BaseModel):
    role_code: str = Field(min_length=2, max_length=100)
    niche_id: str | None = Field(default=None, max_length=36)


class AdminUserCreate(BaseModel):
    subject: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=5, max_length=320)
    display_name: str = Field(min_length=2, max_length=200)
    status: str = Field(default="active", pattern="^(active|disabled)$")
    roles: list[RoleAssignIn] = Field(default_factory=list)


class AdminUserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=200)
    status: str | None = Field(default=None, pattern="^(active|disabled)$")
    mfa_enabled: bool | None = None


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    niche_id: str | None = Field(default=None, max_length=36)
    scopes: list[str] = Field(default_factory=list, max_length=20)


class MfaEnrollIn(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")


class SessionRevokeIn(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)


# --------------------------------------------------------------- audit/ops
class AuditLogIn(BaseModel):
    action: str = Field(min_length=2, max_length=60)
    entity_type: str = Field(min_length=2, max_length=60)
    entity_id: str = Field(default="", max_length=36)
    niche_id: str | None = Field(default=None, max_length=36)
    before_json: str | None = None
    after_json: str | None = None
    ip_hash: str | None = Field(default=None, max_length=128)
    request_id: str | None = Field(default=None, max_length=100)


class OperationLogIn(BaseModel):
    operation: str = Field(min_length=2, max_length=80)
    entity_type: str = Field(default="", max_length=60)
    entity_id: str = Field(default="", max_length=36)
    niche_id: str | None = Field(default=None, max_length=36)
    status: str = Field(default="succeeded", pattern="^(started|succeeded|failed)$")
    message: str = Field(default="", max_length=500)
    details: dict[str, Any] = Field(default_factory=dict)


class QueueEnqueueIn(BaseModel):
    niche_id: str | None = Field(default=None, max_length=36)
    queue: str = Field(min_length=2, max_length=80)
    payload_ref: str = Field(default="", max_length=500)
    run_at: datetime | None = None
    max_attempts: int = Field(default=5, ge=1, le=20)


class WebhookEventIn(BaseModel):
    type: str = Field(min_length=3, max_length=80)
    event_id: str = Field(min_length=8, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)
    aggregate_id: str | None = None


class NotificationCreate(BaseModel):
    niche_id: str | None = Field(default=None, max_length=36)
    recipient_id: str = Field(min_length=1, max_length=36)
    type: str = Field(min_length=3, max_length=60)
    title: str = Field(min_length=2, max_length=300)
    body: str = Field(default="", max_length=2000)
    action_ref: str | None = Field(default=None, max_length=300)


class NotificationPreferenceUpdate(BaseModel):
    channels: list[str] = Field(default_factory=list, max_length=10)
    quiet_hours: dict[str, Any] = Field(default_factory=dict)


class PreferenceUpdate(BaseModel):
    preferences: dict[str, Any] = Field(default_factory=dict, max_length=200)


# ------------------------------------------------------------ response DTOs
class AuditLogOut(BaseModel):
    id: str
    niche_id: str | None
    admin_user_id: str | None
    api_key_id: str | None
    action: str
    entity_type: str
    entity_id: str
    before_json: str | None
    after_json: str | None
    ip_hash: str | None
    request_id: str | None
    occurred_at: datetime


class UserRoleOut(BaseModel):
    role_code: str
    role_name: str
    niche_id: str | None
    assigned_at: datetime
    revoked_at: datetime | None


class AdminUserOut(BaseModel):
    id: str
    subject: str
    email: str
    display_name: str
    status: str
    mfa_enabled: bool
    last_login_at: datetime | None
    created_at: datetime
    roles: list[UserRoleOut] = Field(default_factory=list)


class PermissionOut(BaseModel):
    id: str
    code: str
    name: str
    scope: str
    description: str


class RoleOut(BaseModel):
    id: str
    code: str
    name: str
    description: str
    is_system: bool
    permissions: list[str] = Field(default_factory=list)


class ApiKeyOut(BaseModel):
    id: str
    admin_user_id: str
    niche_id: str | None
    name: str
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime


class ApiKeyCreatedOut(ApiKeyOut):
    raw_key: str  # returned exactly once at creation


class QueueItemOut(BaseModel):
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


class WebhookLogOut(BaseModel):
    id: str
    niche_id: str | None
    source: str
    event_id: str
    status: str
    payload_ref: str | None
    received_at: datetime
    processed_at: datetime | None
    error: str | None


class OperationLogOut(BaseModel):
    id: str
    niche_id: str | None
    operation: str
    entity_type: str
    entity_id: str
    status: str
    message: str
    details_json: str
    occurred_at: datetime


class NotificationOut(BaseModel):
    id: str
    niche_id: str | None
    recipient_id: str
    type: str
    title: str
    body: str
    status: str
    action_ref: str | None
    created_at: datetime
    read_at: datetime | None


class ScheduledJobOut(BaseModel):
    id: str
    niche_id: str | None
    job_key: str
    cron_expr: str
    queue: str
    handler: str
    config_json: str
    status: str
    last_run_at: datetime | None
    next_run_at: datetime | None


class JobRunOut(BaseModel):
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


class ServiceStatusOut(BaseModel):
    name: str
    status: str  # ok | degraded | down | unknown
    version: str | None = None
    latency_ms: int | None = None
    error: str | None = None


class SystemStatusOut(BaseModel):
    overall: str
    services: list[ServiceStatusOut]


class IsolationCheckOut(BaseModel):
    ok: bool
    checks: list[dict[str, Any]]


class OpsOverviewOut(BaseModel):
    failed_queue_items: int
    failed_webhooks: int
    failed_operations: int
    failed_job_runs: int
    open_notifications: int
    audit_entries: int
    queues: dict[str, int]
