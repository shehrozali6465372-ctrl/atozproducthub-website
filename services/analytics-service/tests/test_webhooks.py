"""Webhook tests: HMAC verification, idempotency, unknown event types."""

from .fixtures import api_client, build_app, event_signature, scenario


def _payload(event_id: str, event_type: str = "revenue:attributed.v1", **extra: object) -> dict:
    return {
        "type": event_type,
        "event_id": event_id,
        "payload": {
            "niche_id": "00000000-0000-0000-0000-000000000000",
            "transaction_id": "tx-1",
            "amount": 49.99,
            **extra,
        },
        "aggregate_id": "00000000-0000-0000-0000-000000000000",
    }


def test_webhook_rejects_invalid_signature() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, _backbone, _warehouse = await build_app()
        service = app.state.analytics_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        payload = _payload("evt-w001", niche_id=niche.id)
        async with await api_client(app) as client:
            missing = await client.post("/webhooks/v1/analytics/events", json=payload)
            assert missing.status_code == 401
            bad = await client.post(
                "/webhooks/v1/analytics/events",
                json=payload,
                headers={"X-Event-Signature": "deadbeef"},
            )
            assert bad.status_code == 401
            ok = await client.post(
                "/webhooks/v1/analytics/events",
                json=payload,
                headers={"X-Event-Signature": event_signature("wrong-secret", payload)},
            )
            assert ok.status_code == 401

    scenario(runner)


def test_webhook_accepts_revenue_event_and_is_idempotent() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, backbone, warehouse = await build_app()
        service = app.state.analytics_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        payload = _payload("evt-w002", niche_id=niche.id)
        headers = {
            "X-Event-Signature": event_signature(app.state.settings.event_webhook_secret, payload)
        }
        async with await api_client(app) as client:
            first = await client.post(
                "/webhooks/v1/analytics/events", json=payload, headers=headers
            )
            assert first.status_code == 202
            assert first.json()["status"] == "accepted"
            second = await client.post(
                "/webhooks/v1/analytics/events", json=payload, headers=headers
            )
            assert second.status_code == 202
            assert second.json()["status"] == "duplicate"
        assert len(backbone.published) == 0  # drained into the warehouse
        assert len(warehouse.rows) == 1
        assert warehouse.rows[0]["event_type"] == "analytics:revenue_attributed.v1"

    scenario(runner)


def test_webhook_rejects_unknown_domain_event_type() -> None:
    async def runner() -> None:
        app, _engine, _bus, _captured, _backbone, _warehouse = await build_app()
        service = app.state.analytics_service
        assert service is not None
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        payload = _payload("evt-w003", event_type="ai:generated.v1", niche_id=niche.id)
        headers = {
            "X-Event-Signature": event_signature(app.state.settings.event_webhook_secret, payload)
        }
        async with await api_client(app) as client:
            response = await client.post(
                "/webhooks/v1/analytics/events", json=payload, headers=headers
            )
            assert response.status_code == 422

    scenario(runner)
