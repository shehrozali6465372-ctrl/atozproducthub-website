"""Collector tests: validation, idempotency, sensitive-data guard, batch."""

from .fixtures import api_client, build_app, make_settings, scenario


def _event(event_id: str, **overrides: object) -> dict:
    payload: dict = {
        "event_id": event_id,
        "event_type": "page_view",
        "session_id": "sess-1",
        "page_url": "/articles/kitchen-guide",
        "user_pseudo_id": "u-1",
        "traits": {"device": "mobile", "country": "US"},
    }
    payload.update(overrides)
    return payload


def test_collector_accepts_valid_event_and_is_idempotent() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, backbone, warehouse = await build_app()
        service = app.state.analytics_service
        assert service is not None
        await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        async with await api_client(app) as client:
            first = await client.post("/collect/v1/events?niche=kitchen", json=_event("evt-0001"))
            assert first.status_code == 202
            body = first.json()
            assert body["status"] == "accepted"
            assert body["event_id"] == "evt-0001"
            assert body["ledger_id"]

            duplicate = await client.post(
                "/collect/v1/events?niche=kitchen", json=_event("evt-0001")
            )
            assert duplicate.status_code == 202
            assert duplicate.json()["status"] == "duplicate"
            assert duplicate.json()["ledger_id"] is None
        # Append-only ledger: exactly one row; pipeline drained one envelope.
        assert len(backbone.published) == 0
        assert len(warehouse.rows) == 1
        assert warehouse.rows[0]["event_id"] == "evt-0001"

    scenario(runner)


def test_collector_rejects_unknown_type_unknown_niche_and_sensitive_traits() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, _backbone, _warehouse = await build_app()
        service = app.state.analytics_service
        assert service is not None
        await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        async with await api_client(app) as client:
            bad_type = await client.post(
                "/collect/v1/events?niche=kitchen",
                json=_event("evt-0002", event_type="ai_inference"),
            )
            assert bad_type.status_code == 422

            unknown_niche = await client.post(
                "/collect/v1/events?niche=nope", json=_event("evt-0003")
            )
            assert unknown_niche.status_code == 422

            sensitive = await client.post(
                "/collect/v1/events?niche=kitchen",
                json=_event("evt-0004", traits={"email": "user@example.com"}),
            )
            assert sensitive.status_code == 422

    scenario(runner)


def test_collector_batch_isolates_failures() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, _backbone, _warehouse = await build_app(
            settings=make_settings(collector_max_batch_size=10)
        )
        service = app.state.analytics_service
        assert service is not None
        await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        async with await api_client(app) as client:
            response = await client.post(
                "/collect/v1/events/batch?niche=kitchen",
                json={
                    "events": [
                        _event("evt-batch-01"),
                        _event("evt-batch-02", event_type="not_a_type"),
                        _event("evt-batch-01"),  # duplicate
                    ]
                },
            )
            assert response.status_code == 202
            body = response.json()
            assert body["accepted"] == 1
            assert body["duplicates"] == 1
            assert body["rejected"] == 1

    scenario(runner)
