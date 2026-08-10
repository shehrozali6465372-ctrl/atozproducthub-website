"""Repository layer for the affiliate module.

Extends ``atoz_backend_core.repositories`` and enforces the Database
Blueprint tenancy rules: every business query is scoped by ``niche_id``.
Networks/merchants are global reference tables (blueprint §5.8–5.9);
products, categories, links, tokens, clicks, and revenue records are
niche-scoped. Ledgers are append-only: they expose ``add``/``list`` and
read-only lookups, never update/delete paths.
"""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from sqlalchemy import func, select

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
from atoz_affiliate_service.uuids import uuid7
from atoz_backend_core.repositories import SqlAlchemyRepository, SqlAlchemyUnitOfWork


def _utcnow() -> datetime:
    return datetime.now(UTC)


class AffiliateNicheRepository(SqlAlchemyRepository[AffiliateNiche, str]):
    """Local tenant-registry mirror (ADR-0005) — the affiliate tenancy root."""

    model = AffiliateNiche

    async def get_by_slug(self, slug: str) -> AffiliateNiche | None:
        result = await self._session.scalars(
            select(AffiliateNiche).where(AffiliateNiche.slug == slug)
        )
        return result.first()

    async def slug_exists(self, slug: str, *, exclude_id: str | None = None) -> bool:
        stmt = select(AffiliateNiche.id).where(AffiliateNiche.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(AffiliateNiche.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_status(self, status: str | None = None) -> Sequence[AffiliateNiche]:
        stmt = select(AffiliateNiche).order_by(AffiliateNiche.name)
        if status is not None:
            stmt = stmt.where(AffiliateNiche.status == status)
        return (await self._session.scalars(stmt)).all()


class AffiliateNetworkRepository(SqlAlchemyRepository[AffiliateNetwork, str]):
    """Networks are a global reference table — not niche-scoped."""

    model = AffiliateNetwork

    async def get_by_code(self, code: str) -> AffiliateNetwork | None:
        result = await self._session.scalars(
            select(AffiliateNetwork).where(AffiliateNetwork.code == code)
        )
        return result.first()

    async def code_exists(self, code: str, *, exclude_id: str | None = None) -> bool:
        stmt = select(AffiliateNetwork.id).where(AffiliateNetwork.code == code)
        if exclude_id is not None:
            stmt = stmt.where(AffiliateNetwork.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_status(self, status: str | None = None) -> Sequence[AffiliateNetwork]:
        stmt = select(AffiliateNetwork).order_by(AffiliateNetwork.name)
        if status is not None:
            stmt = stmt.where(AffiliateNetwork.status == status)
        return (await self._session.scalars(stmt)).all()


class AffiliateMerchantRepository(SqlAlchemyRepository[AffiliateMerchant, str]):
    """Merchants are a global reference table within networks."""

    model = AffiliateMerchant

    async def get_by_remote(
        self, network_id: str, remote_merchant_id: str
    ) -> AffiliateMerchant | None:
        result = await self._session.scalars(
            select(AffiliateMerchant).where(
                AffiliateMerchant.network_id == network_id,
                AffiliateMerchant.remote_merchant_id == remote_merchant_id,
            )
        )
        return result.first()

    async def remote_exists(
        self, network_id: str, remote_merchant_id: str, *, exclude_id: str | None = None
    ) -> bool:
        stmt = select(AffiliateMerchant.id).where(
            AffiliateMerchant.network_id == network_id,
            AffiliateMerchant.remote_merchant_id == remote_merchant_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(AffiliateMerchant.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_network(self, network_id: str) -> Sequence[AffiliateMerchant]:
        stmt = (
            select(AffiliateMerchant)
            .where(AffiliateMerchant.network_id == network_id)
            .order_by(AffiliateMerchant.name)
        )
        return (await self._session.scalars(stmt)).all()


class AffiliateProductRepository(SqlAlchemyRepository[AffiliateProduct, str]):
    """Products are niche-scoped; every query carries ``niche_id``."""

    model = AffiliateProduct

    async def get_scoped(self, product_id: str, *, niche_id: str) -> AffiliateProduct | None:
        stmt = select(AffiliateProduct).where(
            AffiliateProduct.id == product_id,
            AffiliateProduct.niche_id == niche_id,
            AffiliateProduct.deleted_at.is_(None),
        )
        return (await self._session.scalars(stmt)).first()

    async def get_by_slug(
        self, slug: str, *, niche_id: str, include_deleted: bool = False
    ) -> AffiliateProduct | None:
        stmt = select(AffiliateProduct).where(
            AffiliateProduct.slug == slug, AffiliateProduct.niche_id == niche_id
        )
        if not include_deleted:
            stmt = stmt.where(AffiliateProduct.deleted_at.is_(None))
        return (await self._session.scalars(stmt)).first()

    async def slug_exists(self, slug: str, *, niche_id: str, exclude_id: str | None = None) -> bool:
        stmt = select(AffiliateProduct.id).where(
            AffiliateProduct.slug == slug, AffiliateProduct.niche_id == niche_id
        )
        if exclude_id is not None:
            stmt = stmt.where(AffiliateProduct.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def sku_exists(
        self, sku: str, *, niche_id: str, merchant_id: str, exclude_id: str | None = None
    ) -> bool:
        stmt = select(AffiliateProduct.id).where(
            AffiliateProduct.sku == sku,
            AffiliateProduct.niche_id == niche_id,
            AffiliateProduct.merchant_id == merchant_id,
        )
        if exclude_id is not None:
            stmt = stmt.where(AffiliateProduct.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_niche(
        self,
        niche_id: str,
        *,
        status: str | None = None,
        merchant_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[AffiliateProduct]:
        stmt = (
            select(AffiliateProduct)
            .where(AffiliateProduct.niche_id == niche_id, AffiliateProduct.deleted_at.is_(None))
            .order_by(AffiliateProduct.updated_at.desc())
        )
        if status is not None:
            stmt = stmt.where(AffiliateProduct.status == status)
        if merchant_id is not None:
            stmt = stmt.where(AffiliateProduct.merchant_id == merchant_id)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_by_niche(self, niche_id: str, *, status: str | None = None) -> int:
        stmt = select(func.count(AffiliateProduct.id)).where(
            AffiliateProduct.niche_id == niche_id, AffiliateProduct.deleted_at.is_(None)
        )
        if status is not None:
            stmt = stmt.where(AffiliateProduct.status == status)
        return int((await self._session.execute(stmt)).scalar_one())

    async def soft_delete(self, product: AffiliateProduct) -> None:
        product.deleted_at = _utcnow()
        if product.status == "active":
            product.status = "disabled"


class ProductCategoryRepository(SqlAlchemyRepository[ProductCategory, str]):
    """Product taxonomy categories are niche-scoped."""

    model = ProductCategory

    async def get_scoped(self, category_id: str, *, niche_id: str) -> ProductCategory | None:
        result = await self._session.scalars(
            select(ProductCategory).where(
                ProductCategory.id == category_id, ProductCategory.niche_id == niche_id
            )
        )
        return result.first()

    async def get_by_slug(self, slug: str, *, niche_id: str) -> ProductCategory | None:
        result = await self._session.scalars(
            select(ProductCategory).where(
                ProductCategory.slug == slug, ProductCategory.niche_id == niche_id
            )
        )
        return result.first()

    async def slug_exists(self, slug: str, *, niche_id: str, exclude_id: str | None = None) -> bool:
        stmt = select(ProductCategory.id).where(
            ProductCategory.slug == slug, ProductCategory.niche_id == niche_id
        )
        if exclude_id is not None:
            stmt = stmt.where(ProductCategory.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_niche(
        self, niche_id: str, *, status: str | None = None
    ) -> Sequence[ProductCategory]:
        stmt = (
            select(ProductCategory)
            .where(ProductCategory.niche_id == niche_id)
            .order_by(ProductCategory.sort_order, ProductCategory.name)
        )
        if status is not None:
            stmt = stmt.where(ProductCategory.status == status)
        return (await self._session.scalars(stmt)).all()

    async def list_ids(self, category_ids: Sequence[str], *, niche_id: str) -> Sequence[str]:
        stmt = select(ProductCategory.id).where(
            ProductCategory.id.in_(category_ids), ProductCategory.niche_id == niche_id
        )
        return list((await self._session.scalars(stmt)).all())


class ProductCategoryLinkRepository(SqlAlchemyRepository[ProductCategoryLink, str]):
    """Niche-scoped link table between products and product categories."""

    model = ProductCategoryLink

    async def list_for_product(
        self, product_id: str, *, niche_id: str
    ) -> Sequence[ProductCategoryLink]:
        stmt = select(ProductCategoryLink).where(
            ProductCategoryLink.product_id == product_id,
            ProductCategoryLink.niche_id == niche_id,
        )
        return (await self._session.scalars(stmt)).all()

    async def replace_for_product(
        self,
        product_id: str,
        *,
        niche_id: str,
        category_ids: Sequence[str],
        primary_category_id: str | None,
    ) -> None:
        from sqlalchemy import delete

        await self._session.execute(
            delete(ProductCategoryLink).where(
                ProductCategoryLink.product_id == product_id,
                ProductCategoryLink.niche_id == niche_id,
            )
        )
        for category_id in category_ids:
            self._session.add(
                ProductCategoryLink(
                    id=uuid7(),
                    niche_id=niche_id,
                    product_id=product_id,
                    product_category_id=category_id,
                    is_primary=category_id == primary_category_id,
                )
            )


class AffiliateLinkRepository(SqlAlchemyRepository[AffiliateLink, str]):
    """Affiliate link registrations are niche-scoped."""

    model = AffiliateLink

    async def get_scoped(self, link_id: str, *, niche_id: str) -> AffiliateLink | None:
        result = await self._session.scalars(
            select(AffiliateLink).where(
                AffiliateLink.id == link_id, AffiliateLink.niche_id == niche_id
            )
        )
        return result.first()

    async def get_by_product_network(
        self, product_id: str, network_id: str, *, niche_id: str
    ) -> AffiliateLink | None:
        result = await self._session.scalars(
            select(AffiliateLink).where(
                AffiliateLink.product_id == product_id,
                AffiliateLink.network_id == network_id,
                AffiliateLink.niche_id == niche_id,
            )
        )
        return result.first()

    async def list_for_product(self, product_id: str, *, niche_id: str) -> Sequence[AffiliateLink]:
        stmt = select(AffiliateLink).where(
            AffiliateLink.product_id == product_id, AffiliateLink.niche_id == niche_id
        )
        return (await self._session.scalars(stmt)).all()

    async def list_by_niche(
        self, niche_id: str, *, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> Sequence[AffiliateLink]:
        stmt = (
            select(AffiliateLink)
            .where(AffiliateLink.niche_id == niche_id)
            .order_by(AffiliateLink.updated_at.desc())
        )
        if status is not None:
            stmt = stmt.where(AffiliateLink.status == status)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_active_for_product(self, product_id: str, *, niche_id: str) -> int:
        stmt = select(func.count(AffiliateLink.id)).where(
            AffiliateLink.product_id == product_id,
            AffiliateLink.niche_id == niche_id,
            AffiliateLink.status == "active",
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def active_disclosure_links_for_product(
        self, product_id: str, *, niche_id: str
    ) -> Sequence[AffiliateLink]:
        stmt = select(AffiliateLink).where(
            AffiliateLink.product_id == product_id,
            AffiliateLink.niche_id == niche_id,
            AffiliateLink.status == "active",
            AffiliateLink.disclosure_required.is_(True),
        )
        return (await self._session.scalars(stmt)).all()


class LinkTokenRepository(SqlAlchemyRepository[LinkToken, str]):
    """Link tokens are niche-scoped; lookup is by the opaque random id."""

    model = LinkToken

    async def get_scoped(self, token_id: str, *, niche_id: str) -> LinkToken | None:
        result = await self._session.scalars(
            select(LinkToken).where(LinkToken.id == token_id, LinkToken.niche_id == niche_id)
        )
        return result.first()

    async def get_by_token(self, token: str) -> LinkToken | None:
        result = await self._session.scalars(select(LinkToken).where(LinkToken.token == token))
        return result.first()

    async def token_exists(self, token: str, *, niche_id: str) -> bool:
        stmt = select(LinkToken.id).where(LinkToken.token == token, LinkToken.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_for_link(
        self, affiliate_link_id: str, *, niche_id: str, limit: int = 100, offset: int = 0
    ) -> Sequence[LinkToken]:
        stmt = (
            select(LinkToken)
            .where(LinkToken.affiliate_link_id == affiliate_link_id, LinkToken.niche_id == niche_id)
            .order_by(LinkToken.created_at.desc())
        )
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def latest_valid_for_link(
        self, affiliate_link_id: str, *, niche_id: str
    ) -> LinkToken | None:
        stmt = (
            select(LinkToken)
            .where(
                LinkToken.affiliate_link_id == affiliate_link_id,
                LinkToken.niche_id == niche_id,
                LinkToken.revoked_at.is_(None),
            )
            .order_by(LinkToken.created_at.desc())
        )
        return (await self._session.scalars(stmt)).first()


class ClickAttributionRepository(SqlAlchemyRepository[ClickAttribution, str]):
    """Append-only attribution records (niche-scoped)."""

    model = ClickAttribution

    async def get_scoped(self, attribution_id: str, *, niche_id: str) -> ClickAttribution | None:
        result = await self._session.scalars(
            select(ClickAttribution).where(
                ClickAttribution.id == attribution_id,
                ClickAttribution.niche_id == niche_id,
            )
        )
        return result.first()

    async def list_by_niche(
        self, niche_id: str, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ClickAttribution]:
        stmt = (
            select(ClickAttribution)
            .where(ClickAttribution.niche_id == niche_id)
            .order_by(ClickAttribution.created_at.desc())
        )
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()


class AffiliateClickRepository(SqlAlchemyRepository[AffiliateClick, str]):
    """Append-only click ledger (niche-scoped)."""

    model = AffiliateClick

    async def get_scoped(self, click_id: str, *, niche_id: str) -> AffiliateClick | None:
        result = await self._session.scalars(
            select(AffiliateClick).where(
                AffiliateClick.id == click_id, AffiliateClick.niche_id == niche_id
            )
        )
        return result.first()

    async def list_by_niche(
        self,
        niche_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        link_token_id: str | None = None,
    ) -> Sequence[AffiliateClick]:
        stmt = (
            select(AffiliateClick)
            .where(AffiliateClick.niche_id == niche_id)
            .order_by(AffiliateClick.clicked_at.desc())
        )
        if link_token_id is not None:
            stmt = stmt.where(AffiliateClick.link_token_id == link_token_id)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_by_niche(self, niche_id: str) -> int:
        stmt = select(func.count(AffiliateClick.id)).where(AffiliateClick.niche_id == niche_id)
        return int((await self._session.execute(stmt)).scalar_one())


class RevenueTransactionRepository(SqlAlchemyRepository[RevenueTransaction, str]):
    """Append-only commission/conversion ledger (niche-scoped)."""

    model = RevenueTransaction

    async def get_scoped(self, transaction_id: str, *, niche_id: str) -> RevenueTransaction | None:
        result = await self._session.scalars(
            select(RevenueTransaction).where(
                RevenueTransaction.id == transaction_id,
                RevenueTransaction.niche_id == niche_id,
            )
        )
        return result.first()

    async def get_by_network_transaction(
        self, network_id: str, network_transaction_id: str
    ) -> RevenueTransaction | None:
        result = await self._session.scalars(
            select(RevenueTransaction).where(
                RevenueTransaction.network_id == network_id,
                RevenueTransaction.network_transaction_id == network_transaction_id,
            )
        )
        return result.first()

    async def list_by_niche(
        self,
        niche_id: str,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[RevenueTransaction]:
        stmt = (
            select(RevenueTransaction)
            .where(RevenueTransaction.niche_id == niche_id)
            .order_by(RevenueTransaction.occurred_at.desc())
        )
        if status is not None:
            stmt = stmt.where(RevenueTransaction.status == status)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_by_niche(self, niche_id: str, *, status: str | None = None) -> int:
        stmt = select(func.count(RevenueTransaction.id)).where(
            RevenueTransaction.niche_id == niche_id
        )
        if status is not None:
            stmt = stmt.where(RevenueTransaction.status == status)
        return int((await self._session.execute(stmt)).scalar_one())

    async def sum_commission_cents(self, niche_id: str, *, status: str | None = None) -> int:
        stmt = select(func.coalesce(func.sum(RevenueTransaction.commission_cents), 0)).where(
            RevenueTransaction.niche_id == niche_id
        )
        if status is not None:
            stmt = stmt.where(RevenueTransaction.status == status)
        return int((await self._session.execute(stmt)).scalar_one())


class RevenueReconciliationRepository(SqlAlchemyRepository[RevenueReconciliation, str]):
    """Nightly reconciliation runs (niche-scoped)."""

    model = RevenueReconciliation

    async def get_scoped(
        self, reconciliation_id: str, *, niche_id: str
    ) -> RevenueReconciliation | None:
        result = await self._session.scalars(
            select(RevenueReconciliation).where(
                RevenueReconciliation.id == reconciliation_id,
                RevenueReconciliation.niche_id == niche_id,
            )
        )
        return result.first()

    async def list_by_niche(
        self, niche_id: str, *, limit: int = 100, offset: int = 0
    ) -> Sequence[RevenueReconciliation]:
        stmt = (
            select(RevenueReconciliation)
            .where(RevenueReconciliation.niche_id == niche_id)
            .order_by(RevenueReconciliation.reported_at.desc())
        )
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()


class RevenueSummaryRepository(SqlAlchemyRepository[RevenueSummary, str]):
    """Daily revenue read model (niche-scoped)."""

    model = RevenueSummary

    async def get_by_niche_network_date(
        self, niche_id: str, network_id: str | None, summary_date: str
    ) -> RevenueSummary | None:
        result = await self._session.scalars(
            select(RevenueSummary).where(
                RevenueSummary.niche_id == niche_id,
                RevenueSummary.network_id == network_id,
                RevenueSummary.summary_date == summary_date,
            )
        )
        return result.first()

    async def list_by_niche(
        self, niche_id: str, *, limit: int = 100, offset: int = 0
    ) -> Sequence[RevenueSummary]:
        stmt = (
            select(RevenueSummary)
            .where(RevenueSummary.niche_id == niche_id)
            .order_by(RevenueSummary.summary_date.desc())
        )
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def upsert(
        self, niche_id: str, network_id: str | None, summary_date: str, *, row: RevenueSummary
    ) -> RevenueSummary:
        """Add or update the daily rollup (read model refresh)."""
        existing = await self.get_by_niche_network_date(niche_id, network_id, summary_date)
        if existing is None:
            self._session.add(row)
            return row
        existing.clicks = row.clicks
        existing.sales = row.sales
        existing.gross_cents = row.gross_cents
        existing.commission_cents = row.commission_cents
        existing.currency = row.currency
        return existing


class AffiliateWebhookLogRepository(SqlAlchemyRepository[AffiliateWebhookLog, str]):
    """Receiver-side webhook delivery ledger (API Contracts §10)."""

    model = AffiliateWebhookLog

    async def get_by_source_event(self, source: str, event_id: str) -> AffiliateWebhookLog | None:
        result = await self._session.scalars(
            select(AffiliateWebhookLog).where(
                AffiliateWebhookLog.source == source, AffiliateWebhookLog.event_id == event_id
            )
        )
        return result.first()

    async def list_recent(self, *, limit: int = 100) -> Sequence[AffiliateWebhookLog]:
        stmt = select(AffiliateWebhookLog).order_by(AffiliateWebhookLog.created_at.desc())
        return (await self._session.scalars(stmt.limit(limit))).all()


class AffiliateUnitOfWork(SqlAlchemyUnitOfWork):
    """Unit of work with typed affiliate-module repositories.

    The base class attaches repositories dynamically on transaction open;
    the declarations below give mypy and editors the concrete types while
    keeping the dynamic attachment behavior from backend-core.
    """

    affiliate_niches: AffiliateNicheRepository
    networks: AffiliateNetworkRepository
    merchants: AffiliateMerchantRepository
    products: AffiliateProductRepository
    categories: ProductCategoryRepository
    category_links: ProductCategoryLinkRepository
    links: AffiliateLinkRepository
    tokens: LinkTokenRepository
    attributions: ClickAttributionRepository
    clicks: AffiliateClickRepository
    revenue: RevenueTransactionRepository
    reconciliations: RevenueReconciliationRepository
    summaries: RevenueSummaryRepository
    webhook_logs: AffiliateWebhookLogRepository

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator["AffiliateUnitOfWork"]:
        """Open a transaction, yielding the typed unit of work."""
        async with SqlAlchemyUnitOfWork.transaction(self):
            yield self
