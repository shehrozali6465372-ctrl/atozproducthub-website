"""Public Read API (12-api-contracts.md §3-4).

Read-only, cacheable, published content only, identified by niche slug.
No credentials; no AI OS interaction. The website never blocks readers on
AI OS availability.
"""

from fastapi import APIRouter, Depends

from atoz_content_service.domain.entities import Niche
from atoz_content_service.errors import NotFoundError
from atoz_content_service.routes.deps import get_content_service, resolve_public_niche
from atoz_content_service.schemas import (
    Page,
    PublicArticleOut,
    PublicCategoryOut,
    PublicNicheOut,
    PublicTagOut,
)
from atoz_content_service.services import ContentService

router = APIRouter(prefix="/api/v1/public", tags=["public"])


def _paragraphs(body: str) -> list[str]:
    return [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]


def _read_time_minutes(body: str) -> int:
    words = len(body.split())
    return max(1, round(words / 200))


@router.get("/niches", summary="List active niches", response_model=list[PublicNicheOut])
async def list_niches(
    service: ContentService = Depends(get_content_service),
) -> list[PublicNicheOut]:
    niches = await service.list_niches(status="active")
    return [PublicNicheOut(id=n.id, slug=n.slug, name=n.name) for n in niches]


@router.get(
    "/articles",
    summary="List published articles (optional category/tag filter)",
    response_model=Page[PublicArticleOut],
)
async def list_articles(
    niche: Niche = Depends(resolve_public_niche),
    category: str | None = None,
    tag: str | None = None,
    page: int = 1,
    page_size: int = 20,
    service: ContentService = Depends(get_content_service),
) -> Page[PublicArticleOut]:
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    items, total = await service.list_published_articles(
        niche.id,
        category_slug=category,
        tag_slug=tag,
        page=page,
        page_size=page_size,
    )
    return Page[PublicArticleOut](
        items=[await _public_article(service, niche.id, article) for article in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/articles/{slug}",
    summary="Get a published article by slug",
    response_model=PublicArticleOut,
)
async def get_article(
    slug: str,
    niche: Niche = Depends(resolve_public_niche),
    service: ContentService = Depends(get_content_service),
) -> PublicArticleOut:
    result = await service.get_published_article(niche.id, slug)
    if result is None:
        raise NotFoundError("Article not found or not published.")
    article, body = result
    return await _public_article(service, niche.id, article, body=body)


@router.get(
    "/categories",
    summary="List active categories for a niche",
    response_model=list[PublicCategoryOut],
)
async def list_categories(
    niche: Niche = Depends(resolve_public_niche),
    service: ContentService = Depends(get_content_service),
) -> list[PublicCategoryOut]:
    categories = await service.list_categories(niche.id, status="active")
    return [
        PublicCategoryOut(slug=c.slug, name=c.name, description=c.description) for c in categories
    ]


@router.get(
    "/tags",
    summary="List active tags for a niche",
    response_model=list[PublicTagOut],
)
async def list_tags(
    niche: Niche = Depends(resolve_public_niche),
    service: ContentService = Depends(get_content_service),
) -> list[PublicTagOut]:
    tags = await service.list_tags(niche.id, status="active")
    return [PublicTagOut(slug=t.slug, name=t.name) for t in tags]


async def _public_article(
    service: ContentService,
    niche_id: str,
    article,
    *,
    body: str | None = None,
) -> PublicArticleOut:
    if body is None:
        published = await service.get_published_article(niche_id, article.slug)
        if published is None:
            raise NotFoundError("Article not found or not published.")
        body = published[1]
    categories = await service.categories_for_article(niche_id, article.id)
    tags = await service.tags_for_article(niche_id, article.id)
    primary = next(
        (c for c in categories if c.id == article.primary_category_id),
        categories[0] if categories else None,
    )
    return PublicArticleOut(
        id=article.id,
        slug=article.slug,
        title=article.title,
        excerpt=article.excerpt,
        category=(
            PublicCategoryOut(slug=primary.slug, name=primary.name, description=primary.description)
            if primary
            else None
        ),
        tags=[PublicTagOut(slug=t.slug, name=t.name) for t in tags],
        read_time_minutes=_read_time_minutes(body),
        published_at=article.published_at,
        body=_paragraphs(body),
    )
