"""ORM entities for the admin module (admin_db).

Table shapes follow Database Blueprint §5.17–§5.26: identity & access rows
(admin_users, roles, permissions, role_permissions, user_roles, api_keys),
admin & governance rows (admin_preferences, audit_logs — append-only,
notifications*), and platform rows used by the operations control plane
(queue_items, webhook_logs, operation_logs, scheduled_jobs, job_runs).
Global reference tables (roles, permissions) carry no ``niche_id``;
every scoped business record does (Blueprint §4). The audit ledger is
append-only and immutable. No AI data lives here.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from atoz_backend_core.db.base import Base

UUID_LEN = 36


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AdminNiche(Base):
    """Local tenant-registry mirror (ADR-0009 mirror policy)."""

    __tablename__ = "admin_niches"

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


class AdminUser(Base):
    """Operator identity (Blueprint §5.17). Subject is the OIDC/JWT sub."""

    __tablename__ = "admin_users"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_secret_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class Role(Base):
    """Named role definition (Blueprint §5.18) — global reference."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Permission(Base):
    """Atomic permission (Blueprint §5.19) — global reference."""

    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="niche")
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")


class RolePermission(Base):
    """Grants permissions to roles (Blueprint §5.18)."""

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    role_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("permissions.id"), nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserRole(Base):
    """Assigns roles to admin users (Blueprint §5.18); niche-scoped roles."""

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("admin_user_id", "role_id", "niche_id", name="uq_user_role_niche"),
        Index("ix_user_roles_role", "role_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    admin_user_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("admin_users.id"), nullable=False
    )
    role_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("roles.id"), nullable=False)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ApiKey(Base):
    """Admin automation keys (Blueprint §5.20) — only the hash is stored."""

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    admin_user_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("admin_users.id"), nullable=False
    )
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    scopes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AdminPreference(Base):
    """Per-operator UI preferences (Blueprint §5.20)."""

    __tablename__ = "admin_preferences"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    admin_user_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("admin_users.id"), nullable=False, unique=True
    )
    preferences_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class AuditLog(Base):
    """Append-only audit ledger (Blueprint §5.25).

    Rows are created once and never updated or deleted; the repository layer
    exposes no mutation paths beyond append.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_entity_time", "entity_type", "entity_id", "occurred_at"),
        Index("ix_audit_user_time", "admin_user_id", "occurred_at"),
        Index("ix_audit_niche_time", "niche_id", "occurred_at"),
        Index("ix_audit_action_time", "action", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    admin_user_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("admin_users.id"), nullable=True
    )
    api_key_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("api_keys.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False, default="")
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Notification(Base):
    """Admin-facing notification (Blueprint §5.26)."""

    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_recipient_status", "recipient_id", "status"),)

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    recipient_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("admin_users.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unread")
    action_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationPreference(Base):
    """Per-user delivery preferences (Blueprint §5.26)."""

    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    admin_user_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("admin_users.id"), nullable=False, unique=True
    )
    channels_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    quiet_hours_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class NotificationDelivery(Base):
    """Delivery record per notification/channel (Blueprint §5.26)."""

    __tablename__ = "notification_deliveries"
    __table_args__ = (Index("ix_notification_deliveries_status", "status"),)

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    notification_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("notifications.id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    provider_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class QueueItem(Base):
    """Durable queue ledger (Blueprint §5.23).

    Redis holds only the live working set; this table is the rebuildable
    source of truth. State transitions are audited.
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


class WebhookLog(Base):
    """Signed webhook delivery records (Blueprint §5.24), replay-safe."""

    __tablename__ = "webhook_logs"
    __table_args__ = (
        UniqueConstraint("source", "event_id", name="uq_webhook_source_event"),
        Index("ix_webhook_logs_status_time", "status", "received_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="received")
    payload_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class OperationLog(Base):
    """Business-relevant operation records (Blueprint §5.24)."""

    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("ix_operation_logs_entity_time", "entity_type", "entity_id", "occurred_at"),
        Index("ix_operation_logs_niche_time", "niche_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    operation: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    entity_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="started")
    message: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ScheduledJob(Base):
    """Persistent scheduled job definition (Blueprint §5.22)."""

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


class JobRun(Base):
    """Execution record for a scheduled job (Blueprint §5.22)."""

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
