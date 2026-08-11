"""SEO module enumerations (string constants, portable across DBs).

Follows Database Blueprint §5.14 and the M7 scope: every SEO record is
niche-scoped, sitemap shards are per (niche, group), and crawl reports come
from GSC/Bing as business data.
"""

from enum import StrEnum


class UrlStatus(StrEnum):
    """URL registry lifecycle."""

    ACTIVE = "active"
    REDIRECT = "redirect"
    REMOVED = "removed"
    HIDDEN = "hidden"


class EntityType(StrEnum):
    """Indexable/public entity kinds (sitemap groups + search documents)."""

    ARTICLE = "article"
    PRODUCT = "product"
    CATEGORY = "category"
    TAG = "tag"
    LANDING = "landing"
    COLLECTION = "collection"
    PAGE = "page"


class RobotsRule(StrEnum):
    """Per-URL robots directives (applied as X-Robots-Tag + <meta>)."""

    INDEX = "index,follow"
    NOINDEX = "noindex,follow"
    NOINDEX_NOFOLLOW = "noindex,nofollow"
    NOFOLLOW = "index,nofollow"


class ShardStatus(StrEnum):
    """Sitemap shard lifecycle."""

    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"
    STALE = "stale"


class CrawlSource(StrEnum):
    """Crawl/index report sources."""

    GSC = "gsc"
    BING = "bing"


class SearchDocType(StrEnum):
    """Search document kinds (Typesense ``type`` facet)."""

    ARTICLE = "article"
    PRODUCT = "product"
    CATEGORY = "category"
    TAG = "tag"
    LANDING = "landing"
    COLLECTION = "collection"


class HealthCheckType(StrEnum):
    """SEO health snapshot kinds."""

    CWV = "core_web_vitals"
    INDEX_COVERAGE = "index_coverage"
    BROKEN_LINKS = "broken_links"
    STRUCTURED_DATA = "structured_data"


class EventKind(StrEnum):
    """Internal event webhook kinds (Task 17 §8)."""

    CONTENT_PUBLISHED = "content:published.v1"
    CONTENT_UPDATED = "content:updated.v1"
    CONTENT_UNPUBLISHED = "content:unpublished.v1"
    PRODUCT_INGESTED = "product:ingested.v1"
    PRODUCT_REMOVED = "product:removed.v1"
