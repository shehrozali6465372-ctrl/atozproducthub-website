"""Service/domain tests: lifecycle, versioning, snapshots, tenancy, slugs."""

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from atoz_backend_core.db.base import Base
from atoz_content_service.errors import DuplicateError, NotFoundError, ValidationError
from atoz_content_service.services import ContentService
from atoz_content_service.storage import checksum_of

from .fixtures import make_settings


def _run(coro):
    return asyncio.run(coro)


async def _service() -> tuple[ContentService, AsyncEngine, list]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    from atoz_backend_core.events.bus import InMemoryEventBus
    from atoz_backend_core.events.publisher import EventPublisher
    from atoz_content_service.storage import InMemoryContentStore

    store = InMemoryContentStore()
    bus = InMemoryEventBus()
    captured: list = []

    async def capture(event) -> None:
        captured.append(event)

    for event_type in ("content:published.v1", "content:updated.v1", "content:unpublished.v1"):
        await bus.subscribe(event_type, capture)
    svc = ContentService(
        uow_factory=lambda: ContentService.build_uow(session_factory),
        content_store=store,
        event_publisher=EventPublisher(bus, publisher="content-service"),
        settings=make_settings(),
    )
    return svc, engine, captured


def test_create_emits_updated_event() -> None:
    async def scenario() -> None:
        svc, engine, events = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            await svc.create_article(niche.id, title="G", body="b")
            types = [e.type for e in events]
            assert "content:updated.v1" in types
            assert types.count("content:updated.v1") == 1
            assert events[0].payload["niche_id"] == niche.id
        finally:
            await engine.dispose()

    _run(scenario())


def test_article_lifecycle_publish_edit_snapshot_republish() -> None:
    async def scenario() -> None:
        svc, engine, events = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            article = await svc.create_article(
                niche.id, title="Guide", excerpt="E", body="First body.", actor="alice"
            )
            assert article.status == "draft"
            assert article.content_checksum == checksum_of("First body.")

            article = await svc.transition(niche.id, article.id, "publish", actor="alice")
            assert article.status == "published"
            published = await svc.get_published_article(niche.id, article.slug)
            assert published is not None
            assert published[0].author_ref == "alice"
            assert published[0].published_at is not None

            # Edit while published: new version, snapshot untouched.
            edited = await svc.update_article(
                niche.id, article.id, actor="bob", body="Second body.", change_summary="rewrite"
            )
            assert edited.content_checksum == checksum_of("First body.")
            snapshot = await svc.get_published_article(niche.id, article.slug)
            assert snapshot is not None and snapshot[1] == "First body."

            # Version history is immutable and complete.
            _, versions = await svc.list_versions(niche.id, article.id)
            assert [(v.version_no, v.checksum) for v in versions] == [
                (2, checksum_of("Second body.")),
                (1, checksum_of("First body.")),
            ]
            assert versions[0].created_by == "bob"
            assert versions[0].change_summary == "rewrite"

            # Re-publish applies the latest draft version.
            article = await svc.transition(niche.id, article.id, "publish", actor="bob")
            assert article.content_checksum == checksum_of("Second body.")
            live = await svc.get_published_article(niche.id, article.slug)
            assert live is not None and live[1] == "Second body."
            assert live[0].author_ref == "alice"  # author never changes

            types = [e.type for e in events]
            assert "content:published.v1" in types
            assert "content:unpublished.v1" not in types
            published_events = [e for e in events if e.type == "content:published.v1"]
            assert published_events[0].payload["checksum"] == checksum_of("First body.")
            assert published_events[1].payload["checksum"] == checksum_of("Second body.")
        finally:
            await engine.dispose()

    _run(scenario())


def test_unpublish_archive_restore_flow() -> None:
    async def scenario() -> None:
        svc, engine, events = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            article = await svc.create_article(niche.id, title="G", body="b", actor="alice")
            article = await svc.transition(niche.id, article.id, "publish", actor="alice")
            article = await svc.transition(niche.id, article.id, "unpublish", actor="alice")
            assert article.status == "unpublished"
            assert await svc.get_published_article(niche.id, article.slug) is None
            article = await svc.transition(niche.id, article.id, "archive", actor="alice")
            assert article.status == "archived"
            article = await svc.transition(niche.id, article.id, "restore", actor="alice")
            assert article.status == "draft"
            event_types = [e.type for e in events]
            assert "content:unpublished.v1" in event_types
        finally:
            await engine.dispose()

    _run(scenario())


def test_review_approve_reject_flow() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            article = await svc.create_article(niche.id, title="G", body="b", actor="alice")
            article = await svc.transition(niche.id, article.id, "submit", actor="alice")
            assert article.status == "review"
            article = await svc.transition(niche.id, article.id, "approve", actor="reviewer")
            assert article.status == "published"
            assert article.author_ref == "reviewer"
            assert article.editor_ref == "reviewer"

            article = await svc.transition(niche.id, article.id, "unpublish", actor="reviewer")
            article = await svc.transition(niche.id, article.id, "archive", actor="reviewer")
            article = await svc.transition(niche.id, article.id, "restore", actor="reviewer")
            article = await svc.transition(niche.id, article.id, "submit", actor="alice")
            assert article.status == "review"
            article = await svc.transition(niche.id, article.id, "reject", actor="reviewer")
            assert article.status == "draft"
        finally:
            await engine.dispose()

    _run(scenario())


