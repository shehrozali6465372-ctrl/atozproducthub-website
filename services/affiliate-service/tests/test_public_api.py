"""Public Read API tests: published-only, niche-slug tenancy, RFC 7807."""

import asyncio

from atoz_affiliate_service.domain.enums import AffiliateLinkStatus, ProductStatus

from .fixtures import api_client, build_app


def _run(coro):
    return asyncio.run(coro)


async def _seed(svc) -> dict:
    """Create an active niche with one published product."""
    niche = await svc.create_niche(name="Kitchen", slug="kitchen", status="active")
    network = await svc.create_network(code="amazon", name="Amazon Associates")
    merchant = await svc.create_merchant(
        network_id=network.id, remote_merchant_id="m-1", name="Acme Kitchen Co."
    )
    category = await svc.create_category(
        niche_id=niche.id,
        name="Cookware",
        slug="cookware",
        parent_id=None,
        sort_order=1,
        status="active",
    )
    product = await svc.create_product(
        niche_id=niche.id,
        merchant_id=merchant.id,
        sku="SKU-1",
        name="Stainless Pan",
        slug="stainless-pan",
        excerpt="A reliable pan.",
        description_ref=None,
        price_cents=4500,
        currency="USD",
        status="draft",
        category_ids=[category.id],
        primary_category_id=category.id,
    )
    link = await svc.create_link(
        niche_id=niche.id,
        product_id=product.id,
        network_id=network.id,
        network_link_url="https://partner.example.com/go?pid=9",
        default_commission_rate="5%",
        status=AffiliateLinkStatus.ACTIVE,
        disclosure_required=True,
    )
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
        status=ProductStatus.ACTIVE,
    )
    return {"niche": niche, "link": link}


def test_public_products_collection_and_go_flow() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            svc = app.state.affiliate_service
            await _seed(svc)
            async with await api_client(app) as client:
                categories = (
                    await client.get("/api/v1/public/product-categories?niche=kitchen")
                ).json()
                assert [c["slug"] for c in categories] == ["cookware"]

                listing = (await client.get("/api/v1/public/products?niche=kitchen")).json()
                assert listing["total"] == 1
                item = listing["items"][0]
                assert item["slug"] == "stainless-pan"
                assert item["disclosure_required"] is True
                assert item["buy_url"].startswith("/api/v1/public/go/")
                assert item["merchant_name"] == "Acme Kitchen Co."
                assert item["network_name"] == "Amazon Associates"

                detail = (
                    await client.get("/api/v1/public/products/stainless-pan?niche=kitchen")
                ).json()
                assert detail["price_cents"] == 4500
                assert detail["currency"] == "USD"

                collection = (
                    await client.get("/api/v1/public/collections/cookware?niche=kitchen")
                ).json()
                assert collection["total"] == 1

                go = (await client.get(item["buy_url"])).json()
                assert go["destination_url"] == "https://partner.example.com/go?pid=9"
                assert go["disclosure_required"] is True
                assert go["click_id"]

        finally:
            await engine.dispose()

    _run(scenario())


def test_public_hides_drafts_and_requires_active_niche() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            svc = app.state.affiliate_service
            await _seed(svc)
            await svc.create_niche(name="Drafts", slug="drafts", status="draft")
            async with await api_client(app) as client:
                # Draft niche slug is not servable.
                response = await client.get("/api/v1/public/products?niche=drafts")
                assert response.status_code == 422
                assert response.json()["code"] == "UNSUPPORTED_NICHE"
                # Unknown niche slug.
                response = await client.get("/api/v1/public/products?niche=missing")
                assert response.status_code == 422
                # Missing niche parameter.
                response = await client.get("/api/v1/public/products")
                assert response.status_code == 422
                # Unknown product slug -> 404 (never 500).
                response = await client.get("/api/v1/public/products/not-there?niche=kitchen")
                assert response.status_code == 404
                assert response.json()["code"] == "NOT_FOUND"

        finally:
            await engine.dispose()

    _run(scenario())


def test_public_go_rejects_invalid_token_with_404() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            svc = app.state.affiliate_service
            await _seed(svc)
            async with await api_client(app) as client:
                response = await client.get("/go/tampered.invalid")
                assert response.status_code == 404
                assert response.json()["code"] == "NOT_FOUND"

        finally:
            await engine.dispose()

    _run(scenario())


def test_public_cross_niche_isolation_over_http() -> None:
    async def scenario() -> None:
        app, engine, bus, events = await build_app()
        try:
            svc = app.state.affiliate_service
            await _seed(svc)
            await svc.create_niche(name="Travel", slug="travel", status="active")
            async with await api_client(app) as client:
                response = await client.get("/api/v1/public/products?niche=travel")
                assert response.status_code == 200
                assert response.json()["total"] == 0
                response = await client.get("/api/v1/public/products/stainless-pan?niche=travel")
                assert response.status_code == 404

        finally:
            await engine.dispose()

    _run(scenario())
