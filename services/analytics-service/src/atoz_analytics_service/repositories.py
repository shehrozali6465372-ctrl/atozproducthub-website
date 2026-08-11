"""Repository layer for the analytics module.

Every repository extends ``atoz_backend_core.repositories`` and enforces
Database Blueprint tenancy: all queries are scoped by ``niche_id`` so one
niche can never read or mutate another niche's analytics state. The event
ledger is append-only — no update/delete surface exists for ledger rows.
"""

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import func, select

from atoz_analytics_service.domain.entities import (
    AnalyticsEventLedger,
    AnalyticsNiche,
    DailyMetric,
    KpiSnapshot,
    TrafficDaily,
    VisitorDaily,
)
from atoz_analytics_service.errors import ValidationError
from atoz_backend_core.repositories import SqlAlchemyRepository, SqlAlchemyUnitOfWork


class AnalyticsNicheRepository(SqlAlchemyRepository[AnalyticsNiche, str]):
    """Niches are a tenant-registry mirror — not niche-scoped themselves."""

    model = AnalyticsNiche

    async def get_by_slug(self, slug: str) -> AnalyticsNiche | None:
        result = await self._session.scalars(
            select(AnalyticsNiche).where(AnalyticsNiche.slug == slug)
        )
        return result.first()

    async def list_by_status(self, status: str | None = None) -> Sequence[AnalyticsNiche]:
        stmt = select(AnalyticsNiche).order_by(AnalyticsNiche.name)
        if status is not None:
            stmt = stmt.where(AnalyticsNiche.status == status)
        return (await self._session.scalars(stmt)).all()

    async def slug_exists(self, slug: str, *, exclude_id: str | None = None) -> bool:
        stmt = select(AnalyticsNiche.id).where(AnalyticsNiche.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(AnalyticsNiche.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None


class AnalyticsEventLedgerRepository(SqlAlchemyRepository[AnalyticsEventLedger, str]):
    """Append-only operational ledger; ``event_id`` is the idempotency key.

    ``update`` and ``delete`` are intentionally unsupported — analytics
    events are immutable business records (Task 18 §8 append-only rules).
    """

    model = AnalyticsEventLedger

    async def get_by_event_id(self, event_id: str) -> AnalyticsEventLedger | None:
        stmt = select(AnalyticsEventLedger).where(AnalyticsEventLedger.event_id == event_id)
        return (await self._session.scalars(stmt)).first()

    async def event_exists(self, event_id: str) -> bool:
        stmt = select(AnalyticsEventLedger.id).where(AnalyticsEventLedger.event_id == event_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def update(self, entity: AnalyticsEventLedger) -> AnalyticsEventLedger:
        raise ValidationError("Analytics events are append-only; ledger rows cannot be updated.")

    async def delete(self, entity_id: str) -> bool:
        raise ValidationError("Analytics events are append-only; ledger rows cannot be deleted.")

    async def list_scoped(
        self,
        niche_id: str,
        *,
        account_id: str | None = None,
        event_type: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AnalyticsEventLedger]:
        stmt = (
            select(AnalyticsEventLedger)
            .where(AnalyticsEventLedger.niche_id == niche_id)
            .order_by(AnalyticsEventLedger.occurred_at.desc())
        )
        if account_id is not None:
            stmt = stmt.where(AnalyticsEventLedger.pinterest_account_id == account_id)
        if event_type is not None:
            stmt = stmt.where(AnalyticsEventLedger.event_type == event_type)
        if start is not None:
            stmt = stmt.where(AnalyticsEventLedger.occurred_at >= start)
        if end is not None:
            stmt = stmt.where(AnalyticsEventLedger.occurred_at < end)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_scoped(
        self,
        niche_id: str,
        *,
        account_id: str | None = None,
        event_type: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> int:
        stmt = select(func.count(AnalyticsEventLedger.id)).where(
            AnalyticsEventLedger.niche_id == niche_id
        )
        if account_id is not None:
            stmt = stmt.where(AnalyticsEventLedger.pinterest_account_id == account_id)
        if event_type is not None:
            stmt = stmt.where(AnalyticsEventLedger.event_type == event_type)
        if start is not None:
            stmt = stmt.where(AnalyticsEventLedger.occurred_at >= start)
        if end is not None:
            stmt = stmt.where(AnalyticsEventLedger.occurred_at < end)
        return int((await self._session.execute(stmt)).scalar_one())

    async def top_pages(
        self,
        niche_id: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 20,
    ) -> Sequence[tuple[str, int, int]]:
        """Pageviews + unique visitors per page_url for a niche."""
        stmt = (
            select(
                AnalyticsEventLedger.page_url,
                func.count(AnalyticsEventLedger.id),
                func.count(func.distinct(AnalyticsEventLedger.user_pseudo_id)),
            )
            .where(
                AnalyticsEventLedger.niche_id == niche_id,
                AnalyticsEventLedger.event_type == "page_view",
                AnalyticsEventLedger.page_url.is_not(None),
            )
            .group_by(AnalyticsEventLedger.page_url)
            .order_by(
                func.count(AnalyticsEventLedger.id).desc(),
                func.count(func.distinct(AnalyticsEventLedger.user_pseudo_id)).desc(),
            )
            .limit(limit)
        )
        if start is not None:
            stmt = stmt.where(AnalyticsEventLedger.occurred_at >= start)
        if end is not None:
            stmt = stmt.where(AnalyticsEventLedger.occurred_at < end)
        return [(row[0] or "", row[1], row[2]) for row in (await self._session.execute(stmt)).all()]


class TrafficDailyRepository(SqlAlchemyRepository[TrafficDaily, str]):
    """Read model upserts (idempotent rollup)."""

    model = TrafficDaily

    async def get_scoped(
        self,
        niche_id: str,
        *,
        account_id: str | None,
        source: str,
        traffic_date: date,
    ) -> TrafficDaily | None:
        stmt = select(TrafficDaily).where(
            TrafficDaily.niche_id == niche_id,
            TrafficDaily.traffic_date == traffic_date,
            TrafficDaily.source == source,
        )
        if account_id is None:
            stmt = stmt.where(TrafficDaily.pinterest_account_id.is_(None))
        else:
            stmt = stmt.where(TrafficDaily.pinterest_account_id == account_id)
        return (await self._session.scalars(stmt)).first()

    async def list_range(
        self,
        niche_id: str,
        *,
        account_id: str | None = None,
        source: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 500,
    ) -> Sequence[TrafficDaily]:
        stmt = (
            select(TrafficDaily)
            .where(TrafficDaily.niche_id == niche_id)
            .order_by(TrafficDaily.traffic_date)
        )
        if account_id is not None:
            stmt = stmt.where(TrafficDaily.pinterest_account_id == account_id)
        if source is not None:
            stmt = stmt.where(TrafficDaily.source == source)
        if start is not None:
            stmt = stmt.where(TrafficDaily.traffic_date >= start)
        if end is not None:
            stmt = stmt.where(TrafficDaily.traffic_date <= end)
        return (await self._session.scalars(stmt.limit(limit))).all()


class VisitorDailyRepository(SqlAlchemyRepository[VisitorDaily, str]):
    """Read model upserts (idempotent rollup)."""

    model = VisitorDaily

    async def get_scoped(
        self, niche_id: str, *, traffic_date: date, device: str, country: str
    ) -> VisitorDaily | None:
        stmt = select(VisitorDaily).where(
            VisitorDaily.niche_id == niche_id,
            VisitorDaily.traffic_date == traffic_date,
            VisitorDaily.device == device,
            VisitorDaily.country == country,
        )
        return (await self._session.scalars(stmt)).first()

    async def list_range(
        self,
        niche_id: str,
        *,
        start: date | None = None,
        end: date | None = None,
        device: str | None = None,
        country: str | None = None,
        limit: int = 500,
    ) -> Sequence[VisitorDaily]:
        stmt = (
            select(VisitorDaily)
            .where(VisitorDaily.niche_id == niche_id)
            .order_by(VisitorDaily.traffic_date)
        )
        if device is not None:
            stmt = stmt.where(VisitorDaily.device == device)
        if country is not None:
            stmt = stmt.where(VisitorDaily.country == country)
        if start is not None:
            stmt = stmt.where(VisitorDaily.traffic_date >= start)
        if end is not None:
            stmt = stmt.where(VisitorDaily.traffic_date <= end)
        return (await self._session.scalars(stmt.limit(limit))).all()


class DailyMetricRepository(SqlAlchemyRepository[DailyMetric, str]):
    """Read model upserts (idempotent rollup)."""

    model = DailyMetric

    async def get_scoped(
        self,
        niche_id: str,
        *,
        account_id: str | None,
        metric_key: str,
        metric_date: date,
    ) -> DailyMetric | None:
        stmt = select(DailyMetric).where(
            DailyMetric.niche_id == niche_id,
            DailyMetric.metric_date == metric_date,
            DailyMetric.metric_key == metric_key,
        )
        if account_id is None:
            stmt = stmt.where(DailyMetric.pinterest_account_id.is_(None))
        else:
            stmt = stmt.where(DailyMetric.pinterest_account_id == account_id)
        return (await self._session.scalars(stmt)).first()

    async def list_range(
        self,
        niche_id: str,
        *,
        account_id: str | None = None,
        metric_key: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 1000,
    ) -> Sequence[DailyMetric]:
        stmt = (
            select(DailyMetric)
            .where(DailyMetric.niche_id == niche_id)
            .order_by(DailyMetric.metric_date)
        )
        if account_id is not None:
            stmt = stmt.where(DailyMetric.pinterest_account_id == account_id)
        if metric_key is not None:
            stmt = stmt.where(DailyMetric.metric_key == metric_key)
        if start is not None:
            stmt = stmt.where(DailyMetric.metric_date >= start)
        if end is not None:
            stmt = stmt.where(DailyMetric.metric_date <= end)
        return (await self._session.scalars(stmt.limit(limit))).all()


class KpiSnapshotRepository(SqlAlchemyRepository[KpiSnapshot, str]):
    """Point-in-time snapshots, upserted by the rollup."""

    model = KpiSnapshot

    async def get_scoped(
        self, niche_id: str, *, snapshot_date: date, snapshot_kind: str
    ) -> KpiSnapshot | None:
        stmt = select(KpiSnapshot).where(
            KpiSnapshot.niche_id == niche_id,
            KpiSnapshot.snapshot_date == snapshot_date,
            KpiSnapshot.snapshot_kind == snapshot_kind,
        )
        return (await self._session.scalars(stmt)).first()

    async def list_scoped(
        self,
        niche_id: str,
        *,
        snapshot_kind: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 100,
    ) -> Sequence[KpiSnapshot]:
        stmt = (
            select(KpiSnapshot)
            .where(KpiSnapshot.niche_id == niche_id)
            .order_by(KpiSnapshot.snapshot_date.desc())
        )
        if snapshot_kind is not None:
            stmt = stmt.where(KpiSnapshot.snapshot_kind == snapshot_kind)
        if start is not None:
            stmt = stmt.where(KpiSnapshot.snapshot_date >= start)
        if end is not None:
            stmt = stmt.where(KpiSnapshot.snapshot_date <= end)
        return (await self._session.scalars(stmt.limit(limit))).all()


class AnalyticsUnitOfWork(SqlAlchemyUnitOfWork):
    """Transaction boundary exposing all analytics repositories."""

    # Repository attributes are wired lazily by ``SqlAlchemyUnitOfWork._open``;
    # declared here so typed service helpers can rely on them (M8 ADR-0008).
    niches: AnalyticsNicheRepository
    events: AnalyticsEventLedgerRepository
    traffic: TrafficDailyRepository
    visitors: VisitorDailyRepository
    metrics: DailyMetricRepository
    snapshots: KpiSnapshotRepository

    @classmethod
    def build(cls, session_factory) -> "AnalyticsUnitOfWork":
        return cls(
            session_factory,
            repositories={
                "niches": AnalyticsNicheRepository,
                "events": AnalyticsEventLedgerRepository,
                "traffic": TrafficDailyRepository,
                "visitors": VisitorDailyRepository,
                "metrics": DailyMetricRepository,
                "snapshots": KpiSnapshotRepository,
            },
        )
