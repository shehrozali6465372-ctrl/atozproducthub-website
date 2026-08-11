"""Service configuration for seo-service (M7 SEO + discovery layer).

Inherits the shared backend-core settings and adds the SEO module tuning:
JWT verification for the admin API, sitemap sharding limits, robots rules,
Typesense search-index configuration, and the Google/Bing integration
boundaries (server-side credentials only; never in the frontend).
"""

from functools import lru_cache

from pydantic import Field

from atoz_backend_core.config import BaseServiceSettings

# Sitemap groups rendered from the URL registry (Task 17 §4).
SITEMAP_GROUPS = ["articles", "categories", "tags", "products", "landing", "collections"]


class Settings(BaseServiceSettings):
    """Runtime settings for seo-service."""

    app_name: str = "AtozProductHub Seo Service"

    # Admin API: JWT access tokens are verified against the same secret the
    # gateway uses to issue them (dev default; production via Vault).
    jwt_secret: str = "dev-only-seo-jwt-secret-change-in-production"
    admin_read_permission: str = "seo:read"
    admin_write_permission: str = "seo:write"

    # Shared secret used to authenticate internal event ingestion
    # (content:published.v1, product:ingested.v1, ...). Dev default; the
    # gateway/producer and this service must share the production value.
    event_webhook_secret: str = "dev-only-seo-event-secret-change-in-production"

    # Canonical site origin used in canonical URLs and sitemaps.
    public_base_url: str = "https://atozproducthub.com"

    # Sitemap sharding: max URLs per shard, one shard index per group.
    sitemap_max_urls: int = 1000
    sitemap_group_chunk_urls: int = 5000

    # Robots rules (Task 17 §5): Pinterestbot + its image proxy are never
    # blocked; admin/private/internal paths are always blocked.
    robots_allow: list[str] = Field(
        default_factory=lambda: [
            "/",
            "/articles/",
            "/categories/",
            "/tags/",
            "/products/",
            "/collections/",
            "/landing/",
        ]
    )
    robots_disallow: list[str] = Field(
        default_factory=lambda: [
            "/admin",
            "/api/",
            "/search",
            "/_next/",
            "/assets/private",
            "/sitemap",
        ]
    )

    # Typesense (Database Blueprint §10 — lexical search only).
    typesense_api_base: str = "http://typesense:8108"
    typesense_api_key: str = "dev-only-typesense-key-change-in-production"
    search_collection: str = "seo_content"
    search_page_size_default: int = 20
    search_page_size_max: int = 50

    # Google Search Console / Bing Webmaster boundaries (Task 17 §6).
    # Credentials stay server-side; endpoints are mocked in tests and never
    # exposed to the frontend.
    gsc_enabled: bool = False
    gsc_service_account_ref: str = "vault://seo/gsc/service-account"
    bing_enabled: bool = False
    bing_api_key_ref: str = "vault://seo/bing/api-key"


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
