"""admin_db tables: RBAC, operators, append-only audit, notifications, ops.

Revision ID: 0001
Revises:
Create Date: 2026-08-12

Portable schema (SQLite in tests, PostgreSQL in prod/CI). Primary keys are
UUID v7 strings assigned by the domain layer (ADR-0009). Global reference
tables (roles, permissions) carry no ``niche_id``; every scoped business
record does, per Database Blueprint §4. The audit ledger is append-only:
no update/delete triggers exist and the repository exposes no mutation
paths. No AI data lives here.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TS = sa.DateTime(timezone=True)
NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    # ------------------------------------- local tenancy mirror (ADR-0009)
    op.create_table(
        "admin_niches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("ix_admin_niches_slug", "admin_niches", ["slug"], unique=True)

    # ----------------------------------------------- operator identity (§5.17)
    op.create_table(
        "admin_users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False),
        sa.Column("mfa_secret_ref", sa.String(200), nullable=True),
        sa.Column("last_login_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("uq_admin_users_subject", "admin_users", ["subject"], unique=True)
    op.create_index("uq_admin_users_email", "admin_users", ["email"], unique=True)

    # ----------------------------------------------- RBAC reference (§5.18-§5.19)
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
    )
    op.create_index("uq_roles_code", "roles", ["code"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
    )
    op.create_index("uq_permissions_code", "permissions", ["code"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("permission_id", sa.String(36), sa.ForeignKey("permissions.id"), nullable=False),
        sa.Column("granted_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_role_permission", "role_permissions", ["role_id", "permission_id"], unique=True
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admin_user_id", sa.String(36), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("assigned_at", TS, nullable=False, server_default=NOW),
        sa.Column("revoked_at", TS, nullable=True),
    )
    op.create_index(
        "uq_user_role_niche", "user_roles", ["admin_user_id", "role_id", "niche_id"], unique=True
    )
    op.create_index("ix_user_roles_role", "user_roles", ["role_id"])

    # ----------------------------------------------------- api keys (§5.20)
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admin_user_id", sa.String(36), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False),
        sa.Column("scopes_json", sa.Text(), nullable=False),
        sa.Column("expires_at", TS, nullable=True),
        sa.Column("revoked_at", TS, nullable=True),
        sa.Column("last_used_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("uq_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    op.create_table(
        "admin_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admin_user_id", sa.String(36), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("preferences_json", sa.Text(), nullable=False),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_admin_preferences_user", "admin_preferences", ["admin_user_id"], unique=True
    )

    # ----------------------------------------- append-only audit (§5.25)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("admin_user_id", sa.String(36), sa.ForeignKey("admin_users.id"), nullable=True),
        sa.Column("api_key_id", sa.String(36), sa.ForeignKey("api_keys.id"), nullable=True),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("before_json", sa.Text(), nullable=True),
        sa.Column("after_json", sa.Text(), nullable=True),
        sa.Column("ip_hash", sa.String(128), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("occurred_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "ix_audit_entity_time", "audit_logs", ["entity_type", "entity_id", "occurred_at"]
    )
    op.create_index("ix_audit_user_time", "audit_logs", ["admin_user_id", "occurred_at"])
    op.create_index("ix_audit_niche_time", "audit_logs", ["niche_id", "occurred_at"])
    op.create_index("ix_audit_action_time", "audit_logs", ["action", "occurred_at"])

    # -------------------------------------------- notifications (§5.26)
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("recipient_id", sa.String(36), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("type", sa.String(60), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("action_ref", sa.String(300), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("read_at", TS, nullable=True),
    )
    op.create_index(
        "ix_notifications_recipient_status", "notifications", ["recipient_id", "status"]
    )

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admin_user_id", sa.String(36), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("channels_json", sa.Text(), nullable=False),
        sa.Column("quiet_hours_json", sa.Text(), nullable=False),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_notification_preferences_user",
        "notification_preferences",
        ["admin_user_id"],
        unique=True,
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "notification_id", sa.String(36), sa.ForeignKey("notifications.id"), nullable=False
        ),
        sa.Column("channel", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("provider_ref", sa.String(200), nullable=True),
        sa.Column("delivered_at", TS, nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
    )
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"])

    # ----------------------------------------- durable queue (§5.23)
    op.create_table(
        "queue_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("queue", sa.String(80), nullable=False),
        sa.Column("payload_ref", sa.String(500), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("run_at", TS, nullable=False, server_default=NOW),
        sa.Column("completed_at", TS, nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
    )
    op.create_index("ix_queue_queue_state_run", "queue_items", ["queue", "state", "run_at"])
    op.create_index("ix_queue_niche_state", "queue_items", ["niche_id", "state"])

    # ----------------------------------------------- webhook records (§5.24)
    op.create_table(
        "webhook_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payload_ref", sa.String(500), nullable=True),
        sa.Column("received_at", TS, nullable=False, server_default=NOW),
        sa.Column("processed_at", TS, nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
    )
    op.create_index("uq_webhook_source_event", "webhook_logs", ["source", "event_id"], unique=True)
    op.create_index("ix_webhook_logs_status_time", "webhook_logs", ["status", "received_at"])

    # --------------------------------------------- operation logs (§5.24)
    op.create_table(
        "operation_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("operation", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("occurred_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "ix_operation_logs_entity_time",
        "operation_logs",
        ["entity_type", "entity_id", "occurred_at"],
    )
    op.create_index("ix_operation_logs_niche_time", "operation_logs", ["niche_id", "occurred_at"])

    # ------------------------------------------------- scheduled jobs (§5.22)
    op.create_table(
        "scheduled_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("job_key", sa.String(120), nullable=False),
        sa.Column("cron_expr", sa.String(100), nullable=False),
        sa.Column("queue", sa.String(80), nullable=False),
        sa.Column("handler", sa.String(200), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("last_run_at", TS, nullable=True),
        sa.Column("next_run_at", TS, nullable=True),
    )
    op.create_index("uq_scheduled_job_key", "scheduled_jobs", ["niche_id", "job_key"], unique=True)
    op.create_index("ix_scheduled_jobs_status_next", "scheduled_jobs", ["status", "next_run_at"])

    op.create_table(
        "job_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column(
            "scheduled_job_id", sa.String(36), sa.ForeignKey("scheduled_jobs.id"), nullable=False
        ),
        sa.Column("run_at", TS, nullable=False, server_default=NOW),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("started_at", TS, nullable=True),
        sa.Column("finished_at", TS, nullable=True),
        sa.Column("output_ref", sa.String(500), nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
    )
    op.create_index("ix_job_runs_job_time", "job_runs", ["scheduled_job_id", "run_at"])
    op.create_index("ix_job_runs_status_time", "job_runs", ["status", "run_at"])


def downgrade() -> None:
    op.drop_table("job_runs")
    op.drop_table("scheduled_jobs")
    op.drop_table("operation_logs")
    op.drop_table("webhook_logs")
    op.drop_table("queue_items")
    op.drop_table("notification_deliveries")
    op.drop_table("notification_preferences")
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("admin_preferences")
    op.drop_table("api_keys")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("admin_users")
    op.drop_table("admin_niches")
