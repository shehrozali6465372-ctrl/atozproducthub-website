"""Content service — the business use cases of the CMS module.

Owns: article lifecycle (draft → review → published → archived), slug
management, immutable versioning, published-snapshot rules, niche tenancy,
and content domain events.

Never owns: AI behavior (research, writing, images, SEO generation,
learning) — those belong to the AI OS and reach the website only through
the AI OS Bridge.
"""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atoz_backend_core.events.publisher import EventPublisher
from atoz_content_service.config import Settings
from atoz_content_service.domain.entities import (
    Article,
    ArticleCategory,
    ArticleTag,
    ArticleVersion,
    Category,
    Niche,
    Tag,
)
from atoz_content_service.domain.enums import ArticleStatus, CategoryStatus, NicheStatus, TagStatus
from atoz_content_service.domain.events import (
    content_published_event,
    content_unpublished_event,
    content_updated_event,
)
from atoz_content_service.domain.lifecycle import transition
from atoz_content_service.domain.slug import slugify, unique_slug
from atoz_content_service.errors import DuplicateError, NotFoundError, ValidationError
from atoz_content_service.repositories import (
    ArticleCategoryRepository,
    ArticleRepository,
    ArticleTagRepository,
    ArticleVersionRepository,
    CategoryRepository,
    ContentUnitOfWork,
    NicheRepository,
    TagRepository,
)
from atoz_content_service.storage import ContentStore, checksum_of
from atoz_content_service.uuids import uuid7

# Statuses an editor may save content in. Published edits create a new
# draft version without touching the published snapshot (ADR-0004); review
# is frozen (reject first); archived requires restore first.
_EDITABLE_STATUSES = frozenset(
    {ArticleStatus.DRAFT, ArticleStatus.UNPUBLISHED, ArticleStatus.PUBLISHED}
)

_REPOSITORY_FACTORIES: dict[str, Callable[[AsyncSession], object]] = {
    "niches": NicheRepository,
    "articles": ArticleRepository,
    "versions": ArticleVersionRepository,
    "categories": CategoryRepository,
    "tags": TagRepository,
    "article_categories": ArticleCategoryRepository,
    "article_tags": ArticleTagRepository,
}


class _SlugListRepository(Protocol):
    """Minimal repo contract for per-niche slug uniqueness checks."""

    async def list_by_niche(self, niche_id: str, *, status: str | None = None) -> Sequence[Any]: ...


def _now() -> datetime:
    """Current UTC timestamp for publish metadata."""
    return datetime.now(UTC)


