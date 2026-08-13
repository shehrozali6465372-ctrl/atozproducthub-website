"""automation_db tables: local niche mirror, rules, runs, AI OS job records.

Revision ID: 0001
Revises:
Create Date: 2026-08-13

Portable schema (SQLite in tests, PostgreSQL in prod/CI). Primary keys are
UUID v7 strings assigned by the domain layer (ADR-0010). Tenancy follows
Database Blueprint §4: ``niche_id`` is nullable for global rules/jobs and
mandatory for AI OS Bridge correlation records. ``automation_runs`` is
append-only execution history with an ``idempotency_key`` extension column
(M10 trigger replay safety, ADR-0010). The Platform tables
``scheduled_jobs`` / ``job_runs`` / ``queue_items`` are NOT created here —
they are owned and migrated by admin-service (ADR-0009); this service maps
ORM entities onto those exact physical tables. No AI data lives here.
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
    # ------------------------------- local tenancy mirror (ADR-0010 policy)
    op.create_table(
        "automation_niches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("ix_automation_niches_slug", "automation_niches", ["slug"], unique=True)

    # ------------------------------------------------ automation rules (§5.21)
    op.create_table(
        "automation_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column("code", sa.String(120), nullable=False),
        sa.Column("trigger_type", sa.String(30), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("run_as_user_id", sa.String(36), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_automation_rules_niche_code", "automation_rules", ["niche_id", "code"], unique=True
    )
    op.create_index("ix_automation_rules_niche_status", "automation_rules", ["niche_id", "status"])

    # ------------------------------------------- automation runs (§5.21, append-only)
    op.create_table(
        "automation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=True),
        sa.Column(
            "automation_rule_id",
            sa.String(36),
            sa.ForeignKey("automation_rules.id"),
            nullable=False,
        ),
        sa.Column("triggered_by", sa.String(36), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", TS, nullable=False, server_default=NOW),
        sa.Column("finished_at", TS, nullable=True),
        sa.Column("result_summary", sa.String(500), nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
    )
    op.create_index(
        "ix_automation_runs_rule_started", "automation_runs", ["automation_rule_id", "started_at"]
    )
    op.create_index("ix_automation_runs_niche_status", "automation_runs", ["niche_id", "status"])
    op.create_index(
        "uq_automation_runs_idempotency", "automation_runs", ["idempotency_key"], unique=True
    )

    # ---------------------------------------- AI OS Bridge records (§5.29)
    op.create_table(
        "aios_job_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("job_id", sa.String(128), nullable=False),
        sa.Column("contract", sa.String(100), nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("payload_ref", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("completed_at", TS, nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
    )
    op.create_index(
        "uq_aios_job_record_job_contract", "aios_job_records", ["job_id", "contract"], unique=True
    )
    op.create_index(
        "ix_aios_job_records_niche_status_created",
        "aios_job_records",
        ["niche_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("aios_job_records")
    op.drop_table("automation_runs")
    op.drop_table("automation_rules")
    op.drop_table("automation_niches")
