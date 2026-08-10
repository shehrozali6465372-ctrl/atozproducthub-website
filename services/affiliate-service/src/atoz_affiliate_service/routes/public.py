"""Public Read API for the affiliate module (12-api-contracts.md §3-4).

Read-only, cacheable, published products/collections only, identified by
niche slug. The redirector (``/go/{token}``) is server-controlled: it
validates the signed token, records the click, and returns the stored
destination — the browser never supplies a URL.
"""

from fastapi import APIRouter, Depends, Request

from atoz_affiliate_service.domain.entities import AffiliateNiche
from atoz_affiliate_service.errors import NotFoundError
from atoz_affiliate_service.routes.deps import get_affiliate_service, resolve_public_niche
from atoz_affiliate_service.schemas import (
    Page,
    PublicCategoryOut,
    PublicGoOut,
    PublicProductOut,
)
from atoz_affiliate_service.services import AffiliateService

router = APIRouter(prefix="/api/v1/public", tags=["public-affiliate"])


@router.get(
    "/product-categories",
    summary="List active product categories for a niche",
    response_model=list[PublicCategoryOut],
)
async def list_categories(
    niche: AffiliateNiche = Depends(resolve_public_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> list[PublicCategoryOut]:
    categories = await service.list_categories(niche.id, status="active")
    return [PublicCategoryOut(slug=c.slug, name=c.name, path=c.path) for c in categories]


@router.get(
    "/products",
    summary="List active products (optional category filter)",
    response_model=Page[PublicProductOut],
)
async def list_products(
    niche: AffiliateNiche = Depends(resolve_public_niche),
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
    service: AffiliateService = Depends(get_affiliate_service),
) -> Page[PublicProductOut]:
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    items, total = await service.list_public_products(
        niche.id, category_slug=category, page=page, page_size=page_size
    )
    return Page[PublicProductOut](
        items=[await _public_product(service, niche.id, product) for product in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/products/{slug}",
    summary="Get an active product by slug",
    response_model=PublicProductOut,
)
async def get_product(
    slug: str,
    niche: AffiliateNiche = Depends(resolve_public_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> PublicProductOut:
    product = await service.get_public_product(slug, niche_id=niche.id)
    if product is None:
        raise NotFoundError("Product not found or not published.")
    return await _public_product(service, niche.id, product)


@router.get(
    "/collections/{slug}",
    summary="Products in a product category (affiliate collection page)",
    response_model=Page[PublicProductOut],
)
async def get_collection(
    slug: str,
    niche: AffiliateNiche = Depends(resolve_public_niche),
    page: int = 1,
    page_size: int = 20,
    service: AffiliateService = Depends(get_affiliate_service),
) -> Page[PublicProductOut]:
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    items, total = await service.list_public_products(
        niche.id, category_slug=slug, page=page, page_size=page_size
    )
    return Page[PublicProductOut](
        items=[await _public_product(service, niche.id, product) for product in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/go/{token}",
    summary="Resolve a signed affiliate link (server-controlled redirect)",
    response_model=PublicGoOut,
)
async def resolve_go(
    token: str,
    request: Request,
    service: AffiliateService = Depends(get_affiliate_service),
) -> PublicGoOut:
    utm: dict[str, str] = {}
    for key in ("utm_source", "utm_medium", "utm_campaign"):
        value = request.query_params.get(key)
        if value:
            utm[key] = value
    destination, disclosure_required, click_id = await service.resolve_redirect(
        token,
        request_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
        source=request.query_params.get("src", "direct"),
        campaign=request.query_params.get("utm_campaign"),
        utm_params=utm,
        landing_url=str(request.url),
    )
    return PublicGoOut(
        destination_url=destination,
        disclosure_required=disclosure_required,
        click_id=click_id,
    )


async def _public_product(service: AffiliateService, niche_id: str, product) -> PublicProductOut:
    view = await service.public_product_view(product, niche_id=niche_id)
    category = view["category"]
    merchant = view["merchant"]
    network = view["network"]
    return PublicProductOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        excerpt=product.excerpt,
        price_cents=product.price_cents,
        currency=product.currency,
        category=PublicCategoryOut(slug=category.slug, name=category.name, path=category.path)
        if category
        else None,
        merchant_name=merchant.name if merchant else "",
        network_name=network.name if network else "",
        disclosure_required=view["disclosure_required"],
        buy_url=view["buy_url"],
    )
