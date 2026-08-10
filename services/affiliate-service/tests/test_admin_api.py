"""Admin API tests: JWT RBAC, X-Niche-Id tenancy, cross-niche isolation."""

import asyncio

from .fixtures import (
    TEST_JWT_SECRET,
    TEST_READ_PERMISSIONS,
    TEST_WRITE_PERMISSIONS,
    access_token,
    api_client,
    build_app,
)


def _run(coro):
    return asyncio.run(coro)


def _headers(token: str, niche_id: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if niche_id:
        headers["X-Niche-Id"] = niche_id
    return headers


def test_admin_requires_authentication() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            async with await api_client(app) as client:
                response = await client.get("/api/v1/admin/networks")
                assert response.status_code == 401
                assert response.json()["code"] == "UNAUTHENTICATED"
        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_requires_permission() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            read_only = access_token(secret=TEST_JWT_SECRET, permissions=TEST_READ_PERMISSIONS)
            async with await api_client(app) as client:
                response = await client.post(
                    "/api/v1/admin/networks",
                    headers=_headers(read_only),
                    json={"code": "amazon", "name": "Amazon"},
                )
                assert response.status_code == 403
                assert response.json()["code"] == "FORBIDDEN"
        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_niche_mirror_and_network_flow() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            token = access_token(secret=TEST_JWT_SECRET, permissions=TEST_WRITE_PERMISSIONS)
            async with await api_client(app) as client:
                # Provision the local tenancy mirror.
                created = await client.post(
                    "/api/v1/admin/niches",
                    headers=_headers(token),
                    json={"name": "Kitchen", "slug": "kitchen", "status": "active"},
                )
                assert created.status_code == 201
                niche_id = created.json()["id"]

                # Networks are global reference tables (RBAC only).
                network = await client.post(
                    "/api/v1/admin/networks",
                    headers=_headers(token),
                    json={"code": "amazon", "name": "Amazon Associates"},
                )
                assert network.status_code == 201
                network_id = network.json()["id"]

                merchant = await client.post(
                    "/api/v1/admin/merchants",
                    headers=_headers(token),
                    json={
                        "network_id": network_id,
                        "remote_merchant_id": "m-1",
                        "name": "Acme Co.",
                    },
                )
                assert merchant.status_code == 201

                # Niche-scoped routes require X-Niche-Id.
                response = await client.get(
                    "/api/v1/admin/product-categories", headers=_headers(token)
                )
                assert response.status_code == 422

                category = await client.post(
                    "/api/v1/admin/product-categories",
                    headers=_headers(token, niche_id),
                    json={"name": "Cookware", "slug": "cookware"},
                )
                assert category.status_code == 201

        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_cross_niche_isolation_over_http() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            svc = app.state.affiliate_service
            token = access_token(secret=TEST_JWT_SECRET, permissions=TEST_WRITE_PERMISSIONS)
            niche_a = await svc.create_niche(name="Kitchen", slug="kitchen", status="active")
            niche_b = await svc.create_niche(name="Travel", slug="travel", status="active")
            network = await svc.create_network(code="amazon", name="Amazon")
            merchant = await svc.create_merchant(
                network_id=network.id, remote_merchant_id="m-1", name="Acme"
            )
            product = await svc.create_product(
                niche_id=niche_a.id,
                merchant_id=merchant.id,
                sku="SKU-1",
                name="Pan",
                slug="pan",
                excerpt="",
                description_ref=None,
                price_cents=100,
                currency="USD",
                status="draft",
                category_ids=[],
                primary_category_id=None,
            )
            async with await api_client(app) as client:
                # Niche B cannot read niche A's product.
                response = await client.get(
                    f"/api/v1/admin/products/{product.id}",
                    headers=_headers(token, niche_b.id),
                )
                assert response.status_code == 404
                # Niche B cannot mutate niche A's product.
                response = await client.patch(
                    f"/api/v1/admin/products/{product.id}",
                    headers=_headers(token, niche_b.id),
                    json={"name": "Hijacked"},
                )
                assert response.status_code == 404
                # Niche A can read its own product.
                response = await client.get(
                    f"/api/v1/admin/products/{product.id}",
                    headers=_headers(token, niche_a.id),
                )
                assert response.status_code == 200
                assert response.json()["name"] == "Pan"

        finally:
            await engine.dispose()

    _run(scenario())


def test_admin_webhook_receiver_http() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            svc = app.state.affiliate_service
            niche = await svc.create_niche(name="Kitchen", slug="kitchen", status="active")
            network = await svc.create_network(code="amazon", name="Amazon")
            merchant = await svc.create_merchant(
                network_id=network.id, remote_merchant_id="m-1", name="Acme"
            )
            product = await svc.create_product(
                niche_id=niche.id,
                merchant_id=merchant.id,
                sku="SKU-1",
                name="Pan",
                slug="pan",
                excerpt="",
                description_ref=None,
                price_cents=100,
                currency="USD",
                status="draft",
                category_ids=[],
                primary_category_id=None,
            )
            link = await svc.create_link(
                niche_id=niche.id,
                product_id=product.id,
                network_id=network.id,
                network_link_url="https://partner.example.com/go",
                default_commission_rate="5%",
                status="active",
                disclosure_required=True,
            )
            from atoz_affiliate_service.domain.tokens import _hmac_hex
            from atoz_affiliate_service.errors import ValidationError

            from .fixtures import make_settings

            try:
                await svc.update_product(
                    product.id,
                    niche_id=niche.id,
                    merchant_id=None,
                    sku=None,
                    name=None,
                    slug=None,
                    excerpt=None,
                    description_ref=None,
                    price_cents=None,
                    currency=None,
                    category_ids=None,
                    primary_category_id=None,
                    status="active",
                )
            except ValidationError:
                pass
            tokens = await svc.list_tokens(link.id, niche_id=niche.id)
            raw = tokens[0].token
            signed = f"{raw}.{_hmac_hex(raw, secret=make_settings().token_signing_secret)}"
            await svc.resolve_redirect(signed)

            import hashlib
            import hmac
            import json
            from datetime import UTC, datetime

            payload = {
                "transaction_id": "tx-1",
                "status": "pending",
                "amount_cents": 1000,
                "gross_cents": 20000,
                "currency": "USD",
                "click_token": signed,
                "occurred_at": datetime.now(UTC).isoformat(),
            }
            body = json.dumps(
                {
                    "event_id": "evt-1",
                    "type": "network.conversion",
                    "version": "v1",
                    "source": "amazon",
                    "occurred_at": datetime.now(UTC).isoformat(),
                    "payload": payload,
                }
            ).encode()
            signature = hmac.new(b"test-network-webhook-secret", body, hashlib.sha256).hexdigest()
            async with await api_client(app) as client:
                response = await client.post(
                    "/webhooks/v1/amazon/conversion",
                    content=body,
                    headers={"X-Webhook-Signature": signature},
                )
                assert response.status_code == 202
                assert response.json()["status"] == "accepted"
                # Invalid signature -> 400 problem+json.
                response = await client.post(
                    "/webhooks/v1/amazon/conversion",
                    content=body,
                    headers={"X-Webhook-Signature": "bad"},
                )
                assert response.status_code == 400
                assert response.json()["code"] == "VALIDATION_FAILED"

        finally:
            await engine.dispose()

    _run(scenario())
