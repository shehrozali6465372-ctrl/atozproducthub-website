"""ORM entities for the affiliate module (affiliate_db).

Table shapes follow the Database Blueprint §5.8–5.13: networks/merchants
are global reference tables; every product/business record carries
``niche_id`` (blueprint §4: niche-first tenancy). Ledgers
(``affiliate_clicks``, ``revenue_transactions``) are append-only —
updates happen through reconciliation fields, never row mutation.

No AI data lives here; product descriptions are stored out-of-DB and
referenced via ``description_ref`` (blueprint §2.1).
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from atoz_backend_core.db.base import Base

UUID_LEN = 36


def _utcnow() -> datetime:
    """Python-side ``updated_at`` value (no post-flush expiry)."""
    return datetime.now(UTC)


class AffiliateNiche(Base):
    """Local tenant-registry mirror (ADR-0005).

    ``niches`` is owned by content-service in ``content_db``; cross-database
    foreign keys are impossible, so affiliate_db keeps this minimal
    read-only-style mirror (id, slug, name, status) for local tenancy
    lookups and slug-based public reads. Provisioned through the affiliate
    admin API and kept in sync by operations; no AI data lives here.
    """

    __tablename__ = "affiliate_niches"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class AffiliateNetwork(Base):
    """Registered affiliate networks — global reference (blueprint §5.8)."""

    __tablename__ = "affiliate_networks"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    feed_type: Mapped[str] = mapped_column(String(50), nullable=False, default="csv")
    webhook_secret_ref: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    settings_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class AffiliateMerchant(Base):
    """Merchants/programs inside networks — global reference (§5.9)."""

    __tablename__ = "affiliate_merchants"
    __table_args__ = (
        UniqueConstraint(
            "network_id", "remote_merchant_id", name="uq_affiliate_merchants_network_remote"
        ),
        Index("ix_affiliate_merchants_network_id", "network_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    network_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_networks.id"), nullable=False
    )
    remote_merchant_id: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    commission_terms_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class AffiliateProduct(Base):
    """Niche-scoped product catalog (blueprint §5.10)."""

    __tablename__ = "affiliate_products"
    __table_args__ = (
        UniqueConstraint(
            "niche_id", "merchant_id", "sku", name="uq_affiliate_products_niche_merchant_sku"
        ),
        Index("ix_affiliate_products_niche_status_updated", "niche_id", "status", "updated_at"),
        Index("ix_affiliate_products_merchant_id", "merchant_id"),
        Index("ix_affiliate_products_niche_slug", "niche_id", "slug"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    merchant_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_merchants.id"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_feed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class ProductCategory(Base):
    """Niche-scoped product taxonomy (blueprint §5.11)."""

    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint("niche_id", "slug", name="uq_product_categories_niche_slug"),
        Index("ix_product_categories_niche_parent_id", "niche_id", "parent_id"),
        Index("ix_product_categories_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("product_categories.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class ProductCategoryLink(Base):
    """Many-to-many link between products and product categories (§5.11)."""

    __tablename__ = "product_category_links"
    __table_args__ = (
        UniqueConstraint("product_id", "product_category_id", name="uq_pcl_product_category"),
        Index("ix_pcl_category_product", "product_category_id", "product_id"),
        Index("ix_pcl_niche_id", "niche_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    product_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_products.id"), nullable=False
    )
    product_category_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("product_categories.id"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AffiliateLink(Base):
    """Per-network link registration for a product (blueprint §5.11)."""

    __tablename__ = "affiliate_links"
    __table_args__ = (
        UniqueConstraint("product_id", "network_id", name="uq_affiliate_links_product_network"),
        Index("ix_affiliate_links_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    product_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_products.id"), nullable=False
    )
    network_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_networks.id"), nullable=False
    )
    network_link_url: Mapped[str] = mapped_column(Text, nullable=False)
    default_commission_rate: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    disclosure_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class LinkToken(Base):
    """Signed short tokens (``/go/{token}``) with attribution (blueprint §5.12)."""

    __tablename__ = "link_tokens"
    __table_args__ = (
        Index("ix_link_tokens_affiliate_link_expires", "affiliate_link_id", "expires_at"),
        Index("ix_link_tokens_niche_id", "niche_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    affiliate_link_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_links.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    destination_url: Mapped[str] = mapped_column(Text, nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AffiliateClick(Base):
    """Append-only click ledger (blueprint §5.12)."""

    __tablename__ = "affiliate_clicks"
    __table_args__ = (
        Index("ix_affiliate_clicks_token_clicked_at", "link_token_id", "clicked_at"),
        Index("ix_affiliate_clicks_niche_clicked_at", "niche_id", "clicked_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    link_token_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("link_tokens.id"), nullable=False
    )
    attribution_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("click_attributions.id"), nullable=True
    )
    revenue_transaction_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("revenue_transactions.id"), nullable=True
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fraud_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ClickAttribution(Base):
    """Append-only click source attribution (blueprint §5.12)."""

    __tablename__ = "click_attributions"
    __table_args__ = (
        Index("ix_click_attributions_pin_created", "pinterest_pin_id", "created_at"),
        Index("ix_click_attributions_niche_source_created", "niche_id", "source", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    pinterest_account_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    pinterest_pin_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="direct")
    campaign: Mapped[str | None] = mapped_column(String(200), nullable=True)
    utm_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    landing_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RevenueTransaction(Base):
    """Append-only commission/conversion ledger (blueprint §5.13)."""

    __tablename__ = "revenue_transactions"
    __table_args__ = (
        UniqueConstraint(
            "network_id", "network_transaction_id", name="uq_revenue_network_transaction"
        ),
        Index("ix_revenue_niche_status_occurred", "niche_id", "status", "occurred_at"),
        Index("ix_revenue_affiliate_click_id", "affiliate_click_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    network_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_networks.id"), nullable=False
    )
    affiliate_link_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_links.id"), nullable=False
    )
    affiliate_click_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_clicks.id"), nullable=True
    )
    network_transaction_id: Mapped[str] = mapped_column(String(200), nullable=False)
    gross_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commission_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RevenueReconciliation(Base):
    """Nightly reconciliation runs vs network reports (blueprint §5.13)."""

    __tablename__ = "revenue_reconciliations"
    __table_args__ = (
        UniqueConstraint("network_id", "reported_at", name="uq_reconciliations_network_date"),
        Index("ix_reconciliations_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    network_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_networks.id"), nullable=False
    )
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delta_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    report_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RevenueSummary(Base):
    """Daily revenue read model (blueprint §5.13)."""

    __tablename__ = "revenue_summaries"
    __table_args__ = (
        UniqueConstraint(
            "niche_id", "network_id", "summary_date", name="uq_revenue_summaries_niche_network_date"
        ),
        Index("ix_revenue_summaries_summary_date", "summary_date"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    network_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_networks.id"), nullable=True
    )
    summary_date: Mapped[str] = mapped_column(String(10), nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gross_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commission_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AffiliateWebhookLog(Base):
    """Receiver-side webhook delivery ledger (API Contracts §10 dedupe)."""

    __tablename__ = "affiliate_webhook_logs"
    __table_args__ = (
        UniqueConstraint("source", "event_id", name="uq_affiliate_webhook_source_event"),
        Index("ix_affiliate_webhook_logs_network_created", "network_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    network_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("affiliate_networks.id"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    event_id: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="received")
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
