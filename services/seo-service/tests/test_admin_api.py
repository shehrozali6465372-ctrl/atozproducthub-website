"""Admin API tests: JWT RBAC, X-Niche-Id tenancy, metadata + sitemap admin."""

from .fixtures import access_token, api_client, build_app, scenario


def test_admin_requires_auth_and_permission() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        async with await api_client(app) as client:
            no_auth = await client.get("/api/v1/admin/niches")
            assert no_auth.status_code == 401
            read_only = await client.get(
                "/api/v1/admin/niches",
                headers={"Authorization": f"Bearer {access_token(permissions=('seo:read',))}"},
            )
            assert read_only.status_code == 200
            write_denied = await client.post(
                "/api/v1/admin/niches",
                headers={"Authorization": f"Bearer {access_token(permissions=('seo:read',))}"},
                json={"name": "Kitchen", "slug": "kitchen"},
            )
            assert write_denied.status_code == 403

    scenario(runner)


def test_admin_requires_niche_header() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        async with await api_client(app) as client:
            response = await client.get(
                "/api/v1/admin/urls",
                headers={"Authorization": f"Bearer {access_token()}"},
            )
            assert response.status_code == 422

    scenario(runner)


def test_admin_register_url_and_metadata_flow() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        service = app.state.seo_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        headers = {
            "Authorization": f"Bearer {access_token()}",
            "X-Niche-Id": niche.id,
        }
        async with await api_client(app) as client:
            created = await client.post(
                "/api/v1/admin/urls",
                headers=headers,
                json={"entity_type": "article", "entity_id": "art-1", "slug": "kitchen-guide"},
            )
            assert created.status_code == 201
            url_id = created.json()["id"]
            meta = await client.post(
                f"/api/v1/admin/urls/{url_id}/metadata",
                headers=headers,
                json={
                    "title": "Kitchen guide",
                    "meta_description": "Everything.",
                    "robots": "index,follow",
                },
            )
            assert meta.status_code == 201
            assert (
                meta.json()["canonical_url"] == "https://atozproducthub.dev/articles/kitchen-guide"
            )
            # Duplicate path for another entity is rejected (409).
            duplicate = await client.post(
                "/api/v1/admin/urls",
                headers=headers,
                json={"entity_type": "product", "entity_id": "prod-1", "slug": "kitchen-guide"},
            )
            assert duplicate.status_code == 409

    scenario(runner)


def test_admin_sitemap_rebuild_and_crawl_report() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured = await build_app()
        service = app.state.seo_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        await service.register_url(
            niche_id=niche.id, entity_type="article", entity_id="art-1", slug="kitchen-guide"
        )
        headers = {
            "Authorization": f"Bearer {access_token()}",
            "X-Niche-Id": niche.id,
        }
        async with await api_client(app) as client:
            rebuilt = await client.post("/api/v1/admin/sitemaps/articles/rebuild", headers=headers)
            assert rebuilt.status_code == 200
            assert rebuilt.json()["shard_count"] == 1
            report = await client.post(
                "/api/v1/admin/crawl-reports",
                headers=headers,
                json={"source": "gsc", "report_date": "2026-08-01", "impressions": 10},
            )
            assert report.status_code == 201
            reports = await client.get("/api/v1/admin/crawl-reports", headers=headers)
            assert reports.status_code == 200
            assert len(reports.json()) == 1

    scenario(runner)
