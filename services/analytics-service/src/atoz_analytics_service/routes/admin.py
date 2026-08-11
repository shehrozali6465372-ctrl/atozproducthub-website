"""Admin analytics API (Task 18 §4, §6).

JWT RBAC ``analytics:read`` / ``analytics:write`` + mandatory ``X-Niche-Id``
tenancy header. All queries are niche-scoped server-side; ``account_id``
additionally isolates Pinterest-account data. Read-only analytical views —
no mutation of events, no AI generation.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query

from atoz_analytics_service.domain.entities import AnalyticsNiche
from atoz_analytics_service.routes.deps import (
    get_analytics_service,
    require_niche,
    require_permission,
)
from atoz_analytics_service.schemas import (
    LedgerEventOut,
    MetricSeriesOut,
    NicheMirrorCreate,
    OverviewKpis,
    RollupOut,
    TopPagesOut,
    TrafficSeriesOut,
    VisitorOut,
)
from atoz_analytics_service.services import AnalyticsService
from atoz_backend_core.auth import TokenClaims

READ = require_permission("analytics:read")
WRITE = require_permission("analytics:write")

router = APIRouter(prefix="/api/v1/admin", tags=["admin-analytics"])


# ------------------------------------------------------------------ niches
@router.get("/niches", summary="List analytics niche mirrors")
async def list_niches(
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[dict]:
    return [
        {"id": n.id, "slug": n.slug, "name": n.name, "status": n.status}
        for n in await service.list_niches()
    ]


@router.post("/niches", summary="Create a niche mirror", status_code=201)
async def create_niche(
    payload: NicheMirrorCreate,
    _claims: TokenClaims = Depends(WRITE),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict:
    niche = await service.create_niche(name=payload.name, slug=payload.slug, status=payload.status)
    return {"id": niche.id, "slug": niche.slug, "name": niche.name, "status": niche.status}


# ------------------------------------------------------------- read models
@router.get("/overview", summary="Dashboard KPI cards for a niche")
async def overview(
    niche: AnalyticsNiche = Depends(require_niche),
    from_date: date = Query(default=...),
    to_date: date = Query(default=...),
    account_id: str | None = Query(default=None, max_length=36),
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> OverviewKpis:
    return OverviewKpis(
        **await service.overview(
            niche.id, from_date=from_date, to_date=to_date, account_id=account_id
        )
    )


@router.get("/traffic", summary="Daily traffic read model")
async def traffic(
    niche: AnalyticsNiche = Depends(require_niche),
    from_date: date = Query(default=...),
    to_date: date = Query(default=...),
    source: str | None = Query(default=None, pattern="^(pinterest|google|direct|email|other)$"),
    account_id: str | None = Query(default=None, max_length=36),
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> TrafficSeriesOut:
    points = await service.traffic_series(
        niche.id,
        from_date=from_date,
        to_date=to_date,
        account_id=account_id,
        source=source,
    )
    return TrafficSeriesOut.model_validate({"points": points})


@router.get("/visitors", summary="Daily visitor profile read model")
async def visitors(
    niche: AnalyticsNiche = Depends(require_niche),
    from_date: date = Query(default=...),
    to_date: date = Query(default=...),
    device: str | None = Query(default=None, max_length=30),
    country: str | None = Query(default=None, max_length=10),
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> VisitorOut:
    points = await service.visitors(
        niche.id, from_date=from_date, to_date=to_date, device=device, country=country
    )
    return VisitorOut.model_validate({"points": points})


@router.get("/metrics", summary="Daily metric read model (affiliate/pinterest/revenue)")
async def metrics(
    niche: AnalyticsNiche = Depends(require_niche),
    from_date: date = Query(default=...),
    to_date: date = Query(default=...),
    metric_key: str | None = Query(default=None, max_length=60),
    account_id: str | None = Query(default=None, max_length=36),
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> MetricSeriesOut:
    points = await service.metrics(
        niche.id,
        from_date=from_date,
        to_date=to_date,
        metric_key=metric_key,
        account_id=account_id,
    )
    return MetricSeriesOut.model_validate({"points": points})


@router.get("/top-pages", summary="Content performance (top pages by pageviews)")
async def top_pages(
    niche: AnalyticsNiche = Depends(require_niche),
    from_date: date = Query(default=...),
    to_date: date = Query(default=...),
    limit: int = Query(default=20, ge=1, le=100),
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> TopPagesOut:
    rows = await service.top_pages(niche.id, from_date=from_date, to_date=to_date, limit=limit)
    return TopPagesOut.model_validate({"rows": rows})


@router.get("/events", summary="Append-only event ledger reads")
async def events(
    niche: AnalyticsNiche = Depends(require_niche),
    event_type: str | None = Query(default=None, max_length=50),
    account_id: str | None = Query(default=None, max_length=36),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[LedgerEventOut]:
    from datetime import UTC, datetime

    def _parse(value: str | None):
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

    rows = await service.list_events(
        niche.id,
        account_id=account_id,
        event_type=event_type,
        start=_parse(start),
        end=_parse(end),
        limit=limit,
        offset=offset,
    )
    return [LedgerEventOut(**row) for row in rows]


@router.get("/kpis", summary="KPI snapshots")
async def kpis(
    niche: AnalyticsNiche = Depends(require_niche),
    snapshot_kind: str | None = Query(default=None, pattern="^(daily|weekly)$"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[dict]:
    return await service.list_snapshots(
        niche.id, snapshot_kind=snapshot_kind, start=start, end=end, limit=limit
    )


# ----------------------------------------------------------------- rollups
@router.post("/rollups", summary="Run daily rollups for a date range")
async def run_rollups(
    niche: AnalyticsNiche = Depends(require_niche),
    from_date: date = Query(default=...),
    to_date: date = Query(default=...),
    _claims: TokenClaims = Depends(WRITE),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[RollupOut]:
    results = await service.run_rollups(niche_id=niche.id, from_date=from_date, to_date=to_date)
    return [RollupOut(niche_id=niche.id, **result) for result in results]


@router.get("/pipeline", summary="Pipeline wiring status (no secrets)")
async def pipeline(
    niche: AnalyticsNiche = Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict:
    return await service.pipeline_status()
