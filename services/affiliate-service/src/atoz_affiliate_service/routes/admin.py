"""Admin API for the affiliate module.

Mirrors the Admin API conventions (12-api-contracts.md §5): Bearer JWT with
``affiliate:read`` / ``affiliate:write`` RBAC claims and a mandatory
``X-Niche-Id`` tenancy header on every niche-scoped route. Networks and
merchants are global reference tables and only need the RBAC claim.
"""

from fastapi import APIRouter, Depends, Request, Response, status

from atoz_affiliate_service.domain.entities import AffiliateNiche
from atoz_affiliate_service.domain.tokens import sign_token
from atoz_affiliate_service.errors import NotFoundError
from atoz_affiliate_service.routes.deps import (
    get_affiliate_service,
    require_niche,
    require_permission,
)
from atoz_affiliate_service.schemas import (
    AffiliateClickOut,
    AffiliateLinkCreate,
    AffiliateLinkOut,
    AffiliateLinkUpdate,
    CommissionTransitionRequest,
    LinkTokenCreateOut,
    LinkTokenOut,
    MerchantCreate,
    MerchantOut,
    MerchantUpdate,
    NetworkCreate,
    NetworkOut,
    NetworkUpdate,
    NicheMirrorCreate,
    NicheMirrorUpdate,
    Page,
    ProductCategoryCreate,
    ProductCategoryOut,
    ProductCategoryUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    ReconciliationCreate,
    ReconciliationOut,
    RevenueDashboardOut,
    RevenueSummaryOut,
    RevenueTransactionOut,
)
from atoz_affiliate_service.services import AffiliateService
from atoz_backend_core.auth import TokenClaims

router = APIRouter(prefix="/api/v1/admin", tags=["admin-affiliate"])

READ = require_permission("affiliate:read")
WRITE = require_permission("affiliate:write")


# ------------------------------------------------------- niche registry mirror
@router.get("/niches", summary="List affiliate tenancy mirror niches")
async def list_niches(
    _claims: TokenClaims = Depends(READ),
    service: AffiliateService = Depends(get_affiliate_service),
):
    niches = await service.list_niches()
    return [{"id": n.id, "slug": n.slug, "name": n.name, "status": n.status} for n in niches]


@router.post("/niches", summary="Provision the local tenancy mirror niche", status_code=201)
async def create_niche(
    payload: NicheMirrorCreate,
    _claims: TokenClaims = Depends(WRITE),
    service: AffiliateService = Depends(get_affiliate_service),
):
    niche = await service.create_niche(name=payload.name, slug=payload.slug, status=payload.status)
    return {"id": niche.id, "slug": niche.slug, "name": niche.name, "status": niche.status}


@router.patch("/niches/{niche_id}", summary="Update the local tenancy mirror niche")
async def update_niche(
    niche_id: str,
    payload: NicheMirrorUpdate,
    _claims: TokenClaims = Depends(WRITE),
    service: AffiliateService = Depends(get_affiliate_service),
):
    niche = await service.update_niche(
        niche_id, name=payload.name, slug=payload.slug, status=payload.status
    )
    return {"id": niche.id, "slug": niche.slug, "name": niche.name, "status": niche.status}


# --------------------------------------------------------------- networks
@router.get("/networks", summary="List affiliate networks", response_model=list[NetworkOut])
async def list_networks(
    _claims: TokenClaims = Depends(READ),
    service: AffiliateService = Depends(get_affiliate_service),
) -> list[NetworkOut]:
    return [NetworkOut.model_validate(n) for n in await service.list_networks()]


@router.post(
    "/networks", summary="Register an affiliate network", response_model=NetworkOut, status_code=201
)
async def create_network(
    payload: NetworkCreate,
    _claims: TokenClaims = Depends(WRITE),
    service: AffiliateService = Depends(get_affiliate_service),
) -> NetworkOut:
    network = await service.create_network(
        code=payload.code,
        name=payload.name,
        status=payload.status,
        feed_type=payload.feed_type,
        webhook_secret_ref=payload.webhook_secret_ref,
        settings_json=payload.settings_json,
    )
    return NetworkOut.model_validate(network)


