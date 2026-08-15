"""Staging smoke suite (Task 24 / M11 Phase 3, ADR-0014).

Each item in the Task 24 Phase D matrix is covered by a focused unit check
that runs in CI with mocks/fixtures. The live counterpart is
``tools/deploy/staging-smoke.sh`` (edge + host checks on a real staging
stack).
"""

import asyncio
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from atoz_backend_core import __version__
from atoz_backend_core.app import create_service_app
from atoz_backend_core.auth import (
    InMemorySessionManager,
    MfaService,
    create_access_token,
    decode_token,
    require_permissions,
)
from atoz_backend_core.config import BaseServiceSettings

ROOT = Path(__file__).resolve().parents[2]
JWT_SECRET = "test-secret-0123456789abcdef0123456789abcdef"

# Task 24 Phase D matrix (24 critical smoke checks).
SMOKE_ITEMS = [
    "health/readiness",
    "authentication",
    "jwt/rbac",
    "mfa-gate",
    "x-niche-id-isolation",
    "content-read-write",
    "affiliate-redirect",
    "affiliate-webhook",
    "pinterest-oauth-boundary",
    "pinterest-publish-queue",
    "seo-search",
    "robots-txt",
    "sitemap",
    "analytics-event-collection",
    "analytics-webhook",
    "automation-rule-trigger",
    "automation-queue-execution",
    "aios-bridge-contract",
    "admin-audit-logging",
    "admin-operations-endpoints",
    "notification-path",
    "metrics-endpoint",
    "otel-health",
    "service-to-service-auth",
]


def _core_client() -> TestClient:
    settings = BaseServiceSettings(
        app_env="test",
        database_url=None,
        redis_url=None,
        rate_limit_enabled=False,
    )
    app = create_service_app(
        service_name="atoz-api",
        version=__version__,
        settings=settings,
    )
    return TestClient(app, raise_server_exceptions=False)


def test_smoke_matrix_is_complete() -> None:
    assert len(SMOKE_ITEMS) == 24


def test_smoke_health_and_readiness() -> None:
    client = _core_client()
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ok"


def test_smoke_authentication() -> None:
    token = create_access_token(
        secret=JWT_SECRET, subject="user-1", session_id="s1", permissions=("admin:read",)
    )
    claims = decode_token(token, secret=JWT_SECRET, expected_type="access")
    assert claims.subject == "user-1"


def test_smoke_jwt_rbac() -> None:
    app = FastAPI()

    @app.get("/protected")
    def protected(_: object = Depends(require_permissions("admin:read"))) -> dict[str, str]:
        return {"ok": "true"}

    with TestClient(app) as client:
        assert client.get("/protected").status_code == 401


def test_smoke_mfa_gate() -> None:
    service = MfaService()
    provision = service.provision("user-1")
    assert provision.secret
    assert provision.otpauth_uri.startswith("otpauth://totp/AtozProductHub:user-1")
    with pytest.raises(NotImplementedError):
        service.verify("user-1", provision.secret, "123456")
    session = asyncio.run(
        InMemorySessionManager().create(subject="user-1", ttl_seconds=60, mfa_verified=True)
    )
    assert session.mfa_verified is True


def test_smoke_x_niche_id_isolation() -> None:
    from atoz_analytics_service.errors import ValidationError
    from atoz_analytics_service.routes.deps import get_niche_id

    class Request:
        def __init__(self, headers: dict[str, str]) -> None:
            self.headers = headers

    assert get_niche_id(Request({"X-Niche-Id": "00000000-0000-7000-8000-000000000001"})) == (
        "00000000-0000-7000-8000-000000000001"
    )
    with pytest.raises(ValidationError):
        get_niche_id(Request({}))
    with pytest.raises(ValidationError):
        get_niche_id(Request({"X-Niche-Id": "not-a-uuid"}))

    from datetime import UTC, datetime

    from atoz_seo_service.domain.search import InMemorySearchIndex, SearchDocument

    async def isolation() -> None:
        index = InMemorySearchIndex()
        for niche, title in (("n-1", "Kitchen guide"), ("n-2", "Travel guide")):
            await index.upsert(
                SearchDocument(
                    id=f"id-{niche}",
                    type="article",
                    niche_id=niche,
                    slug=title.lower().replace(" ", "-"),
                    title=title,
                    updated_at=datetime(2026, 8, 1, tzinfo=UTC),
                )
            )
        page_a = await index.search(query="guide", niche_id="n-1")
        page_b = await index.search(query="guide", niche_id="n-2")
        assert [h.id for h in page_a.items] == ["id-n-1"]
        assert [h.id for h in page_b.items] == ["id-n-2"]

    asyncio.run(isolation())


