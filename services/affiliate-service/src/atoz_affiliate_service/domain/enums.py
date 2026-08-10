"""Affiliate module enumerations (string constants, portable across DBs).

Lifecycle values follow Database Blueprint §5.8–5.13 and the M5 scope:
commissions move pending → approved → paid (or pending → rejected) and
webhook deliveries are deduplicated by (source, event_id).
"""

from enum import StrEnum


class NetworkStatus(StrEnum):
    """Affiliate network availability (global reference)."""

    ACTIVE = "active"
    DISABLED = "disabled"


class MerchantStatus(StrEnum):
    """Merchant/program availability within a network."""

    ACTIVE = "active"
    DISABLED = "disabled"


class ProductStatus(StrEnum):
    """Product catalog lifecycle (niche-scoped)."""

    DRAFT = "draft"
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class ProductCategoryStatus(StrEnum):
    """Product taxonomy category availability within a niche."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class AffiliateLinkStatus(StrEnum):
    """Affiliate link registration lifecycle."""

    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"


class CommissionStatus(StrEnum):
    """Revenue transaction/commission lifecycle (blueprint §5.13 + M5)."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ReconciliationStatus(StrEnum):
    """Nightly reconciliation run states."""

    OPEN = "open"
    MATCHED = "matched"
    MISMATCH = "mismatch"
    CLOSED = "closed"


class WebhookEventStatus(StrEnum):
    """Receiver-side delivery ledger states (API Contracts §10)."""

    RECEIVED = "received"
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
