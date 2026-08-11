"""Internal event ingestion for search indexing (Task 17 §8).

Content and affiliate services emit domain events; the SEO service consumes
them to index/re-index/de-index search documents. The endpoint verifies a
shared HMAC signature (event_webhook_secret) so only trusted producers can
drive the index. Idempotent by nature: re-indexing is an upsert and
de-indexing a missing document is a no-op.
"""

import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, Request

from atoz_backend_core.events.envelope import EventEnvelope
from atoz_seo_service.errors import AuthenticationError
from atoz_seo_service.routes.deps import get_seo_service
from atoz_seo_service.schemas import EventWebhookIn
from atoz_seo_service.services import SeoService

router = APIRouter(prefix="/webhooks/v1", tags=["seo-events"])


def _verify_signature(secret: str, payload: bytes, signature: str | None) -> None:
    if not signature:
        raise AuthenticationError("Missing X-Event-Signature header.")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature.strip().lower()):
        raise AuthenticationError("Invalid event signature.")


@router.post("/events", summary="Ingest a content/product lifecycle event", status_code=202)
async def ingest_event(
    request: Request,
    payload: EventWebhookIn,
    x_event_signature: str | None = Header(default=None),
    service: SeoService = Depends(get_seo_service),
) -> dict:
    raw = await request.body()
    settings = request.app.state.settings
    _verify_signature(settings.event_webhook_secret, raw, x_event_signature)
    envelope = EventEnvelope(
        type=payload.type,
        event_id=payload.event_id or "",
        payload=payload.payload,
        aggregate_id=payload.aggregate_id or "",
    )
    await service.handle_event(envelope)
    return {"status": "accepted", "event_id": envelope.event_id}
