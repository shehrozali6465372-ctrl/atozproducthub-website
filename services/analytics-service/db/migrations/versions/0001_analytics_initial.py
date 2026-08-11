"""analytics_db tables: niche mirror, event ledger, traffic/visitor/metric
read models, kpi_snapshots

Revision ID: 0001
Revises:
Create Date: 2026-08-11

Portable schema (SQLite in tests, PostgreSQL in prod/CI). Primary keys are
UUID v7 strings assigned by the domain layer (ADR-0008). Every business
record carries ``niche_id`` per Database Blueprint §4. The operational
event ledger is append-only with a unique ``event_id`` idempotency key;
the ClickHouse warehouse table is infrastructure, created outside this
stream. No AI data lives here.
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
    # ----------------------------------------- local tenancy mirror (ADR-0008)
    op.create_table(
        "analytics_niches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("ix_analytics_niches_slug", "analytics_niches", ["slug"], unique=True)

    # ------------------------------------- operational event ledger (append-only)
    op.create_table(
        "analytics_event_ledger",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("pinterest_account_id", sa.String(36), nullable=True),
        sa.Column("pinterest_pin_id", sa.String(36), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("page_url", sa.String(700), nullable=True),
        sa.Column("referrer", sa.String(700), nullable=True),
        sa.Column("user_pseudo_id", sa.String(128), nullable=True),
        sa.Column("traits_json", sa.Text(), nullable=False),
        sa.Column("occurred_at", TS, nullable=False),
        sa.Column("received_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "ix_analytics_ledger_event_id", "analytics_event_ledger", ["event_id"], unique=True
    )
    op.create_index(
        "ix_analytics_ledger_niche_type_time",
        "analytics_event_ledger",
        ["niche_id", "event_type", "occurred_at"],
    )
    op.create_index(
        "ix_analytics_ledger_niche_account_time",
        "analytics_event_ledger",
        ["niche_id", "pinterest_account_id", "occurred_at"],
    )
    op.create_index("ix_analytics_ledger_time", "analytics_event_ledger", ["occurred_at"])

    # ----------------------------------------------- traffic_daily (§5.15)
    op.create_table(
        "traffic_daily",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("pinterest_account_id", sa.String(36), nullable=True),
        sa.Column("traffic_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("sessions", sa.Integer(), nullable=False),
        sa.Column("pageviews", sa.Integer(), nullable=False),
        sa.Column("unique_visitors", sa.Integer(), nullable=False),
        sa.Column("bounce_rate", sa.Float(), nullable=False),
    )
    op.create_index("ix_traffic_daily_date", "traffic_daily", ["traffic_date"])
    op.create_index(
        "uq_traffic_daily_niche_account_source_date",
        "traffic_daily",
        ["niche_id", "pinterest_account_id", "source", "traffic_date"],
        unique=True,
    )

    # ----------------------------------------------- visitor_daily (§5.15)
    op.create_table(
        "visitor_daily",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("traffic_date", sa.Date(), nullable=False),
        sa.Column("device", sa.String(30), nullable=False),
        sa.Column("country", sa.String(10), nullable=False),
        sa.Column("sessions", sa.Integer(), nullable=False),
        sa.Column("unique_visitors", sa.Integer(), nullable=False),
        sa.Column("avg_duration_sec", sa.Float(), nullable=False),
    )
    op.create_index("ix_visitor_daily_date", "visitor_daily", ["traffic_date"])
    op.create_index(
        "uq_visitor_daily_niche_date_device_country",
        "visitor_daily",
        ["niche_id", "traffic_date", "device", "country"],
        unique=True,
    )

    # ------------------------------------------------ daily_metrics (§5.16)
    op.create_table(
        "daily_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("pinterest_account_id", sa.String(36), nullable=True),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("metric_key", sa.String(60), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("units", sa.String(20), nullable=False),
    )
    op.create_index("ix_daily_metrics_date", "daily_metrics", ["metric_date"])
    op.create_index(
        "uq_daily_metrics_niche_account_key_date",
        "daily_metrics",
        ["niche_id", "pinterest_account_id", "metric_key", "metric_date"],
        unique=True,
    )

    # ------------------------------------------------ kpi_snapshots (§5.16)
    op.create_table(
        "kpi_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("snapshot_kind", sa.String(20), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_kpi_snapshots_niche_date_kind",
        "kpi_snapshots",
        ["niche_id", "snapshot_date", "snapshot_kind"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("kpi_snapshots")
    op.drop_table("daily_metrics")
    op.drop_table("visitor_daily")
    op.drop_table("traffic_daily")
    op.drop_table("analytics_event_ledger")
    op.drop_table("analytics_niches")
