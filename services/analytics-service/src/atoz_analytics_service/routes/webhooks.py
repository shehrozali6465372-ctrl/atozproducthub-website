"""Internal event ingestion (Task 18 §1, API Contracts §11).

Content, affiliate, Pinterest, and SEO services emit domain events; the
analytics service consumes them to record business events (published pins,
affiliate clicks, attributed revenue, ...) into the append-only ledger and
pipeline. The endpoint verifies a shared HMAC signature
(``event_webhook_secret``) so only trusted producers can write analytics
data. Idempotent by ``event_id``.
"""

import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, Request

from atoz_analytics_service.errors import AuthenticationError
from atoz_analytics_service.routes.deps import get_analytics_service
from atoz_analytics_service.schemas import EventWebhookIn
from atoz_analytics_service.services import AnalyticsService
from atoz_backend_core.events.envelope import EventEnvelope

router = APIRouter(prefix="/webhooks/v1/analytics", tags=["analytics-events"])


def _verify_signature(secret: str, payload: bytes, signature: str | None) -> None:
    if not signature:
        raise AuthenticationError("Missing X-Event-Signature header.")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature.strip().lower()):
        raise AuthenticationError("Invalid event signature.")


@router.post("/events", summary="Ingest an internal domain event", status_code=202)
async def ingest_event(
    request: Request,
    payload: EventWebhookIn,
    x_event_signature: str | None = Header(default=None),
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict:
    raw = await request.body()
    settings = request.app.state.settings
    _verify_signature(settings.event_webhook_secret, raw, x_event_signature)
    envelope = EventEnvelope(
        type=payload.type,
        event_id=payload.event_id,
        payload=payload.payload,
        aggregate_id=payload.aggregate_id,
    )
    status = await service.ingest_webhook_event(envelope)
    return {"status": status, "event_id": envelope.event_id}