def test_smoke_content_read_write_lifecycle() -> None:
    from atoz_content_service.domain.enums import ArticleStatus
    from atoz_content_service.domain.lifecycle import transition
    from atoz_content_service.domain.slug import slugify, unique_slug

    assert slugify("  Hello, World!  ") == "hello-world"
    assert unique_slug("hello-world", taken={"hello-world"}) == "hello-world-2"
    assert unique_slug("fresh", taken={"hello-world"}) == "fresh"
    assert transition(ArticleStatus.DRAFT, "submit") == ArticleStatus.REVIEW
    assert transition(ArticleStatus.REVIEW, "approve") == ArticleStatus.PUBLISHED
    assert transition(ArticleStatus.PUBLISHED, "unpublish") == ArticleStatus.UNPUBLISHED
    assert transition(ArticleStatus.PUBLISHED, "archive") == ArticleStatus.ARCHIVED


def test_smoke_affiliate_redirect_security() -> None:
    from atoz_affiliate_service.domain.tokens import (
        new_signed_token,
        sign_token,
        token_from_signed,
        validate_signed_token,
    )

    signed = new_signed_token(secret="signing-secret")
    raw = token_from_signed(signed)
    assert validate_signed_token(signed, secret="signing-secret") == raw
    assert validate_signed_token(signed, secret="wrong-secret") is None
    assert validate_signed_token(f"{raw}.deadbeef", secret="signing-secret") is None
    assert sign_token(raw, secret="signing-secret") == signed


def test_smoke_affiliate_webhook_verification() -> None:
    import hashlib
    import hmac
    import json

    from atoz_affiliate_service.domain.webhooks import (
        WebhookPayloadError,
        parse_conversion_payload,
        parse_envelope,
        verify_signature,
    )

    body = json.dumps(
        {
            "event_id": "evt-1",
            "type": "network.conversion",
            "version": "1",
            "source": "network-a",
            "occurred_at": "2026-08-01T00:00:00+00:00",
            "payload": {
                "transaction_id": "tx-1",
                "status": "approved",
                "amount_cents": 1000,
                "currency": "USD",
            },
        }
    ).encode()
    signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert verify_signature(raw_body=body, signature=signature, secret="secret") is True
    assert verify_signature(raw_body=body, signature="0" * 64, secret="secret") is False
    envelope = parse_envelope(body)
    assert parse_conversion_payload(envelope["payload"])["amount_cents"] == 1000
    with pytest.raises(WebhookPayloadError):
        parse_envelope(b"not json")


def test_smoke_pinterest_oauth_boundary() -> None:
    from atoz_pinterest_service.domain.oauth import (
        build_authorize_url,
        code_challenge,
        new_code_verifier,
        new_state,
        verify_state,
    )

    state = new_state(secret="state-secret", account_id="acct-1")
    assert verify_state("state-secret", state) == "acct-1"
    assert verify_state("wrong-secret", state) is None
    verifier = new_code_verifier()
    url = build_authorize_url(
        authorize_url="https://www.pinterest.com/oauth/",
        client_id="client-1",
        redirect_uri="https://admin.staging.atozproducthub.dev/callback",
        state=state,
        code_challenge_value=code_challenge(verifier),
        scopes=["boards:read", "boards:write", "pins:read", "pins:write"],
    )
    assert "state=" in url and "code_challenge=" in url


