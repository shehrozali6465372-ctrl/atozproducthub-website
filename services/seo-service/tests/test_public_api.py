"""Public API tests: metadata, robots, sitemaps, and niche-scoped search."""

from .fixtures import api_client, build_app, make_settings, scenario


async def _seed(service, *, niche_id: str) -> None:
    article = await service.register_url(
        niche_id=niche_id, entity_type="article", entity_id="art-1", slug="kitchen-guide"
    )
    await service.upsert_metadata(
        niche_id=niche_id,
        url_registry_id=article.id,
        title="Kitchen guide",
        meta_description="Everything kitchen.",
    )
    await service.index_document(
        __import__("atoz_seo_service.domain.search", fromlist=["SearchDocument"]).SearchDocument(
            id="art-1",
            type="article",
            niche_id=niche_id,
            slug="kitchen-guide",
            title="Kitchen guide",
            excerpt="Everything kitchen.",
            url="/articles/kitchen-guide",
        )
    )


def test_public_metadata_and_robots_and_search() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        service = app.state.seo_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        await _seed(service, niche_id=niche.id)
        async with await api_client(app) as client:
            meta = await client.get(
                "/api/v1/public/seo/meta?niche=kitchen&path=/articles/kitchen-guide"
            )
            assert meta.status_code == 200
            body = meta.json()
            assert body["title"] == "Kitchen guide"
            assert body["canonical_url"] == "https://atozproducthub.dev/articles/kitchen-guide"

            robots = await client.get("/api/v1/public/seo/robots?niche=kitchen")
            assert robots.status_code == 200
            assert "Pinterestbot" in robots.text
            assert "Disallow: /admin" in robots.text

            search = await client.get("/api/v1/public/search?niche=kitchen&q=kitchen")
            assert search.status_code == 200
            results = search.json()
            assert results["total"] == 1
            assert results["items"][0]["id"] == "art-1"

    scenario(runner)


def test_public_search_never_leaks_across_niches() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        service = app.state.seo_service
        assert service is not None
        n1 = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        n2 = await service.create_niche(name="Travel", slug="travel", status="active")
        await _seed(service, niche_id=n1.id)
        await service.index_document(
            __import__(
                "atoz_seo_service.domain.search", fromlist=["SearchDocument"]
            ).SearchDocument(
                id="art-2",
                type="article",
                niche_id=n2.id,
                slug="pack-light",
                title="Pack light guide",
                excerpt="Travel.",
                url="/articles/pack-light",
            )
        )
        async with await api_client(app) as client:
            kitchen = await client.get("/api/v1/public/search?niche=kitchen&q=guide")
            travel = await client.get("/api/v1/public/search?niche=travel&q=guide")
            assert [item["id"] for item in kitchen.json()["items"]] == ["art-1"]
            assert [item["id"] for item in travel.json()["items"]] == ["art-2"]

    scenario(runner)


def test_public_sitemap_shard_and_index() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app(settings=make_settings(sitemap_max_urls=2))
        service = app.state.seo_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        for index in range(3):
            await service.register_url(
                niche_id=niche.id, entity_type="article", entity_id=f"a{index}", slug=f"a{index}"
            )
        await service.rebuild_sitemap_group(niche_id=niche.id, group_name="articles")
        async with await api_client(app) as client:
            shard = await client.get("/api/v1/public/seo/sitemaps/articles-1.xml?niche=kitchen")
            assert shard.status_code == 200
            assert "urlset" in shard.text and "<loc>" in shard.text
            index = await client.get("/api/v1/public/seo/sitemaps/articles-index.xml?niche=kitchen")
            assert index.status_code == 200
            assert "sitemapindex" in index.text
            # Unknown shard is a 404 (never an error page with private data).
            missing = await client.get("/api/v1/public/seo/sitemaps/articles-99.xml?niche=kitchen")
            assert missing.status_code == 404

    scenario(runner)


def test_public_routes_reject_unknown_niche() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        async with await api_client(app) as client:
            response = await client.get("/api/v1/public/search?niche=nope&q=x")
            assert response.status_code == 422

    scenario(runner)


def test_health_and_ready_unchanged() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        async with await api_client(app) as client:
            health = await client.get("/health")
            assert health.status_code == 200
            assert health.json()["service"] == "seo-service"

    scenario(runner)
