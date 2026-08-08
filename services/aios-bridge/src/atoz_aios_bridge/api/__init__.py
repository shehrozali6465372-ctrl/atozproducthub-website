"""Bridge internal API (skeleton).

M3 ships a read-only status endpoint. Inbound webhook receivers
(``AIOS.Job.Status``, ``AIOS.Content.Intake``, ``AIOS.SEO.Metadata``,
``AIOS.Pinterest.Assets``, ``AIOS.Analytics.Insights``) land here in
Phase 4+ — with signature verification and contract validation first.
"""

from fastapi import APIRouter, Depends

from atoz_aios_bridge.config import get_settings

router = APIRouter(tags=["bridge"], prefix="/bridge")


@router.get("/status", summary="Bridge status (non-secret transport metadata)")
def bridge_status(settings=Depends(get_settings)) -> dict[str, object]:
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
