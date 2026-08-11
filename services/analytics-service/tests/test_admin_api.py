"""Admin API tests: JWT RBAC, X-Niche-Id tenancy, read models, rollups."""

from datetime import date

from .fixtures import access_token, api_client, build_app, scenario


async def _seed(app) -> str:
    service = app.state.analytics_service
    assert service is not None
    niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
    await service.ingest_event(
        niche_slug="kitchen",
        event={
            "event_id": "admin-001",
            "event_type": "page_view",
            "session_id": "s1",
            "page_url": "/articles/kitchen-guide",
            "user_pseudo_id": "u1",
            "occurred_at": "2026-08-01T10:00:00+00:00",
        },
    )
    await service.ingest_event(
        niche_slug="kitchen",
        event={
            "event_id": "admin-002",
            "event_type": "affiliate_click",
            "session_id": "s1",
            "page_url": "/products/pan",
            "user_pseudo_id": "u1",
            "occurred_at": "2026-08-01T11:00:00+00:00",
        },
    )
    return niche.id


def test_admin_requires_auth_and_permission() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, _backbone, _warehouse = await build_app()
        niche_id = await _seed(app)
        headers = {"X-Niche-Id": niche_id}
        async with await api_client(app) as client:
            no_auth = await client.get(
                "/api/v1/admin/overview?from_date=2026-08-01&to_date=2026-08-01", headers=headers
            )
            assert no_auth.status_code == 401
            read_only = await client.get(
                "/api/v1/admin/overview?from_date=2026-08-01&to_date=2026-08-01",
                headers={
                    **headers,
                    "Authorization": f"Bearer {access_token(permissions=('analytics:read',))}",
                },
            )
            assert read_only.status_code == 200
            write_denied = await client.post(
                "/api/v1/admin/rollups?from_date=2026-08-01&to_date=2026-08-01",
                headers={
                    **headers,
                    "Authorization": f"Bearer {access_token(permissions=('analytics:read',))}",
                },
            )
            assert write_denied.status_code == 403

    scenario(runner)


def test_admin_requires_niche_header() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, _backbone, _warehouse = await build_app()
        async with await api_client(app) as client:
            response = await client.get(
                "/api/v1/admin/overview?from_date=2026-08-01&to_date=2026-08-01",
                headers={"Authorization": f"Bearer {access_token()}"},
            )
            assert response.status_code == 422

    scenario(runner)


def test_admin_overview_traffic_metrics_and_rollups() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, _backbone, _warehouse = await build_app()
        niche_id = await _seed(app)
        headers = {
            "Authorization": f"Bearer {access_token()}",
            "X-Niche-Id": niche_id,
        }
        async with await api_client(app) as client:
            rolled = await client.post(
                "/api/v1/admin/rollups?from_date=2026-08-01&to_date=2026-08-01", headers=headers
            )
            assert rolled.status_code == 200
            assert rolled.json()[0]["metric_rows"] >= 1

            overview = await client.get(
                "/api/v1/admin/overview?from_date=2026-08-01&to_date=2026-08-01", headers=headers
            )
            assert overview.status_code == 200
            body = overview.json()
            assert body["pageviews"] == 1
            assert body["affiliate_clicks"] == 1

            traffic = await client.get(
                "/api/v1/admin/traffic?from_date=2026-08-01&to_date=2026-08-01", headers=headers
            )
            assert traffic.status_code == 200
            assert traffic.json()["points"][0]["source"] == "direct"

            metrics = await client.get(
                "/api/v1/admin/metrics?from_date=2026-08-01&to_date=2026-08-01&metric_key=affiliate.clicks",
                headers=headers,
            )
            assert metrics.status_code == 200
            assert metrics.json()["points"][0]["value"] == 1

            top_pages = await client.get(
                "/api/v1/admin/top-pages?from_date=2026-08-01&to_date=2026-08-01", headers=headers
            )
            assert top_pages.status_code == 200
            assert top_pages.json()["rows"][0]["page_url"] == "/articles/kitchen-guide"

            events = await client.get("/api/v1/admin/events?limit=10", headers=headers)
            assert events.status_code == 200
            assert len(events.json()) == 2

            pipeline = await client.get("/api/v1/admin/pipeline", headers=headers)
            assert pipeline.status_code == 200
            assert pipeline.json()["backbone"] == "in-memory"

    scenario(runner)


def test_admin_isolation_blocks_other_niche_queries() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, _backbone, _warehouse = await build_app()
        service = app.state.analytics_service
        assert service is not None
        kitchen = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        travel = await service.create_niche(name="Travel", slug="travel", status="active")
        await service.ingest_event(
            niche_slug="kitchen",
            event={
                "event_id": "iso-k001",
                "event_type": "page_view",
                "session_id": "s1",
                "page_url": "/articles/kitchen",
                "user_pseudo_id": "u1",
                "occurred_at": "2026-08-01T10:00:00+00:00",
            },
        )
        await service.ingest_event(
            niche_slug="travel",
            event={
                "event_id": "iso-t001",
                "event_type": "page_view",
                "session_id": "s2",
                "page_url": "/articles/travel",
                "user_pseudo_id": "u2",
                "occurred_at": "2026-08-01T10:00:00+00:00",
            },
        )
        await service.run_rollups(
            niche_id=kitchen.id, from_date=date(2026, 8, 1), to_date=date(2026, 8, 1)
        )
        await service.run_rollups(
            niche_id=travel.id, from_date=date(2026, 8, 1), to_date=date(2026, 8, 1)
        )
        headers = {"Authorization": f"Bearer {access_token()}", "X-Niche-Id": kitchen.id}
        async with await api_client(app) as client:
            traffic = await client.get(
                "/api/v1/admin/traffic?from_date=2026-08-01&to_date=2026-08-01", headers=headers
            )
            assert traffic.status_code == 200
            points = traffic.json()["points"]
            # Kitchen sees only its own pageviews; travel data is invisible.
            assert sum(p["pageviews"] for p in points) == 1
            events = await client.get("/api/v1/admin/events?limit=50", headers=headers)
            assert len(events.json()) == 1
            assert events.json()[0]["page_url"] == "/articles/kitchen"

    scenario(runner)
