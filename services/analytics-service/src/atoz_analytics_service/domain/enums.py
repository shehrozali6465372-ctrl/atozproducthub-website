"""Analytics enums: event types, sources, and metric keys (Task 18 §1).

Frozen values used by the collector, the internal-event webhook, and the
rollup aggregation. Business-layer only — no AI event types exist.
"""

from enum import StrEnum


class EventType(StrEnum):
    """First-party collector event types."""

    PAGE_VIEW = "page_view"
    SESSION_START = "session_start"
    ENGAGEMENT = "engagement"
    AFFILIATE_CLICK = "affiliate_click"
    CONVERSION = "conversion"
    PIN_CLICK = "pin_click"
    PIN_SAVE = "pin_save"
    CUSTOM = "custom"


class InternalEventType(StrEnum):
    """Analytics event types derived from internal domain events."""

    CONTENT_PUBLISHED = "content_published"
    CONTENT_UPDATED = "content_updated"
    CONTENT_UNPUBLISHED = "content_unpublished"
    PIN_PUBLISHED = "pin_published"
    PIN_FAILED = "pin_failed"
    PRODUCT_INGESTED = "product_ingested"
    PRODUCT_REMOVED = "product_removed"
    AFFILIATE_CLICK = "affiliate_click"
    REVENUE_ATTRIBUTED = "revenue_attributed"
    SITEMAP_REBUILT = "sitemap_rebuilt"


class EventSource(StrEnum):
    """Where an analytics event originated."""

    WEB = "web"
    PINTEREST = "pinterest"
    AFFILIATE = "affiliate"
    CONTENT = "content"
    REVENUE = "revenue"
    INTERNAL = "internal"


class TrafficSource(StrEnum):
    """Traffic attribution buckets (Database Blueprint §5.15)."""

    PINTEREST = "pinterest"
    GOOGLE = "google"
    DIRECT = "direct"
    EMAIL = "email"
    OTHER = "other"


class MetricKey(StrEnum):
    """Daily metric keys aggregated by the rollup (Blueprint §5.16)."""

    SESSIONS = "traffic.sessions"
    PAGEVIEWS = "traffic.pageviews"
    UNIQUE_VISITORS = "traffic.unique_visitors"
    AVG_DURATION_SEC = "traffic.avg_duration_sec"
    BOUNCE_RATE = "traffic.bounce_rate"
    PIN_CLICKS = "pinterest.pin_clicks"
    PIN_SAVES = "pinterest.pin_saves"
    PIN_IMPRESSIONS = "pinterest.pin_impressions"
    AFFILIATE_CLICKS = "affiliate.clicks"
    CONVERSIONS = "affiliate.conversions"
    REVENUE_AMOUNT = "revenue.amount"
    REVENUE_COMMISSION = "revenue.commission"


# Maps internal domain events to internal analytics event types.
DOMAIN_EVENT_TO_INTERNAL: dict[str, InternalEventType] = {
    "content:published.v1": InternalEventType.CONTENT_PUBLISHED,
    "content:updated.v1": InternalEventType.CONTENT_UPDATED,
    "content:unpublished.v1": InternalEventType.CONTENT_UNPUBLISHED,
    "pin:published.v1": InternalEventType.PIN_PUBLISHED,
    "pin:failed.v1": InternalEventType.PIN_FAILED,
    "product:ingested.v1": InternalEventType.PRODUCT_INGESTED,
    "product:removed.v1": InternalEventType.PRODUCT_REMOVED,
    "affiliate:click.v1": InternalEventType.AFFILIATE_CLICK,
    "revenue:attributed.v1": InternalEventType.REVENUE_ATTRIBUTED,
    "seo:sitemap-rebuilt.v1": InternalEventType.SITEMAP_REBUILT,
}
