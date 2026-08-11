"""First-party event collector (Task 18 §2).

No authentication — readers are anonymous. The collector validates the
payload, applies the sensitive-data guard, enforces ``event_id``
idempotency, appends to the append-only operational ledger, and publishes
to the event backbone. Server-side timestamps are authoritative.
"""

from fastapi import APIRouter, Depends

from atoz_analytics_service.domain.entities import AnalyticsNiche
from atoz_analytics_service.routes.deps import get_analytics_service, resolve_public_niche
from atoz_analytics_service.schemas import (
    CollectorBatchIn,
    CollectorBatchOut,
    CollectorEventIn,
    CollectorEventOut,
)
from atoz_analytics_service.services import AnalyticsService

router = APIRouter(prefix="/collect/v1", tags=["collector"])


@router.post(
    "/events",
    summary="Accept one first-party analytics event",
    status_code=202,
)
async def collect_event(
    payload: CollectorEventIn,
    niche: AnalyticsNiche = Depends(resolve_public_niche),
    service: AnalyticsService = Depends(get_analytics_service),
) -> CollectorEventOut:
    status, event_id, ledger_id = await service.ingest_event(
        niche_slug=niche.slug,
        event=payload.model_dump(exclude_none=True),
    )
    return CollectorEventOut(event_id=event_id, status=status, ledger_id=ledger_id)


@router.post(
    "/events/batch",
    summary="Accept a batch of first-party analytics events",
    status_code=202,
)
async def collect_batch(
    payload: CollectorBatchIn,
    niche: AnalyticsNiche = Depends(resolve_public_niche),
    service: AnalyticsService = Depends(get_analytics_service),
) -> CollectorBatchOut:
    items: list[CollectorEventOut] = []
    accepted = duplicates = rejected = 0
    for event in payload.events:
        try:
            status, event_id, ledger_id = await service.ingest_event(
                niche_slug=niche.slug, event=event.model_dump(exclude_none=True)
            )
        except Exception as exc:  # noqa: BLE001 — per-item failure isolation
            rejected += 1
            items.append(
                CollectorEventOut(event_id=event.event_id, status="rejected", error=str(exc))
            )
            continue
        if status == "duplicate":
            duplicates += 1
        else:
            accepted += 1
        items.append(CollectorEventOut(event_id=event_id, status=status, ledger_id=ledger_id))
    return CollectorBatchOut(
        accepted=accepted, duplicates=duplicates, rejected=rejected, items=items
    )
