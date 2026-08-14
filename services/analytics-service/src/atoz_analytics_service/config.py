"""Service configuration for analytics-service (M8 analytics business layer).

Inherits the shared backend-core settings and adds the analytics module
tuning: JWT verification for the admin API, the shared event-ingestion
secret, the Kafka event backbone, the ClickHouse warehouse, collector
limits, and the rollup window.
"""

from functools import lru_cache

from pydantic import Field

from atoz_backend_core.config import BaseServiceSettings


class Settings(BaseServiceSettings):
    """Runtime settings for analytics-service."""

    app_name: str = "AtozProductHub Analytics Service"

    # Admin API: JWT access tokens are verified against the same secret the
    # gateway uses to issue them (dev default; production via Vault).
    jwt_secret: str = "dev-only-analytics-jwt-secret-change-in-production"
    admin_read_permission: str = "analytics:read"
    admin_write_permission: str = "analytics:write"

    # Shared secret used to authenticate internal event ingestion
    # (content:published.v1, pin:published.v1, affiliate:click.v1,
    # revenue:attributed.v1, ...). Dev default; producers must share the
    # production value.
    event_webhook_secret: str = "dev-only-analytics-event-secret-change-in-production"

    # Pipeline: PostgreSQL operational ledger -> Kafka event backbone ->
    # ClickHouse analytical warehouse (Database Blueprint §5.16, §11).
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic: str = "atoz.analytics.events.v1"
    kafka_group_id: str = "analytics-service"
    kafka_enabled: bool = False  # production enables the real backbone
    # SASL_PLAINTEXT auth (M11 Phase C — store security). Empty = plaintext
    # internal broker (dev); production sets these via Vault-injected env.
    kafka_security_protocol: str = "PLAINTEXT"
    kafka_sasl_mechanism: str = "PLAIN"
    kafka_sasl_username: str = ""
    kafka_sasl_password: str = ""
    clickhouse_url: str = "http://clickhouse:8123"
    clickhouse_database: str = "atoz_analytics"
    clickhouse_table: str = "analytics_events"
    warehouse_enabled: bool = False  # production enables the real warehouse

    # First-party collector limits (Task 18 §2).
    collector_max_batch_size: int = 100
    collector_max_traits_bytes: int = 4096
    collector_max_page_url: int = 700
    collector_max_referrer: int = 700
    collector_max_session_id: int = 128
    collector_max_user_pseudo_id: int = 128
    allowed_event_types: list[str] = Field(
        default_factory=lambda: [
            "page_view",
            "session_start",
            "engagement",
            "affiliate_click",
            "conversion",
            "pin_click",
            "pin_save",
            "custom",
        ]
    )
    # Traits with these keys are rejected at the collector (privacy guard).
    sensitive_trait_keys: list[str] = Field(
        default_factory=lambda: [
            "email",
            "phone",
            "password",
            "ssn",
            "credit_card",
            "token",
            "authorization",
            "api_key",
        ]
    )

    # Rollup window: how far back daily rollups may run.
    rollup_window_days: int = 400


@lru_cache
def get_settings() -> Settings:
    """Return the cached service settings."""
    return Settings()
