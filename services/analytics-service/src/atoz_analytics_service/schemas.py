"""Pydantic schemas for the analytics module (collector + admin APIs)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ collector
class CollectorEventIn(BaseModel):
    """One first-party event from the public website (Task 18 §2)."""

    event_id: str = Field(min_length=8, max_length=64)
    event_type: str = Field(min_length=3, max_length=50)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)
    page_url: str | None = Field(default=None, min_length=1, max_length=700)
    referrer: str | None = Field(default=None, min_length=1, max_length=700)
    user_pseudo_id: str | None = Field(default=None, min_length=1, max_length=128)
    pinterest_account_id: str | None = Field(default=None, min_length=1, max_length=36)
    pinterest_pin_id: str | None = Field(default=None, min_length=1, max_length=36)
    traits: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class CollectorBatchIn(BaseModel):
    """Batch of first-party events; each is validated independently."""

    events: list[CollectorEventIn] = Field(min_length=1, max_length=100)


class CollectorEventOut(BaseModel):
    event_id: str
    status: str  # accepted | duplicate
    ledger_id: str | None = None
    error: str | None = None


class CollectorBatchOut(BaseModel):
    accepted: int
    duplicates: int
    rejected: int
    items: list[CollectorEventOut]


# --------------------------------------------------------------------- admin
class TrafficPoint(BaseModel):
    date: str
    source: str
    sessions: int = 0
    pageviews: int = 0
    unique_visitors: int = 0
    bounce_rate: float = 0.0


class TrafficSeriesOut(BaseModel):
    points: list[TrafficPoint]


class VisitorPoint(BaseModel):
    date: str
    device: str
    country: str
    sessions: int = 0
    unique_visitors: int = 0
    avg_duration_sec: float = 0.0


class VisitorOut(BaseModel):
    points: list[VisitorPoint]


class MetricPoint(BaseModel):
    date: str
    metric_key: str
    value: float
    units: str = "count"
    pinterest_account_id: str | None = None


class MetricSeriesOut(BaseModel):
    points: list[MetricPoint]


class TopPageRow(BaseModel):
    page_url: str
    pageviews: int
    unique_visitors: int
    last_seen: datetime | None = None


class TopPagesOut(BaseModel):
    rows: list[TopPageRow]


class OverviewKpis(BaseModel):
    sessions: int
    pageviews: int
    unique_visitors: int
    bounce_rate: float
    affiliate_clicks: int
    conversions: int
    revenue_amount: float
    pin_clicks: int


class LedgerEventOut(BaseModel):
    id: str
    event_id: str
    event_type: str
    source: str
    session_id: str | None
    page_url: str | None
    pinterest_account_id: str | None = None
    occurred_at: datetime
    received_at: datetime


class RollupOut(BaseModel):
    niche_id: str
    rollup_date: str
    traffic_rows: int
    visitor_rows: int
    metric_rows: int
    snapshot_kinds: list[str]


# -------------------------------------------------------------------- events
class EventWebhookIn(BaseModel):
    """Internal domain event envelope (mirrors seo-service webhook)."""

    type: str
    event_id: str = Field(min_length=8, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)
    aggregate_id: str | None = None


# ------------------------------------------------------------------- niches
class NicheMirrorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")
