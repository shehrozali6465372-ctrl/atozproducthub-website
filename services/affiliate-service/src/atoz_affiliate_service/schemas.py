"""Pydantic DTOs for the affiliate API (Public Read + Admin).

Public DTOs carry only published business data; admin DTOs mirror the
Admin API conventions of 12-api-contracts.md §5. Amounts are integer
minor units (cents) with an ISO currency code — never floats.
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class Page(BaseModel, Generic[T]):
    """Pagination envelope: ``{items, page, page_size, total}``."""

    items: list[T]
    page: int
    page_size: int
    total: int


# -------------------------------------------------------------- networks
class NetworkCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    status: str = Field(default="active", pattern="^(active|disabled)$")
    feed_type: str = Field(default="csv", max_length=50)
    webhook_secret_ref: str = Field(default="", max_length=200)
    settings_json: str = Field(default="{}", max_length=4000)


class NetworkUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern="^(active|disabled)$")
    feed_type: str | None = Field(default=None, max_length=50)
    webhook_secret_ref: str | None = Field(default=None, max_length=200)
    settings_json: str | None = Field(default=None, max_length=4000)


class NetworkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    status: str
    feed_type: str
    webhook_secret_ref: str
    settings_json: str
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------- niche mirror (ADR-0005)
class NicheMirrorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    status: str = Field(default="draft", pattern="^(draft|active|disabled)$")


class NicheMirrorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = Field(default=None, pattern="^(draft|active|disabled)$")


# -------------------------------------------------------------- merchants
class MerchantCreate(BaseModel):
    network_id: str = Field(pattern=UUID_PATTERN)
    remote_merchant_id: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=300)
    status: str = Field(default="active", pattern="^(active|disabled)$")
    commission_terms_json: str = Field(default="{}", max_length=4000)


class MerchantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    status: str | None = Field(default=None, pattern="^(active|disabled)$")
    commission_terms_json: str | None = Field(default=None, max_length=4000)


class MerchantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    network_id: str
    remote_merchant_id: str
    name: str
    status: str
    commission_terms_json: str
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------ categories
class ProductCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: str | None = Field(default=None, pattern=UUID_PATTERN)
    sort_order: int = 0
    status: str = Field(default="active", pattern="^(active|archived)$")


class ProductCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: str | None = Field(default=None, pattern=UUID_PATTERN)
    sort_order: int | None = None
    status: str | None = Field(default=None, pattern="^(active|archived)$")


class ProductCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    parent_id: str | None
    name: str
    slug: str
    path: str | None
    sort_order: int
    status: str
    created_at: datetime
    updated_at: datetime


class PublicCategoryOut(BaseModel):
    slug: str
    name: str
    path: str | None


# --------------------------------------------------------------- products
class ProductCreate(BaseModel):
    merchant_id: str = Field(pattern=UUID_PATTERN)
    sku: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=300)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    excerpt: str = Field(default="", max_length=4000)
    description_ref: str | None = Field(default=None, max_length=500)
    price_cents: int = Field(default=0, ge=0, le=10_000_000_000)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: str = Field(default="draft", pattern="^(draft|active|disabled|archived)$")
    category_ids: list[str] = Field(default_factory=list)
    primary_category_id: str | None = Field(default=None, pattern=UUID_PATTERN)


class ProductUpdate(BaseModel):
    merchant_id: str | None = Field(default=None, pattern=UUID_PATTERN)
    sku: str | None = Field(default=None, min_length=1, max_length=200)
    name: str | None = Field(default=None, min_length=1, max_length=300)
    slug: str | None = Field(default=None, min_length=1, max_length=200)
    excerpt: str | None = Field(default=None, max_length=4000)
    description_ref: str | None = Field(default=None, max_length=500)
    price_cents: int | None = Field(default=None, ge=0, le=10_000_000_000)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    status: str | None = Field(default=None, pattern="^(draft|active|disabled|archived)$")
    category_ids: list[str] | None = None
    primary_category_id: str | None = Field(default=None, pattern=UUID_PATTERN)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    merchant_id: str
    sku: str
    slug: str
    name: str
    excerpt: str
    description_ref: str | None
    price_cents: int
    currency: str
    status: str
    checksum: str | None
    last_feed_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PublicProductOut(BaseModel):
    id: str
    slug: str
    name: str
    excerpt: str
    price_cents: int
    currency: str
    category: PublicCategoryOut | None
    merchant_name: str
    network_name: str
    disclosure_required: bool
    buy_url: str | None


# ----------------------------------------------------------------- links
class AffiliateLinkCreate(BaseModel):
    product_id: str = Field(pattern=UUID_PATTERN)
    network_id: str = Field(pattern=UUID_PATTERN)
    network_link_url: str = Field(min_length=1, max_length=4000)
    default_commission_rate: str = Field(default="", max_length=20)
    status: str = Field(default="active", pattern="^(active|disabled|expired)$")
    disclosure_required: bool = Field(default=True)


class AffiliateLinkUpdate(BaseModel):
    network_link_url: str | None = Field(default=None, min_length=1, max_length=4000)
    default_commission_rate: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, pattern="^(active|disabled|expired)$")
    disclosure_required: bool | None = None


class AffiliateLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    product_id: str
    network_id: str
    network_link_url: str
    default_commission_rate: str
    status: str
    disclosure_required: bool
    created_at: datetime
    updated_at: datetime


class LinkTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    affiliate_link_id: str
    token: str
    destination_url: str
    params_json: str
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class LinkTokenCreateOut(BaseModel):
    token: str
    go_url: str


# ------------------------------------------------------------------ clicks
class ClickAttributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    pinterest_account_id: str | None
    pinterest_pin_id: str | None
    source: str
    campaign: str | None
    utm_json: str
    landing_url: str | None
    created_at: datetime


class AffiliateClickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    link_token_id: str
    attribution_id: str | None
    revenue_transaction_id: str | None
    clicked_at: datetime
    ip_hash: str | None
    user_agent_hash: str | None
    referrer: str | None
    is_bot: bool
    fraud_flag: bool


# ------------------------------------------------------- revenue/commissions
class RevenueTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    network_id: str
    affiliate_link_id: str
    affiliate_click_id: str | None
    network_transaction_id: str
    gross_cents: int
    commission_cents: int
    currency: str
    status: str
    occurred_at: datetime
    reconciled_at: datetime | None
    created_at: datetime


class CommissionTransitionRequest(BaseModel):
    action: str = Field(pattern="^(approve|reject|mark_paid)$")


class ReconciliationCreate(BaseModel):
    network_id: str = Field(pattern=UUID_PATTERN)
    reported_at: datetime
    expected_total_cents: int = Field(default=0, ge=0)
    actual_total_cents: int = Field(default=0, ge=0)
    report_ref: str | None = Field(default=None, max_length=500)


class ReconciliationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    network_id: str
    reported_at: datetime
    expected_total_cents: int
    actual_total_cents: int
    delta_cents: int
    status: str
    report_ref: str | None
    created_at: datetime


class RevenueSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    niche_id: str
    network_id: str | None
    summary_date: str
    clicks: int
    sales: int
    gross_cents: int
    commission_cents: int
    currency: str


class RevenueDashboardOut(BaseModel):
    """Revenue summary for the admin dashboard (per niche)."""

    total_commission_cents: int
    approved_commission_cents: int
    pending_commission_cents: int
    paid_commission_cents: int
    transaction_count: int
    click_count: int


# ---------------------------------------------------------------- redirect
class PublicGoOut(BaseModel):
    destination_url: str
    disclosure_required: bool
    click_id: str


# ---------------------------------------------------------------- webhooks
class WebhookEnvelope(BaseModel):
    event_id: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=20)
    source: str = Field(min_length=1, max_length=100)
    occurred_at: str
    nonce: str | None = None
    payload: dict = Field(default_factory=dict)