def test_invalid_transitions_rejected() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            article = await svc.create_article(niche.id, title="G", body="b")
            with pytest.raises(ValidationError, match="Invalid lifecycle action"):
                await svc.transition(niche.id, article.id, "approve", actor="x")
            with pytest.raises(ValidationError, match="Invalid lifecycle action"):
                await svc.transition(niche.id, article.id, "unpublish", actor="x")
            with pytest.raises(ValidationError, match="Unknown lifecycle action"):
                await svc.transition(niche.id, article.id, "launch", actor="x")
        finally:
            await engine.dispose()

    _run(scenario())


def test_publish_requires_content() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            article = await svc.create_article(niche.id, title="G", body="", actor="alice")
            # Empty body still yields a content version, so publish is legal.
            article = await svc.transition(niche.id, article.id, "publish", actor="alice")
            assert article.status == "published"
        finally:
            await engine.dispose()

    _run(scenario())


def test_slug_auto_suffix_within_niche() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            first = await svc.create_article(niche.id, title="My Kitchen Guide", body="a")
            second = await svc.create_article(niche.id, title="My Kitchen Guide", body="b")
            third = await svc.create_article(niche.id, title="My Kitchen Guide", body="c")
            assert first.slug == "my-kitchen-guide"
            assert second.slug == "my-kitchen-guide-2"
            assert third.slug == "my-kitchen-guide-3"
        finally:
            await engine.dispose()

    _run(scenario())


def test_explicit_slug_conflict_raises_duplicate() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            await svc.create_article(niche.id, title="First", slug="explicit", body="a")
            with pytest.raises(DuplicateError):
                await svc.create_article(niche.id, title="Second", slug="explicit", body="b")
            # Updating to a conflicting slug also raises.
            other = await svc.create_article(niche.id, title="Other", body="c")
            with pytest.raises(DuplicateError):
                await svc.update_article(niche.id, other.id, actor="x", slug="explicit")
        finally:
            await engine.dispose()

    _run(scenario())


def test_same_slug_in_different_niches_allowed() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            kitchen = await svc.create_niche(name="Kitchen", slug="kitchen")
            travel = await svc.create_niche(name="Travel", slug="travel")
            a = await svc.create_article(kitchen.id, title="Same Title", body="a")
            b = await svc.create_article(travel.id, title="Same Title", body="b")
            assert a.slug == b.slug == "same-title"
        finally:
            await engine.dispose()

    _run(scenario())


def test_cross_niche_isolation_enforced() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            kitchen = await svc.create_niche(name="Kitchen", slug="kitchen")
            travel = await svc.create_niche(name="Travel", slug="travel")
            article = await svc.create_article(kitchen.id, title="G", body="b")
            # Read, update, transition, delete with the wrong niche -> 404 semantics.
            assert await svc.get_article(travel.id, article.id) is None
            with pytest.raises(NotFoundError):
                await svc.update_article(travel.id, article.id, actor="x", title="Nope")
            with pytest.raises(NotFoundError):
                await svc.transition(travel.id, article.id, "publish", actor="x")
            with pytest.raises(NotFoundError):
                await svc.soft_delete(travel.id, article.id, actor="x")
            with pytest.raises(NotFoundError):
                await svc.list_versions(travel.id, article.id)
            # Listing scoped to the other niche excludes it.
            items, total = await svc.list_articles(travel.id)
            assert items == [] and total == 0
            assert await svc.get_published_article(travel.id, article.slug) is None
        finally:
            await engine.dispose()

    _run(scenario())


def test_taxonomy_belongs_to_niche() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            kitchen = await svc.create_niche(name="Kitchen", slug="kitchen")
            travel = await svc.create_niche(name="Travel", slug="travel")
            travel_cat = await svc.create_category(travel.id, name="Bags", slug="bags")
            travel_tag = await svc.create_tag(travel.id, name="Packing", slug="packing")
            with pytest.raises(ValidationError, match="requested niche"):
                await svc.create_article(
                    kitchen.id, title="G", body="b", category_ids=[travel_cat.id]
                )
            with pytest.raises(ValidationError, match="requested niche"):
                await svc.create_article(kitchen.id, title="G", body="b", tag_ids=[travel_tag.id])
            # primary must be among category_ids.
            kitchen_cat = await svc.create_category(kitchen.id, name="Cookware", slug="cookware")
            with pytest.raises(ValidationError, match="primary category"):
                await svc.create_article(
                    kitchen.id,
                    title="G",
                    body="b",
                    category_ids=[kitchen_cat.id],
                    primary_category_id=travel_cat.id,
                )
        finally:
            await engine.dispose()

    _run(scenario())


