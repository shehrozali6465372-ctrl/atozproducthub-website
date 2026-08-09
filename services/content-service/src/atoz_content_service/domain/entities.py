"""ORM entities for the content module (content_db).

Table shapes follow the Database Blueprint §5 exactly for the M4 scope:
``niches``, ``articles``, ``article_versions``, ``categories``,
``article_categories``, ``tags``, ``article_tags``. Every business table
carries ``niche_id`` (blueprint §4: niche-first tenancy). No AI data lives
here — bodies are stored out-of-DB and referenced via ``content_ref``.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
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


class Niche(Base):
    """Foundation tenant registry (Database Blueprint §5.1)."""

    __tablename__ = "niches"

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    default_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class Article(Base):
    """Article records — metadata + publishing state; body lives out-of-DB."""

    __tablename__ = "articles"
    __table_args__ = (
        UniqueConstraint("niche_id", "slug", name="uq_articles_niche_slug"),
        Index("ix_articles_niche_status_published_at", "niche_id", "status", "published_at"),
        Index("ix_articles_primary_category_id", "primary_category_id"),
        Index("ix_articles_niche_deleted_at", "niche_id", "deleted_at"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("niches.id"), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    content_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    author_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    editor_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_category_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("categories.id"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class ArticleVersion(Base):
    """Immutable version history; updates create new versions (§5.5)."""

    __tablename__ = "article_versions"
    __table_args__ = (
        UniqueConstraint("article_id", "version_no", name="uq_article_versions_article_version"),
        Index("ix_article_versions_article_created_at", "article_id", "created_at"),
        Index("ix_article_versions_niche_id", "niche_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("niches.id"), nullable=False)
    article_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("articles.id"), nullable=False
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Category(Base):
    """Niche-scoped article taxonomy (§5.6)."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("niche_id", "slug", name="uq_categories_niche_slug"),
        Index("ix_categories_niche_parent_id", "niche_id", "parent_id"),
        Index("ix_categories_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("niches.id"), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(
        String(UUID_LEN), ForeignKey("categories.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class ArticleCategory(Base):
    """Many-to-many link between articles and categories (§5.6)."""

    __tablename__ = "article_categories"
    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "category_id",
            name="uq_article_categories_article_category",
        ),
        Index("ix_article_categories_category_article", "category_id", "article_id"),
        Index("ix_article_categories_niche_id", "niche_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("niches.id"), nullable=False)
    article_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("articles.id"), nullable=False
    )
    category_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("categories.id"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Tag(Base):
    """Niche-scoped article tags (§5.7)."""

    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("niche_id", "slug", name="uq_tags_niche_slug"),
        Index("ix_tags_niche_status", "niche_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("niches.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class ArticleTag(Base):
    """Many-to-many link between articles and tags (§5.7)."""

    __tablename__ = "article_tags"
    __table_args__ = (
        UniqueConstraint("article_id", "tag_id", name="uq_article_tags_article_tag"),
        Index("ix_article_tags_tag_article", "tag_id", "article_id"),
        Index("ix_article_tags_niche_id", "niche_id"),
    )

    id: Mapped[str] = mapped_column(String(UUID_LEN), primary_key=True)
    niche_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("niches.id"), nullable=False)
    article_id: Mapped[str] = mapped_column(
        String(UUID_LEN), ForeignKey("articles.id"), nullable=False
    )
    tag_id: Mapped[str] = mapped_column(String(UUID_LEN), ForeignKey("tags.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
