"""ORM entities for the analytics module (analytics_db).

Table shapes follow Database Blueprint §5.15–§5.16: every record carries
``niche_id``; the operational event ledger is append-only with a unique
``event_id`` for idempotency; read models (traffic_daily, visitor_daily,
daily_metrics, kpi_snapshots) are upserted by the rollup. The ClickHouse
warehouse table (analytics_events) is infrastructure, not an ORM entity —
its schema is owned by the pipeline (Task 18 §3). No AI data lives here.
"""

from datetime import UTC, date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
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
    """Python-side ``updated_at`` value (no post-flush expiry)."""
    return datetime.now(UTC)


class AnalyticsNiche(Base):
    """Local tenant-registry mirror (ADR-0008).

    ``niches`` is owned by content-service in ``content_db``; cross-database
    foreign keys are impossible, so analytics_db keeps this minimal
    read-only-style mirror for local tenancy lookups and slug-based reads.
    """

    __tablename__ = "analytics_niches"

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


class AnalyticsEventLedger(Base):
    """Append-only operational event ledger (Blueprint §5.16, operational).

    One row per accepted event; ``event_id`` is the idempotency key — a
    duplicate delivery is a no-op, never a second row. Rows are never
    updated or deleted after insertion.
    """

    __tablename__ = "analytics_event_ledger"
    __table_args__ = (
        Index("ix_analytics_ledger_niche_type_time", "niche_id", "event_type", "occurred_at"),
        Index(
            "ix_analytics_ledger_niche_account_time",
            "niche_id",
            "pinterest_account_id",
            "occurred_at",
        ),
        Index("ix_analytics_ledger_time", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    pinterest_pin_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    page_url: Mapped[str | None] = mapped_column(String(700), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(700), nullable=True)
    user_pseudo_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    traits_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TrafficDaily(Base):
    """Daily traffic read model (Blueprint §5.15)."""

    __tablename__ = "traffic_daily"
    __table_args__ = (
        UniqueConstraint(
            "niche_id",
            "pinterest_account_id",
            "source",
            "traffic_date",
            name="uq_traffic_daily_niche_account_source_date",
        ),
        Index("ix_traffic_daily_date", "traffic_date"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    traffic_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pageviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_visitors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bounce_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class VisitorDaily(Base):
    """Daily visitor profile rollups (Blueprint §5.15)."""

    __tablename__ = "visitor_daily"
    __table_args__ = (
        UniqueConstraint(
            "niche_id",
            "traffic_date",
            "device",
            "country",
            name="uq_visitor_daily_niche_date_device_country",
        ),
        Index("ix_visitor_daily_date", "traffic_date"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    traffic_date: Mapped[date] = mapped_column(Date, nullable=False)
    device: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="unknown")
    sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unique_visitors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_duration_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class DailyMetric(Base):
    """KPI rollups per niche/account/day (Blueprint §5.16)."""

    __tablename__ = "daily_metrics"
    __table_args__ = (
        UniqueConstraint(
            "niche_id",
            "pinterest_account_id",
            "metric_key",
            "metric_date",
            name="uq_daily_metrics_niche_account_key_date",
        ),
        Index("ix_daily_metrics_date", "metric_date"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    metric_key: Mapped[str] = mapped_column(String(60), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    units: Mapped[str] = mapped_column(String(20), nullable=False, default="count")


class KpiSnapshot(Base):
    """Point-in-time KPI snapshots (Blueprint §5.16)."""

    __tablename__ = "kpi_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "niche_id",
            "snapshot_date",
            "snapshot_kind",
            name="uq_kpi_snapshots_niche_date_kind",
        ),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    snapshot_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="daily")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
