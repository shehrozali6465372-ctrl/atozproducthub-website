"""Inbound network webhook receiver (API Contracts §10).

Affiliate networks deliver ``network.conversion`` events to
``POST /webhooks/v1/{network_code}/conversion``. Every delivery is verified
(HMAC-SHA256 of the raw body with the per-network secret), schema-validated,
and deduplicated by ``(source, event_id)`` plus the revenue ledger's
``UNIQUE (network_id, network_transaction_id)`` constraint. Valid events
are acknowledged immediately with 202; rejected deliveries return
problem+json (400) without recording a commission.

No AI functionality exists here — conversion data is pure business data.
"""

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse

from atoz_affiliate_service.errors import WebhookRejectedError
from atoz_affiliate_service.routes.deps import get_affiliate_service
from atoz_affiliate_service.services import AffiliateService

router = APIRouter(prefix="/webhooks/v1", tags=["affiliate-webhooks"])


@router.post(
    "/{network_code}/conversion",
    summary="Ingest a network.conversion webhook (fast-ack, idempotent)",
    status_code=202,
    response_class=JSONResponse,
)
async def ingest_conversion(
    network_code: str,
    request: Request,
    x_webhook_signature: str = Header(default="", alias="X-Webhook-Signature"),
    service: AffiliateService = Depends(get_affiliate_service),
) -> JSONResponse:
    raw_body = await request.body()
    if not raw_body:
        raise WebhookRejectedError("Webhook body is required.")
    transaction, _duplicate = await service.process_conversion(
        network_code=network_code, raw_body=raw_body, signature=x_webhook_signature
    )
    # Fast-ack semantics: 202 for every accepted delivery (processed or
    # duplicate). Rejected deliveries raise WebhookRejectedError (400).
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "duplicate": transaction is None,
        },
    )
