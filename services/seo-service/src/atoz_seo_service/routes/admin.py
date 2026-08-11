"""Admin API for the SEO module.

Mirrors the Admin API conventions (12-api-contracts.md §5): Bearer JWT with
``seo:read`` / ``seo:write`` RBAC claims and a mandatory ``X-Niche-Id``
tenancy header.
"""

from fastapi import APIRouter, Depends, Query

from atoz_backend_core.auth import TokenClaims
from atoz_seo_service.domain.entities import SeoNiche
from atoz_seo_service.routes.deps import (
    get_seo_service,
    require_niche,
    require_permission,
)
from atoz_seo_service.schemas import (
    CrawlReportIn,
    CrawlReportOut,
    MetadataOut,
    MetadataUpsertIn,
    NicheMirrorCreate,
    SearchHitOut,
    SearchPageOut,
    SitemapRebuildOut,
    SitemapShardOut,
    UrlOut,
    UrlRegisterIn,
)
from atoz_seo_service.services import SeoService

READ = require_permission("seo:read")
WRITE = require_permission("seo:write")

router = APIRouter(prefix="/api/v1/admin", tags=["admin-seo"])


# ------------------------------------------------------------------ niches
@router.get("/niches", summary="List SEO niche mirrors")
async def list_niches(
    _claims: TokenClaims = Depends(READ),
    service: SeoService = Depends(get_seo_service),
) -> list[dict]:
    return [
        {"id": n.id, "slug": n.slug, "name": n.name, "status": n.status}
        for n in await service.list_niches()
    ]


@router.post("/niches", summary="Create a niche mirror", status_code=201)
async def create_niche(
    payload: NicheMirrorCreate,
    _claims: TokenClaims = Depends(WRITE),
    service: SeoService = Depends(get_seo_service),
) -> dict:
    niche = await service.create_niche(name=payload.name, slug=payload.slug, status=payload.status)
    return {"id": niche.id, "slug": niche.slug, "name": niche.name, "status": niche.status}


# ---------------------------------------------------------- URL + metadata
@router.post("/urls", summary="Register a public URL", status_code=201)
async def register_url(
    payload: UrlRegisterIn,
    niche: SeoNiche = Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: SeoService = Depends(get_seo_service),
) -> UrlOut:
    row = await service.register_url(
        niche_id=niche.id,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        slug=payload.slug,
        path=payload.path,
        status=payload.status,
    )
    return UrlOut.model_validate(row, from_attributes=True)


@router.get("/urls", summary="List active URLs for a niche")
async def list_urls(
    niche: SeoNiche = Depends(require_niche),
    entity_type: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    _claims: TokenClaims = Depends(READ),
    service: SeoService = Depends(get_seo_service),
) -> list[UrlOut]:
    rows = await service.list_urls(
        niche.id, entity_types=[entity_type] if entity_type else None, limit=limit, offset=offset
    )
    return [UrlOut.model_validate(r, from_attributes=True) for r in rows]


@router.post(
    "/urls/{url_registry_id}/metadata", summary="Validate + apply SEO metadata", status_code=201
)
async def upsert_metadata(
    url_registry_id: str,
    payload: MetadataUpsertIn,
    niche: SeoNiche = Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: SeoService = Depends(get_seo_service),
) -> MetadataOut:
    row = await service.upsert_metadata(
        niche_id=niche.id,
        url_registry_id=url_registry_id,
        title=payload.title,
        meta_description=payload.meta_description,
        robots=payload.robots,
        og=payload.og,
        structured_data=payload.structured_data,
    )
    return MetadataOut.model_validate(row, from_attributes=True)


# ---------------------------------------------------------------- sitemaps
@router.post("/sitemaps/{group_name}/rebuild", summary="Rebuild one sitemap group")
async def rebuild_sitemap(
    group_name: str,
    niche: SeoNiche = Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: SeoService = Depends(get_seo_service),
) -> SitemapRebuildOut:
    shards = await service.rebuild_sitemap_group(niche_id=niche.id, group_name=group_name)
    return SitemapRebuildOut(group=group_name, shard_count=len(shards), shards=shards)


@router.get("/sitemaps", summary="Sitemap shard state for a niche")
async def list_sitemaps(
    niche: SeoNiche = Depends(require_niche),
    group_name: str | None = Query(default=None),
    _claims: TokenClaims = Depends(READ),
    service: SeoService = Depends(get_seo_service),
) -> list[SitemapShardOut]:
    rows = await service.list_sitemap_shards(niche.id, group_name=group_name)
    return [SitemapShardOut.model_validate(r, from_attributes=True) for r in rows]


# ------------------------------------------------------------------ search
@router.get("/search", summary="Niche-scoped admin search")
async def admin_search(
    niche: SeoNiche = Depends(require_niche),
    q: str = Query(min_length=1, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    _claims: TokenClaims = Depends(READ),
    service: SeoService = Depends(get_seo_service),
) -> SearchPageOut:
    result = await service.search(query=q, niche_id=niche.id, page=page, page_size=page_size)
    return SearchPageOut(
        items=[
            SearchHitOut(
                id=hit.id,
                type=hit.type,
                slug=hit.slug,
                title=hit.title,
                excerpt=hit.excerpt,
                url=hit.url,
                score=hit.score,
            )
            for hit in result.items
        ],
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )


# ------------------------------------------------------------ crawl reports
@router.post("/crawl-reports", summary="Record a GSC/Bing crawl report", status_code=201)
async def record_crawl_report(
    payload: CrawlReportIn,
    niche: SeoNiche = Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: SeoService = Depends(get_seo_service),
) -> CrawlReportOut:
    row = await service.record_crawl_report(
        niche_id=niche.id,
        source=payload.source,
        report_date=payload.report_date,
        pages_indexed=payload.pages_indexed,
        impressions=payload.impressions,
        clicks=payload.clicks,
        position_avg=payload.position_avg,
        raw=payload.raw,
    )
    return CrawlReportOut.model_validate(row, from_attributes=True)


@router.get("/crawl-reports", summary="Crawl reports for a niche")
async def list_crawl_reports(
    niche: SeoNiche = Depends(require_niche),
    source: str | None = Query(default=None, pattern="^(gsc|bing)$"),
    limit: int = Query(default=100, ge=1, le=365),
    _claims: TokenClaims = Depends(READ),
    service: SeoService = Depends(get_seo_service),
) -> list[CrawlReportOut]:
    rows = await service.list_crawl_reports(niche.id, source=source, limit=limit)
    return [CrawlReportOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/crawl/submit", summary="Submit sitemaps to GSC/Bing (server-side boundary)")
async def submit_sitemaps(
    source: str = Query(pattern="^(gsc|bing)$"),
    niche: SeoNiche = Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: SeoService = Depends(get_seo_service),
) -> dict:
    return await service.submit_sitemap(niche_id=niche.id, source=source)


# ---------------------------------------------------------------- health
@router.get("/health-checks", summary="SEO health snapshots for a niche")
async def list_health_checks(
    niche: SeoNiche = Depends(require_niche),
    check_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    _claims: TokenClaims = Depends(READ),
    service: SeoService = Depends(get_seo_service),
) -> list[dict]:
    rows = await service.list_health_checks(niche.id, check_type=check_type, limit=limit)
    return [
        {
            "id": r.id,
            "niche_id": r.niche_id,
            "url_registry_id": r.url_registry_id,
            "check_type": r.check_type,
            "score": r.score,
            "details": r.details_json,
            "checked_at": r.checked_at.isoformat() if r.checked_at else None,
        }
        for r in rows
    ]