class ContentService:
    """Aggregate the content module use cases behind one facade."""

    def __init__(
        self,
        *,
        uow_factory: Callable[[], ContentUnitOfWork],
        content_store: ContentStore,
        event_publisher: EventPublisher,
        settings: Settings,
    ) -> None:
        self._uow_factory = uow_factory
        self._store = content_store
        self._events = event_publisher
        self._settings = settings

    @staticmethod
    def build_uow(session_factory: async_sessionmaker[AsyncSession]) -> ContentUnitOfWork:
        """Build a UoW with the content module repositories."""
        return ContentUnitOfWork(session_factory, repositories=dict(_REPOSITORY_FACTORIES))

    # ------------------------------------------------------------------ niches
    async def create_niche(
        self, *, name: str, slug: str | None = None, default_currency: str | None = None
    ) -> Niche:
        desired = slug or slugify(name)
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            if await unit.niches.slug_exists(desired):
                raise DuplicateError(f"Niche slug {desired!r} is already registered.")
            niche = Niche(
                id=uuid7(),
                name=name,
                slug=desired,
                status=NicheStatus.DRAFT,
                default_currency=default_currency,
            )
            await unit.niches.add(niche)
            return niche

    async def list_niches(self, *, status: str | None = None) -> Sequence[Niche]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.niches.list_by_status(status)

    async def get_niche(self, niche_id: str) -> Niche | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.niches.get(niche_id)

    async def get_niche_by_slug(self, slug: str) -> Niche | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.niches.get_by_slug(slug)

    async def update_niche(
        self,
        niche_id: str,
        *,
        name: str | None = None,
        slug: str | None = None,
        status: str | None = None,
        default_currency: str | None = None,
    ) -> Niche:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            niche = await unit.niches.get(niche_id)
            if niche is None:
                raise NotFoundError("Niche not found.")
            if name is not None:
                niche.name = name
            if slug is not None and slug != niche.slug:
                if await unit.niches.slug_exists(slug, exclude_id=niche_id):
                    raise DuplicateError(f"Niche slug {slug!r} is already registered.")
                niche.slug = slug
            if status is not None:
                niche.status = status
            if default_currency is not None:
                niche.default_currency = default_currency
            return niche

    # ------------------------------------------------------------- categories
    async def create_category(
        self,
        niche_id: str,
        *,
        name: str,
        slug: str | None = None,
        description: str = "",
        parent_id: str | None = None,
        sort_order: int = 0,
    ) -> Category:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            if parent_id is not None:
                parent = await unit.categories.get_scoped(parent_id, niche_id=niche_id)
                if parent is None:
                    raise ValidationError("Parent category does not belong to the requested niche.")
            category = Category(
                id=uuid7(),
                niche_id=niche_id,
                parent_id=parent_id,
                name=name,
                slug=await self._unique_taxonomy_slug(
                    unit.categories, niche_id, slug or slugify(name)
                ),
                description=description,
                sort_order=sort_order,
                status=CategoryStatus.ACTIVE,
            )
            await unit.categories.add(category)
            return category

    async def update_category(
        self,
        niche_id: str,
        category_id: str,
        *,
        name: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        parent_id: str | None = None,
        sort_order: int | None = None,
        status: str | None = None,
    ) -> Category:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            category = await unit.categories.get_scoped(category_id, niche_id=niche_id)
            if category is None:
                raise NotFoundError("Category not found.")
            if name is not None:
                category.name = name
            if slug is not None and slug != category.slug:
                if await unit.categories.slug_exists(
                    slug, niche_id=niche_id, exclude_id=category_id
                ):
                    raise DuplicateError(f"Category slug {slug!r} is already used in this niche.")
                category.slug = slug
            if description is not None:
                category.description = description
            if parent_id is not None:
                if parent_id == category_id:
                    raise ValidationError("A category cannot be its own parent.")
                parent = await unit.categories.get_scoped(parent_id, niche_id=niche_id)
                if parent is None:
                    raise ValidationError("Parent category does not belong to the requested niche.")
                category.parent_id = parent_id
            if sort_order is not None:
                category.sort_order = sort_order
            if status is not None:
                category.status = status
            return category

    async def delete_category(self, niche_id: str, category_id: str) -> None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            category = await unit.categories.get_scoped(category_id, niche_id=niche_id)
            if category is None:
                raise NotFoundError("Category not found.")
            linked = await unit.categories.count_articles(category_id)
            if linked > 0:
                raise DuplicateError(
                    f"Category is still linked to {linked} article(s); unlink first."
                )
            await unit.categories.delete_links(category_id)
            await unit.categories.delete(category_id)

    async def list_categories(
        self, niche_id: str, *, status: str | None = None
    ) -> Sequence[Category]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.categories.list_by_niche(niche_id, status=status)

    # ------------------------------------------------------------------- tags
    async def create_tag(self, niche_id: str, *, name: str, slug: str | None = None) -> Tag:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            tag = Tag(
                id=uuid7(),
                niche_id=niche_id,
                name=name,
                slug=await self._unique_taxonomy_slug(unit.tags, niche_id, slug or slugify(name)),
                status=TagStatus.ACTIVE,
            )
            await unit.tags.add(tag)
            return tag

    async def update_tag(
        self,
        niche_id: str,
        tag_id: str,
        *,
        name: str | None = None,
        slug: str | None = None,
        status: str | None = None,
    ) -> Tag:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            tag = await unit.tags.get_scoped(tag_id, niche_id=niche_id)
            if tag is None:
                raise NotFoundError("Tag not found.")
            if name is not None:
                tag.name = name
            if slug is not None and slug != tag.slug:
                if await unit.tags.slug_exists(slug, niche_id=niche_id, exclude_id=tag_id):
                    raise DuplicateError(f"Tag slug {slug!r} is already used in this niche.")
                tag.slug = slug
            if status is not None:
                tag.status = status
            return tag

    async def delete_tag(self, niche_id: str, tag_id: str) -> None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            tag = await unit.tags.get_scoped(tag_id, niche_id=niche_id)
            if tag is None:
                raise NotFoundError("Tag not found.")
            linked = await unit.tags.count_articles(tag_id)
            if linked > 0:
                raise DuplicateError(f"Tag is still linked to {linked} article(s); unlink first.")
            await unit.tags.delete_links(tag_id)
            await unit.tags.delete(tag_id)

    async def list_tags(self, niche_id: str, *, status: str | None = None) -> Sequence[Tag]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.tags.list_by_niche(niche_id, status=status)

    # ---------------------------------------------------------------- articles
    async def create_article(
        self,
        niche_id: str,
        *,
        title: str,
        excerpt: str = "",
        body: str,
        slug: str | None = None,
        category_ids: Sequence[str] = (),
        primary_category_id: str | None = None,
        tag_ids: Sequence[str] = (),
        actor: str | None = None,
        change_summary: str | None = None,
    ) -> Article:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            await self._validate_taxonomy(
                unit, niche_id, category_ids, primary_category_id, tag_ids
            )
            article = Article(
                id=uuid7(),
                niche_id=niche_id,
                slug=slug or slugify(title),
                title=title,
                excerpt=excerpt,
                status=ArticleStatus.DRAFT,
                author_ref=None,
                editor_ref=actor,
            )
            if slug is None:
                existing = await self._existing_article_slugs(unit, niche_id)
                article.slug = unique_slug(article.slug, taken=set(existing))
            elif await unit.articles.slug_exists(slug, niche_id=niche_id):
                raise DuplicateError(f"Article slug {slug!r} is already used in this niche.")
            await unit.articles.add(article)
            version = await self._save_version(
                unit,
                article=article,
                title=article.title,
                excerpt=article.excerpt,
                body=body,
                actor=actor,
                change_summary=change_summary or "Created article.",
            )
            article.content_ref = version.content_ref
            article.content_checksum = version.checksum
            await self._replace_taxonomy(
                unit,
                article,
                niche_id=niche_id,
                category_ids=category_ids,
                primary_category_id=primary_category_id,
                tag_ids=tag_ids,
            )
        await self._events.publish(
            content_updated_event(article_id=article.id, niche_id=niche_id, status=article.status)
        )
        return article

    async def update_article(
        self,
        niche_id: str,
        article_id: str,
        *,
        actor: str,
        title: str | None = None,
        excerpt: str | None = None,
        body: str | None = None,
        slug: str | None = None,
        category_ids: Sequence[str] | None = None,
        primary_category_id: str | None = None,
        tag_ids: Sequence[str] | None = None,
        change_summary: str | None = None,
    ) -> Article:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            article = await unit.articles.get_scoped(article_id, niche_id=niche_id)
            if article is None:
                raise NotFoundError("Article not found.")
            if ArticleStatus(article.status) not in _EDITABLE_STATUSES:
                raise ValidationError(
                    f"Articles in status {article.status!r} cannot be edited; "
                    "reject or restore first."
                )
            published = ArticleStatus(article.status) == ArticleStatus.PUBLISHED

            slug_changed = False
            if slug is not None and slug != article.slug:
                slug_changed = True
                if published:
                    raise ValidationError("The slug (public URL) cannot change while published.")
                if await unit.articles.slug_exists(slug, niche_id=niche_id, exclude_id=article_id):
                    raise DuplicateError(f"Article slug {slug!r} is already used in this niche.")
                article.slug = slug

            taxonomy_changed = category_ids is not None or tag_ids is not None
            if taxonomy_changed and published:
                raise ValidationError(
                    "Taxonomy changes require unpublishing the article first "
                    "(published snapshot must stay immutable)."
                )

            current_body = await self._read_current_body(unit, article)
            new_title = title if title is not None else article.title
            new_excerpt = excerpt if excerpt is not None else article.excerpt
            new_body = body if body is not None else current_body
            content_changed = (
                new_title != article.title
                or new_excerpt != article.excerpt
                or new_body != current_body
            )

            if taxonomy_changed:
                await self._validate_taxonomy(
                    unit, niche_id, category_ids or (), primary_category_id, tag_ids or ()
                )
                await self._replace_taxonomy(
                    unit,
                    article,
                    niche_id=niche_id,
                    category_ids=category_ids or (),
                    primary_category_id=primary_category_id,
                    tag_ids=tag_ids or (),
                )

            if content_changed:
                version = await self._save_version(
                    unit,
                    article=article,
                    title=new_title,
                    excerpt=new_excerpt,
                    body=new_body,
                    actor=actor,
                    change_summary=change_summary,
                )
                if not published:
                    article.title = new_title
                    article.excerpt = new_excerpt
                    article.content_ref = version.content_ref
                    article.content_checksum = version.checksum
                article.editor_ref = actor
            elif taxonomy_changed or slug_changed:
                article.editor_ref = actor

        if content_changed:
            await self._events.publish(
                content_updated_event(
                    article_id=article.id, niche_id=niche_id, status=article.status
                )
            )
        return article

    async def transition(
        self, niche_id: str, article_id: str, action: str, *, actor: str
    ) -> Article:
        events: list = []
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            article = await unit.articles.get_scoped(article_id, niche_id=niche_id)
            if article is None:
                raise NotFoundError("Article not found.")
            current = ArticleStatus(article.status)
            try:
                target = transition(current, action)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

            if action in {"publish", "approve"}:
                if not article.content_ref or not article.content_checksum:
                    raise ValidationError("Cannot publish an article without content.")
                await self._apply_latest_version(unit, article)
                if article.author_ref is None:
                    article.author_ref = actor
                if article.published_at is None:
                    article.published_at = _now()
                article.editor_ref = actor
                events.append(
                    content_published_event(
                        article_id=article.id,
                        niche_id=niche_id,
                        url=f"{self._settings.public_base_url}/articles/{article.slug}",
                        checksum=article.content_checksum,
                    )
                )
            elif action == "unpublish":
                events.append(content_unpublished_event(article_id=article.id, niche_id=niche_id))
            else:
                events.append(
                    content_updated_event(
                        article_id=article.id, niche_id=niche_id, status=target.value
                    )
                )
            article.status = target.value
            article.editor_ref = actor
        for event in events:
            await self._events.publish(event)
        return article

    async def soft_delete(self, niche_id: str, article_id: str, *, actor: str) -> None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            article = await unit.articles.get_scoped(article_id, niche_id=niche_id)
            if article is None:
                raise NotFoundError("Article not found.")
            if ArticleStatus(article.status) in {
                ArticleStatus.PUBLISHED,
                ArticleStatus.UNPUBLISHED,
            }:
                raise ValidationError("Published articles must be archived before deletion.")
            await unit.articles.soft_delete(article)
            article.editor_ref = actor

    async def get_article(self, niche_id: str, article_id: str) -> Article | None:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            return await unit.articles.get_scoped(article_id, niche_id=niche_id)

    async def list_articles(
        self, niche_id: str, *, status: str | None = None, page: int = 1, page_size: int = 20
    ) -> tuple[Sequence[Article], int]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            items = await unit.articles.list_by_niche(
                niche_id, status=status, limit=page_size, offset=(page - 1) * page_size
            )
            total = await unit.articles.count_by_niche(niche_id, status=status)
            return items, total

    async def list_published_articles(
        self,
        niche_id: str,
        *,
        category_slug: str | None = None,
        tag_slug: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Article], int]:
        """Published-only listing with same-niche taxonomy filters (SQL-side)."""
        conditions = [
            Article.niche_id == niche_id,
            Article.status == ArticleStatus.PUBLISHED,
            Article.deleted_at.is_(None),
        ]
        if category_slug is not None:
            conditions.append(
                select(1)
                .select_from(ArticleCategory)
                .join(Category, Category.id == ArticleCategory.category_id)
                .where(
                    ArticleCategory.article_id == Article.id,
                    Category.niche_id == niche_id,
                    Category.slug == category_slug,
                )
                .exists()
            )
        if tag_slug is not None:
            conditions.append(
                select(1)
                .select_from(ArticleTag)
                .join(Tag, Tag.id == ArticleTag.tag_id)
                .where(
                    ArticleTag.article_id == Article.id,
                    Tag.niche_id == niche_id,
                    Tag.slug == tag_slug,
                )
                .exists()
            )
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            stmt = (
                select(Article)
                .where(*conditions)
                .order_by(Article.published_at.desc())
                .limit(page_size)
                .offset((page - 1) * page_size)
            )
            items = (await unit.session.scalars(stmt)).all()
            total = int(
                (
                    await unit.session.execute(select(func.count(Article.id)).where(*conditions))
                ).scalar_one()
            )
            return items, total

    async def get_published_article(self, niche_id: str, slug: str) -> tuple[Article, str] | None:
        """Return (article, body) when the article is published and not deleted."""
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            article = await unit.articles.get_by_slug(slug, niche_id=niche_id)
            if article is None or article.status != ArticleStatus.PUBLISHED:
                return None
            body = await self._store.get(article.content_ref or "")
            if body is None:
                return None
            return article, body

    async def list_versions(
        self, niche_id: str, article_id: str
    ) -> tuple[Article, Sequence[ArticleVersion]]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            article = await unit.articles.get_scoped(article_id, niche_id=niche_id)
            if article is None:
                raise NotFoundError("Article not found.")
            versions = await unit.versions.list_for_article(article_id, niche_id=niche_id)
            return article, versions

    async def categories_for_article(self, niche_id: str, article_id: str) -> Sequence[Category]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            links = await unit.article_categories.list_for_article(article_id, niche_id=niche_id)
            categories = [await unit.categories.get(link.category_id) for link in links]
            return [category for category in categories if category is not None]

    async def tags_for_article(self, niche_id: str, article_id: str) -> Sequence[Tag]:
        uow = self._uow_factory()
        async with uow.transaction() as unit:
            links = await unit.article_tags.list_for_article(article_id, niche_id=niche_id)
            tags = [await unit.tags.get(link.tag_id) for link in links]
            return [tag for tag in tags if tag is not None]

    # ------------------------------------------------------------ internals
    async def _unique_taxonomy_slug(
        self, repo: _SlugListRepository, niche_id: str, desired: str
    ) -> str:
        existing = await repo.list_by_niche(niche_id)
        return unique_slug(desired, taken={item.slug for item in existing})

    async def _existing_article_slugs(self, unit: ContentUnitOfWork, niche_id: str) -> list[str]:
        stmt = select(Article.slug).where(Article.niche_id == niche_id)
        return list((await unit.session.execute(stmt)).scalars().all())

    async def _save_version(
        self,
        unit: ContentUnitOfWork,
        *,
        article: Article,
        title: str,
        excerpt: str,
        body: str,
        actor: str | None,
        change_summary: str | None,
    ) -> ArticleVersion:
        version_no = await unit.versions.next_version_no(article.id)
        ref = f"articles/{article.id}/v{version_no}.txt"
        checksum = checksum_of(body)
        await self._store.put(ref=ref, content=body)
        version = ArticleVersion(
            id=uuid7(),
            niche_id=article.niche_id,
            article_id=article.id,
            version_no=version_no,
            title=title,
            excerpt=excerpt,
            content_ref=ref,
            checksum=checksum,
            change_summary=change_summary,
            created_by=actor,
        )
        await unit.versions.add(version)
        return version

    async def _read_current_body(self, unit: ContentUnitOfWork, article: Article) -> str:
        body = await self._store.get(article.content_ref or "")
        return body or ""

    async def _apply_latest_version(self, unit: ContentUnitOfWork, article: Article) -> None:
        versions = await unit.versions.list_for_article(article.id, niche_id=article.niche_id)
        if not versions:
            raise ValidationError("Cannot publish an article without a content version.")
        latest = versions[0]  # ordered version_no desc
        article.title = latest.title
        article.excerpt = latest.excerpt
        article.content_ref = latest.content_ref
        article.content_checksum = latest.checksum

    async def _validate_taxonomy(
        self,
        unit: ContentUnitOfWork,
        niche_id: str,
        category_ids: Sequence[str],
        primary_category_id: str | None,
        tag_ids: Sequence[str],
    ) -> None:
        if primary_category_id is not None and primary_category_id not in set(category_ids):
            raise ValidationError("The primary category must be one of the article's categories.")
        for category_id in category_ids:
            category = await unit.categories.get_scoped(category_id, niche_id=niche_id)
            if category is None:
                raise ValidationError("Category does not belong to the requested niche.")
        for tag_id in tag_ids:
            tag = await unit.tags.get_scoped(tag_id, niche_id=niche_id)
            if tag is None:
                raise ValidationError("Tag does not belong to the requested niche.")

    async def _replace_taxonomy(
        self,
        unit: ContentUnitOfWork,
        article: Article,
        *,
        niche_id: str,
        category_ids: Sequence[str],
        primary_category_id: str | None,
        tag_ids: Sequence[str],
    ) -> None:
        await unit.article_categories.replace_for_article(
            article.id,
            niche_id=niche_id,
            category_ids=category_ids,
            primary_category_id=primary_category_id,
        )
        await unit.article_tags.replace_for_article(article.id, niche_id=niche_id, tag_ids=tag_ids)
        article.primary_category_id = primary_category_id