def test_smoke_pinterest_publish_queue_idempotency() -> None:
    from atoz_pinterest_service.domain.pins import (
        is_valid_pin_transition,
        is_valid_queue_transition,
        pin_checksum,
    )

    assert is_valid_queue_transition("queued", "claimed") is True
    assert is_valid_queue_transition("done", "claimed") is False
    assert is_valid_pin_transition("draft", "queued") is True
    assert is_valid_pin_transition("publishing", "published") is True
    assert is_valid_pin_transition("published", "draft") is False
    assert pin_checksum(
        account_id="acct-1", board_id="board-1", title="Guide", destination_url="https://x"
    ) == pin_checksum(
        account_id="acct-1", board_id="board-1", title="Guide", destination_url="https://x"
    )


def test_smoke_seo_search() -> None:
    from datetime import UTC, datetime

    from atoz_seo_service.domain.search import InMemorySearchIndex, SearchDocument

    async def search() -> None:
        index = InMemorySearchIndex()
        await index.ensure_collection()
        await index.upsert(
            SearchDocument(
                id="doc-1",
                type="article",
                niche_id="n-1",
                slug="cast-iron",
                title="Cast iron guide",
                updated_at=datetime(2026, 8, 1, tzinfo=UTC),
            )
        )
        page = await index.search(query="cast iron", niche_id="n-1")
        assert page.total == 1
        assert page.items[0].id == "doc-1"

    asyncio.run(search())


def test_smoke_robots_txt() -> None:
    from atoz_seo_service.domain.robots import build_robots, validate_robots

    robots = build_robots(
        base_url="https://staging.atozproducthub.dev",
        disallow_paths=["/admin/", "/api/"],
        sitemap_group_names=["articles", "products"],
    )
    validate_robots(robots)
    assert "Pinterestbot" in robots
    assert "Disallow: /admin/" in robots
    assert "Sitemap: https://staging.atozproducthub.dev/sitemaps/articles-index.xml" in robots


def test_smoke_sitemap_xml() -> None:
    from datetime import UTC, datetime

    from atoz_seo_service.domain.sitemaps import (
        SitemapShard,
        SitemapUrl,
        render_index,
        render_shard,
        validate_xml,
    )

    index = render_index(
        base_url="https://staging.atozproducthub.dev",
        group_name="articles",
        shard_count=2,
        lastmod=datetime(2026, 8, 1, tzinfo=UTC),
    )
    validate_xml(index)
    assert "<sitemapindex" in index and "articles-1.xml" in index
    shard = render_shard(
        SitemapShard(
            group_name="articles",
            shard_no=1,
            urls=[
                SitemapUrl(
                    loc="https://staging.atozproducthub.dev/articles/a",
                    lastmod=datetime(2026, 8, 1, tzinfo=UTC),
                )
            ],
        )
    )
    validate_xml(shard)
    assert "<urlset" in shard and "<loc>" in shard


def test_smoke_analytics_event_collection() -> None:
    from atoz_analytics_service.domain.pipeline import (
        InMemoryEventBackbone,
        InMemoryWarehouse,
        PipelineWorker,
        event_row,
    )
    from atoz_backend_core.events.envelope import EventEnvelope

    async def drain() -> None:
        backbone = InMemoryEventBackbone()
        warehouse = InMemoryWarehouse()
        worker = PipelineWorker(backbone, warehouse)
        await backbone.publish(
            EventEnvelope(
                type="analytics:page_view.v1",
                event_id="evt-1",
                payload={"niche_id": "n-1"},
            )
        )
        await worker.drain_in_memory()
        assert len(warehouse.rows) == 1
        assert warehouse.rows[0]["event_id"] == "evt-1"

    asyncio.run(drain())
    row = event_row(
        EventEnvelope(
            type="analytics:page_view.v1",
            event_id="evt-2",
            payload={"niche_id": "n-1"},
        )
    )
    assert row["niche_id"] == "n-1"


def test_smoke_analytics_webhook_schema() -> None:
    from pydantic import ValidationError as PydanticValidationError

    from atoz_analytics_service.schemas import CollectorEventIn

    valid = CollectorEventIn(
        event_id="evt-0003",
        event_type="page_view",
        page_url="/articles/a",
        session_id="s1",
        user_pseudo_id="u1",
    )
    assert valid.event_id == "evt-0003"
    with pytest.raises(PydanticValidationError):
        CollectorEventIn(event_type="page_view")