@router.patch(
    "/networks/{network_id}", summary="Update an affiliate network", response_model=NetworkOut
)
async def update_network(
    network_id: str,
    payload: NetworkUpdate,
    _claims: TokenClaims = Depends(WRITE),
    service: AffiliateService = Depends(get_affiliate_service),
) -> NetworkOut:
    network = await service.update_network(
        network_id,
        name=payload.name,
        status=payload.status,
        feed_type=payload.feed_type,
        webhook_secret_ref=payload.webhook_secret_ref,
        settings_json=payload.settings_json,
    )
    return NetworkOut.model_validate(network)


# --------------------------------------------------------------- merchants
@router.get("/merchants", summary="List affiliate merchants", response_model=list[MerchantOut])
async def list_merchants(
    _claims: TokenClaims = Depends(READ),
    network_id: str | None = None,
    service: AffiliateService = Depends(get_affiliate_service),
) -> list[MerchantOut]:
    return [
        MerchantOut.model_validate(m) for m in await service.list_merchants(network_id=network_id)
    ]


@router.post(
    "/merchants", summary="Register a merchant", response_model=MerchantOut, status_code=201
)
async def create_merchant(
    payload: MerchantCreate,
    _claims: TokenClaims = Depends(WRITE),
    service: AffiliateService = Depends(get_affiliate_service),
) -> MerchantOut:
    merchant = await service.create_merchant(
        network_id=payload.network_id,
        remote_merchant_id=payload.remote_merchant_id,
        name=payload.name,
        status=payload.status,
        commission_terms_json=payload.commission_terms_json,
    )
    return MerchantOut.model_validate(merchant)


@router.patch("/merchants/{merchant_id}", summary="Update a merchant", response_model=MerchantOut)
async def update_merchant(
    merchant_id: str,
    payload: MerchantUpdate,
    _claims: TokenClaims = Depends(WRITE),
    service: AffiliateService = Depends(get_affiliate_service),
) -> MerchantOut:
    merchant = await service.update_merchant(
        merchant_id,
        name=payload.name,
        status=payload.status,
        commission_terms_json=payload.commission_terms_json,
    )
    return MerchantOut.model_validate(merchant)


