"""AiosBridgeClient transport tests (MockTransport: no real AI OS calls)."""

import httpx
import pytest

from atoz_aios_bridge.client import AiosBridgeClient, BridgeUnavailable
from atoz_aios_bridge.config import Settings
from atoz_aios_bridge.jobs.circuit import CircuitBreaker
from atoz_aios_bridge.jobs.retry import backoff_delay, is_retryable

VALID_JOB_REQUEST = {
    "request_id": "a8f5f167-f44f-4a01-a0f8-9d4f0d8a7b1e",
    "job_type": "pinterest_assets",
    "niche_id": "b8f5f167-f44f-4a01-a0f8-9d4f0d8a7b2f",
    "context": {"pin_id": "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"},
    "callback": {
        "url": "https://atozproducthub.dev/webhooks/aios/job-status",
        "event_contract": "aios.job.status.v1",
    },
}


def make_svc_client(handler, **overrides) -> AiosBridgeClient:
    settings = Settings(
        app_env="test",
        aios_base_url="http://aios.test",
        aios_api_key="test-key-0123456789abcdef0123456789abcdef",
        **overrides,
    )
    return AiosBridgeClient(settings, transport=httpx.MockTransport(handler))


def test_submit_job_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/jobs"
        assert request.headers["X-AIOS-Signature"]
        assert request.headers["X-AIOS-Timestamp"]
        assert request.headers["X-AIOS-Nonce"]
        return httpx.Response(202, json={"job_id": "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"})

    svc_client = make_svc_client(handler)
    try:
        result = svc_client.submit_job(VALID_JOB_REQUEST)
        assert result["job_id"]
    finally:
        svc_client.close()


def test_submit_job_validates_before_sending() -> None:
    sent: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request.url.path)
        return httpx.Response(202, json={"job_id": "x"})

    svc_client = make_svc_client(handler)
    try:
        bad = dict(VALID_JOB_REQUEST)
        bad.pop("callback")
        with pytest.raises(ValueError):
            svc_client.submit_job(bad)
        assert sent == []  # never reached the AI OS
    finally:
        svc_client.close()


def test_retries_on_503_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={"status": "busy"})
        return httpx.Response(202, json={"job_id": "c8f5f167-f44f-4a01-a0f8-9d4f0d8a7b3a"})

    svc_client = make_svc_client(handler, aios_max_retries=3, aios_retry_backoff_base=0.01)
    try:
        result = svc_client.submit_job(VALID_JOB_REQUEST)
        assert calls["n"] == 2
        assert result["job_id"]
    finally:
        svc_client.close()


def test_validation_error_fails_fast() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"code": "VALIDATION_FAILED"})

    svc_client = make_svc_client(handler)
    try:
        with pytest.raises(BridgeUnavailable):
            svc_client.submit_job(VALID_JOB_REQUEST)
    finally:
        svc_client.close()


def test_heartbeat_validates_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/heartbeat"
        return httpx.Response(200, json={"status": "ok", "latency_ms": 8.0})

    svc_client = make_svc_client(handler)
    try:
        body = svc_client.heartbeat()
        assert body["status"] == "ok"
    finally:
        svc_client.close()


def test_circuit_breaker_opens_and_rejects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"status": "busy"})

    svc_client = make_svc_client(
        handler,
        aios_max_retries=0,  # no retries: each call records one failure
        aios_circuit_failure_threshold=3,
    )
    try:
        for _ in range(3):
            with pytest.raises(BridgeUnavailable):
                svc_client.submit_job(VALID_JOB_REQUEST)
        with pytest.raises(BridgeUnavailable) as exc_info:
            svc_client.submit_job(VALID_JOB_REQUEST)
        assert "circuit breaker is open" in str(exc_info.value)
    finally:
        svc_client.close()


def test_backoff_delay_policy() -> None:
    assert backoff_delay(0) == 1.0
    assert backoff_delay(1) == 2.0
    assert backoff_delay(10) == 60.0  # capped
    assert backoff_delay(1, retry_after=5) == 5.0


def test_is_retryable() -> None:
    assert is_retryable(httpx.ConnectError("no route"))
    assert is_retryable(httpx.TimeoutException("slow"))
    response = httpx.Response(
        429, headers={"Retry-After": "2"}, request=httpx.Request("GET", "http://x")
    )
    assert is_retryable(httpx.HTTPStatusError("429", request=response.request, response=response))
    response = httpx.Response(400, request=httpx.Request("GET", "http://x"))
    assert not is_retryable(
        httpx.HTTPStatusError("400", request=response.request, response=response)
    )


def test_circuit_breaker_states() -> None:
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60.0)
    assert breaker.is_open is False
    breaker.record_failure()
    assert breaker.is_open is False
    breaker.record_failure()
    assert breaker.is_open is True
    breaker.record_success()
    assert breaker.is_open is False
