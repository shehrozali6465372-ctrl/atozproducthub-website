"""Affiliate service — the business use cases of the affiliate module.

Owns: network/merchant/product catalog, product taxonomy, affiliate links,
signed link tokens, the server-controlled redirector, click attribution,
conversion webhook ingestion with idempotency, commission lifecycle,
reconciliation, and revenue summaries.

Never owns: AI behavior (product recommendation intelligence, copywriting,
feed curation, learning) — those belong to the AI OS and reach the website
only through the AI OS Bridge. No LLM/model SDK is used anywhere here.
"""

import hashlib
import json
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_affiliate_service.config import Settings
from atoz_affiliate_service.domain.commissions import (
    NETWORK_STATUS_TO_COMMISSION,
    can_transition,
)
from atoz_affiliate_service.domain.entities import (
    AffiliateClick,
    AffiliateLink,
    AffiliateMerchant,
    AffiliateNetwork,
    AffiliateNiche,
    AffiliateProduct,
    AffiliateWebhookLog,
    ClickAttribution,
    LinkToken,
    ProductCategory,
    ProductCategoryLink,
    RevenueReconciliation,
    RevenueSummary,
    RevenueTransaction,
)
from atoz_affiliate_service.domain.enums import (
    AffiliateLinkStatus,
    CommissionStatus,
    NetworkStatus,
    ProductStatus,
    WebhookEventStatus,
)
from atoz_affiliate_service.domain.events import (
    affiliate_click_event,
    product_removed_event,
    revenue_attributed_event,
)
from atoz_affiliate_service.domain.tokens import (
    new_signed_token,
    sign_token,
    token_from_signed,
    validate_signed_token,
)
from atoz_affiliate_service.domain.webhooks import (
    WebhookPayloadError,
    parse_conversion_payload,
    parse_envelope,
    verify_signature,
)
from atoz_affiliate_service.errors import (
    DuplicateError,
    NotFoundError,
    RedirectForbiddenError,
    ValidationError,
    WebhookRejectedError,
)
from atoz_affiliate_service.repositories import (
    AffiliateClickRepository,
    AffiliateLinkRepository,
    AffiliateMerchantRepository,
    AffiliateNetworkRepository,
    AffiliateNicheRepository,
    AffiliateProductRepository,
    AffiliateUnitOfWork,
    AffiliateWebhookLogRepository,
    ClickAttributionRepository,
    LinkTokenRepository,
    ProductCategoryLinkRepository,
    ProductCategoryRepository,
    RevenueReconciliationRepository,
    RevenueSummaryRepository,
    RevenueTransactionRepository,
)
from atoz_affiliate_service.uuids import uuid7
from atoz_backend_core.events.publisher import EventPublisher
from atoz_backend_core.slug import slugify

_REPOSITORY_FACTORIES: dict[str, Callable[[AsyncSession], object]] = {
    "affiliate_niches": AffiliateNicheRepository,
    "networks": AffiliateNetworkRepository,
    "merchants": AffiliateMerchantRepository,
    "products": AffiliateProductRepository,
    "categories": ProductCategoryRepository,
    "category_links": ProductCategoryLinkRepository,
    "links": AffiliateLinkRepository,
    "tokens": LinkTokenRepository,
    "attributions": ClickAttributionRepository,
    "clicks": AffiliateClickRepository,
    "revenue": RevenueTransactionRepository,
    "reconciliations": RevenueReconciliationRepository,
    "summaries": RevenueSummaryRepository,
    "webhook_logs": AffiliateWebhookLogRepository,
}