# ------------------------------------------------------------ product categories
@router.get(
    "/product-categories",
    summary="List niche product categories",
    response_model=list[ProductCategoryOut],
)
async def list_categories(
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> list[ProductCategoryOut]:
    return [ProductCategoryOut.model_validate(c) for c in await service.list_categories(niche.id)]


@router.post(
    "/product-categories",
    summary="Create a niche product category",
    response_model=ProductCategoryOut,
    status_code=201,
)
async def create_category(
    payload: ProductCategoryCreate,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> ProductCategoryOut:
    category = await service.create_category(
        niche_id=niche.id,
        name=payload.name,
        slug=payload.slug,
        parent_id=payload.parent_id,
        sort_order=payload.sort_order,
        status=payload.status,
    )
    return ProductCategoryOut.model_validate(category)


@router.patch(
    "/product-categories/{category_id}",
    summary="Update a niche product category",
    response_model=ProductCategoryOut,
)
async def update_category(
    category_id: str,
    payload: ProductCategoryUpdate,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> ProductCategoryOut:
    category = await service.update_category(
        category_id,
        niche_id=niche.id,
        name=payload.name,
        slug=payload.slug,
        parent_id=payload.parent_id,
        sort_order=payload.sort_order,
        status=payload.status,
    )
    return ProductCategoryOut.model_validate(category)


# ---------------------------------------------------------------- products
@router.get("/products", summary="List niche products", response_model=Page[ProductOut])
async def list_products(
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    service: AffiliateService = Depends(get_affiliate_service),
) -> Page[ProductOut]:
    items, total = await service.list_products(
        niche.id, status=status_filter, page=page, page_size=page_size
    )
    return Page[ProductOut](
        items=[ProductOut.model_validate(p) for p in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/products", summary="Create a product (draft)", response_model=ProductOut, status_code=201
)
async def create_product(
    payload: ProductCreate,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> ProductOut:
    product = await service.create_product(
        niche_id=niche.id,
        merchant_id=payload.merchant_id,
        sku=payload.sku,
        name=payload.name,
        slug=payload.slug,
        excerpt=payload.excerpt,
        description_ref=payload.description_ref,
        price_cents=payload.price_cents,
        currency=payload.currency,
        status=payload.status,
        category_ids=payload.category_ids,
        primary_category_id=payload.primary_category_id,
    )
    return ProductOut.model_validate(product)


@router.get(
    "/products/{product_id}", summary="Get a product (detail view)", response_model=ProductOut
)
async def get_product(
    product_id: str,
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> ProductOut:
    product = await service.get_product(product_id, niche_id=niche.id)
    if product is None:
        raise NotFoundError("Product not found.")
    return ProductOut.model_validate(product)


@router.patch("/products/{product_id}", summary="Update a product", response_model=ProductOut)
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> ProductOut:
    product = await service.update_product(
        product_id,
        niche_id=niche.id,
        merchant_id=payload.merchant_id,
        sku=payload.sku,
        name=payload.name,
        slug=payload.slug,
        excerpt=payload.excerpt,
        description_ref=payload.description_ref,
        price_cents=payload.price_cents,
        currency=payload.currency,
        status=payload.status,
        category_ids=payload.category_ids,
        primary_category_id=payload.primary_category_id,
    )
    return ProductOut.model_validate(product)


@router.delete("/products/{product_id}", summary="Soft-delete a product", status_code=204)
async def delete_product(
    product_id: str,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> Response:
    await service.delete_product(product_id, niche_id=niche.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ links
@router.get("/links", summary="List niche affiliate links", response_model=Page[AffiliateLinkOut])
async def list_links(
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    service: AffiliateService = Depends(get_affiliate_service),
) -> Page[AffiliateLinkOut]:
    items, total = await service.list_links(
        niche.id, status=status_filter, page=page, page_size=page_size
    )
    return Page[AffiliateLinkOut](
        items=[AffiliateLinkOut.model_validate(link) for link in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/links",
    summary="Create an affiliate link (auto token)",
    response_model=AffiliateLinkOut,
    status_code=201,
)
async def create_link(
    payload: AffiliateLinkCreate,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> AffiliateLinkOut:
    link = await service.create_link(
        niche_id=niche.id,
        product_id=payload.product_id,
        network_id=payload.network_id,
        network_link_url=payload.network_link_url,
        default_commission_rate=payload.default_commission_rate,
        status=payload.status,
        disclosure_required=payload.disclosure_required,
    )
    return AffiliateLinkOut.model_validate(link)


@router.patch(
    "/links/{link_id}", summary="Update an affiliate link", response_model=AffiliateLinkOut
)
async def update_link(
    link_id: str,
    payload: AffiliateLinkUpdate,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> AffiliateLinkOut:
    link = await service.update_link(
        link_id,
        niche_id=niche.id,
        network_link_url=payload.network_link_url,
        default_commission_rate=payload.default_commission_rate,
        status=payload.status,
        disclosure_required=payload.disclosure_required,
    )
    return AffiliateLinkOut.model_validate(link)


# ------------------------------------------------------------------ tokens
@router.get(
    "/links/{link_id}/tokens",
    summary="List link tokens for an affiliate link",
    response_model=list[LinkTokenOut],
)
async def list_tokens(
    link_id: str,
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> list[LinkTokenOut]:
    return [
        LinkTokenOut.model_validate(t)
        for t in await service.list_tokens(link_id, niche_id=niche.id)
    ]


@router.post(
    "/links/{link_id}/tokens",
    summary="Issue a new signed link token",
    response_model=LinkTokenCreateOut,
    status_code=201,
)
async def create_token(
    link_id: str,
    request: Request,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> LinkTokenCreateOut:
    token = await service.create_token(link_id, niche_id=niche.id, params=None)
    signing_secret = request.app.state.settings.token_signing_secret
    return LinkTokenCreateOut(
        token=token.token,
        go_url=f"/api/v1/public/go/{sign_token(token.token, secret=signing_secret)}",
    )


@router.post(
    "/tokens/{token_id}/revoke", summary="Revoke a link token", response_model=LinkTokenOut
)
async def revoke_token(
    token_id: str,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> LinkTokenOut:
    token = await service.revoke_token(token_id, niche_id=niche.id)
    return LinkTokenOut.model_validate(token)


# ------------------------------------------------------------------ clicks
@router.get("/clicks", summary="List niche click ledger", response_model=Page[AffiliateClickOut])
async def list_clicks(
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    page: int = 1,
    page_size: int = 20,
    service: AffiliateService = Depends(get_affiliate_service),
) -> Page[AffiliateClickOut]:
    items, total = await service.list_clicks(niche.id, page=page, page_size=page_size)
    return Page[AffiliateClickOut](
        items=[AffiliateClickOut.model_validate(c) for c in items],
        page=page,
        page_size=page_size,
        total=total,
    )


# -------------------------------------------------------- revenue/commissions
@router.get(
    "/revenue/dashboard",
    summary="Revenue summary for the niche",
    response_model=RevenueDashboardOut,
)
async def revenue_dashboard(
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> RevenueDashboardOut:
    return RevenueDashboardOut(**await service.revenue_dashboard(niche.id))


@router.get(
    "/revenue",
    summary="List niche revenue transactions",
    response_model=Page[RevenueTransactionOut],
)
async def list_revenue(
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    service: AffiliateService = Depends(get_affiliate_service),
) -> Page[RevenueTransactionOut]:
    items, total = await service.list_revenue(
        niche.id, status=status_filter, page=page, page_size=page_size
    )
    return Page[RevenueTransactionOut](
        items=[RevenueTransactionOut.model_validate(t) for t in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/revenue/{transaction_id}",
    summary="Get a revenue transaction",
    response_model=RevenueTransactionOut,
)
async def get_revenue(
    transaction_id: str,
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> RevenueTransactionOut:
    transaction = await service.get_revenue(transaction_id, niche_id=niche.id)
    if transaction is None:
        raise NotFoundError("Revenue transaction not found.")
    return RevenueTransactionOut.model_validate(transaction)


@router.post(
    "/revenue/{transaction_id}/transition",
    summary="Transition a commission (approve/reject/mark_paid)",
    response_model=RevenueTransactionOut,
)
async def transition_commission(
    transaction_id: str,
    payload: CommissionTransitionRequest,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> RevenueTransactionOut:
    transaction = await service.transition_commission(
        transaction_id, niche_id=niche.id, action=payload.action
    )
    return RevenueTransactionOut.model_validate(transaction)


# ------------------------------------------------------------- reconciliation
@router.get(
    "/reconciliations", summary="List niche reconciliations", response_model=Page[ReconciliationOut]
)
async def list_reconciliations(
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    page: int = 1,
    page_size: int = 20,
    service: AffiliateService = Depends(get_affiliate_service),
) -> Page[ReconciliationOut]:
    items, total = await service.list_reconciliations(niche.id, page=page, page_size=page_size)
    return Page[ReconciliationOut](
        items=[ReconciliationOut.model_validate(r) for r in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/reconciliations",
    summary="Record a reconciliation run",
    response_model=ReconciliationOut,
    status_code=201,
)
async def create_reconciliation(
    payload: ReconciliationCreate,
    _claims: TokenClaims = Depends(WRITE),
    niche: AffiliateNiche = Depends(require_niche),
    service: AffiliateService = Depends(get_affiliate_service),
) -> ReconciliationOut:
    reconciliation = await service.create_reconciliation(
        niche_id=niche.id,
        network_id=payload.network_id,
        reported_at=payload.reported_at,
        expected_total_cents=payload.expected_total_cents,
        actual_total_cents=payload.actual_total_cents,
        report_ref=payload.report_ref,
    )
    return ReconciliationOut.model_validate(reconciliation)


# ------------------------------------------------------------ revenue summaries
@router.get(
    "/revenue-summaries",
    summary="List niche daily revenue summaries",
    response_model=Page[RevenueSummaryOut],
)
async def list_summaries(
    _claims: TokenClaims = Depends(READ),
    niche: AffiliateNiche = Depends(require_niche),
    page: int = 1,
    page_size: int = 20,
    service: AffiliateService = Depends(get_affiliate_service),
) -> Page[RevenueSummaryOut]:
    items, total = await service.list_summaries(niche.id, page=page, page_size=page_size)
    return Page[RevenueSummaryOut](
        items=[RevenueSummaryOut.model_validate(s) for s in items],
        page=page,
        page_size=page_size,
        total=total,
    )
