"""Service-layer tests: CRUD, redirect security, disclosure, niche isolation,
conversion webhooks, commission lifecycle, revenue, reconciliation."""

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

import pytest

from atoz_affiliate_service.domain.enums import AffiliateLinkStatus, CommissionStatus, ProductStatus
from atoz_affiliate_service.domain.tokens import new_signed_token
from atoz_affiliate_service.errors import (
    DuplicateError,
    NotFoundError,
    RedirectForbiddenError,
    ValidationError,
    WebhookRejectedError,
)

from .fixtures import (
    TEST_NETWORK_SECRET,
    build_repositories,
    make_settings,
    scenario,
)


async def _seed(svc) -> dict:
    """Create an active niche, network, merchant, category, and draft product."""
    niche = await svc.create_niche(name="Kitchen", slug="kitchen", status="active")
    network = await svc.create_network(code="amazon", name="Amazon Associates")
    merchant = await svc.create_merchant(
        network_id=network.id, remote_merchant_id="m-100", name="Acme Kitchen Co."
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
        sku="SKU-PAN-1",
        name="Stainless Steel Pan",
        slug="stainless-pan",
        excerpt="A reliable pan.",
        description_ref="s3://content/products/stainless-pan.md",
        price_cents=4500,
        currency="USD",
        status="draft",
        category_ids=[category.id],
        primary_category_id=category.id,
    )
    return {
        "niche": niche,
        "network": network,
        "merchant": merchant,
        "category": category,
        "product": product,
    }


