"""Repository-layer tests: niche scoping, global references, append-only."""

from datetime import UTC, datetime

from atoz_affiliate_service.domain.entities import (
    AffiliateClick,
    AffiliateLink,
    AffiliateMerchant,
    AffiliateNetwork,
    AffiliateNiche,
    AffiliateProduct,
    AffiliateWebhookLog,
    ClickAttribution,
    LinkToken,
    ProductCategory,
    RevenueTransaction,
)
from atoz_affiliate_service.uuids import uuid7

from .fixtures import build_repositories, scenario


async def _seed(session_factory, service) -> dict:
    uow_factory = service.build_uow(session_factory)
    async with uow_factory.transaction() as unit:
        niche_a = AffiliateNiche(id=uuid7(), slug="niche-a", name="Niche A", status="active")
        niche_b = AffiliateNiche(id=uuid7(), slug="niche-b", name="Niche B", status="draft")
        await unit.affiliate_niches.add(niche_a)
        await unit.affiliate_niches.add(niche_b)
        network = AffiliateNetwork(
            id=uuid7(), code="amazon", name="Amazon Associates", status="active"
        )
        await unit.networks.add(network)
        merchant = AffiliateMerchant(
            id=uuid7(),
            network_id=network.id,
            remote_merchant_id="m-1",
            name="Merchant One",
        )
        await unit.merchants.add(merchant)
        category = ProductCategory(
            id=uuid7(), niche_id=niche_a.id, name="Cooks", slug="cooks", status="active"
        )
        await unit.categories.add(category)
        product = AffiliateProduct(
            id=uuid7(),
            niche_id=niche_a.id,
            merchant_id=merchant.id,
            sku="SKU-1",
            slug="pan",
            name="Pan",
            price_cents=5000,
            currency="USD",
            status="draft",
        )
        await unit.products.add(product)
        link = AffiliateLink(
            id=uuid7(),
            niche_id=niche_a.id,
            product_id=product.id,
            network_id=network.id,
            network_link_url="https://partner.example.com/go",
            status="active",
            disclosure_required=True,
        )
        await unit.links.add(link)
        token = LinkToken(
            id=uuid7(),
            niche_id=niche_a.id,
            affiliate_link_id=link.id,
            token="raw-token-1",
            destination_url="https://partner.example.com/go",
        )
        await unit.tokens.add(token)
        attribution = ClickAttribution(id=uuid7(), niche_id=niche_a.id, source="pinterest")
        await unit.attributions.add(attribution)
        click = AffiliateClick(
            id=uuid7(),
            niche_id=niche_a.id,
            link_token_id=token.id,
            attribution_id=attribution.id,
        )
        await unit.clicks.add(click)
        revenue = RevenueTransaction(
            id=uuid7(),
            niche_id=niche_a.id,
            network_id=network.id,
            affiliate_link_id=link.id,
            affiliate_click_id=click.id,
            network_transaction_id="ntx-1",
            gross_cents=50000,
            commission_cents=2500,
            currency="USD",
            status="pending",
            occurred_at=datetime.now(UTC),
        )
        await unit.revenue.add(revenue)
        return {"niche_a": niche_a.id, "niche_b": niche_b.id, "network": network.id}


def test_niche_repository_scoping() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        await _seed(session_factory, service)
        async with service.build_uow(session_factory).transaction() as unit:
            niche = await unit.affiliate_niches.get_by_slug("niche-a")
            assert niche is not None and niche.name == "Niche A"
            assert await unit.affiliate_niches.slug_exists("niche-a")
            assert not await unit.affiliate_niches.slug_exists("missing")
            assert [n.slug for n in await unit.affiliate_niches.list_by_status("active")] == [
                "niche-a"
            ]

    scenario(runner)