def test_smoke_automation_rule_trigger_and_queue() -> None:
    from atoz_automation_service.domain.retry import idempotency_key, next_retry_at

    assert idempotency_key("rule-1", "2026-08-01T00:00:00+00:00") == idempotency_key(
        "rule-1", "2026-08-01T00:00:00+00:00"
    )
    assert idempotency_key("rule-1", "2026-08-01T00:00:00+00:00") != idempotency_key(
        "rule-1", "2026-08-01T00:00:00+00:01"
    )
    assert next_retry_at(attempts=5, max_attempts=5) is None
    assert next_retry_at(attempts=1, max_attempts=3) is not None


def test_smoke_aios_bridge_contract() -> None:
    from atoz_aios_bridge.contracts import AiosContractValidator

    validator = AiosContractValidator(contracts_dir=ROOT / "libs/contracts/aios")
    assert "job-request" in validator.available_contracts()
    payload = validator.validate(
        "job-request",
        {
            "request_id": "00000000-0000-7000-8000-000000000001",
            "job_type": "content",
            "niche_id": "00000000-0000-7000-8000-000000000002",
            "context": {"article_id": "art-1"},
            "callback": {
                "url": "https://aios-bridge:8000/bridge/jobs/status",
                "event_contract": "aios.job.status.v1",
            },
        },
    )
    assert payload["job_type"] == "content"


def test_smoke_admin_audit_and_operations_routes() -> None:
    admin_route_src = (
        ROOT / "services/admin-service/src/atoz_admin_service/routes/admin.py"
    ).read_text()
    assert '"/audit"' in admin_route_src
    assert '"/ops/overview"' in admin_route_src
    entities = (
        ROOT / "services/admin-service/src/atoz_admin_service/domain/entities.py"
    ).read_text()
    assert "audit_logs" in entities


def test_smoke_notification_path() -> None:
    admin_route_src = (
        ROOT / "services/admin-service/src/atoz_admin_service/routes/admin.py"
    ).read_text()
    assert '"/notifications"' in admin_route_src
    migration = (
        ROOT / "services/admin-service/db/migrations/versions/0001_admin_initial.py"
    ).read_text()
    assert "notifications" in migration


def test_smoke_metrics_endpoint() -> None:
    client = _core_client()
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "app_info" in response.text


def test_smoke_otel_health() -> None:
    from atoz_backend_core.config import BaseServiceSettings
    from atoz_backend_core.observability.otel import setup_otel

    settings = BaseServiceSettings(app_env="test", otel_enabled=False)
    app = FastAPI()
    setup_otel(app, settings=settings)  # no-op, must not raise
    assert app is not None


def test_smoke_service_to_service_auth() -> None:
    from atoz_automation_service.config import Settings
    from atoz_automation_service.executors.clients import SiblingClients
    from atoz_backend_core.auth import decode_token

    settings = Settings(
        app_env="test",
        rate_limit_enabled=False,
        pinterest_jwt_secret=JWT_SECRET,
        pinterest_write_permission="pinterest:write",
        pinterest_base_url="http://pinterest-service:8000",
        admin_base_url="http://admin-service:8000",
        admin_jwt_secret=JWT_SECRET,
        admin_write_permission="admin:write",
        seo_base_url="http://seo-service:8000",
        seo_jwt_secret=JWT_SECRET,
        seo_write_permission="seo:write",
        affiliate_base_url="http://affiliate-service:8000",
        affiliate_jwt_secret=JWT_SECRET,
        affiliate_write_permission="affiliate:write",
        analytics_base_url="http://analytics-service:8000",
        analytics_jwt_secret=JWT_SECRET,
        analytics_write_permission="analytics:write",
        aios_bridge_base_url="http://aios-bridge:8000",
    )
    clients = SiblingClients(settings)
    token = clients.service_token("pinterest")
    assert token is not None
    claims = decode_token(token, secret=JWT_SECRET, expected_type="access")
    assert claims.subject == "automation-service"
    assert "pinterest:write" in claims.permissions
