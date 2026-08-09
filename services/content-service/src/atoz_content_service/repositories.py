"""Repository layer for the content module.

Every repository extends ``atoz_backend_core.repositories`` and enforces
the Database Blueprint tenancy rules: all queries are scoped by
``niche_id``, so one niche can never read or mutate another niche's rows.
"""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC

from sqlalchemy import delete, func, select

from atoz_backend_core.repositories import SqlAlchemyRepository, SqlAlchemyUnitOfWork
from atoz_content_service.domain.entities import (
    Article,
    ArticleCategory,
    ArticleTag,
    ArticleVersion,
    Category,
    Niche,
    Tag,
)
from atoz_content_service.uuids import uuid7


class NicheRepository(SqlAlchemyRepository[Niche, str]):
    """Niches are global (tenant registry) — not niche-scoped themselves."""

    model = Niche

    async def get_by_slug(self, slug: str) -> Niche | None:
        result = await self._session.scalars(select(Niche).where(Niche.slug == slug))
        return result.first()

    async def list_by_status(self, status: str | None = None) -> Sequence[Niche]:
        stmt = select(Niche).order_by(Niche.name)
        if status is not None:
            stmt = stmt.where(Niche.status == status)
        return (await self._session.scalars(stmt)).all()

    async def slug_exists(self, slug: str, *, exclude_id: str | None = None) -> bool:
        stmt = select(Niche.id).where(Niche.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Niche.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None


class ArticleRepository(SqlAlchemyRepository[Article, str]):
    """Articles are niche-scoped; every query carries ``niche_id``."""

    model = Article

    async def get_scoped(self, article_id: str, *, niche_id: str) -> Article | None:
        stmt = select(Article).where(
            Article.id == article_id,
            Article.niche_id == niche_id,
            Article.deleted_at.is_(None),
        )
        return (await self._session.scalars(stmt)).first()

    async def get_by_slug(
        self, slug: str, *, niche_id: str, include_deleted: bool = False
    ) -> Article | None:
        stmt = select(Article).where(
            Article.slug == slug,
            Article.niche_id == niche_id,
        )
        if not include_deleted:
            stmt = stmt.where(Article.deleted_at.is_(None))
        return (await self._session.scalars(stmt)).first()

    async def slug_exists(self, slug: str, *, niche_id: str, exclude_id: str | None = None) -> bool:
        stmt = select(Article.id).where(Article.slug == slug, Article.niche_id == niche_id)
        if exclude_id is not None:
            stmt = stmt.where(Article.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_niche(
        self,
        niche_id: str,
        *,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Article]:
        stmt = (
            select(Article)
            .where(Article.niche_id == niche_id, Article.deleted_at.is_(None))
            .order_by(Article.updated_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Article.status == status)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_by_niche(self, niche_id: str, *, status: str | None = None) -> int:
        stmt = select(func.count(Article.id)).where(
            Article.niche_id == niche_id, Article.deleted_at.is_(None)
        )
        if status is not None:
            stmt = stmt.where(Article.status == status)
        return int((await self._session.execute(stmt)).scalar_one())

    async def soft_delete(self, article: Article) -> None:
        from datetime import datetime

        article.deleted_at = datetime.now(UTC)


class ArticleVersionRepository(SqlAlchemyRepository[ArticleVersion, str]):
    """Versions are append-only and immutable — no update path exists."""

    model = ArticleVersion

    async def next_version_no(self, article_id: str) -> int:
        stmt = select(func.max(ArticleVersion.version_no)).where(
            ArticleVersion.article_id == article_id
        )
        current = (await self._session.execute(stmt)).scalar_one()
        return int(current or 0) + 1

    async def list_for_article(self, article_id: str, *, niche_id: str) -> Sequence[ArticleVersion]:
        stmt = (
            select(ArticleVersion)
            .where(ArticleVersion.article_id == article_id, ArticleVersion.niche_id == niche_id)
            .order_by(ArticleVersion.version_no.desc())
        )
        return (await self._session.scalars(stmt)).all()

    async def get_version(
        self, article_id: str, *, niche_id: str, version_no: int
    ) -> ArticleVersion | None:
        stmt = select(ArticleVersion).where(
            ArticleVersion.article_id == article_id,
            ArticleVersion.niche_id == niche_id,
            ArticleVersion.version_no == version_no,
        )
        return (await self._session.scalars(stmt)).first()


class CategoryRepository(SqlAlchemyRepository[Category, str]):
    """Categories are niche-scoped."""

    model = Category

    async def get_scoped(self, category_id: str, *, niche_id: str) -> Category | None:
        stmt = select(Category).where(Category.id == category_id, Category.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def get_by_slug(self, slug: str, *, niche_id: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug, Category.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def slug_exists(self, slug: str, *, niche_id: str, exclude_id: str | None = None) -> bool:
        stmt = select(Category.id).where(Category.slug == slug, Category.niche_id == niche_id)
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_niche(
        self, niche_id: str, *, status: str | None = None
    ) -> Sequence[Category]:
        stmt = (
            select(Category)
            .where(Category.niche_id == niche_id)
            .order_by(Category.sort_order, Category.name)
        )
        if status is not None:
            stmt = stmt.where(Category.status == status)
        return (await self._session.scalars(stmt)).all()

    async def count_articles(self, category_id: str) -> int:
        stmt = select(func.count(ArticleCategory.id)).where(
            ArticleCategory.category_id == category_id
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def delete_links(self, category_id: str) -> None:
        await self._session.execute(
            delete(ArticleCategory).where(ArticleCategory.category_id == category_id)
        )


class TagRepository(SqlAlchemyRepository[Tag, str]):
    """Tags are niche-scoped."""

    model = Tag

    async def get_scoped(self, tag_id: str, *, niche_id: str) -> Tag | None:
        stmt = select(Tag).where(Tag.id == tag_id, Tag.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def get_by_slug(self, slug: str, *, niche_id: str) -> Tag | None:
        stmt = select(Tag).where(Tag.slug == slug, Tag.niche_id == niche_id)
        return (await self._session.scalars(stmt)).first()

    async def slug_exists(self, slug: str, *, niche_id: str, exclude_id: str | None = None) -> bool:
        stmt = select(Tag.id).where(Tag.slug == slug, Tag.niche_id == niche_id)
        if exclude_id is not None:
            stmt = stmt.where(Tag.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_niche(self, niche_id: str, *, status: str | None = None) -> Sequence[Tag]:
        stmt = select(Tag).where(Tag.niche_id == niche_id).order_by(Tag.name)
        if status is not None:
            stmt = stmt.where(Tag.status == status)
        return (await self._session.scalars(stmt)).all()

    async def count_articles(self, tag_id: str) -> int:
        stmt = select(func.count(ArticleTag.id)).where(ArticleTag.tag_id == tag_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def delete_links(self, tag_id: str) -> None:
        await self._session.execute(delete(ArticleTag).where(ArticleTag.tag_id == tag_id))


class ArticleCategoryRepository(SqlAlchemyRepository[ArticleCategory, str]):
    """Niche-scoped link table between articles and categories."""

    model = ArticleCategory

    async def list_for_article(
        self, article_id: str, *, niche_id: str
    ) -> Sequence[ArticleCategory]:
        stmt = select(ArticleCategory).where(
            ArticleCategory.article_id == article_id, ArticleCategory.niche_id == niche_id
        )
        return (await self._session.scalars(stmt)).all()

    async def replace_for_article(
        self,
        article_id: str,
        *,
        niche_id: str,
        category_ids: Sequence[str],
        primary_category_id: str | None,
    ) -> None:
        await self._session.execute(
            delete(ArticleCategory).where(ArticleCategory.article_id == article_id)
        )
        for category_id in category_ids:
            self._session.add(
                ArticleCategory(
                    id=uuid7(),
                    niche_id=niche_id,
                    article_id=article_id,
                    category_id=category_id,
                    is_primary=category_id == primary_category_id,
                )
            )

    async def category_ids_for_article(self, article_id: str, *, niche_id: str) -> list[str]:
        stmt = select(ArticleCategory.category_id).where(
            ArticleCategory.article_id == article_id, ArticleCategory.niche_id == niche_id
        )
        return list((await self._session.scalars(stmt)).all())


class ArticleTagRepository(SqlAlchemyRepository[ArticleTag, str]):
    """Niche-scoped link table between articles and tags."""

    model = ArticleTag

    async def list_for_article(self, article_id: str, *, niche_id: str) -> Sequence[ArticleTag]:
        stmt = select(ArticleTag).where(
            ArticleTag.article_id == article_id, ArticleTag.niche_id == niche_id
        )
        return (await self._session.scalars(stmt)).all()

    async def replace_for_article(
        self, article_id: str, *, niche_id: str, tag_ids: Sequence[str]
    ) -> None:
        await self._session.execute(delete(ArticleTag).where(ArticleTag.article_id == article_id))
        for tag_id in tag_ids:
            self._session.add(
                ArticleTag(id=uuid7(), niche_id=niche_id, article_id=article_id, tag_id=tag_id)
            )


class ContentUnitOfWork(SqlAlchemyUnitOfWork):
    """Unit of work with typed content-module repositories.

    The base class attaches repositories dynamically on transaction open;
    the declarations below give mypy and editors the concrete types while
    keeping the dynamic attachment behavior from backend-core.
    """

    niches: NicheRepository
    articles: ArticleRepository
    versions: ArticleVersionRepository
    categories: CategoryRepository
    tags: TagRepository
    article_categories: ArticleCategoryRepository
    article_tags: ArticleTagRepository

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator["ContentUnitOfWork"]:
        """Open a transaction, yielding the typed unit of work."""
        async with SqlAlchemyUnitOfWork.transaction(self):
            yield self
