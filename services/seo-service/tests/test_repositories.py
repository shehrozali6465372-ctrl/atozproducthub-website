"""Repository isolation tests: niche scoping, duplicate-URL prevention."""

from .fixtures import build_service, scenario


def test_url_registry_scoped_queries() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        n1 = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        n2 = await service.create_niche(name="Travel", slug="travel", status="active")
        url1 = await service.register_url(
            niche_id=n1.id, entity_type="article", entity_id="a", slug="guide"
        )
        await service.register_url(
            niche_id=n2.id, entity_type="article", entity_id="b", slug="guide"
        )
        # Metadata read-back returns safe defaults (never a cross-niche leak).
        for niche_id in (n1.id, n2.id):
            meta = await service.get_metadata_for_path(niche_id=niche_id, path="/articles/guide")
            assert meta is not None
            assert meta["robots"] == "index,follow"
        # Unknown paths still resolve to nothing.
        assert await service.get_metadata_for_path(niche_id=n1.id, path="/admin") is None
        # URL listing is niche-scoped.
        urls_n1 = await service.list_urls(n1.id)
        urls_n2 = await service.list_urls(n2.id)
        assert [u.id for u in urls_n1] == [url1.id]
        assert len(urls_n2) == 1

    scenario(runner)


def test_sitemap_shards_are_niche_scoped() -> None:
    async def runner() -> None:
        _session_factory, service = await build_service()
        n1 = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        n2 = await service.create_niche(name="Travel", slug="travel", status="active")
        for index in range(5):
            await service.register_url(
                niche_id=n1.id, entity_type="article", entity_id=f"a{index}", slug=f"a{index}"
            )
        await service.rebuild_sitemap_group(niche_id=n1.id, group_name="articles")
        # Niche 2 has no shards (cross-niche sitemap reads are empty).
        assert await service.render_sitemap_index(niche_id=n2.id, group_name="articles") is None
        shards = await service.list_sitemap_shards(n1.id, group_name="articles")
        assert len(shards) == 2

    scenario(runner)
