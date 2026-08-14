"""AI OS Bridge outbound dispatch tests (M10 Step 2).

The /bridge/jobs endpoint maps the business dispatch envelope to the frozen
AIOS.Job.Request contract and submits it through a mocked client transport —
no real AI OS calls, no AI logic.
"""

import json

import httpx

from atoz_aios_bridge.client import AiosBridgeClient
from atoz_aios_bridge.config import Settings
from atoz_aios_bridge.main import create_app

VALID_JOB_ID = "a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e"
VALID_NICHE = "b8f5f167-f44f-4a01-a0f8-9d4f0d8a7b2f"


def build_client(handler, **overrides) -> AiosBridgeClient:
    settings = Settings(
        app_env="test",
        aios_base_url="http://aios.test",
        aios_api_key="test-key-0123456789abcdef0123456789abcdef",
        aios_max_retries=0,
        **overrides,
    )
    return AiosBridgeClient(settings, transport=httpx.MockTransport(handler))


def test_dispatch_job_maps_contract_and_submits() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        return httpx.Response(202, json={"job_id": "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"})

    client = build_client(handler, aios_callback_url="http://localhost:8100/bridge/jobs/status")
    app = create_app(client=client)
    try:
        with TestClient(app) as tc:
            response = tc.post(
                "/bridge/jobs",
                json={
                    "job_id": VALID_JOB_ID,
                    "contract": "content-intake",
                    "niche_id": VALID_NICHE,
                    "request": {"article_id": "art-1"},
                },
            )
            assert response.status_code == 200
            body = response.json()
            assert body["aios_job_id"] == "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"
            assert body["request_id"] == VALID_JOB_ID
            assert body["job_type"] == "content"
            assert captured["path"] == "/v1/jobs"
            sent = captured["body"]
            assert sent["request_id"] == VALID_JOB_ID
            assert sent["job_type"] == "content"
            assert sent["niche_id"] == VALID_NICHE
            assert sent["context"] == {"article_id": "art-1"}
            assert sent["callback"]["event_contract"] == "aios.job.status.v1"
            assert sent["callback"]["url"] == "http://localhost:8100/bridge/jobs/status"
    finally:
        client.close()


def test_dispatch_generates_uuid_request_id_for_non_uuid_job() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(202, json={"job_id": "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"})

    client = build_client(handler)
    app = create_app(client=client)
    try:
        with TestClient(app) as tc:
            response = tc.post(
                "/bridge/jobs",
                json={
                    "job_id": "automation-job-123",
                    "contract": "seo-metadata",
                    "niche_id": VALID_NICHE,
                    "request": {"article_id": "art-1"},
                },
            )
            assert response.status_code == 200
            body = response.json()
            assert body["request_id"] != "automation-job-123"
            sent = captured["body"]
            assert sent["context"]["automation_job_id"] == "automation-job-123"
    finally:
        client.close()


def test_dispatch_rejects_unknown_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must not reach the AI OS")

    client = build_client(handler)
    app = create_app(client=client)
    try:
        with TestClient(app) as tc:
            response = tc.post(
                "/bridge/jobs",
                json={"job_id": VALID_JOB_ID, "contract": "evil", "niche_id": VALID_NICHE},
            )
            assert response.status_code == 422
    finally:
        client.close()


def test_dispatch_enforces_internal_token_when_configured() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(202, json={"job_id": "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"})

    client = build_client(handler)
    app = create_app(
        client=client,
        settings=Settings(app_env="test", internal_token="shared-secret-1"),
    )
    try:
        with TestClient(app) as tc:
            # No header → 403.
            denied = tc.post(
                "/bridge/jobs",
                json={
                    "job_id": VALID_JOB_ID,
                    "contract": "content-intake",
                    "niche_id": VALID_NICHE,
                },
            )
            assert denied.status_code == 403
            # Matching header → 200.
            allowed = tc.post(
                "/bridge/jobs",
                json={
                    "job_id": VALID_JOB_ID,
                    "contract": "content-intake",
                    "niche_id": VALID_NICHE,
                },
                headers={"X-Bridge-Token": "shared-secret-1"},
            )
            assert allowed.status_code == 200
    finally:
        client.close()


def test_dispatch_returns_503_when_aios_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"status": "busy"})

    client = build_client(handler)
    app = create_app(client=client)
    try:
        with TestClient(app) as tc:
            response = tc.post(
                "/bridge/jobs",
                json={
                    "job_id": VALID_JOB_ID,
                    "contract": "analytics-insights",
                    "niche_id": VALID_NICHE,
                    "request": {"period": "2026-08-13"},
                },
            )
            assert response.status_code == 503
            assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    finally:
        client.close()


def test_dispatch_rejects_invalid_contract_payload_from_client() -> None:
    """BridgeContractError maps to 422 VALIDATION_FAILED."""
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.url.path)
        return httpx.Response(202, json={"job_id": "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"})

    client = build_client(handler)
    app = create_app(client=client)
    try:
        with TestClient(app) as tc:
            response = tc.post(
                "/bridge/jobs",
                json={
                    "job_id": "not-a-uuid",
                    "contract": "content-intake",
                    "niche_id": "also-not-a-uuid",  # fails the job-request schema
                    "request": {},
                },
            )
            assert response.status_code == 422
            assert captured == []  # never reached the AI OS
    finally:
        client.close()


from fastapi.testclient import TestClient  # noqa: E402
