"""Public read API for the SEO module.

Read-only metadata, sitemaps, robots, and niche-scoped search. Search is
strictly filtered by the active niche — no cross-niche leakage is possible
because the niche slug resolves to a single local mirror record.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response

from atoz_seo_service.domain.entities import SeoNiche
from atoz_seo_service.routes.deps import get_seo_service, resolve_public_niche
from atoz_seo_service.schemas import PublicMetadataOut, SearchHitOut, SearchPageOut
from atoz_seo_service.services import SeoService

router = APIRouter(prefix="/api/v1/public", tags=["public-seo"])


@router.get("/seo/meta", summary="Applied SEO metadata for a public path")
async def public_metadata(
    niche: SeoNiche = Depends(resolve_public_niche),
    path: str = Query(min_length=1, max_length=500),
    service: SeoService = Depends(get_seo_service),
) -> PublicMetadataOut | None:
    metadata = await service.get_metadata_for_path(niche_id=niche.id, path=path)
    if metadata is None:
        return None
    return PublicMetadataOut(**metadata)


@router.get(
    "/seo/robots",
    summary="robots.txt for a niche (Pinterestbot always allowed)",
    response_model=None,
)
async def public_robots(
    niche: SeoNiche = Depends(resolve_public_niche),
    service: SeoService = Depends(get_seo_service),
) -> Response:
    robots = await service.render_robots(niche_id=niche.id)
    return Response(content=robots, media_type="text/plain")


@router.get(
    "/seo/sitemaps/{group_name}-index.xml",
    summary="Sitemap index for a group",
    response_model=None,
)
async def public_sitemap_index(
    niche: SeoNiche = Depends(resolve_public_niche),
    group_name: str = Path(pattern="^(articles|categories|tags|products|landing|collections)$"),
    service: SeoService = Depends(get_seo_service),
) -> Response | None:
    xml = await service.render_sitemap_index(niche_id=niche.id, group_name=group_name)
    if xml is None:
        raise HTTPException(status_code=404, detail="Sitemap index not found.")
    return Response(content=xml, media_type="application/xml")


@router.get(
    "/seo/sitemaps/{group_name}-{shard_no}.xml",
    summary="Sitemap shard XML",
    response_model=None,
)
async def public_sitemap_shard(
    niche: SeoNiche = Depends(resolve_public_niche),
    group_name: str = Path(pattern="^(articles|categories|tags|products|landing|collections)$"),
    shard_no: int = Path(ge=1),
    service: SeoService = Depends(get_seo_service),
) -> Response | None:
    xml = await service.render_sitemap_shard(
        niche_id=niche.id, group_name=group_name, shard_no=shard_no
    )
    if xml is None:
        raise HTTPException(status_code=404, detail="Sitemap shard not found.")
    return Response(content=xml, media_type="application/xml")


@router.get("/search", summary="Niche-scoped site search")
async def public_search(
    niche: SeoNiche = Depends(resolve_public_niche),
    q: str = Query(min_length=1, max_length=200),
    type: str | None = Query(
        default=None,
        pattern="^(article|product|category|tag|landing|collection)$",
        alias="type",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    service: SeoService = Depends(get_seo_service),
) -> SearchPageOut:
    types = [type] if type else None
    result = await service.search(
        query=q, niche_id=niche.id, types=types, page=page, page_size=page_size
    )
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
