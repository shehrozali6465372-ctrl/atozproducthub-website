"""Bridge internal API: status + outbound job dispatch (M10 Step 2).

The bridge remains transport-only: it validates the frozen ``AIOS.Job.Request``
contract, signs, retries, and circuit-breaks — it contains no AI logic and
never inspects the business meaning of ``context`` payloads. Inbound webhook
receivers (``AIOS.Job.Status``, ``AIOS.Content.Intake``, ``AIOS.SEO.Metadata``,
``AIOS.Pinterest.Assets``, ``AIOS.Analytics.Insights``) verify signatures and
validate contracts before any processing (API Contracts §8).
"""

import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Request

from atoz_aios_bridge.client import AiosBridgeClient, BridgeUnavailable
from atoz_aios_bridge.config import Settings, get_settings
from atoz_aios_bridge.contracts import BridgeContractError
from atoz_aios_bridge.errors import (
    PermissionDeniedError,
    ServiceUnavailableError,
    ValidationError,
)
from atoz_aios_bridge.schemas import BridgeJobOut, BridgeJobRequest

router = APIRouter(tags=["bridge"], prefix="/bridge")

# Business contract → frozen AIOS job type (API Contracts §12.2).
CONTRACT_TO_JOB_TYPE: dict[str, str] = {
    "content-intake": "content",
    "seo-metadata": "seo_metadata",
    "pinterest-assets": "pinterest_assets",
    "analytics-insights": "analytics_insights",
}


def _bridge_client(request: Request) -> AiosBridgeClient:
    """Resolve the shared bridge client (circuit state persists per process)."""
    client = getattr(request.app.state, "aios_bridge_client", None)
    if client is None:
        raise RuntimeError("aios_bridge_client is not configured.")
    return client


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


@router.get("/status", summary="Bridge status (non-secret transport metadata)")
def bridge_status(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    """Expose transport configuration only — never credentials or AI data."""
    return {
        "status": "ok",
        "service": "aios-bridge",
        "aios_base_url": settings.aios_base_url,
        "timeout_seconds": settings.aios_timeout_seconds,
        "max_retries": settings.aios_max_retries,
        "circuit_failure_threshold": settings.aios_circuit_failure_threshold,
        "circuit_recovery_timeout": settings.aios_circuit_recovery_timeout,
        "hmac_signing_enabled": bool(settings.aios_api_key),
        "contracts": ["heartbeat", "job-request", "job-status"],
    }


@router.post("/jobs", summary="Dispatch an approved job request to the AI OS")
async def dispatch_job(
    payload: BridgeJobRequest,
    request: Request,
    x_bridge_token: str | None = Header(default=None, alias="X-Bridge-Token"),
    client: AiosBridgeClient = Depends(_bridge_client),
) -> BridgeJobOut:
    """Submit a validated job request through the AI OS client.

    Website → Bridge → AI OS only. The bridge maps the internal dispatch
    envelope to the frozen ``AIOS.Job.Request`` contract, generates the
    ``request_id`` (UUID idempotency key), and delegates to the client
    (signing, retry, timeout, circuit breaker). No AI logic exists here.
    """
    settings: Settings = request.app.state.settings
    if settings.internal_token:
        if x_bridge_token != settings.internal_token:
            raise PermissionDeniedError("Invalid bridge token.")
    if not _is_uuid(payload.niche_id):
        raise ValidationError("niche_id must be a valid UUID.")
    job_type = CONTRACT_TO_JOB_TYPE[payload.contract]
    request_id = payload.job_id if _is_uuid(payload.job_id) else str(uuid.uuid4())
    context: dict[str, Any] = dict(payload.request)
    if request_id != payload.job_id:
        # Preserve the automation correlation id when it is not a UUID.
        context["automation_job_id"] = payload.job_id
    aios_payload: dict[str, Any] = {
        "request_id": request_id,
        "job_type": job_type,
        "niche_id": payload.niche_id,
        "context": context,
        "callback": {
            "url": settings.aios_callback_url,
            "event_contract": "aios.job.status.v1",
        },
    }
    try:
        result = await asyncio.to_thread(client.submit_job, aios_payload)
    except BridgeContractError as exc:
        raise ValidationError(str(exc)) from exc
    except BridgeUnavailable as exc:
        raise ServiceUnavailableError(str(exc)) from exc
    aios_job_id = str(result.get("job_id") or request_id)
    return BridgeJobOut(
        aios_job_id=aios_job_id,
        request_id=request_id,
        contract=payload.contract,
        job_type=job_type,
    )
