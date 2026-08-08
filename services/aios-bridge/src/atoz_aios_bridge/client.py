"""AI OS Bridge client — the business layer's ONLY outbound AI OS call.

Implements transport guarantees only:
- request validation (schema-first, frozen contracts)
- contract validation of responses
- retry with exponential backoff (1s x 2, cap 60s, max 5)
- timeout on every call
- HMAC request signing (API Contracts §8)
- circuit breaker (stub)

There is no AI logic here: no prompts, no models, no generation, no
learning, no memory. This client only moves approved messages.
"""

import logging
import time
from typing import Any

import httpx

from atoz_aios_bridge.adapters.signing import AiosSigner
from atoz_aios_bridge.config import Settings
from atoz_aios_bridge.contracts import AiosContractValidator
from atoz_aios_bridge.jobs.circuit import CircuitBreaker
from atoz_aios_bridge.jobs.retry import backoff_delay, is_retryable, retry_after_from

logger = logging.getLogger("atoz.bridge")

HEARTBEAT_PATH = "/heartbeat"
JOBS_PATH = "/v1/jobs"


class BridgeUnavailable(RuntimeError):
    """Raised when the AI OS cannot be reached or the circuit is open."""


class AiosBridgeClient:
    """Synchronous HTTP client (run via asyncio.to_thread from async routes)."""

    def __init__(
        self,
        settings: Settings,
        *,
        contracts_dir: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._validator = AiosContractValidator(contracts_dir or settings.aios_contracts_dir)
        self._signer = AiosSigner(settings.aios_api_key) if settings.aios_api_key else None
        self._circuit = CircuitBreaker(
            failure_threshold=settings.aios_circuit_failure_threshold,
            recovery_timeout=settings.aios_circuit_recovery_timeout,
        )
        self._client = httpx.Client(
            base_url=settings.aios_base_url.rstrip("/"),
            timeout=settings.aios_timeout_seconds,
            transport=transport,
        )

    def validate(self, contract: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate a payload against a frozen contract (also exposed for webhook receivers)."""
        return self._validator.validate(contract, payload)

    def _headers(self, method: str, path: str, body: dict[str, Any]) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._signer is not None:
            headers.update(self._signer.sign(method=method, path=path, body=body))
        return headers

    def _request(
        self, method: str, path: str, *, payload: dict[str, Any] | None = None
    ) -> httpx.Response:
        if self._circuit.is_open:
            raise BridgeUnavailable("AI OS circuit breaker is open; request rejected without retry")
        body = payload or {}
        attempt = 0
        while True:
            try:
                response = self._client.request(
                    method, path, json=body, headers=self._headers(method, path, body)
                )
                response.raise_for_status()
                self._circuit.record_success()
                return response
            except BridgeUnavailable:
                raise
            except Exception as exc:  # noqa: BLE001
                self._circuit.record_failure()
                if not is_retryable(exc) or attempt >= self._settings.aios_max_retries:
                    if isinstance(exc, httpx.HTTPStatusError):
                        raise BridgeUnavailable(
                            f"AI OS request failed: {exc.response.status_code} {path}"
                        ) from exc
                    raise BridgeUnavailable(f"AI OS request failed: {path}: {exc}") from exc
                delay = backoff_delay(
                    attempt,
                    base=self._settings.aios_retry_backoff_base,
                    cap=self._settings.aios_retry_backoff_cap,
                    retry_after=retry_after_from(exc),
                )
                logger.warning(
                    "aios_retry",
                    extra={
                        "extra_fields": {
                            "path": path,
                            "attempt": attempt + 1,
                            "delay_seconds": round(delay, 2),
                        }
                    },
                )
                time.sleep(delay)
                attempt += 1

    def submit_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit an ``AIOS.Job.Request``; returns the AI OS ``{job_id}`` response."""
        self._validator.validate("job-request", payload)
        response = self._request("POST", JOBS_PATH, payload=payload)
        return response.json()

    def heartbeat(self) -> dict[str, Any]:
        """``AIOS.Heartbeat`` — liveness probe; never carries business data."""
        response = self._request("GET", HEARTBEAT_PATH)
        body = response.json()
        return self._validator.validate("heartbeat", body)

    def close(self) -> None:
        self._client.close()