def test_product_queries_are_niche_scoped() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        ids = await _seed(session_factory, service)
        async with service.build_uow(session_factory).transaction() as unit:
            products = await unit.products.list_by_niche(ids["niche_a"])
            assert len(products) == 1
            assert await unit.products.get_scoped(products[0].id, niche_id=ids["niche_b"]) is None
            assert len(await unit.products.list_by_niche(ids["niche_b"])) == 0
            assert await unit.products.count_by_niche(ids["niche_b"]) == 0
            assert await unit.products.slug_exists("pan", niche_id=ids["niche_b"]) is False

    scenario(runner)


def test_categories_and_links_are_niche_scoped() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        ids = await _seed(session_factory, service)
        async with service.build_uow(session_factory).transaction() as unit:
            categories = await unit.categories.list_by_niche(ids["niche_a"])
            assert len(categories) == 1
            assert len(await unit.categories.list_by_niche(ids["niche_b"])) == 0
            assert (
                await unit.categories.get_scoped(categories[0].id, niche_id=ids["niche_b"]) is None
            )
            links = await unit.links.list_by_niche(ids["niche_a"])
            assert len(links) == 1
            assert len(await unit.links.list_by_niche(ids["niche_b"])) == 0

    scenario(runner)


def test_links_tokens_are_niche_scoped() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        ids = await _seed(session_factory, service)
        async with service.build_uow(session_factory).transaction() as unit:
            token = await unit.tokens.get_by_token("raw-token-1")
            assert token is not None
            assert await unit.tokens.get_scoped(token.id, niche_id=ids["niche_b"]) is None
            assert not await unit.tokens.token_exists("raw-token-1", niche_id=ids["niche_b"])

    scenario(runner)


def test_clicks_and_revenue_are_niche_scoped() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        ids = await _seed(session_factory, service)
        async with service.build_uow(session_factory).transaction() as unit:
            assert len(await unit.clicks.list_by_niche(ids["niche_a"])) == 1
            assert len(await unit.clicks.list_by_niche(ids["niche_b"])) == 0
            assert await unit.clicks.count_by_niche(ids["niche_b"]) == 0
            transactions = await unit.revenue.list_by_niche(ids["niche_a"])
            assert len(transactions) == 1
            assert len(await unit.revenue.list_by_niche(ids["niche_b"])) == 0
            assert (
                await unit.revenue.get_scoped(transactions[0].id, niche_id=ids["niche_b"]) is None
            )

    scenario(runner)


def test_revenue_idempotency_lookup_and_sums() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        ids = await _seed(session_factory, service)
        async with service.build_uow(session_factory).transaction() as unit:
            tx = await unit.revenue.get_by_network_transaction(ids["network"], "ntx-1")
            assert tx is not None and tx.commission_cents == 2500
            assert await unit.revenue.sum_commission_cents(ids["niche_a"]) == 2500
            assert await unit.revenue.sum_commission_cents(ids["niche_a"], status="approved") == 0
            assert await unit.revenue.sum_commission_cents(ids["niche_b"]) == 0

    scenario(runner)


def test_webhook_log_idempotency_lookup() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        async with service.build_uow(session_factory).transaction() as unit:
            network = AffiliateNetwork(id=uuid7(), code="impact", name="Impact", status="active")
            await unit.networks.add(network)
            log = AffiliateWebhookLog(
                id=uuid7(),
                network_id=network.id,
                source="impact",
                event_id="evt-1",
                event_type="network.conversion",
                status="processed",
            )
            await unit.webhook_logs.add(log)
        async with service.build_uow(session_factory).transaction() as unit:
            found = await unit.webhook_logs.get_by_source_event("impact", "evt-1")
            assert found is not None and found.status == "processed"
            assert await unit.webhook_logs.get_by_source_event("impact", "evt-2") is None

    scenario(runner)


def test_global_reference_tables_are_not_niche_scoped() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        ids = await _seed(session_factory, service)
        async with service.build_uow(session_factory).transaction() as unit:
            network = await unit.networks.get_by_code("amazon")
            assert network is not None and network.id == ids["network"]
            assert await unit.networks.code_exists("amazon")
            merchants = await unit.merchants.list_by_network(network.id)
            assert len(merchants) == 1
            assert await unit.merchants.get_by_remote(network.id, "m-1") is not None

    scenario(runner)
