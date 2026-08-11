"""SeoService tests: URL registry, metadata, sitemap rebuild, event-driven
indexing/de-indexing, niche isolation, and crawl-report boundaries."""

from atoz_affiliate_service.domain.events import product_ingested_event, product_removed_event
from atoz_content_service.domain.events import (
    content_published_event,
    content_unpublished_event,
    content_updated_event,
)
from atoz_seo_service.domain.sitemaps import validate_no_private_urls, validate_xml
from atoz_seo_service.errors import DuplicateError

from .fixtures import build_service, scenario


async def _seed(service):
    niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
    article = await service.register_url(
        niche_id=niche.id, entity_type="article", entity_id="art-1", slug="kitchen-guide"
    )
    await service.upsert_metadata(
        niche_id=niche.id,
        url_registry_id=article.id,
        title="Kitchen guide",
        meta_description="Everything kitchen.",
        robots="index,follow",
    )
    return niche, article


def test_register_url_duplicate_prevention() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        await service.register_url(
            niche_id=niche.id, entity_type="article", entity_id="art-1", slug="kitchen-guide"
        )
        try:
            # Same path claimed by a different entity is a duplicate (409).
            await service.register_url(
                niche_id=niche.id,
                entity_type="product",
                entity_id="prod-1",
                path="/articles/kitchen-guide",
            )
            raise AssertionError("expected DuplicateError")
        except DuplicateError:
            pass

    scenario(runner)


def test_same_path_allowed_in_different_niches() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        n1 = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        n2 = await service.create_niche(name="Travel", slug="travel", status="active")
        a = await service.register_url(
            niche_id=n1.id, entity_type="article", entity_id="a", slug="guide"
        )
        b = await service.register_url(
            niche_id=n2.id, entity_type="article", entity_id="b", slug="guide"
        )
        assert a.path == b.path == "/articles/guide"
        assert a.id != b.id

    scenario(runner)


def test_metadata_upsert_and_read_back() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        niche, article = await _seed(service)
        meta = await service.get_metadata_for_path(
            niche_id=niche.id, path="/articles/kitchen-guide"
        )
        assert meta is not None
        assert meta["title"] == "Kitchen guide"
        assert meta["canonical_url"] == "https://atozproducthub.dev/articles/kitchen-guide"
        assert meta["robots"] == "index,follow"
        # Unknown paths resolve to nothing (never a private leak).
        assert (
            await service.get_metadata_for_path(niche_id=niche.id, path="/admin/dashboard") is None
        )

    scenario(runner)


def test_sitemap_rebuild_shards_and_renders() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        for index in range(7):
            await service.register_url(
                niche_id=niche.id,
                entity_type="article",
                entity_id=f"art-{index}",
                slug=f"guide-{index}",
            )
        shards = await service.rebuild_sitemap_group(niche_id=niche.id, group_name="articles")
        assert len(shards) == 3  # sitemap_max_urls=3 in test settings
        xml = await service.render_sitemap_shard(
            niche_id=niche.id, group_name="articles", shard_no=1
        )
        assert xml is not None
        validate_xml(xml)
        validate_no_private_urls(xml)
        index_xml = await service.render_sitemap_index(niche_id=niche.id, group_name="articles")
        assert index_xml is not None
        validate_xml(index_xml)

    scenario(runner)


def test_content_published_indexes_and_unpublished_deindexes() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        await service.handle_event(
            content_published_event(
                article_id="art-1",
                niche_id=niche.id,
                url="/articles/kitchen-guide",
                checksum="abc",
            )
        )
        found = await service.search(query="untitled", niche_id=niche.id)
        assert found.total == 1
        # Re-index on update is idempotent.
        await service.handle_event(
            content_updated_event(article_id="art-1", niche_id=niche.id, status="published")
        )
        assert (await service.search(query="untitled", niche_id=niche.id)).total == 1
        await service.handle_event(content_unpublished_event(article_id="art-1", niche_id=niche.id))
        assert (await service.search(query="untitled", niche_id=niche.id)).total == 0

    scenario(runner)


def test_product_ingested_indexes_and_removed_deindexes() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        await service.handle_event(
            product_ingested_event(product_id="prod-1", niche_id=niche.id, checksum="xyz")
        )
        page = await service.search(query="product", niche_id=niche.id, types=["product"])
        assert page.total == 1
        await service.handle_event(product_removed_event(product_id="prod-1", niche_id=niche.id))
        assert (await service.search(query="product", niche_id=niche.id)).total == 0

    scenario(runner)


def test_event_indexing_is_niche_isolated() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        n1 = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        n2 = await service.create_niche(name="Travel", slug="travel", status="active")
        await service.handle_event(
            content_published_event(article_id="a", niche_id=n1.id, url="/articles/a", checksum="1")
        )
        await service.handle_event(
            content_published_event(article_id="b", niche_id=n2.id, url="/articles/b", checksum="2")
        )
        assert (await service.search(query="untitled", niche_id=n1.id)).total == 1
        assert (await service.search(query="untitled", niche_id=n2.id)).total == 1
        # De-indexing in niche 1 must never touch niche 2.
        await service.handle_event(content_unpublished_event(article_id="a", niche_id=n1.id))
        assert (await service.search(query="untitled", niche_id=n2.id)).total == 1

    scenario(runner)


def test_crawl_report_boundary_and_records() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        report = await service.record_crawl_report(
            niche_id=niche.id, source="gsc", report_date="2026-08-01", impressions=100, clicks=5
        )
        assert report.source == "gsc"
        assert report.impressions == 100
        rows = await service.list_crawl_reports(niche.id, source="gsc")
        assert len(rows) == 1
        # Unsupported source is rejected.
        try:
            await service.record_crawl_report(
                niche_id=niche.id, source="yahoo", report_date="2026-08-01"
            )
            raise AssertionError("expected ValidationError")
        except Exception as exc:
            assert "source" in str(exc)

    scenario(runner)


def test_health_check_records() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        row = await service.record_health_check(
            niche_id=niche.id, check_type="core_web_vitals", score=0.95, details={"lcp": 1.2}
        )
        assert row.score == 0.95
        rows = await service.list_health_checks(niche.id)
        assert len(rows) == 1

    scenario(runner)