async def _seed_active_product(svc) -> dict:
    """Seed a fully public product (draft product + active disclosure link)."""
    data = await _seed(svc)
    link = await svc.create_link(
        niche_id=data["niche"].id,
        product_id=data["product"].id,
        network_id=data["network"].id,
        network_link_url="https://partner.example.com/go?pid=100",
        default_commission_rate="5%",
        status=AffiliateLinkStatus.ACTIVE,
        disclosure_required=True,
    )
    activated = await svc.update_product(
        data["product"].id,
        niche_id=data["niche"].id,
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
    data["link"] = link
    data["product"] = activated
    return data


def test_niche_mirror_crud_and_slug_uniqueness() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        niche = await svc.create_niche(name="Kitchen", slug="kitchen")
        assert niche.slug == "kitchen"
        with pytest.raises(DuplicateError):
            await svc.create_niche(name="Other", slug="kitchen")
        updated = await svc.update_niche(niche.id, name="Kitchen Pro", slug=None, status="active")
        assert updated.name == "Kitchen Pro" and updated.status == "active"
        assert (await svc.get_niche_by_slug("kitchen")) is not None
        with pytest.raises(NotFoundError):
            await svc.update_niche("missing-id", name="X", slug=None, status=None)

    scenario(runner)


def test_network_and_merchant_crud() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        network = await svc.create_network(code="impact", name="Impact Radius")
        assert (await svc.get_network_by_code("impact")) is not None
        with pytest.raises(DuplicateError):
            await svc.create_network(code="impact", name="Dup")
        merchant = await svc.create_merchant(
            network_id=network.id, remote_merchant_id="r1", name="Merchant A"
        )
        with pytest.raises(DuplicateError):
            await svc.create_merchant(
                network_id=network.id, remote_merchant_id="r1", name="Merchant A dup"
            )
        with pytest.raises(ValidationError):
            await svc.create_merchant(
                network_id="missing-network", remote_merchant_id="r2", name="Merchant B"
            )
        updated = await svc.update_merchant(
            merchant.id, name="Merchant A+", status=None, commission_terms_json=None
        )
        assert updated.name == "Merchant A+"

    scenario(runner)


def test_category_crud_is_niche_scoped() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed(svc)
        other_niche = await svc.create_niche(name="Travel", slug="travel", status="active")
        assert await svc.get_category(data["category"].id, niche_id=other_niche.id) is None
        with pytest.raises(DuplicateError):
            await svc.create_category(
                niche_id=data["niche"].id,
                name="Cookware 2",
                slug="cookware",
                parent_id=None,
                sort_order=0,
                status="active",
            )
        # Parent must belong to the same niche.
        with pytest.raises(ValidationError):
            await svc.create_category(
                niche_id=other_niche.id,
                name="Child",
                slug="child",
                parent_id=data["category"].id,
                sort_order=0,
                status="active",
            )

    scenario(runner)


def test_product_cannot_be_created_active() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed(svc)
        with pytest.raises(ValidationError):
            await svc.create_product(
                niche_id=data["niche"].id,
                merchant_id=data["merchant"].id,
                sku="SKU-X",
                name="X",
                slug="x",
                excerpt="",
                description_ref=None,
                price_cents=100,
                currency="USD",
                status=ProductStatus.ACTIVE,
                category_ids=[],
                primary_category_id=None,
            )

    scenario(runner)


def test_disclosure_enforcement_blocks_activation_without_link() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed(svc)
        with pytest.raises(ValidationError):
            await svc.update_product(
                data["product"].id,
                niche_id=data["niche"].id,
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

    scenario(runner)


def test_disclosure_enforcement_requires_disclosure_required_link() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed(svc)
        await svc.create_link(
            niche_id=data["niche"].id,
            product_id=data["product"].id,
            network_id=data["network"].id,
            network_link_url="https://partner.example.com/go?pid=1",
            default_commission_rate="5%",
            status=AffiliateLinkStatus.ACTIVE,
            disclosure_required=False,
        )
        with pytest.raises(ValidationError):
            await svc.update_product(
                data["product"].id,
                niche_id=data["niche"].id,
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

    scenario(runner)


def test_product_activation_with_disclosure_link_and_lifecycle() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed(svc)
        link = await svc.create_link(
            niche_id=data["niche"].id,
            product_id=data["product"].id,
            network_id=data["network"].id,
            network_link_url="https://partner.example.com/go?pid=2",
            default_commission_rate="5%",
            status=AffiliateLinkStatus.ACTIVE,
            disclosure_required=True,
        )
        assert link.status == AffiliateLinkStatus.ACTIVE
        activated = await svc.update_product(
            data["product"].id,
            niche_id=data["niche"].id,
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
        assert activated.status == ProductStatus.ACTIVE
        # Active product slug cannot change (public URL stability).
        with pytest.raises(ValidationError):
            await svc.update_product(
                activated.id,
                niche_id=data["niche"].id,
                merchant_id=None,
                sku=None,
                name=None,
                slug="new-slug",
                excerpt=None,
                description_ref=None,
                price_cents=None,
                currency=None,
                category_ids=None,
                primary_category_id=None,
                status=None,
            )
        await svc.delete_product(activated.id, niche_id=data["niche"].id)
        assert await svc.get_product(activated.id, niche_id=data["niche"].id) is None

    scenario(runner)


def test_link_token_lifecycle() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed(svc)
        link = await svc.create_link(
            niche_id=data["niche"].id,
            product_id=data["product"].id,
            network_id=data["network"].id,
            network_link_url="https://partner.example.com/go?pid=3",
            default_commission_rate="5%",
            status=AffiliateLinkStatus.ACTIVE,
            disclosure_required=True,
        )
        tokens = await svc.list_tokens(link.id, niche_id=data["niche"].id)
        assert len(tokens) == 1  # auto token on activation
        issued = await svc.create_token(
            link.id, niche_id=data["niche"].id, params={"campaign": "summer"}
        )
        assert issued.destination_url == link.network_link_url
        revoked = await svc.revoke_token(issued.id, niche_id=data["niche"].id)
        assert revoked.revoked_at is not None
        with pytest.raises(NotFoundError):
            await svc.revoke_token(issued.id, niche_id="other-niche")

    scenario(runner)


def test_redirect_flow_records_click_and_returns_stored_destination() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        tokens = await svc.list_tokens(data["link"].id, niche_id=data["niche"].id)
        signed = new_signed_token(secret=make_settings().token_signing_secret)
        # Use the server-issued token; sign it with the same secret.
        raw = tokens[0].token
        from atoz_affiliate_service.domain.tokens import _hmac_hex

        signed = f"{raw}.{_hmac_hex(raw, secret=make_settings().token_signing_secret)}"
        destination, disclosure, click_id = await svc.resolve_redirect(
            signed,
            request_ip="1.2.3.4",
            user_agent="Mozilla/5.0",
            source="pinterest",
            utm_params={"utm_source": "pinterest", "utm_medium": "pin"},
        )
        assert destination == data["link"].network_link_url
        assert disclosure is True
        clicks = await svc.list_clicks(data["niche"].id, page=1, page_size=10)
        assert clicks[1] == 1
        assert clicks[0][0].ip_hash == hashlib.sha256(b"1.2.3.4").hexdigest()

    scenario(runner)


def test_redirect_rejects_invalid_signature() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        await _seed_active_product(svc)
        with pytest.raises(RedirectForbiddenError):
            await svc.resolve_redirect("garbage.invalidsig")

    scenario(runner)


def test_redirect_rejects_disabled_and_revoked_links() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        tokens = await svc.list_tokens(data["link"].id, niche_id=data["niche"].id)
        raw = tokens[0].token
        from atoz_affiliate_service.domain.tokens import _hmac_hex

        settings = make_settings()
        signed = f"{raw}.{_hmac_hex(raw, secret=settings.token_signing_secret)}"
        # Disable the link: redirect must fail with the indistinguishable 404.
        await svc.update_link(
            data["link"].id,
            niche_id=data["niche"].id,
            network_link_url=None,
            default_commission_rate=None,
            status=AffiliateLinkStatus.DISABLED,
            disclosure_required=None,
        )
        with pytest.raises(RedirectForbiddenError):
            await svc.resolve_redirect(signed)
        # Re-enable and revoke the token instead.
        await svc.update_link(
            data["link"].id,
            niche_id=data["niche"].id,
            network_link_url=None,
            default_commission_rate=None,
            status=AffiliateLinkStatus.ACTIVE,
            disclosure_required=None,
        )
        await svc.revoke_token(tokens[0].id, niche_id=data["niche"].id)
        with pytest.raises(RedirectForbiddenError):
            await svc.resolve_redirect(signed)

    scenario(runner)


def test_open_redirect_prevention_browser_url_never_used() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        tokens = await svc.list_tokens(data["link"].id, niche_id=data["niche"].id)
        raw = tokens[0].token
        from atoz_affiliate_service.domain.tokens import _hmac_hex

        signed = f"{raw}.{_hmac_hex(raw, secret=make_settings().token_signing_secret)}"
        # A browser-supplied destination query cannot override the stored URL:
        # resolve_redirect accepts no destination parameter at all.
        destination, _, _ = await svc.resolve_redirect(signed)
        assert destination == data["link"].network_link_url
        assert "evil.example.com" not in destination

    scenario(runner)


def _webhook_body(**payload_overrides) -> bytes:
    payload = {
        "transaction_id": "tx-100",
        "status": "approved",
        "amount_cents": 2500,
        "gross_cents": 50000,
        "currency": "USD",
        "click_token": None,
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    payload.update(payload_overrides)
    return json.dumps(
        {
            "event_id": "evt-100",
            "type": "network.conversion",
            "version": "v1",
            "source": "amazon",
            "occurred_at": datetime.now(UTC).isoformat(),
            "nonce": "nonce-1",
            "payload": payload,
        }
    ).encode()


def _sig(raw: bytes) -> str:
    return hmac.new(TEST_NETWORK_SECRET.encode(), raw, hashlib.sha256).hexdigest()


def test_conversion_webhook_full_flow() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        tokens = await svc.list_tokens(data["link"].id, niche_id=data["niche"].id)
        from atoz_affiliate_service.domain.tokens import _hmac_hex

        raw_token = tokens[0].token
        signed_click = (
            f"{raw_token}.{_hmac_hex(raw_token, secret=make_settings().token_signing_secret)}"
        )
        destination, _, click_id = await svc.resolve_redirect(signed_click)
        assert destination
        body = _webhook_body(click_token=signed_click)
        transaction, duplicate = await svc.process_conversion(
            network_code="amazon", raw_body=body, signature=_sig(body)
        )
        assert transaction is not None
        assert duplicate is False
        assert transaction.commission_cents == 2500
        assert transaction.status == CommissionStatus.APPROVED
        assert transaction.affiliate_click_id == click_id
        dashboard = await svc.revenue_dashboard(data["niche"].id)
        assert dashboard["approved_commission_cents"] == 2500
        assert dashboard["click_count"] == 1

    scenario(runner)


def test_conversion_webhook_invalid_signature_rejected() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        await _seed_active_product(svc)
        body = _webhook_body()
        with pytest.raises(WebhookRejectedError):
            await svc.process_conversion(
                network_code="amazon", raw_body=body, signature="invalid-signature"
            )

    scenario(runner)


def test_conversion_webhook_duplicate_delivery_is_idempotent() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        tokens = await svc.list_tokens(data["link"].id, niche_id=data["niche"].id)
        from atoz_affiliate_service.domain.tokens import _hmac_hex

        raw_token = tokens[0].token
        signed_click = (
            f"{raw_token}.{_hmac_hex(raw_token, secret=make_settings().token_signing_secret)}"
        )
        await svc.resolve_redirect(signed_click)
        body = _webhook_body(click_token=signed_click)
        first, dup1 = await svc.process_conversion(
            network_code="amazon", raw_body=body, signature=_sig(body)
        )
        assert first is not None and dup1 is False
        second, dup2 = await svc.process_conversion(
            network_code="amazon", raw_body=body, signature=_sig(body)
        )
        assert second is None and dup2 is True
        transactions, total = await svc.list_revenue(data["niche"].id)
        assert total == 1

    scenario(runner)


def test_conversion_webhook_same_transaction_different_event_deduplicated() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        tokens = await svc.list_tokens(data["link"].id, niche_id=data["niche"].id)
        from atoz_affiliate_service.domain.tokens import _hmac_hex

        raw_token = tokens[0].token
        signed_click = (
            f"{raw_token}.{_hmac_hex(raw_token, secret=make_settings().token_signing_secret)}"
        )
        await svc.resolve_redirect(signed_click)
        body1 = _webhook_body(click_token=signed_click)
        await svc.process_conversion(network_code="amazon", raw_body=body1, signature=_sig(body1))
        # Same network transaction, different envelope event_id.
        body2 = _webhook_body(click_token=signed_click)
        body2 = body2.replace(b"evt-100", b"evt-101")
        transaction, duplicate = await svc.process_conversion(
            network_code="amazon", raw_body=body2, signature=_sig(body2)
        )
        assert transaction is None and duplicate is True
        _, total = await svc.list_revenue(data["niche"].id)
        assert total == 1

    scenario(runner)


def test_conversion_amount_limit_rejected() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        tokens = await svc.list_tokens(data["link"].id, niche_id=data["niche"].id)
        from atoz_affiliate_service.domain.tokens import _hmac_hex

        raw_token = tokens[0].token
        signed_click = (
            f"{raw_token}.{_hmac_hex(raw_token, secret=make_settings().token_signing_secret)}"
        )
        await svc.resolve_redirect(signed_click)
        body = _webhook_body(click_token=signed_click, amount_cents=999_999_999)
        with pytest.raises(WebhookRejectedError):
            await svc.process_conversion(network_code="amazon", raw_body=body, signature=_sig(body))

    scenario(runner)


def test_commission_lifecycle_transitions() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        tokens = await svc.list_tokens(data["link"].id, niche_id=data["niche"].id)
        from atoz_affiliate_service.domain.tokens import _hmac_hex

        raw_token = tokens[0].token
        signed_click = (
            f"{raw_token}.{_hmac_hex(raw_token, secret=make_settings().token_signing_secret)}"
        )
        await svc.resolve_redirect(signed_click)
        body = _webhook_body(click_token=signed_click, status="pending")
        transaction, _ = await svc.process_conversion(
            network_code="amazon", raw_body=body, signature=_sig(body)
        )
        assert transaction is not None and transaction.status == CommissionStatus.PENDING
        # pending → rejected
        rejected = await svc.transition_commission(
            transaction.id, niche_id=data["niche"].id, action="reject"
        )
        assert rejected.status == CommissionStatus.REJECTED
        with pytest.raises(ValidationError):
            await svc.transition_commission(
                transaction.id, niche_id=data["niche"].id, action="approve"
            )
        # A fresh pending one: pending → approved → paid.
        body2 = _webhook_body(click_token=signed_click, transaction_id="tx-101", status="pending")
        body2 = body2.replace(b"evt-100", b"evt-103")
        transaction2, _ = await svc.process_conversion(
            network_code="amazon", raw_body=body2, signature=_sig(body2)
        )
        assert transaction2 is not None
        approved = await svc.transition_commission(
            transaction2.id, niche_id=data["niche"].id, action="approve"
        )
        assert approved.status == CommissionStatus.APPROVED
        paid = await svc.transition_commission(
            transaction2.id, niche_id=data["niche"].id, action="mark_paid"
        )
        assert paid.status == CommissionStatus.PAID and paid.reconciled_at is not None

    scenario(runner)


def test_niche_isolation_end_to_end() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        other_niche = await svc.create_niche(name="Travel", slug="travel", status="active")
        other_network = await svc.create_network(code="impact", name="Impact")
        other_merchant = await svc.create_merchant(
            network_id=other_network.id, remote_merchant_id="m-1", name="Travel Co."
        )
        other_product = await svc.create_product(
            niche_id=other_niche.id,
            merchant_id=other_merchant.id,
            sku="SKU-T-1",
            name="Travel Backpack",
            slug="travel-backpack",
            excerpt="",
            description_ref=None,
            price_cents=9900,
            currency="USD",
            status="draft",
            category_ids=[],
            primary_category_id=None,
        )
        # Niche A cannot see Niche B products.
        assert await svc.get_public_product(other_product.slug, niche_id=data["niche"].id) is None
        assert await svc.get_product(other_product.id, niche_id=data["niche"].id) is None
        public_a, total_a = await svc.list_public_products(data["niche"].id)
        assert total_a == 1
        public_b, total_b = await svc.list_public_products(other_niche.id)
        assert total_b == 0  # Niche B has no active products yet
        # No cross-niche revenue leakage.
        assert (await svc.revenue_dashboard(data["niche"].id))["transaction_count"] == 0

    scenario(runner)


def test_reconciliation_and_summaries() -> None:
    async def runner() -> None:
        session_factory, svc = await build_repositories()
        data = await _seed_active_product(svc)
        reconciliation = await svc.create_reconciliation(
            niche_id=data["niche"].id,
            network_id=data["network"].id,
            reported_at=datetime.now(UTC),
            expected_total_cents=1000,
            actual_total_cents=900,
            report_ref="report-1",
        )
        assert reconciliation.status == "mismatch"
        matched = await svc.create_reconciliation(
            niche_id=data["niche"].id,
            network_id=data["network"].id,
            reported_at=datetime.now(UTC) + timedelta(days=1),
            expected_total_cents=500,
            actual_total_cents=500,
            report_ref="report-2",
        )
        assert matched.status == "matched"
        rows, total = await svc.list_reconciliations(data["niche"].id)
        assert total == 2
        summary = await svc.rollup_summaries(data["niche"].id, summary_date="2026-08-09")
        assert summary is not None
        summaries, stotal = await svc.list_summaries(data["niche"].id)
        assert stotal == 1

    scenario(runner)
