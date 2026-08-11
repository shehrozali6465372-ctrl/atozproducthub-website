"""seo_db tables: niches mirror, url_registry, seo_metadata, sitemap_shards,
seo_crawl_reports, seo_health_checks

Revision ID: 0001
Revises:
Create Date: 2026-08-10

Portable schema (SQLite in tests, PostgreSQL in prod/CI). Primary keys are
UUID v7 strings assigned by the domain layer (ADR-0007). Every business
record carries ``niche_id`` per Database Blueprint §4. No AI data lives
here — search index state (Typesense) is derived, never stored.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TS = sa.DateTime(timezone=True)
NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    # ----------------------------------------- local tenancy mirror (ADR-0007)
    op.create_table(
        "seo_niches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("ix_seo_niches_slug", "seo_niches", ["slug"], unique=True)

    # ---------------------------------------------------------- URL registry
    op.create_table(
        "url_registry",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("canonical_path", sa.String(500), nullable=False, server_default=""),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False, server_default=""),
        sa.Column("article_id", sa.String(36), nullable=True),
        sa.Column("product_id", sa.String(36), nullable=True),
        sa.Column("redirect_to", sa.String(500), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("changed_at", TS, nullable=False, server_default=NOW),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("uq_url_registry_niche_path", "url_registry", ["niche_id", "path"], unique=True)
    op.create_index(
        "ix_url_registry_niche_entity", "url_registry", ["niche_id", "entity_type", "entity_id"]
    )
    op.create_index("ix_url_registry_niche_status", "url_registry", ["niche_id", "status"])

    # ------------------------------------------------------------- metadata
    op.create_table(
        "seo_metadata",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column(
            "url_registry_id", sa.String(36), sa.ForeignKey("url_registry.id"), nullable=False
        ),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("meta_description", sa.Text(), nullable=False, server_default=""),
        sa.Column("canonical_url", sa.String(700), nullable=False, server_default=""),
        sa.Column("robots", sa.String(30), nullable=False, server_default="index,follow"),
        sa.Column("og_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("structured_data_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("checksum", sa.String(64), nullable=False, server_default=""),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_seo_metadata_url_registry", "seo_metadata", ["url_registry_id"], unique=True
    )
    op.create_index("ix_seo_metadata_niche_updated", "seo_metadata", ["niche_id", "updated_at"])

    # ------------------------------------------------------- sitemap shards
    op.create_table(
        "sitemap_shards",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("group_name", sa.String(30), nullable=False),
        sa.Column("shard_no", sa.Integer(), nullable=False),
        sa.Column("object_ref", sa.String(700), nullable=False, server_default=""),
        sa.Column("url_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("generated_at", TS, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ready"),
        sa.Column("last_url", sa.String(700), nullable=False, server_default=""),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_sitemap_shards_group_no",
        "sitemap_shards",
        ["niche_id", "group_name", "shard_no"],
        unique=True,
    )
    op.create_index("ix_sitemap_shards_niche_status", "sitemap_shards", ["niche_id", "status"])

    # -------------------------------------------------------- crawl reports
    op.create_table(
        "seo_crawl_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column("source", sa.String(10), nullable=False),
        sa.Column("report_date", sa.String(10), nullable=False),
        sa.Column("pages_indexed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("position_avg", sa.Float(), nullable=False, server_default="0"),
        sa.Column("raw_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_seo_crawl_reports_date",
        "seo_crawl_reports",
        ["niche_id", "source", "report_date"],
        unique=True,
    )

    # --------------------------------------------------------- health checks
    op.create_table(
        "seo_health_checks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), nullable=False),
        sa.Column(
            "url_registry_id", sa.String(36), sa.ForeignKey("url_registry.id"), nullable=True
        ),
        sa.Column("check_type", sa.String(30), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("checked_at", TS, nullable=False, server_default=NOW),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "ix_seo_health_checks_niche_type",
        "seo_health_checks",
        ["niche_id", "check_type", "checked_at"],
    )


def downgrade() -> None:
    op.drop_table("seo_health_checks")
    op.drop_table("seo_crawl_reports")
    op.drop_table("sitemap_shards")
    op.drop_table("seo_metadata")
    op.drop_table("url_registry")
    op.drop_table("seo_niches")
