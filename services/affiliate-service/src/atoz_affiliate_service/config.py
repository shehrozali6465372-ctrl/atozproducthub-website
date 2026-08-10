"""Service configuration (pydantic-settings + environment loading).

Inherits the shared backend-core settings and adds the affiliate module
tuning: JWT verification for the admin API, webhook signing secrets,
token signing, and public-read defaults.
"""

from functools import lru_cache

from pydantic import Field

from atoz_backend_core.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Runtime settings for affiliate-service."""

    app_name: str = "AtozProductHub Affiliate Service"

    # Admin API: JWT access tokens are verified against the same secret the
    # gateway uses to issue them (dev default; production via Vault).
    jwt_secret: str = "dev-only-affiliate-jwt-secret-change-in-production"
    admin_read_permission: str = "affiliate:read"
    admin_write_permission: str = "affiliate:write"

    # Link tokens: HMAC key that signs redirect identifiers (API Contracts
    # §4 redirector: server-controlled resolution, never raw browser URLs).
    token_signing_secret: str = "dev-only-affiliate-token-signing-secret-change-in-production"

    # Network webhook secrets, keyed by network code (dev defaults; per
    # network ``webhook_secret_ref`` in production via Vault).
    webhook_secrets: dict[str, str] = Field(
        default_factory=lambda: {
            "amazon": "dev-only-amazon-webhook-secret",
            "impact": "dev-only-impact-webhook-secret",
            "shareasale": "dev-only-shareasale-webhook-secret",
        }
    )

    # Server-side commission rules: conversion payload amounts are validated
    # against these limits; values outside the range are rejected.
    max_commission_cents: int = 1_000_000  # $10,000
    max_gross_cents: int = 10_000_000  # $100,000
    default_currency: str = "USD"

    # Public read defaults (API Contracts §7: budgets are per surface).
    default_page_size: int = 20
    max_page_size: int = 100

    # Canonical site origin used in redirect events and public URLs.
    public_base_url: str = "https://atozproducthub.com"


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
