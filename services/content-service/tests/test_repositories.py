"""Repository tests: CRUD, tenancy scoping, slug uniqueness, link tables."""

import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from atoz_backend_core.db.base import Base
from atoz_content_service.domain.entities import (
    Article,
    ArticleVersion,
    Category,
    Niche,
    Tag,
)
from atoz_content_service.repositories import (
    ArticleCategoryRepository,
    ArticleRepository,
    ArticleTagRepository,
    ArticleVersionRepository,
    CategoryRepository,
    NicheRepository,
    TagRepository,
)
from atoz_content_service.uuids import uuid7


def _run(coro):
    return asyncio.run(coro)


async def _factory() -> tuple[async_sessionmaker, AsyncEngine]:
    """Create engine + tables inside the caller's event loop (StaticPool)."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False), engine


def test_article_repository_tenancy_scoping() -> None:
    async def scenario() -> None:
        session_factory, engine = await _factory()
        try:
            async with session_factory() as session:
                niche_a = Niche(id=uuid7(), name="A", slug="a", status="active")
                niche_b = Niche(id=uuid7(), name="B", slug="b", status="active")
                article = Article(
                    id=uuid7(),
                    niche_id=niche_a.id,
                    slug="shared-slug",
                    title="Title",
                    status="draft",
                )
                session.add_all([niche_a, niche_b, article])
                await session.commit()

            async with session_factory() as session:
                repo = ArticleRepository(session)
                found_a = await repo.get_scoped(article.id, niche_id=niche_a.id)
                assert found_a is not None and found_a.slug == "shared-slug"
                # Cross-niche access must never return the row.
                assert await repo.get_scoped(article.id, niche_id=niche_b.id) is None
                assert await repo.get_by_slug("shared-slug", niche_id=niche_b.id) is None
                listed = await repo.list_by_niche(niche_b.id)
                assert listed == []
                assert await repo.count_by_niche(niche_b.id) == 0

            async with session_factory() as session:
                repo = ArticleRepository(session)
                # slug_exists is niche-scoped.
                assert await repo.slug_exists("shared-slug", niche_id=niche_a.id) is True
                assert await repo.slug_exists("shared-slug", niche_id=niche_b.id) is False
        finally:
            await engine.dispose()

    _run(scenario())


def test_article_repository_soft_delete_hides_rows() -> None:
    async def scenario() -> None:
        session_factory, engine = await _factory()
        try:
            async with session_factory() as session:
                niche = Niche(id=uuid7(), name="A", slug="a", status="active")
                article = Article(
                    id=uuid7(), niche_id=niche.id, slug="gone", title="T", status="draft"
                )
                session.add_all([niche, article])
                await session.commit()
            async with session_factory() as session:
                repo = ArticleRepository(session)
                stored = await repo.get_scoped(article.id, niche_id=niche.id)
                assert stored is not None
                await repo.soft_delete(stored)
                await session.commit()
            async with session_factory() as session:
                repo = ArticleRepository(session)
                assert await repo.get_scoped(article.id, niche_id=niche.id) is None
                assert await repo.get_by_slug("gone", niche_id=niche.id) is None
                assert await repo.count_by_niche(niche.id) == 0
        finally:
            await engine.dispose()

    _run(scenario())


def test_version_repository_next_and_list() -> None:
    async def scenario() -> None:
        session_factory, engine = await _factory()
        try:
            async with session_factory() as session:
                niche = Niche(id=uuid7(), name="A", slug="a", status="active")
                article = Article(
                    id=uuid7(), niche_id=niche.id, slug="v", title="T", status="draft"
                )
                session.add_all([niche, article])
                await session.commit()
            async with session_factory() as session:
                versions = ArticleVersionRepository(session)
                assert await versions.next_version_no(article.id) == 1
                await versions.add(
                    ArticleVersion(
                        id=uuid7(),
                        niche_id=niche.id,
                        article_id=article.id,
                        version_no=1,
                        title="T",
                        content_ref="articles/x/v1.txt",
                        checksum="c1",
                    )
                )
                await session.commit()
            async with session_factory() as session:
                versions = ArticleVersionRepository(session)
                assert await versions.next_version_no(article.id) == 2
                listed = await versions.list_for_article(article.id, niche_id=niche.id)
                assert len(listed) == 1 and listed[0].version_no == 1
                # Cross-niche listing returns nothing.
                assert await versions.list_for_article(article.id, niche_id="other") == []
        finally:
            await engine.dispose()

    _run(scenario())


def test_category_and_tag_repositories_tenancy() -> None:
    async def scenario() -> None:
        session_factory, engine = await _factory()
        try:
            async with session_factory() as session:
                niche_a = Niche(id=uuid7(), name="A", slug="a", status="active")
                niche_b = Niche(id=uuid7(), name="B", slug="b", status="active")
                cat = Category(id=uuid7(), niche_id=niche_a.id, name="Cookware", slug="cookware")
                tag = Tag(id=uuid7(), niche_id=niche_a.id, name="Guide", slug="guide")
                session.add_all([niche_a, niche_b, cat, tag])
                await session.commit()

            async with session_factory() as session:
                cats = CategoryRepository(session)
                assert await cats.get_scoped(cat.id, niche_id=niche_a.id) is not None
                assert await cats.get_scoped(cat.id, niche_id=niche_b.id) is None
                assert await cats.get_by_slug("cookware", niche_id=niche_b.id) is None
                assert await cats.slug_exists("cookware", niche_id=niche_a.id) is True
                assert await cats.slug_exists("cookware", niche_id=niche_b.id) is False

                tags = TagRepository(session)
                assert await tags.get_scoped(tag.id, niche_id=niche_a.id) is not None
                assert await tags.get_scoped(tag.id, niche_id=niche_b.id) is None
                assert await tags.slug_exists("guide", niche_id=niche_a.id) is True
                assert await tags.slug_exists("guide", niche_id=niche_b.id) is False
        finally:
            await engine.dispose()

    _run(scenario())


def test_article_link_repositories_replace_and_scope() -> None:
    async def scenario() -> None:
        session_factory, engine = await _factory()
        try:
            async with session_factory() as session:
                niche_a = Niche(id=uuid7(), name="A", slug="a", status="active")
                niche_b = Niche(id=uuid7(), name="B", slug="b", status="active")
                article = Article(
                    id=uuid7(), niche_id=niche_a.id, slug="s", title="T", status="draft"
                )
                cat1 = Category(id=uuid7(), niche_id=niche_a.id, name="C1", slug="c1")
                cat2 = Category(id=uuid7(), niche_id=niche_a.id, name="C2", slug="c2")
                tag1 = Tag(id=uuid7(), niche_id=niche_a.id, name="T1", slug="t1")
                tag2 = Tag(id=uuid7(), niche_id=niche_a.id, name="T2", slug="t2")
                session.add_all([niche_a, niche_b, article, cat1, cat2, tag1, tag2])
                await session.commit()

            async with session_factory() as session:
                links = ArticleCategoryRepository(session)
                await links.replace_for_article(
                    article.id,
                    niche_id=niche_a.id,
                    category_ids=[cat1.id, cat2.id],
                    primary_category_id=cat1.id,
                )
                await session.commit()
                stored = await links.list_for_article(article.id, niche_id=niche_a.id)
                assert {link.category_id for link in stored} == {cat1.id, cat2.id}
                primary = [link for link in stored if link.is_primary]
                assert [link.category_id for link in primary] == [cat1.id]
                # Cross-niche read of the links is empty.
                assert await links.list_for_article(article.id, niche_id=niche_b.id) == []

                tags = ArticleTagRepository(session)
                await tags.replace_for_article(
                    article.id, niche_id=niche_a.id, tag_ids=[tag1.id, tag2.id]
                )
                await session.commit()
                assert len(await tags.list_for_article(article.id, niche_id=niche_a.id)) == 2
        finally:
            await engine.dispose()

    _run(scenario())


def test_niche_repository() -> None:
    async def scenario() -> None:
        session_factory, engine = await _factory()
        try:
            async with session_factory() as session:
                niche = Niche(id=uuid7(), name="Kitchen", slug="kitchen", status="active")
                session.add(niche)
                await session.commit()
            async with session_factory() as session:
                repo = NicheRepository(session)
                found = await repo.get_by_slug("kitchen")
                assert found is not None and found.id == niche.id
                assert await repo.get_by_slug("nope") is None
                assert await repo.slug_exists("kitchen") is True
                assert await repo.slug_exists("kitchen", exclude_id=niche.id) is False
                assert len(await repo.list_by_status("active")) == 1
                assert len(await repo.list_by_status("draft")) == 0
        finally:
            await engine.dispose()

    _run(scenario())