def test_published_article_rejects_slug_and_taxonomy_edits() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            cat = await svc.create_category(niche.id, name="Cookware", slug="cookware")
            article = await svc.create_article(niche.id, title="G", body="b", category_ids=[cat.id])
            await svc.transition(niche.id, article.id, "publish", actor="x")
            with pytest.raises(ValidationError, match="slug"):
                await svc.update_article(niche.id, article.id, actor="x", slug="new-slug")
            with pytest.raises(ValidationError, match="Taxonomy changes"):
                await svc.update_article(niche.id, article.id, actor="x", category_ids=[])
        finally:
            await engine.dispose()

    _run(scenario())


def test_soft_delete_rules() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            article = await svc.create_article(niche.id, title="G", body="b")
            await svc.soft_delete(niche.id, article.id, actor="x")
            assert await svc.get_article(niche.id, article.id) is None

            published = await svc.create_article(niche.id, title="P", body="b")
            await svc.transition(niche.id, published.id, "publish", actor="x")
            with pytest.raises(ValidationError, match="archived before deletion"):
                await svc.soft_delete(niche.id, published.id, actor="x")
        finally:
            await engine.dispose()

    _run(scenario())


def test_category_delete_blocked_when_linked() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            cat = await svc.create_category(niche.id, name="Cookware", slug="cookware")
            await svc.create_article(niche.id, title="G", body="b", category_ids=[cat.id])
            with pytest.raises(DuplicateError, match="linked"):
                await svc.delete_category(niche.id, cat.id)
            await svc.delete_tag(niche.id, "nope")
        finally:
            await engine.dispose()

    with pytest.raises(NotFoundError):
        _run(scenario())


def test_list_articles_pagination_and_status_filter() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            for i in range(5):
                article = await svc.create_article(niche.id, title=f"Article {i}", body="b")
                await svc.transition(niche.id, article.id, "publish", actor="x")
            items, total = await svc.list_articles(
                niche.id, status="published", page=2, page_size=2
            )
            assert total == 5 and len(items) == 2
            drafts, drafts_total = await svc.list_articles(niche.id, status="draft")
            assert drafts_total == 0
        finally:
            await engine.dispose()

    _run(scenario())


def test_public_list_filters_by_category_and_tag() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            cookware = await svc.create_category(niche.id, name="Cookware", slug="cookware")
            gadgets = await svc.create_category(niche.id, name="Gadgets", slug="gadgets")
            guide = await svc.create_tag(niche.id, name="Guide", slug="guide")
            a = await svc.create_article(
                niche.id, title="A", body="b", category_ids=[cookware.id], tag_ids=[guide.id]
            )
            b = await svc.create_article(
                niche.id, title="B", body="b", category_ids=[gadgets.id], tag_ids=[guide.id]
            )
            c = await svc.create_article(niche.id, title="C", body="b")
            for article in (a, b, c):
                await svc.transition(niche.id, article.id, "publish", actor="x")

            by_cat, cat_total = await svc.list_published_articles(
                niche.id, category_slug="cookware"
            )
            assert {x.slug for x in by_cat} == {"a"} and cat_total == 1
            by_tag, tag_total = await svc.list_published_articles(niche.id, tag_slug="guide")
            assert {x.slug for x in by_tag} == {"a", "b"} and tag_total == 2
            all_items, all_total = await svc.list_published_articles(niche.id)
            assert all_total == 3

            # Draft/unpublished never appear publicly.
            await svc.transition(niche.id, a.id, "unpublish", actor="x")
            items, total = await svc.list_published_articles(niche.id, tag_slug="guide")
            assert {x.slug for x in items} == {"b"} and total == 1
        finally:
            await engine.dispose()

    _run(scenario())


def test_author_editor_metadata() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            article = await svc.create_article(niche.id, title="G", body="b", actor="writer")
            assert article.editor_ref == "writer"
            assert article.author_ref is None
            article = await svc.transition(niche.id, article.id, "publish", actor="editor-chief")
            assert article.author_ref == "editor-chief"
            article = await svc.transition(niche.id, article.id, "unpublish", actor="editor-chief")
            article = await svc.update_article(niche.id, article.id, actor="copy-editor", body="v2")
            assert article.editor_ref == "copy-editor"
        finally:
            await engine.dispose()

    _run(scenario())


def test_niche_management() -> None:
    async def scenario() -> None:
        svc, engine, _ = await _service()
        try:
            niche = await svc.create_niche(name="Kitchen", slug="kitchen")
            assert niche.status == "draft"
            by_slug = await svc.get_niche_by_slug("kitchen")
            assert by_slug is not None and by_slug.id == niche.id
            updated = await svc.update_niche(niche.id, status="active")
            assert updated.status == "active"
            with pytest.raises(DuplicateError):
                await svc.create_niche(name="Other", slug="kitchen")
            assert len(await svc.list_niches(status="active")) == 1
        finally:
            await engine.dispose()

    _run(scenario())
