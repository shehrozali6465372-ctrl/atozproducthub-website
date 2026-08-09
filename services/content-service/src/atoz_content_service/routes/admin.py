"""Admin Content API (12-api-contracts.md §4: Admin API).

JWT access tokens + RBAC permissions (``content:read`` / ``content:write``)
and the mandatory ``X-Niche-Id`` tenancy header. All queries and mutations
are niche-scoped server-side; cross-niche requests 404/422.

Auth note (ADR-0004): tokens are verified in-service against the shared
JWT secret. The gateway remains the primary authentication entry point;
session revocation and OIDC land in Phase 5.
"""

from fastapi import APIRouter, Depends, Response, status

from atoz_backend_core.auth import TokenClaims
from atoz_content_service.domain.entities import Niche
from atoz_content_service.errors import NotFoundError
from atoz_content_service.routes.deps import (
    get_content_service,
    require_niche,
    require_permission,
)
from atoz_content_service.schemas import (
    ArticleCreate,
    ArticleDetailOut,
    ArticleListItemOut,
    ArticleOut,
    ArticleUpdate,
    CategoryCreate,
    CategoryOut,
    CategoryRefOut,
    CategoryUpdate,
    LifecycleRequest,
    NicheCreate,
    NicheOut,
    NicheUpdate,
    Page,
    TagCreate,
    TagOut,
    TagRefOut,
    TagUpdate,
    VersionOut,
)
from atoz_content_service.services import ContentService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

READ = require_permission("content:read")
WRITE = require_permission("content:write")


# ------------------------------------------------------------------ niches
@router.get("/niches", summary="List all niches", response_model=list[NicheOut])
async def list_niches(
    _: TokenClaims = Depends(READ),
    service: ContentService = Depends(get_content_service),
) -> list[NicheOut]:
    return [NicheOut.model_validate(n) for n in await service.list_niches()]


