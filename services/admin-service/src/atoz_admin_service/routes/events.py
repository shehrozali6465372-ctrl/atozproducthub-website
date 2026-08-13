"""Internal event ingestion for admin-service (API Contracts §8).

Business services deliver domain events (content:published.v1,
pin:published.v1, affiliate:click.v1, revenue:attributed.v1, ...) through
the shared webhook. Signatures are HMAC-SHA256 over the exact request bytes
(same convention as the analytics webhook); replays are idempotent on
(source, event_id). This surface only records operations for the control
plane — no AI logic, no business mutation.
"""

from fastapi import APIRouter, Depends, Header, Request

from atoz_admin_service.errors import ValidationError
from atoz_admin_service.routes.deps import get_admin_service
from atoz_admin_service.services import AdminService

router = APIRouter(prefix="/api/v1/admin/events", tags=["admin-events"])


@router.post("/ingest", summary="Ingest a signed internal domain event", status_code=202)
async def ingest_event(
    request: Request,
    x_event_signature: str | None = Header(default=None, alias="X-Event-Signature"),
    x_event_source: str | None = Header(default=None, alias="X-Event-Source"),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    if not x_event_source:
        raise ValidationError("X-Event-Source header is required.")
    if not x_event_signature:
        raise ValidationError("X-Event-Signature header is required.")
    raw_body = await request.body()
    log = await service.ingest_event(
        source=x_event_source,
        signature=x_event_signature,
        raw_body=raw_body,
    )
    return {"id": log.id, "status": log.status, "event_id": log.event_id}
