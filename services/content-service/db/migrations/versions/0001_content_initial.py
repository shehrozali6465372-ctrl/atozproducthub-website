"""content tables: niches, articles, versions, categories, tags, links

Revision ID: 0001
Revises:
Create Date: 2026-08-08

Portable schema (SQLite in tests, PostgreSQL in prod/CI). Primary keys are
UUID v7 strings assigned by the domain layer (ADR-0004); every business
table carries ``niche_id`` per Database Blueprint §4. Bodies live in object
storage — tables only store ``content_ref`` + ``content_checksum``.
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
    op.create_table(
        "niches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("ix_niches_name", "niches", ["name"], unique=True)
    op.create_index("ix_niches_slug", "niches", ["slug"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), sa.ForeignKey("niches.id"), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("uq_categories_niche_slug", "categories", ["niche_id", "slug"], unique=True)
    op.create_index("ix_categories_niche_parent_id", "categories", ["niche_id", "parent_id"])
    op.create_index("ix_categories_niche_status", "categories", ["niche_id", "status"])

    op.create_table(
        "articles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), sa.ForeignKey("niches.id"), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("content_ref", sa.String(500), nullable=True),
        sa.Column("content_checksum", sa.String(64), nullable=True),
        sa.Column("author_ref", sa.String(200), nullable=True),
        sa.Column("editor_ref", sa.String(200), nullable=True),
        sa.Column(
            "primary_category_id", sa.String(36), sa.ForeignKey("categories.id"), nullable=True
        ),
        sa.Column("published_at", TS, nullable=True),
        sa.Column("deleted_at", TS, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("uq_articles_niche_slug", "articles", ["niche_id", "slug"], unique=True)
    op.create_index(
        "ix_articles_niche_status_published_at",
        "articles",
        ["niche_id", "status", "published_at"],
    )
    op.create_index("ix_articles_primary_category_id", "articles", ["primary_category_id"])
    op.create_index("ix_articles_niche_deleted_at", "articles", ["niche_id", "deleted_at"])

    op.create_table(
        "article_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), sa.ForeignKey("niches.id"), nullable=False),
        sa.Column("article_id", sa.String(36), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_ref", sa.String(500), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("change_summary", sa.String(500), nullable=True),
        sa.Column("created_by", sa.String(200), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_article_versions_article_version",
        "article_versions",
        ["article_id", "version_no"],
        unique=True,
    )
    op.create_index(
        "ix_article_versions_article_created_at", "article_versions", ["article_id", "created_at"]
    )
    op.create_index("ix_article_versions_niche_id", "article_versions", ["niche_id"])

    op.create_table(
        "article_categories",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), sa.ForeignKey("niches.id"), nullable=False),
        sa.Column("article_id", sa.String(36), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("category_id", sa.String(36), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_article_categories_article_category",
        "article_categories",
        ["article_id", "category_id"],
        unique=True,
    )
    op.create_index(
        "ix_article_categories_category_article",
        "article_categories",
        ["category_id", "article_id"],
    )
    op.create_index("ix_article_categories_niche_id", "article_categories", ["niche_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), sa.ForeignKey("niches.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
        sa.Column("updated_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index("uq_tags_niche_slug", "tags", ["niche_id", "slug"], unique=True)
    op.create_index("ix_tags_niche_status", "tags", ["niche_id", "status"])

    op.create_table(
        "article_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("niche_id", sa.String(36), sa.ForeignKey("niches.id"), nullable=False),
        sa.Column("article_id", sa.String(36), sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("tag_id", sa.String(36), sa.ForeignKey("tags.id"), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=NOW),
    )
    op.create_index(
        "uq_article_tags_article_tag", "article_tags", ["article_id", "tag_id"], unique=True
    )
    op.create_index("ix_article_tags_tag_article", "article_tags", ["tag_id", "article_id"])
    op.create_index("ix_article_tags_niche_id", "article_tags", ["niche_id"])


def downgrade() -> None:
    op.drop_table("article_tags")
    op.drop_table("tags")
    op.drop_table("article_categories")
    op.drop_table("article_versions")
    op.drop_table("articles")
    op.drop_table("categories")
    op.drop_table("niches")