@router.post(
    "/niches",
    summary="Create a niche",
    response_model=NicheOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_niche(
    payload: NicheCreate,
    _: TokenClaims = Depends(WRITE),
    service: ContentService = Depends(get_content_service),
) -> NicheOut:
    niche = await service.create_niche(
        name=payload.name, slug=payload.slug, default_currency=payload.default_currency
    )
    return NicheOut.model_validate(niche)


@router.patch("/niches/{niche_id}", summary="Update a niche", response_model=NicheOut)
async def update_niche(
    niche_id: str,
    payload: NicheUpdate,
    _: TokenClaims = Depends(WRITE),
    service: ContentService = Depends(get_content_service),
) -> NicheOut:
    niche = await service.update_niche(
        niche_id,
        name=payload.name,
        slug=payload.slug,
        status=payload.status,
        default_currency=payload.default_currency,
    )
    return NicheOut.model_validate(niche)


# -------------------------------------------------------------- categories
@router.get("/categories", summary="List niche categories", response_model=list[CategoryOut])
async def list_categories(
    _: TokenClaims = Depends(READ),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> list[CategoryOut]:
    categories = await service.list_categories(niche.id)
    return [CategoryOut.model_validate(c) for c in categories]


@router.post(
    "/categories",
    summary="Create a category",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    payload: CategoryCreate,
    _: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> CategoryOut:
    category = await service.create_category(
        niche.id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        parent_id=payload.parent_id,
        sort_order=payload.sort_order,
    )
    return CategoryOut.model_validate(category)


@router.patch("/categories/{category_id}", summary="Update a category", response_model=CategoryOut)
async def update_category(
    category_id: str,
    payload: CategoryUpdate,
    _: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> CategoryOut:
    category = await service.update_category(
        niche.id,
        category_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        parent_id=payload.parent_id,
        sort_order=payload.sort_order,
        status=payload.status,
    )
    return CategoryOut.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    summary="Delete a category",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_category(
    category_id: str,
    _: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> Response:
    await service.delete_category(niche.id, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------- tags
@router.get("/tags", summary="List niche tags", response_model=list[TagOut])
async def list_tags(
    _: TokenClaims = Depends(READ),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> list[TagOut]:
    return [TagOut.model_validate(t) for t in await service.list_tags(niche.id)]


@router.post(
    "/tags", summary="Create a tag", response_model=TagOut, status_code=status.HTTP_201_CREATED
)
async def create_tag(
    payload: TagCreate,
    _: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> TagOut:
    tag = await service.create_tag(niche.id, name=payload.name, slug=payload.slug)
    return TagOut.model_validate(tag)


@router.patch("/tags/{tag_id}", summary="Update a tag", response_model=TagOut)
async def update_tag(
    tag_id: str,
    payload: TagUpdate,
    _: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> TagOut:
    tag = await service.update_tag(
        niche.id, tag_id, name=payload.name, slug=payload.slug, status=payload.status
    )
    return TagOut.model_validate(tag)


@router.delete("/tags/{tag_id}", summary="Delete a tag", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    _: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> Response:
    await service.delete_tag(niche.id, tag_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------- articles
@router.get("/articles", summary="List niche articles", response_model=Page[ArticleListItemOut])
async def list_articles(
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    _: TokenClaims = Depends(READ),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> Page[ArticleListItemOut]:
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    items, total = await service.list_articles(
        niche.id, status=status_filter, page=page, page_size=page_size
    )
    return Page[ArticleListItemOut](
        items=[ArticleListItemOut.model_validate(a) for a in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/articles",
    summary="Create an article (draft)",
    response_model=ArticleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_article(
    payload: ArticleCreate,
    claims: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> ArticleOut:
    article = await service.create_article(
        niche.id,
        title=payload.title,
        excerpt=payload.excerpt,
        body=payload.body,
        slug=payload.slug,
        category_ids=payload.category_ids,
        primary_category_id=payload.primary_category_id,
        tag_ids=payload.tag_ids,
        actor=claims.subject,
        change_summary=payload.change_summary,
    )
    return ArticleOut.model_validate(article)


@router.get("/articles/{article_id}", summary="Get an article (detail view)")
async def get_article(
    article_id: str,
    _claims: TokenClaims = Depends(READ),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> ArticleDetailOut:
    article = await service.get_article(niche.id, article_id)
    if article is None:
        raise NotFoundError("Article not found.")
    categories = await service.categories_for_article(niche.id, article.id)
    tags = await service.tags_for_article(niche.id, article.id)
    _, versions = await service.list_versions(niche.id, article.id)
    return ArticleDetailOut(
        article=ArticleOut.model_validate(article),
        categories=[
            CategoryRefOut(
                id=c.id,
                slug=c.slug,
                name=c.name,
                is_primary=c.id == article.primary_category_id,
            )
            for c in categories
        ],
        tags=[TagRefOut(id=t.id, slug=t.slug, name=t.name) for t in tags],
        versions=[VersionOut.model_validate(v) for v in versions],
    )


@router.patch("/articles/{article_id}", summary="Update an article", response_model=ArticleOut)
async def update_article(
    article_id: str,
    payload: ArticleUpdate,
    claims: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> ArticleOut:
    article = await service.update_article(
        niche.id,
        article_id,
        actor=claims.subject,
        title=payload.title,
        excerpt=payload.excerpt,
        body=payload.body,
        slug=payload.slug,
        category_ids=payload.category_ids,
        primary_category_id=payload.primary_category_id,
        tag_ids=payload.tag_ids,
        change_summary=payload.change_summary,
    )
    return ArticleOut.model_validate(article)


@router.delete(
    "/articles/{article_id}",
    summary="Soft-delete an article",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_article(
    article_id: str,
    claims: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> Response:
    await service.soft_delete(niche.id, article_id, actor=claims.subject)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/articles/{article_id}/lifecycle",
    summary="Apply a lifecycle action (submit/approve/reject/publish/unpublish/archive/restore)",
    response_model=ArticleOut,
)
async def article_lifecycle(
    article_id: str,
    payload: LifecycleRequest,
    claims: TokenClaims = Depends(WRITE),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> ArticleOut:
    article = await service.transition(niche.id, article_id, payload.action, actor=claims.subject)
    return ArticleOut.model_validate(article)


@router.get(
    "/articles/{article_id}/versions",
    summary="List immutable versions of an article",
    response_model=Page[VersionOut],
)
async def list_versions(
    article_id: str,
    _claims: TokenClaims = Depends(READ),
    niche: Niche = Depends(require_niche),
    service: ContentService = Depends(get_content_service),
) -> Page[VersionOut]:
    _, versions = await service.list_versions(niche.id, article_id)
    return Page[VersionOut](
        items=[VersionOut.model_validate(v) for v in versions],
        page=1,
        page_size=len(versions),
        total=len(versions),
    )
