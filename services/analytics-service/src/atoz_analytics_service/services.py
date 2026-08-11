"""Analytics business layer (Task 18).

Facade over the analytics_db repositories: first-party event ingestion with
``event_id`` idempotency and append-only ledger writes, internal-event
ingestion from the shared webhook, daily/weekly rollups that build the
frozen read models, and niche-scoped read queries for the admin dashboards.

The service never performs AI work: event pipelines and aggregations are
pure business computation; AI-derived insights arrive read-only through the
AI OS Bridge (AIOS.Analytics.Insights), never computed here.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from atoz_analytics_service.config import Settings
from atoz_analytics_service.domain.entities import (
    AnalyticsEventLedger,
    AnalyticsNiche,
    DailyMetric,
    KpiSnapshot,
    TrafficDaily,
    VisitorDaily,
)
from atoz_analytics_service.domain.enums import (
    DOMAIN_EVENT_TO_INTERNAL,
    EventType,
    MetricKey,
    TrafficSource,
)
from atoz_analytics_service.domain.events import rollup_completed_event
from atoz_analytics_service.domain.pipeline import (
    EventBackbone,
    InMemoryEventBackbone,
    PipelineWorker,
    Warehouse,
)
from atoz_analytics_service.domain.privacy import assert_no_sensitive_traits
from atoz_analytics_service.errors import (
    DuplicateError,
    ValidationError,
)
from atoz_analytics_service.repositories import AnalyticsUnitOfWork
from atoz_analytics_service.uuids import uuid7
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher

logger = logging.getLogger("atoz.analytics.service")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _day_start(value: datetime) -> datetime:
    return datetime.combine(value.date(), time.min, tzinfo=UTC)


def _day_end(value: datetime) -> datetime:
    return _day_start(value) + timedelta(days=1)


def derive_traffic_source(referrer: str | None) -> str:
    """Map a referrer to the frozen traffic-source buckets (§5.15)."""
    if not referrer:
        return TrafficSource.DIRECT.value
    lowered = referrer.lower()
    if "pinterest." in lowered or "pin.it" in lowered:
        return TrafficSource.PINTEREST.value
    if "mail." in lowered or "outlook." in lowered or "yahoo." in lowered:
        return TrafficSource.EMAIL.value
    if "google." in lowered or "bing." in lowered:
        return TrafficSource.GOOGLE.value
    return TrafficSource.OTHER.value


class AnalyticsService:
    """Facade for the analytics business layer (niche-scoped everywhere)."""

    def __init__(
        self,
        *,
        uow_factory,
        event_publisher: EventPublisher,
        settings: Settings,
        backbone: EventBackbone,
        warehouse: Warehouse,
        pipeline_worker: PipelineWorker | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._event_publisher = event_publisher
        self._settings = settings
        self._backbone = backbone
        self._warehouse = warehouse
        self._pipeline_worker = pipeline_worker or PipelineWorker(backbone, warehouse)

    @staticmethod
    def build_uow(session_factory) -> AnalyticsUnitOfWork:
        return AnalyticsUnitOfWork.build(session_factory)

    # ----------------------------------------------------------- niches
    async def create_niche(self, *, name: str, slug: str, status: str = "draft") -> AnalyticsNiche:
        async with self._uow_factory().transaction() as unit:
            if await unit.niches.slug_exists(slug):
                raise DuplicateError("A niche with this slug already exists.")
            row = AnalyticsNiche(id=uuid7(), slug=slug, name=name, status=status)
            await unit.niches.add(row)
            return row

    async def get_niche(self, niche_id: str) -> AnalyticsNiche | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.get(niche_id)

    async def get_niche_by_slug(self, slug: str) -> AnalyticsNiche | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.get_by_slug(slug)

    async def list_niches(self) -> Sequence[AnalyticsNiche]:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.list_by_status()

    async def _require_active_niche(self, slug: str) -> AnalyticsNiche:
        niche = await self.get_niche_by_slug(slug)
        if niche is None or niche.status != "active":
            raise ValidationError("The requested niche is not registered or active.")
        return niche

    # ----------------------------------------------------------- ingest
    async def ingest_event(
        self, *, niche_slug: str, event: dict[str, Any]
    ) -> tuple[str, str, str | None]:
        """Collector path: validate, dedupe, append, publish.

        Returns ``(status, event_id, ledger_id)`` where status is
        ``accepted`` or ``duplicate``. Server-side ``received_at`` is always
        authoritative; client-supplied timestamps are best-effort.
        """
        niche = await self._require_active_niche(niche_slug)
        event_type = event.get("event_type", "")
        if event_type not in self._settings.allowed_event_types:
            raise ValidationError(f"Unsupported event type: {event_type!r}.")
        traits = event.get("traits") or {}
        assert_no_sensitive_traits(traits, sensitive_keys=self._settings.sensitive_trait_keys)
        if len(json.dumps(traits)) > self._settings.collector_max_traits_bytes:
            raise ValidationError("Event traits exceed the size limit.")

        event_id = event.get("event_id", "")
        occurred_at = _parse_datetime(event.get("occurred_at"))
        if occurred_at is None:
            occurred_at = _utcnow()
        received_at = _utcnow()

        ledger_id: str | None = None
        async with self._uow_factory().transaction() as unit:
            if await unit.events.event_exists(event_id):
                return "duplicate", event_id, None
            row = AnalyticsEventLedger(
                id=uuid7(),
                event_id=event_id,
                niche_id=niche.id,
                pinterest_account_id=event.get("pinterest_account_id"),
                pinterest_pin_id=event.get("pinterest_pin_id"),
                event_type=event_type,
                source="web",
                session_id=event.get("session_id"),
                page_url=event.get("page_url"),
                referrer=event.get("referrer"),
                user_pseudo_id=event.get("user_pseudo_id"),
                traits_json=json.dumps(traits, separators=(",", ":")),
                occurred_at=occurred_at,
                received_at=received_at,
            )
            await unit.events.add(row)
            ledger_id = row.id

        envelope = EventEnvelope(
            type=f"analytics:{event_type}.v1",
            event_id=event_id,
            payload={
                "niche_id": niche.id,
                "pinterest_account_id": event.get("pinterest_account_id"),
                "pinterest_pin_id": event.get("pinterest_pin_id"),
                "event_type": event_type,
                "page_url": event.get("page_url"),
                "referrer": event.get("referrer"),
                "session_id": event.get("session_id"),
                "user_pseudo_id": event.get("user_pseudo_id"),
                "traits": traits,
                "occurred_at": occurred_at.isoformat(),
                "received_at": received_at.isoformat(),
            },
            aggregate_id=event_id,
        )
        await self._backbone.publish(envelope)
        await self._pipeline_worker.drain_in_memory()
        return "accepted", event_id, ledger_id

    async def ingest_webhook_event(self, envelope: EventEnvelope) -> str:
        """Internal event ingestion (HMAC-verified route): map + record.

        Idempotent on ``envelope.event_id``; unknown domain event types are
        rejected so producers cannot inject arbitrary analytics data.
        """
        internal_type = DOMAIN_EVENT_TO_INTERNAL.get(envelope.type)
        if internal_type is None:
            raise ValidationError(f"Unsupported domain event type: {envelope.type!r}.")
        payload = envelope.payload or {}
        niche_id = payload.get("niche_id")
        if not niche_id:
            raise ValidationError("Domain events must carry niche_id.")
        niche = await self.get_niche(niche_id)
        if niche is None or niche.status != "active":
            raise ValidationError("The requested niche is not registered or active.")

        received_at = _utcnow()
        async with self._uow_factory().transaction() as unit:
            if await unit.events.event_exists(envelope.event_id):
                return "duplicate"
            row = AnalyticsEventLedger(
                id=uuid7(),
                event_id=envelope.event_id,
                niche_id=niche_id,
                pinterest_account_id=payload.get("pinterest_account_id"),
                pinterest_pin_id=payload.get("pinterest_pin_id") or payload.get("pin_id"),
                event_type=internal_type.value,
                source="internal",
                session_id=None,
                page_url=payload.get("url") or payload.get("page_url"),
                referrer=None,
                user_pseudo_id=None,
                traits_json=json.dumps(payload, separators=(",", ":")),
                occurred_at=datetime.fromtimestamp(envelope.occurred_at, tz=UTC),
                received_at=received_at,
            )
            await unit.events.add(row)

        publish_payload = dict(payload)
        publish_payload.update(
            {
                "event_type": internal_type.value,
                "received_at": received_at.isoformat(),
                "occurred_at": datetime.fromtimestamp(envelope.occurred_at, tz=UTC).isoformat(),
            }
        )
        await self._backbone.publish(
            EventEnvelope(
                type=f"analytics:{internal_type.value}.v1",
                event_id=envelope.event_id,
                payload=publish_payload,
                aggregate_id=envelope.aggregate_id or niche_id,
            )
        )
        await self._pipeline_worker.drain_in_memory()
        return "accepted"

    # ----------------------------------------------------------- rollups
    async def run_rollups(
        self, *, niche_id: str, from_date: date, to_date: date
    ) -> list[dict[str, Any]]:
        """Daily (and weekly on Sundays) rollups for a niche date range.

        Idempotent: read models are upserted, never duplicated. Emits
        ``analytics:rollup-completed.v1`` per processed day.
        """
        if from_date > to_date:
            raise ValidationError("from_date must be <= to_date.")
        window = (datetime.now(UTC).date() - from_date).days
        if window > self._settings.rollup_window_days:
            raise ValidationError("Rollup window exceeds the configured limit.")

        results: list[dict[str, Any]] = []
        cursor = from_date
        while cursor <= to_date:
            results.append(await self._run_daily_rollup(niche_id=niche_id, day=cursor))
            cursor += timedelta(days=1)
        return results

    async def _run_daily_rollup(self, *, niche_id: str, day: date) -> dict[str, Any]:
        start = datetime.combine(day, time.min, tzinfo=UTC)
        end = start + timedelta(days=1)
        async with self._uow_factory().transaction() as unit:
            events = await unit.events.list_scoped(niche_id, start=start, end=end, limit=100_000)
            if not events:
                # Still record a daily snapshot so dashboards can show zeros.
                await self._upsert_daily_snapshot(unit, niche_id=niche_id, day=day, metrics={})
                await self._event_publisher.publish(
                    rollup_completed_event(
                        niche_id=niche_id, rollup_date=day.isoformat(), snapshot_kinds=["daily"]
                    )
                )
                return {
                    "rollup_date": day.isoformat(),
                    "traffic_rows": 0,
                    "visitor_rows": 0,
                    "metric_rows": 0,
                    "snapshot_kinds": ["daily"],
                }

            traffic, visitors, metrics = aggregate_events(events)
            traffic_rows = await self._upsert_traffic(
                unit, niche_id=niche_id, day=day, traffic=traffic
            )
            visitor_rows = await self._upsert_visitors(
                unit, niche_id=niche_id, day=day, visitors=visitors
            )
            metric_rows = await self._upsert_metrics(
                unit, niche_id=niche_id, day=day, metrics=metrics
            )
            snapshot_kinds = await self._upsert_daily_snapshot(
                unit,
                niche_id=niche_id,
                day=day,
                metrics=metrics,
                traffic=traffic,
                visitors=visitors,
            )
        await self._event_publisher.publish(
            rollup_completed_event(
                niche_id=niche_id, rollup_date=day.isoformat(), snapshot_kinds=snapshot_kinds
            )
        )
        return {
            "rollup_date": day.isoformat(),
            "traffic_rows": traffic_rows,
            "visitor_rows": visitor_rows,
            "metric_rows": metric_rows,
            "snapshot_kinds": snapshot_kinds,
        }

    async def _upsert_traffic(
        self,
        unit: AnalyticsUnitOfWork,
        *,
        niche_id: str,
        day: date,
        traffic: dict[tuple[str, str | None], dict[str, Any]],
    ) -> int:
        count = 0
        for (source, account_id), agg in traffic.items():
            row = await unit.traffic.get_scoped(
                niche_id, account_id=account_id, source=source, traffic_date=day
            )
            if row is None:
                row = TrafficDaily(
                    id=uuid7(),
                    niche_id=niche_id,
                    pinterest_account_id=account_id,
                    traffic_date=day,
                    source=source,
                )
                await unit.traffic.add(row)
            row.sessions = agg["sessions"]
            row.pageviews = agg["pageviews"]
            row.unique_visitors = agg["unique_visitors"]
            row.bounce_rate = agg["bounce_rate"]
            count += 1
        return count

    async def _upsert_visitors(
        self,
        unit: AnalyticsUnitOfWork,
        *,
        niche_id: str,
        day: date,
        visitors: dict[tuple[str, str], dict[str, Any]],
    ) -> int:
        count = 0
        for (device, country), agg in visitors.items():
            row = await unit.visitors.get_scoped(
                niche_id, traffic_date=day, device=device, country=country
            )
            if row is None:
                row = VisitorDaily(
                    id=uuid7(),
                    niche_id=niche_id,
                    traffic_date=day,
                    device=device,
                    country=country,
                )
                await unit.visitors.add(row)
            row.sessions = agg["sessions"]
            row.unique_visitors = agg["unique_visitors"]
            row.avg_duration_sec = agg["avg_duration_sec"]
            count += 1
        return count

    async def _upsert_metrics(
        self,
        unit: AnalyticsUnitOfWork,
        *,
        niche_id: str,
        day: date,
        metrics: dict[tuple[str, str | None], float],
    ) -> int:
        count = 0
        for (metric_key, account_id), value in metrics.items():
            row = await unit.metrics.get_scoped(
                niche_id, account_id=account_id, metric_key=metric_key, metric_date=day
            )
            if row is None:
                row = DailyMetric(
                    id=uuid7(),
                    niche_id=niche_id,
                    pinterest_account_id=account_id,
                    metric_date=day,
                    metric_key=metric_key,
                    units="count"
                    if metric_key != MetricKey.REVENUE_AMOUNT.value
                    and metric_key != MetricKey.REVENUE_COMMISSION.value
                    else "currency",
                )
                await unit.metrics.add(row)
            row.value = value
            count += 1
        return count

    async def _upsert_daily_snapshot(
        self,
        unit: AnalyticsUnitOfWork,
        *,
        niche_id: str,
        day: date,
        metrics: dict[tuple[str, str | None], float],
        traffic: dict[tuple[str, str | None], dict[str, Any]] | None = None,
        visitors: dict[tuple[str, str], dict[str, Any]] | None = None,
    ) -> list[str]:
        traffic = traffic or {}
        visitors = visitors or {}
        total_sessions = sum(agg["sessions"] for agg in traffic.values())
        total_pageviews = sum(agg["pageviews"] for agg in traffic.values())
        total_visitors = sum(agg["unique_visitors"] for agg in traffic.values())
        payload = {
            "sessions": total_sessions,
            "pageviews": total_pageviews,
            "unique_visitors": total_visitors,
            "metrics": {f"{k[0]}:{k[1] or 'all'}": v for k, v in metrics.items()},
            "devices": {f"{k[0]}:{k[1]}": v["sessions"] for k, v in visitors.items()},
        }
        kinds = ["daily"]
        snapshot = await unit.snapshots.get_scoped(
            niche_id, snapshot_date=day, snapshot_kind="daily"
        )
        if snapshot is None:
            snapshot = KpiSnapshot(
                id=uuid7(), niche_id=niche_id, snapshot_date=day, snapshot_kind="daily"
            )
            await unit.snapshots.add(snapshot)
        snapshot.payload_json = json.dumps(payload, separators=(",", ":"))
        if day.isoweekday() == 7:  # Sunday: weekly snapshot too
            weekly = await unit.snapshots.get_scoped(
                niche_id, snapshot_date=day, snapshot_kind="weekly"
            )
            if weekly is None:
                weekly = KpiSnapshot(
                    id=uuid7(), niche_id=niche_id, snapshot_date=day, snapshot_kind="weekly"
                )
                await unit.snapshots.add(weekly)
            weekly.payload_json = json.dumps(payload, separators=(",", ":"))
            kinds.append("weekly")
        return kinds

    # ------------------------------------------------------------ queries
    async def traffic_series(
        self,
        niche_id: str,
        *,
        from_date: date,
        to_date: date,
        account_id: str | None = None,
        source: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        async with self._uow_factory().transaction() as unit:
            rows = await unit.traffic.list_range(
                niche_id,
                account_id=account_id,
                source=source,
                start=from_date,
                end=to_date,
                limit=limit,
            )
            return [
                {
                    "date": row.traffic_date.isoformat(),
                    "source": row.source,
                    "sessions": row.sessions,
                    "pageviews": row.pageviews,
                    "unique_visitors": row.unique_visitors,
                    "bounce_rate": row.bounce_rate,
                }
                for row in rows
            ]

    async def visitors(
        self,
        niche_id: str,
        *,
        from_date: date,
        to_date: date,
        device: str | None = None,
        country: str | None = None,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        async with self._uow_factory().transaction() as unit:
            rows = await unit.visitors.list_range(
                niche_id, start=from_date, end=to_date, device=device, country=country, limit=limit
            )
            return [
                {
                    "date": row.traffic_date.isoformat(),
                    "device": row.device,
                    "country": row.country,
                    "sessions": row.sessions,
                    "unique_visitors": row.unique_visitors,
                    "avg_duration_sec": row.avg_duration_sec,
                }
                for row in rows
            ]

    async def metrics(
        self,
        niche_id: str,
        *,
        from_date: date,
        to_date: date,
        account_id: str | None = None,
        metric_key: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        async with self._uow_factory().transaction() as unit:
            rows = await unit.metrics.list_range(
                niche_id,
                account_id=account_id,
                metric_key=metric_key,
                start=from_date,
                end=to_date,
                limit=limit,
            )
            return [
                {
                    "date": row.metric_date.isoformat(),
                    "metric_key": row.metric_key,
                    "value": row.value,
                    "units": row.units,
                    "pinterest_account_id": row.pinterest_account_id,
                }
                for row in rows
            ]

    async def top_pages(
        self, niche_id: str, *, from_date: date, to_date: date, limit: int = 20
    ) -> list[dict[str, Any]]:
        async with self._uow_factory().transaction() as unit:
            rows = await unit.events.top_pages(
                niche_id,
                start=datetime.combine(from_date, time.min, tzinfo=UTC),
                end=datetime.combine(to_date, time.min, tzinfo=UTC) + timedelta(days=1),
                limit=limit,
            )
            return [
                {"page_url": path, "pageviews": count, "unique_visitors": visitors}
                for path, count, visitors in rows
            ]

    async def overview(
        self,
        niche_id: str,
        *,
        from_date: date,
        to_date: date,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._uow_factory().transaction() as unit:
            traffic = await unit.traffic.list_range(
                niche_id, account_id=account_id, start=from_date, end=to_date
            )
            metrics = await unit.metrics.list_range(
                niche_id, account_id=account_id, start=from_date, end=to_date
            )
        sessions = sum(row.sessions for row in traffic)
        pageviews = sum(row.pageviews for row in traffic)
        unique_visitors = sum(row.unique_visitors for row in traffic)
        bounce = (
            sum(row.bounce_rate * row.sessions for row in traffic) / sessions if sessions else 0.0
        )
        by_key: dict[str, float] = {}
        for row in metrics:
            by_key[row.metric_key] = by_key.get(row.metric_key, 0.0) + row.value
        return {
            "sessions": sessions,
            "pageviews": pageviews,
            "unique_visitors": unique_visitors,
            "bounce_rate": round(bounce, 4),
            "affiliate_clicks": int(by_key.get(MetricKey.AFFILIATE_CLICKS.value, 0.0)),
            "conversions": int(by_key.get(MetricKey.CONVERSIONS.value, 0.0)),
            "revenue_amount": by_key.get(MetricKey.REVENUE_AMOUNT.value, 0.0),
            "pin_clicks": int(by_key.get(MetricKey.PIN_CLICKS.value, 0.0)),
        }

    async def list_events(
        self,
        niche_id: str,
        *,
        account_id: str | None = None,
        event_type: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        async with self._uow_factory().transaction() as unit:
            rows = await unit.events.list_scoped(
                niche_id,
                account_id=account_id,
                event_type=event_type,
                start=start,
                end=end,
                limit=limit,
                offset=offset,
            )
            return [
                {
                    "id": row.id,
                    "event_id": row.event_id,
                    "event_type": row.event_type,
                    "source": row.source,
                    "session_id": row.session_id,
                    "page_url": row.page_url,
                    "pinterest_account_id": row.pinterest_account_id,
                    "occurred_at": row.occurred_at,
                    "received_at": row.received_at,
                }
                for row in rows
            ]

    async def list_snapshots(
        self,
        niche_id: str,
        *,
        snapshot_kind: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        async with self._uow_factory().transaction() as unit:
            rows = await unit.snapshots.list_scoped(
                niche_id, snapshot_kind=snapshot_kind, start=start, end=end, limit=limit
            )
            return [
                {
                    "id": row.id,
                    "niche_id": row.niche_id,
                    "snapshot_date": row.snapshot_date.isoformat(),
                    "snapshot_kind": row.snapshot_kind,
                    "payload": json.loads(row.payload_json),
                }
                for row in rows
            ]

    async def pipeline_status(self) -> dict[str, str]:
        """Expose the pipeline wiring for admin/observability (no secrets)."""
        backbone_name = (
            "kafka" if not isinstance(self._backbone, InMemoryEventBackbone) else "in-memory"
        )
        return {
            "backbone": backbone_name,
            "warehouse": "clickhouse"
            if type(self._warehouse).__name__ == "ClickHouseWarehouse"
            else "in-memory",
            "kafka_enabled": str(self._settings.kafka_enabled).lower(),
            "warehouse_enabled": str(self._settings.warehouse_enabled).lower(),
        }


# ------------------------------------------------------------ aggregation
def aggregate_events(
    events: Sequence[AnalyticsEventLedger],
) -> tuple[
    dict[tuple[str, str | None], dict[str, Any]],
    dict[tuple[str, str], dict[str, Any]],
    dict[tuple[str, str | None], float],
]:
    """Aggregate ledger rows into traffic/visitor/metric accumulators.

    Pure function — no I/O — so rollup math is unit-testable. Sessions and
    unique visitors are distinct-counted by ``session_id`` /
    ``user_pseudo_id``; bounce rate is the share of sessions that recorded
    exactly one page view.
    """
    traffic: dict[tuple[str, str | None], dict[str, Any]] = defaultdict(
        lambda: {
            "sessions": 0,
            "pageviews": 0,
            "unique_visitors": 0,
            "bounce_rate": 0.0,
            "_sessions": set(),
            "_users": set(),
            "_pages": defaultdict(set),
        }
    )
    visitors: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "sessions": 0,
            "unique_visitors": 0,
            "avg_duration_sec": 0.0,
            "_sessions": set(),
            "_users": set(),
        }
    )
    metrics: dict[tuple[str, str | None], float] = defaultdict(float)
    session_page_count: dict[str, int] = defaultdict(int)

    for event in events:
        account_id = event.pinterest_account_id
        traits = _load_traits(event.traits_json)
        if event.event_type in (EventType.PAGE_VIEW.value, EventType.SESSION_START.value):
            source = derive_traffic_source(event.referrer)
            key = (source, account_id)
            if event.event_type == EventType.PAGE_VIEW.value:
                traffic[key]["pageviews"] += 1
                metrics[(MetricKey.PAGEVIEWS.value, None)] += 1
                if event.session_id:
                    traffic[key]["_pages"][event.session_id].add(source)
                    session_page_count[event.session_id] += 1
            if event.session_id:
                traffic[key]["_sessions"].add(event.session_id)
            if event.user_pseudo_id:
                traffic[key]["_users"].add(event.user_pseudo_id)
            device = str(traits.get("device", "unknown"))[:30] or "unknown"
            country = str(traits.get("country", "unknown"))[:10] or "unknown"
            vkey = (device, country)
            if event.session_id:
                visitors[vkey]["_sessions"].add(event.session_id)
            if event.user_pseudo_id:
                visitors[vkey]["_users"].add(event.user_pseudo_id)
            visitors[vkey]["avg_duration_sec"] += float(traits.get("duration_sec", 0) or 0)
        elif event.event_type == EventType.PIN_CLICK.value:
            metrics[(MetricKey.PIN_CLICKS.value, account_id)] += 1
        elif event.event_type == EventType.PIN_SAVE.value:
            metrics[(MetricKey.PIN_SAVES.value, account_id)] += 1
        elif event.event_type == EventType.AFFILIATE_CLICK.value:
            metrics[(MetricKey.AFFILIATE_CLICKS.value, account_id)] += 1
        elif event.event_type == EventType.CONVERSION.value:
            metrics[(MetricKey.CONVERSIONS.value, account_id)] += 1
        elif event.event_type == "revenue_attributed":
            amount = float(traits.get("amount", 0) or 0)
            commission = float(traits.get("commission", amount) or 0)
            metrics[(MetricKey.REVENUE_AMOUNT.value, account_id)] += amount
            metrics[(MetricKey.REVENUE_COMMISSION.value, account_id)] += commission
        elif event.event_type == "pin_published":
            metrics[(MetricKey.PIN_IMPRESSIONS.value, account_id)] += float(
                traits.get("impressions", 0) or 0
            )

    for _key, agg in traffic.items():
        sessions = len(agg["_sessions"])
        agg["sessions"] = sessions
        agg["unique_visitors"] = len(agg["_users"])
        bounced = sum(1 for sid in agg["_pages"] if session_page_count[sid] == 1)
        agg["bounce_rate"] = round(bounced / sessions, 4) if sessions else 0.0
        del agg["_sessions"], agg["_users"], agg["_pages"]
    for _vkey, agg in visitors.items():
        sessions = len(agg["_sessions"])
        agg["sessions"] = sessions
        agg["unique_visitors"] = len(agg["_users"])
        agg["avg_duration_sec"] = round(agg["avg_duration_sec"] / sessions, 2) if sessions else 0.0
        del agg["_sessions"], agg["_users"]
    metrics[(MetricKey.SESSIONS.value, None)] = sum(agg["sessions"] for agg in traffic.values())
    metrics[(MetricKey.UNIQUE_VISITORS.value, None)] = sum(
        agg["unique_visitors"] for agg in traffic.values()
    )
    return dict(traffic), dict(visitors), dict(metrics)


def _load_traits(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}


def _parse_datetime(value: Any) -> datetime | None:
    """Accept datetime or ISO-8601 strings (collector robustness)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None
