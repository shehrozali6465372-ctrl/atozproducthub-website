"""ORM entities for the SEO module (seo_db).

Table shapes follow Database Blueprint §5.14: every record carries
``niche_id``; ``url_registry`` is the URL-policy source of truth and
``seo_metadata`` is one-to-one with it. Search index state (Typesense) is
derived from domain events and is never stored here — PostgreSQL remains
the source of truth. No AI data lives here: metadata produced by the AI OS
arrives via the Bridge and is stored as applied business output.
"""

from datetime import UTC, datetime

from sqlalchemy import (
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


class SeoNiche(Base):
    """Local tenant-registry mirror (ADR-0007).

    ``niches`` is owned by content-service in ``content_db``; cross-database
    foreign keys are impossible, so seo_db keeps this minimal read-only-style
    mirror for local tenancy lookups and slug-based public reads.
    """

    __tablename__ = "seo_niches"

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


class UrlRegistry(Base):
    """URL policy: canonical paths, redirects, and page references (blueprint §5.14)."""

    __tablename__ = "url_registry"
    __table_args__ = (
        UniqueConstraint("niche_id", "path", name="uq_url_registry_niche_path"),
        Index("ix_url_registry_niche_entity", "niche_id", "entity_type", "entity_id"),
        Index("ix_url_registry_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False, default="")
    # Cross-database references (content_db.articles / affiliate_db.products)
    # are plain indexed columns, never FKs (ADR-0007 mirror policy).
    article_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    product_id: Mapped[str | None] = mapped_column(String(UUID_LEN), nullable=True)
    redirect_to: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class SeoMetadata(Base):
    """Applied SEO metadata per URL (title, description, canonical, robots, OG, JSON-LD)."""

    __tablename__ = "seo_metadata"
    __table_args__ = (
        UniqueConstraint("url_registry_id", name="uq_seo_metadata_url_registry"),
        Index("ix_seo_metadata_niche_updated", "niche_id", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    url_registry_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("url_registry.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    meta_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    canonical_url: Mapped[str] = mapped_column(String(700), nullable=False, default="")
    robots: Mapped[str] = mapped_column(String(30), nullable=False, default="index,follow")
    og_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    structured_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SitemapShard(Base):
    """State of generated sitemap shards served from the CDN (blueprint §5.14)."""

    __tablename__ = "sitemap_shards"
    __table_args__ = (
        UniqueConstraint("niche_id", "group_name", "shard_no", name="uq_sitemap_shards_group_no"),
        Index("ix_sitemap_shards_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    group_name: Mapped[str] = mapped_column(String(30), nullable=False)
    shard_no: Mapped[int] = mapped_column(Integer, nullable=False)
    object_ref: Mapped[str] = mapped_column(String(700), nullable=False, default="")
    url_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ready")
    last_url: Mapped[str] = mapped_column(String(700), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SeoCrawlReport(Base):
    """Crawl/index data ingested from Search Console/Bing per niche."""

    __tablename__ = "seo_crawl_reports"
    __table_args__ = (
        UniqueConstraint("niche_id", "source", "report_date", name="uq_seo_crawl_reports_date"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    report_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD
    pages_indexed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    position_avg: Mapped[float] = mapped_column(nullable=False, default=0.0)
    raw_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class SeoHealthCheck(Base):
    """Scheduled SEO health snapshots (CWV, index coverage, broken links)."""

    __tablename__ = "seo_health_checks"
    __table_args__ = (
        Index("ix_seo_health_checks_niche_type", "niche_id", "check_type", "checked_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), nullable=False)
    url_registry_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("url_registry.id"), nullable=True
    )
    check_type: Mapped[str] = mapped_column(String(30), nullable=False)
    score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    details_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