def _now() -> datetime:
    return datetime.now(UTC)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AffiliateService:
    """Aggregate the affiliate module use cases behind one facade."""

    def __init__(
        self,
        *,
        uow_factory: Callable[[], AffiliateUnitOfWork],
        event_publisher: EventPublisher,
        settings: Settings,
    ) -> None:
        self._uow_factory = uow_factory
        self._events = event_publisher
        self._settings = settings

    @staticmethod
    def build_uow(session_factory: async_sessionmaker[AsyncSession]) -> AffiliateUnitOfWork:
        """Build a UoW with the affiliate module repositories."""
        return AffiliateUnitOfWork(session_factory, repositories=dict(_REPOSITORY_FACTORIES))

    # ------------------------------------------------------ niche registry
    async def create_niche(
        self, *, name: str, slug: str | None, status: str = "draft"
    ) -> AffiliateNiche:
        desired = slug or slugify(name)
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            if await unit.affiliate_niches.slug_exists(desired):
                raise DuplicateError(f"Niche slug {desired!r} is already registered.")
            niche = AffiliateNiche(
                id=uuid7(),
                name=name,
                slug=desired,
                status=status,
            )
            await unit.affiliate_niches.add(niche)
            return niche

    async def update_niche(
        self, niche_id: str, *, name: str | None, slug: str | None, status: str | None
    ) -> AffiliateNiche:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            niche = await unit.affiliate_niches.get(niche_id)
            if niche is None:
                raise NotFoundError("Niche mirror not found.")
            if slug is not None and slug != niche.slug:
                if await unit.affiliate_niches.slug_exists(slug, exclude_id=niche_id):
                    raise DuplicateError(f"Niche slug {slug!r} is already registered.")
                niche.slug = slug
            if name is not None:
                niche.name = name
            if status is not None:
                niche.status = status
            return niche

    async def get_niche(self, niche_id: str) -> AffiliateNiche | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.affiliate_niches.get(niche_id)

    async def get_niche_by_slug(self, slug: str) -> AffiliateNiche | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.affiliate_niches.get_by_slug(slug)

    async def list_niches(self, *, status: str | None = None) -> Sequence[AffiliateNiche]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.affiliate_niches.list_by_status(status)

    # ------------------------------------------------------------- networks
    async def create_network(
        self,
        *,
        code: str,
        name: str,
        status: str = NetworkStatus.ACTIVE,
        feed_type: str = "csv",
        webhook_secret_ref: str = "",
        settings_json: str = "{}",
    ) -> AffiliateNetwork:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            if await unit.networks.code_exists(code):
                raise DuplicateError(f"Network code {code!r} is already registered.")
            network = AffiliateNetwork(
                id=uuid7(),
                code=code,
                name=name,
                status=status,
                feed_type=feed_type,
                webhook_secret_ref=webhook_secret_ref,
                settings_json=settings_json,
            )
            await unit.networks.add(network)
            return network

    async def update_network(
        self,
        network_id: str,
        *,
        name: str | None,
        status: str | None,
        feed_type: str | None,
        webhook_secret_ref: str | None,
        settings_json: str | None,
    ) -> AffiliateNetwork:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            network = await unit.networks.get(network_id)
            if network is None:
                raise NotFoundError("Network not found.")
            if name is not None:
                network.name = name
            if status is not None:
                network.status = status
            if feed_type is not None:
                network.feed_type = feed_type
            if webhook_secret_ref is not None:
                network.webhook_secret_ref = webhook_secret_ref
            if settings_json is not None:
                network.settings_json = settings_json
            return network

    async def get_network(self, network_id: str) -> AffiliateNetwork | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.networks.get(network_id)

    async def list_networks(self, *, status: str | None = None) -> Sequence[AffiliateNetwork]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.networks.list_by_status(status)

    # ------------------------------------------------------------- merchants
    async def create_merchant(
        self,
        *,
        network_id: str,
        remote_merchant_id: str,
        name: str,
        status: str = "active",
        commission_terms_json: str = "{}",
    ) -> AffiliateMerchant:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            network = await unit.networks.get(network_id)
            if network is None:
                raise ValidationError("Network does not exist.")
            if await unit.merchants.remote_exists(network_id, remote_merchant_id):
                raise DuplicateError(
                    f"Merchant {remote_merchant_id!r} already exists in this network."
                )
            merchant = AffiliateMerchant(
                id=uuid7(),
                network_id=network_id,
                remote_merchant_id=remote_merchant_id,
                name=name,
                status=status,
                commission_terms_json=commission_terms_json,
            )
            await unit.merchants.add(merchant)
            return merchant

    async def update_merchant(
        self,
        merchant_id: str,
        *,
        name: str | None,
        status: str | None,
        commission_terms_json: str | None,
    ) -> AffiliateMerchant:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            merchant = await unit.merchants.get(merchant_id)
            if merchant is None:
                raise NotFoundError("Merchant not found.")
            if name is not None:
                merchant.name = name
            if status is not None:
                merchant.status = status
            if commission_terms_json is not None:
                merchant.commission_terms_json = commission_terms_json
            return merchant

    async def get_merchant(self, merchant_id: str) -> AffiliateMerchant | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.merchants.get(merchant_id)

    async def list_merchants(self, *, network_id: str | None = None) -> Sequence[AffiliateMerchant]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            if network_id is not None:
                return await unit.merchants.list_by_network(network_id)
            return await unit.merchants.list()

    # --------------------------------------------------------- categories
    async def create_category(
        self,
        *,
        niche_id: str,
        name: str,
        slug: str | None,
        parent_id: str | None,
        sort_order: int,
        status: str,
    ) -> ProductCategory:
        desired = slug or slugify(name)
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            if await unit.categories.slug_exists(desired, niche_id=niche_id):
                raise DuplicateError(f"Category slug {desired!r} already exists in this niche.")
            if parent_id is not None:
                parent = await unit.categories.get_scoped(parent_id, niche_id=niche_id)
                if parent is None:
                    raise ValidationError("Parent category does not belong to the niche.")
            category = ProductCategory(
                id=uuid7(),
                niche_id=niche_id,
                parent_id=parent_id,
                name=name,
                slug=desired,
                path=parent_id or None,
                sort_order=sort_order,
                status=status,
            )
            await unit.categories.add(category)
            return category

    async def update_category(
        self,
        category_id: str,
        *,
        niche_id: str,
        name: str | None,
        slug: str | None,
        parent_id: str | None,
        sort_order: int | None,
        status: str | None,
    ) -> ProductCategory:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            category = await unit.categories.get_scoped(category_id, niche_id=niche_id)
            if category is None:
                raise NotFoundError("Category not found in this niche.")
            if slug is not None and slug != category.slug:
                if await unit.categories.slug_exists(
                    slug, niche_id=niche_id, exclude_id=category_id
                ):
                    raise DuplicateError(f"Category slug {slug!r} already exists in this niche.")
                category.slug = slug
            if name is not None:
                category.name = name
            if parent_id is not None:
                parent = await unit.categories.get_scoped(parent_id, niche_id=niche_id)
                if parent is None:
                    raise ValidationError("Parent category does not belong to the niche.")
                category.parent_id = parent_id
            if sort_order is not None:
                category.sort_order = sort_order
            if status is not None:
                category.status = status
            return category

    async def get_category(self, category_id: str, *, niche_id: str) -> ProductCategory | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.categories.get_scoped(category_id, niche_id=niche_id)

    async def list_categories(
        self, niche_id: str, *, status: str | None = None
    ) -> Sequence[ProductCategory]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.categories.list_by_niche(niche_id, status=status)

    # -------------------------------------------------------------- products
    async def create_product(
        self,
        *,
        niche_id: str,
        merchant_id: str,
        sku: str,
        name: str,
        slug: str | None,
        excerpt: str,
        description_ref: str | None,
        price_cents: int,
        currency: str,
        status: str,
        category_ids: Sequence[str],
        primary_category_id: str | None,
    ) -> AffiliateProduct:
        desired = slug or slugify(name)
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            merchant = await unit.merchants.get(merchant_id)
            if merchant is None:
                raise ValidationError("Merchant does not exist.")
            if await unit.products.sku_exists(sku, niche_id=niche_id, merchant_id=merchant_id):
                raise DuplicateError(
                    f"Product SKU {sku!r} already exists for this merchant in the niche."
                )
            if await unit.products.slug_exists(desired, niche_id=niche_id):
                raise DuplicateError(f"Product slug {desired!r} already exists in this niche.")
            await self._validate_taxonomy(
                unit,
                niche_id=niche_id,
                category_ids=category_ids,
                primary_category_id=primary_category_id,
            )
            if status == ProductStatus.ACTIVE:
                raise ValidationError(
                    "Create the product as a draft, add an affiliate link with "
                    "disclosure, then activate it."
                )
            product = AffiliateProduct(
                id=uuid7(),
                niche_id=niche_id,
                merchant_id=merchant_id,
                sku=sku,
                slug=desired,
                name=name,
                excerpt=excerpt,
                description_ref=description_ref,
                price_cents=price_cents,
                currency=currency or self._settings.default_currency,
                status=status,
                checksum=_sha256(f"{sku}:{name}"),
            )
            await unit.products.add(product)
            if category_ids:
                await unit.category_links.replace_for_product(
                    product.id,
                    niche_id=niche_id,
                    category_ids=category_ids,
                    primary_category_id=primary_category_id,
                )
            return product

    async def update_product(
        self,
        product_id: str,
        *,
        niche_id: str,
        merchant_id: str | None,
        sku: str | None,
        name: str | None,
        slug: str | None,
        excerpt: str | None,
        description_ref: str | None,
        price_cents: int | None,
        currency: str | None,
        status: str | None,
        category_ids: Sequence[str] | None,
        primary_category_id: str | None,
    ) -> AffiliateProduct:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            product = await unit.products.get_scoped(product_id, niche_id=niche_id)
            if product is None:
                raise NotFoundError("Product not found in this niche.")
            was_active = product.status == ProductStatus.ACTIVE
            if slug is not None and slug != product.slug:
                if was_active:
                    raise ValidationError(
                        "The product slug (public URL) cannot change while active."
                    )
                if await unit.products.slug_exists(slug, niche_id=niche_id, exclude_id=product_id):
                    raise DuplicateError(f"Product slug {slug!r} already exists in this niche.")
                product.slug = slug
            if sku is not None and sku != product.sku:
                new_merchant_id = merchant_id or product.merchant_id
                if await unit.products.sku_exists(
                    sku, niche_id=niche_id, merchant_id=new_merchant_id, exclude_id=product_id
                ):
                    raise DuplicateError(f"Product SKU {sku!r} already exists for this merchant.")
                product.sku = sku
            if merchant_id is not None:
                if await unit.merchants.get(merchant_id) is None:
                    raise ValidationError("Merchant does not exist.")
                product.merchant_id = merchant_id
            if name is not None:
                product.name = name
            if excerpt is not None:
                product.excerpt = excerpt
            if description_ref is not None:
                product.description_ref = description_ref
            if price_cents is not None:
                product.price_cents = price_cents
            if currency is not None:
                product.currency = currency
            if category_ids is not None:
                await self._validate_taxonomy(
                    unit,
                    niche_id=niche_id,
                    category_ids=category_ids,
                    primary_category_id=primary_category_id,
                )
                await unit.category_links.replace_for_product(
                    product.id,
                    niche_id=niche_id,
                    category_ids=category_ids,
                    primary_category_id=primary_category_id,
                )
            if status is not None and status != product.status:
                if status == ProductStatus.ACTIVE:
                    await self._require_disclosure_links(
                        unit, niche_id=niche_id, product_id=product.id
                    )
                product.status = status
                product.checksum = _sha256(f"{product.sku}:{product.name}:{product.status}")
            return product

    async def _require_disclosure_links(
        self, unit: AffiliateUnitOfWork, *, niche_id: str, product_id: str
    ) -> None:
        """Disclosure enforcement: a product cannot go public without an
        active affiliate link carrying required-disclosure metadata."""
        if not product_id:
            return
        links = await unit.links.active_disclosure_links_for_product(product_id, niche_id=niche_id)
        if not links:
            raise ValidationError(
                "Product cannot be activated without at least one active affiliate "
                "link with disclosure_required=true."
            )

    async def _validate_taxonomy(
        self,
        unit: AffiliateUnitOfWork,
        *,
        niche_id: str,
        category_ids: Sequence[str],
        primary_category_id: str | None,
    ) -> None:
        if primary_category_id is not None and primary_category_id not in set(category_ids):
            raise ValidationError("The primary category must be one of the product's categories.")
        for category_id in category_ids:
            category = await unit.categories.get_scoped(category_id, niche_id=niche_id)
            if category is None:
                raise ValidationError("Category does not belong to the requested niche.")

    async def get_product(self, product_id: str, *, niche_id: str) -> AffiliateProduct | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.products.get_scoped(product_id, niche_id=niche_id)

    async def list_products(
        self,
        niche_id: str,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[AffiliateProduct], int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            items = await unit.products.list_by_niche(
                niche_id, status=status, limit=page_size, offset=(page - 1) * page_size
            )
            total = await unit.products.count_by_niche(niche_id, status=status)
            return items, total

    async def delete_product(self, product_id: str, *, niche_id: str) -> None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            product = await unit.products.get_scoped(product_id, niche_id=niche_id)
            if product is None:
                raise NotFoundError("Product not found in this niche.")
            await unit.products.soft_delete(product)
            await self._events.publish(
                product_removed_event(product_id=product.id, niche_id=niche_id)
            )

    # ----------------------------------------------------------------- links
    async def create_link(
        self,
        *,
        niche_id: str,
        product_id: str,
        network_id: str,
        network_link_url: str,
        default_commission_rate: str,
        status: str,
        disclosure_required: bool,
    ) -> AffiliateLink:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            product = await unit.products.get_scoped(product_id, niche_id=niche_id)
            if product is None:
                raise ValidationError("Product does not belong to the requested niche.")
            network = await unit.networks.get(network_id)
            if network is None:
                raise ValidationError("Network does not exist.")
            existing = await unit.links.get_by_product_network(
                product_id, network_id, niche_id=niche_id
            )
            if existing is not None:
                raise DuplicateError("A link for this product and network already exists.")
            link = AffiliateLink(
                id=uuid7(),
                niche_id=niche_id,
                product_id=product_id,
                network_id=network_id,
                network_link_url=network_link_url,
                default_commission_rate=default_commission_rate,
                status=status,
                disclosure_required=disclosure_required,
            )
            await unit.links.add(link)
            if status == AffiliateLinkStatus.ACTIVE:
                await unit.tokens.add(
                    await self._build_token(unit, link, niche_id=niche_id, params=None)
                )
            return link

    async def update_link(
        self,
        link_id: str,
        *,
        niche_id: str,
        network_link_url: str | None,
        default_commission_rate: str | None,
        status: str | None,
        disclosure_required: bool | None,
    ) -> AffiliateLink:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            link = await unit.links.get_scoped(link_id, niche_id=niche_id)
            if link is None:
                raise NotFoundError("Affiliate link not found in this niche.")
            if network_link_url is not None:
                link.network_link_url = network_link_url
            if default_commission_rate is not None:
                link.default_commission_rate = default_commission_rate
            if disclosure_required is not None:
                link.disclosure_required = disclosure_required
            if status is not None and status != link.status:
                link.status = status
                if status == AffiliateLinkStatus.ACTIVE:
                    await unit.tokens.add(
                        await self._build_token(unit, link, niche_id=niche_id, params=None)
                    )
            return link

    async def _build_token(
        self,
        unit: AffiliateUnitOfWork,
        link: AffiliateLink,
        *,
        niche_id: str,
        params: dict[str, Any] | None,
    ) -> LinkToken:
        signed = new_signed_token(secret=self._settings.token_signing_secret)
        raw = token_from_signed(signed)
        while True:
            if not await unit.tokens.token_exists(raw, niche_id=niche_id):
                break
            signed = new_signed_token(secret=self._settings.token_signing_secret)
            raw = token_from_signed(signed)
        return LinkToken(
            id=uuid7(),
            niche_id=niche_id,
            affiliate_link_id=link.id,
            token=raw,
            destination_url=link.network_link_url,
            params_json=json.dumps(params or {}, sort_keys=True),
        )

    async def list_links(
        self, niche_id: str, *, status: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[AffiliateLink], int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            items = await unit.links.list_by_niche(
                niche_id, status=status, limit=page_size, offset=(page - 1) * page_size
            )
            total = len(await unit.links.list_by_niche(niche_id, status=status))
            return items, total

    async def create_token(
        self, link_id: str, *, niche_id: str, params: dict[str, Any] | None
    ) -> LinkToken:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            link = await unit.links.get_scoped(link_id, niche_id=niche_id)
            if link is None:
                raise NotFoundError("Affiliate link not found in this niche.")
            token = await self._build_token(unit, link, niche_id=niche_id, params=params)
            await unit.tokens.add(token)
            return token

    async def list_tokens(self, link_id: str, *, niche_id: str) -> Sequence[LinkToken]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.tokens.list_for_link(link_id, niche_id=niche_id)

    async def revoke_token(self, token_id: str, *, niche_id: str) -> LinkToken:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            token = await unit.tokens.get_scoped(token_id, niche_id=niche_id)
            if token is None:
                raise NotFoundError("Link token not found in this niche.")
            token.revoked_at = _now()
            return token

    # ------------------------------------------------- redirector (server-side)
    async def resolve_redirect(
        self,
        signed_token: str,
        *,
        request_ip: str | None = None,
        user_agent: str | None = None,
        referrer: str | None = None,
        source: str = "direct",
        campaign: str | None = None,
        utm_params: dict[str, str] | None = None,
        landing_url: str | None = None,
    ) -> tuple[str, bool, str]:
        """Validate a signed token, record the click, return the destination.

        Security: the destination URL comes from the stored token record —
        never from the browser. Invalid signatures, revoked/expired tokens,
        and disabled links all resolve to the same 404 (no state leak).
        """
        raw = validate_signed_token(signed_token, secret=self._settings.token_signing_secret)
        if raw is None:
            raise RedirectForbiddenError("Link not found or no longer available.")
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            token = await unit.tokens.get_by_token(raw)
            if token is None:
                raise RedirectForbiddenError("Link not found or no longer available.")
            if token.revoked_at is not None:
                raise RedirectForbiddenError("Link not found or no longer available.")
            if token.expires_at is not None and token.expires_at < _now():
                raise RedirectForbiddenError("Link not found or no longer available.")
            link = await unit.links.get_scoped(token.affiliate_link_id, niche_id=token.niche_id)
            if link is None or link.status != AffiliateLinkStatus.ACTIVE:
                raise RedirectForbiddenError("Link not found or no longer available.")
            attribution = ClickAttribution(
                id=uuid7(),
                niche_id=token.niche_id,
                source=source,
                campaign=campaign,
                utm_json=json.dumps(utm_params or {}, sort_keys=True),
                landing_url=landing_url,
            )
            await unit.attributions.add(attribution)
            click = AffiliateClick(
                id=uuid7(),
                niche_id=token.niche_id,
                link_token_id=token.id,
                attribution_id=attribution.id,
                ip_hash=_sha256(request_ip) if request_ip else None,
                user_agent_hash=_sha256(user_agent) if user_agent else None,
                referrer=referrer,
                is_bot=False,
                fraud_flag=False,
            )
            await unit.clicks.add(click)
        await self._events.publish(
            affiliate_click_event(
                click_id=click.id, link_token_id=token.id, niche_id=token.niche_id
            )
        )
        return link.network_link_url, link.disclosure_required, click.id

    # ----------------------------------------------------------------- clicks
    async def list_clicks(
        self, niche_id: str, *, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[AffiliateClick], int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            items = await unit.clicks.list_by_niche(
                niche_id, limit=page_size, offset=(page - 1) * page_size
            )
            total = await unit.clicks.count_by_niche(niche_id)
            return items, total

    # ------------------------------------------------------------ webhooks
    async def process_conversion(
        self, *, network_code: str, raw_body: bytes, signature: str
    ) -> tuple[RevenueTransaction | None, bool]:
        """Verify + ingest ``network.conversion`` webhooks (idempotent).

        Returns ``(transaction, duplicate)``; ``transaction`` is None for
        duplicates, ``duplicate=True`` when the event or conversion was
        already processed. Never creates duplicate commission records.
        """
        network = await self.get_network_by_code(network_code)
        if network is None or network.status != NetworkStatus.ACTIVE:
            raise WebhookRejectedError(f"Unknown or disabled network: {network_code}.")
        secret = self._settings.webhook_secrets.get(network.code, "")
        if not secret:
            raise WebhookRejectedError("No webhook secret configured for the network.")
        if not verify_signature(raw_body=raw_body, signature=signature, secret=secret):
            raise WebhookRejectedError("Invalid webhook signature.")
        try:
            envelope = parse_envelope(raw_body)
            payload = parse_conversion_payload(envelope["payload"])
        except WebhookPayloadError as exc:
            raise WebhookRejectedError(str(exc)) from exc

        uow = self._uow_factory()
        try:
            async with uow.transaction() as unit:
                existing_delivery = await unit.webhook_logs.get_by_source_event(
                    envelope["source"], envelope["event_id"]
                )
                if existing_delivery is not None:
                    existing_delivery.status = WebhookEventStatus.DUPLICATE
                    return None, True
                if payload["click_token"]:
                    raw = validate_signed_token(
                        payload["click_token"], secret=self._settings.token_signing_secret
                    )
                    if raw is None:
                        raise WebhookRejectedError("Conversion references an invalid click token.")
                    token = await unit.tokens.get_by_token(raw)
                    if token is None:
                        raise WebhookRejectedError("Conversion references an unknown click token.")
                    click = await self._latest_click_for_token(unit, token.id, token.niche_id)
                    link = await unit.links.get_scoped(
                        token.affiliate_link_id, niche_id=token.niche_id
                    )
                    if link is None:
                        raise WebhookRejectedError(
                            "Conversion references a link that no longer exists."
                        )
                    niche_id = token.niche_id
                    affiliate_link_id = link.id
                    affiliate_click_id = click.id if click else None
                else:
                    raise WebhookRejectedError(
                        "Conversion payload must include a valid click_token for attribution."
                    )

                amount_cents = payload["amount_cents"]
                gross_cents = payload["gross_cents"]
                if amount_cents > self._settings.max_commission_cents:
                    raise WebhookRejectedError("Commission amount exceeds the server-side limit.")
                if gross_cents > self._settings.max_gross_cents:
                    raise WebhookRejectedError("Gross amount exceeds the server-side limit.")

                commission_status = NETWORK_STATUS_TO_COMMISSION.get(
                    payload["status"], CommissionStatus.PENDING
                )

                existing = await unit.revenue.get_by_network_transaction(
                    network.id, payload["transaction_id"]
                )
                if existing is not None:
                    await self._log_webhook(
                        unit,
                        network=network,
                        niche_id=niche_id,
                        envelope=envelope,
                        status=WebhookEventStatus.DUPLICATE,
                    )
                    return None, True

                transaction = RevenueTransaction(
                    id=uuid7(),
                    niche_id=niche_id,
                    network_id=network.id,
                    affiliate_link_id=affiliate_link_id,
                    affiliate_click_id=affiliate_click_id,
                    network_transaction_id=payload["transaction_id"],
                    gross_cents=gross_cents,
                    commission_cents=amount_cents,
                    currency=payload["currency"],
                    status=commission_status,
                    occurred_at=payload["occurred_at"],
                )
                await unit.revenue.add(transaction)
                await unit.session.flush()
                await self._log_webhook(
                    unit,
                    network=network,
                    niche_id=niche_id,
                    envelope=envelope,
                    status=WebhookEventStatus.PROCESSED,
                )
        except IntegrityError:
            # Concurrent delivery: the ledger's
            # UNIQUE (network_id, network_transaction_id) constraint is the
            # hard idempotency guarantee — the whole transaction rolls back
            # (including the duplicate webhook log) and the second writer
            # loses cleanly.
            return None, True
        await self._events.publish(
            revenue_attributed_event(
                transaction_id=transaction.id,
                niche_id=transaction.niche_id,
                amount_cents=transaction.commission_cents,
                currency=transaction.currency,
            )
        )
        return transaction, False

    async def _latest_click_for_token(
        self, unit: AffiliateUnitOfWork, token_id: str, niche_id: str
    ) -> AffiliateClick | None:
        clicks = await unit.clicks.list_by_niche(niche_id, limit=1, link_token_id=token_id)
        return clicks[0] if clicks else None

    async def _log_webhook(
        self,
        unit: AffiliateUnitOfWork,
        *,
        network: AffiliateNetwork,
        niche_id: str | None,
        envelope: dict[str, Any],
        status: WebhookEventStatus,
        error: str | None = None,
    ) -> None:
        record = AffiliateWebhookLog(
            id=uuid7(),
            niche_id=niche_id,
            network_id=network.id,
            source=envelope["source"],
            event_id=envelope["event_id"],
            event_type=envelope["type"],
            status=status,
            payload_hash=hashlib.sha256(str(envelope["payload"]).encode()).hexdigest(),
            error=error,
        )
        await unit.webhook_logs.add(record)

    async def get_network_by_code(self, code: str) -> AffiliateNetwork | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.networks.get_by_code(code)

    # ----------------------------------------------------------- commissions
    async def list_revenue(
        self,
        niche_id: str,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RevenueTransaction], int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            items = await unit.revenue.list_by_niche(
                niche_id, status=status, limit=page_size, offset=(page - 1) * page_size
            )
            total = await unit.revenue.count_by_niche(niche_id, status=status)
            return items, total

    async def get_revenue(self, transaction_id: str, *, niche_id: str) -> RevenueTransaction | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.revenue.get_scoped(transaction_id, niche_id=niche_id)

    async def transition_commission(
        self, transaction_id: str, *, niche_id: str, action: str
    ) -> RevenueTransaction:
        target = {
            "approve": CommissionStatus.APPROVED,
            "reject": CommissionStatus.REJECTED,
            "mark_paid": CommissionStatus.PAID,
        }.get(action)
        if target is None:
            raise ValidationError(f"Unknown commission action: {action}.")
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            transaction = await unit.revenue.get_scoped(transaction_id, niche_id=niche_id)
            if transaction is None:
                raise NotFoundError("Revenue transaction not found in this niche.")
            current = CommissionStatus(transaction.status)
            if not can_transition(current, target):
                raise ValidationError(
                    f"Cannot move commission from {current.value!r} to {target.value!r}."
                )
            transaction.status = target
            if target == CommissionStatus.PAID:
                transaction.reconciled_at = _now()
            return transaction

    async def revenue_dashboard(self, niche_id: str) -> dict[str, int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            total = await unit.revenue.sum_commission_cents(niche_id)
            approved = await unit.revenue.sum_commission_cents(niche_id, status="approved")
            pending = await unit.revenue.sum_commission_cents(niche_id, status="pending")
            paid = await unit.revenue.sum_commission_cents(niche_id, status="paid")
            transaction_count = await unit.revenue.count_by_niche(niche_id)
            click_count = await unit.clicks.count_by_niche(niche_id)
            return {
                "total_commission_cents": total,
                "approved_commission_cents": approved,
                "pending_commission_cents": pending,
                "paid_commission_cents": paid,
                "transaction_count": transaction_count,
                "click_count": click_count,
            }

    # -------------------------------------------------------- reconciliation
    async def create_reconciliation(
        self,
        *,
        niche_id: str,
        network_id: str,
        reported_at: datetime,
        expected_total_cents: int,
        actual_total_cents: int,
        report_ref: str | None,
    ) -> RevenueReconciliation:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            network = await unit.networks.get(network_id)
            if network is None:
                raise ValidationError("Network does not exist.")
            delta = actual_total_cents - expected_total_cents
            status = "matched" if delta == 0 else "mismatch"
            reconciliation = RevenueReconciliation(
                id=uuid7(),
                niche_id=niche_id,
                network_id=network_id,
                reported_at=reported_at,
                expected_total_cents=expected_total_cents,
                actual_total_cents=actual_total_cents,
                delta_cents=delta,
                status=status,
                report_ref=report_ref,
            )
            await unit.reconciliations.add(reconciliation)
            return reconciliation

    async def list_reconciliations(
        self, niche_id: str, *, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[RevenueReconciliation], int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            items = await unit.reconciliations.list_by_niche(
                niche_id, limit=page_size, offset=(page - 1) * page_size
            )
            total = len(await unit.reconciliations.list_by_niche(niche_id))
            return items, total

    # ------------------------------------------------------- revenue summaries
    async def list_summaries(
        self, niche_id: str, *, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[RevenueSummary], int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            items = await unit.summaries.list_by_niche(
                niche_id, limit=page_size, offset=(page - 1) * page_size
            )
            total = len(await unit.summaries.list_by_niche(niche_id))
            return items, total

    async def rollup_summaries(self, niche_id: str, *, summary_date: str) -> RevenueSummary | None:
        """Compute the daily revenue read model from the ledgers."""
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            transactions = await unit.revenue.list_by_niche(niche_id, limit=10_000)
            clicks = await unit.clicks.count_by_niche(niche_id)
            sales = 0
            gross = 0
            commission = 0
            network_ids: set[str] = set()
            for transaction in transactions:
                occurred = transaction.occurred_at.astimezone(UTC).date().isoformat()
                if occurred != summary_date:
                    continue
                sales += 1
                gross += transaction.gross_cents
                commission += transaction.commission_cents
                network_ids.add(transaction.network_id)
            row = RevenueSummary(
                id=uuid7(),
                niche_id=niche_id,
                network_id=next(iter(network_ids), None),
                summary_date=summary_date,
                clicks=clicks,
                sales=sales,
                gross_cents=gross,
                commission_cents=commission,
                currency=self._settings.default_currency,
            )
            return await unit.summaries.upsert(niche_id, row.network_id, summary_date, row=row)

    # ------------------------------------------------------------ public reads
    async def list_public_products(
        self,
        niche_id: str,
        *,
        category_slug: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[AffiliateProduct], int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            if category_slug is not None:
                category = await unit.categories.get_by_slug(category_slug, niche_id=niche_id)
                if category is None or category.status != "active":
                    return [], 0
                links = await self._products_for_category(unit, category.id, niche_id=niche_id)
                product_ids = [link.product_id for link in links]
                products = await unit.products.list_by_niche(
                    niche_id, status="active", limit=page_size, offset=(page - 1) * page_size
                )
                products = [p for p in products if p.id in set(product_ids)]
                total = len(products)
                return products, total
            items = await unit.products.list_by_niche(
                niche_id, status="active", limit=page_size, offset=(page - 1) * page_size
            )
            total = await unit.products.count_by_niche(niche_id, status="active")
            return items, total

    async def _products_for_category(
        self, unit: AffiliateUnitOfWork, category_id: str, *, niche_id: str
    ) -> Sequence[ProductCategoryLink]:
        from sqlalchemy import select

        stmt = (
            select(ProductCategoryLink)
            .where(
                ProductCategoryLink.product_category_id == category_id,
                ProductCategoryLink.niche_id == niche_id,
            )
            .limit(10_000)
        )
        return (await unit.session.execute(stmt)).scalars().all()

    async def get_public_product(self, slug: str, *, niche_id: str) -> AffiliateProduct | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            product = await unit.products.get_by_slug(slug, niche_id=niche_id)
            if product is None or product.status != ProductStatus.ACTIVE:
                return None
            return product

    async def public_product_view(
        self, product: AffiliateProduct, *, niche_id: str
    ) -> dict[str, Any]:
        """Assemble the public product read model (disclosure + buy URL).

        The buy URL is always a server-controlled ``/go/{token}`` identifier
        resolved from the newest valid token of a disclosure-required active
        link — never a raw network URL, and never client-supplied.
        """
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            links = await unit.category_links.list_for_product(product.id, niche_id=niche_id)
            category = None
            for link in links:
                if link.is_primary:
                    category = await unit.categories.get_scoped(
                        link.product_category_id, niche_id=niche_id
                    )
                    break
            else:
                if links:
                    category = await unit.categories.get_scoped(
                        links[0].product_category_id, niche_id=niche_id
                    )
            merchant = await unit.merchants.get(product.merchant_id)
            disclosure_links = await unit.links.active_disclosure_links_for_product(
                product.id, niche_id=niche_id
            )
            network = None
            buy_url = None
            for aff_link in disclosure_links:
                network = await unit.networks.get(aff_link.network_id)
                if buy_url is None:
                    token = await unit.tokens.latest_valid_for_link(aff_link.id, niche_id=niche_id)
                    if token is not None:
                        buy_url = (
                            f"/api/v1/public/go/"
                            f"{sign_token(token.token, secret=self._settings.token_signing_secret)}"
                        )
            return {
                "category": category,
                "merchant": merchant,
                "network": network,
                "disclosure_required": bool(disclosure_links),
                "buy_url": buy_url,
            }
