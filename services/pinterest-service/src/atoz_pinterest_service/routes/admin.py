"""Admin API for the Pinterest module.

Mirrors the Admin API conventions (12-api-contracts.md §5): Bearer JWT with
``pinterest:read`` / ``pinterest:write`` RBAC claims, a mandatory
``X-Niche-Id`` tenancy header, and a mandatory account id in every
account-scoped path. Token VALUES are never returned — only vault refs,
scopes, and expiry metadata.
"""

from fastapi import APIRouter, Depends, Query

from atoz_backend_core.auth import TokenClaims
from atoz_pinterest_service.domain.entities import PinterestAccount, PinterestNiche
from atoz_pinterest_service.routes.deps import (
    get_pinterest_service,
    require_account,
    require_niche,
    require_permission,
)
from atoz_pinterest_service.schemas import (
    AccountCreate,
    AccountOut,
    AccountStatusOut,
    AccountUpdate,
    AnalyticsOut,
    AnalyticsUpsert,
    BoardCreate,
    BoardOut,
    ConnectStartOut,
    NicheMirrorCreate,
    NicheMirrorUpdate,
    Page,
    PinCreate,
    PinOut,
    PublishAttemptOut,
    QueueItemOut,
)
from atoz_pinterest_service.services import PinterestService

router = APIRouter(prefix="/api/v1/admin", tags=["admin-pinterest"])

READ = require_permission("pinterest:read")
WRITE = require_permission("pinterest:write")


# ------------------------------------------------------- niche registry mirror
@router.get("/niches", summary="List Pinterest tenancy mirror niches")
async def list_niches(
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
):
    niches = await service.list_niches()
    return [{"id": n.id, "slug": n.slug, "name": n.name, "status": n.status} for n in niches]


@router.post("/niches", summary="Provision the local tenancy mirror niche", status_code=201)
async def create_niche(
    payload: NicheMirrorCreate,
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
):
    niche = await service.create_niche(name=payload.name, slug=payload.slug, status=payload.status)
    return {"id": niche.id, "slug": niche.slug, "name": niche.name, "status": niche.status}


@router.patch("/niches/{niche_id}", summary="Update the local tenancy mirror niche")
async def update_niche(
    niche_id: str,
    payload: NicheMirrorUpdate,
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
):
    niche = await service.update_niche(
        niche_id, name=payload.name, slug=payload.slug, status=payload.status
    )
    return {"id": niche.id, "slug": niche.slug, "name": niche.name, "status": niche.status}


# --------------------------------------------------------------- accounts
@router.get("/accounts", summary="List Pinterest accounts for the active niche")
async def list_accounts(
    _niche: PinterestNiche = Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
) -> list[AccountOut]:
    accounts = await service.list_accounts(_niche.id)
    return [AccountOut.model_validate(a, from_attributes=True) for a in accounts]


@router.post("/accounts", summary="Create a Pinterest account (draft)", status_code=201)
async def create_account(
    payload: AccountCreate,
    _niche: PinterestNiche = Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> AccountOut:
    account = await service.create_account(
        niche_id=_niche.id, name=payload.name, username=payload.username
    )
    return AccountOut.model_validate(account, from_attributes=True)


@router.patch("/accounts/{account_id}", summary="Update a Pinterest account")
async def update_account(
    payload: AccountUpdate,
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> AccountOut:
    updated = await service.update_account(
        account.id, niche_id=account.niche_id, name=payload.name, username=payload.username
    )
    return AccountOut.model_validate(updated, from_attributes=True)


@router.get("/accounts/{account_id}", summary="Get a Pinterest account")
async def get_account(
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
) -> AccountOut:
    return AccountOut.model_validate(account, from_attributes=True)


@router.get("/accounts/{account_id}/status", summary="Per-account status and rate-limit summary")
async def account_status(
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
) -> AccountStatusOut:
    return AccountStatusOut(**await service.account_status(account.id, niche_id=account.niche_id))


@router.post(
    "/accounts/{account_id}/connect", summary="Start OAuth connect (returns authorize URL)"
)
async def start_connect(
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> ConnectStartOut:
    authorize_url = await service.start_connect(account.id, niche_id=account.niche_id)
    return ConnectStartOut(account_id=account.id, authorize_url=authorize_url)


@router.post("/accounts/{account_id}/disconnect", summary="Disconnect a Pinterest account")
async def disconnect_account(
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> AccountOut:
    updated = await service.disconnect_account(account.id, niche_id=account.niche_id)
    return AccountOut.model_validate(updated, from_attributes=True)


# ---------------------------------------------------------------- boards
@router.get("/accounts/{account_id}/boards", summary="List boards for an account")
async def list_boards(
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
) -> list[BoardOut]:
    boards = await service.list_boards(account.id, niche_id=account.niche_id)
    return [BoardOut.model_validate(b, from_attributes=True) for b in boards]


@router.post("/accounts/{account_id}/boards/sync", summary="Sync boards from Pinterest")
async def sync_boards(
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> list[BoardOut]:
    boards = await service.sync_boards(account.id, niche_id=account.niche_id)
    return [BoardOut.model_validate(b, from_attributes=True) for b in boards]


@router.post(
    "/accounts/{account_id}/boards",
    summary="Create a board on Pinterest + record it",
    status_code=201,
)
async def create_board(
    payload: BoardCreate,
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> BoardOut:
    board = await service.create_board(
        niche_id=account.niche_id,
        account_id=account.id,
        name=payload.name,
        description=payload.description,
    )
    return BoardOut.model_validate(board, from_attributes=True)


# -------------------------------------------------------------------- pins
@router.post("/accounts/{account_id}/pins", summary="Register a pin draft", status_code=201)
async def create_pin_draft(
    payload: PinCreate,
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> PinOut:
    pin = await service.create_pin_draft(
        niche_id=account.niche_id,
        account_id=account.id,
        board_id=payload.board_id,
        title=payload.title,
        destination_url=payload.destination_url,
        media_ref=payload.media_ref,
        description=payload.description,
        link=payload.link,
        article_id=payload.article_id,
        scheduled_at=payload.scheduled_at,
        utms=payload.utms,
    )
    return PinOut.model_validate(pin, from_attributes=True)


@router.get("/accounts/{account_id}/pins", summary="List pins for an account")
async def list_pins(
    account: PinterestAccount = Depends(require_account),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
) -> Page[PinOut]:
    pins = await service.list_pins(
        account.id, niche_id=account.niche_id, status=status_filter, limit=limit, offset=offset
    )
    return Page[PinOut](
        items=[PinOut.model_validate(p, from_attributes=True) for p in pins],
        page=offset // limit + 1,
        page_size=limit,
        total=len(pins),
    )


@router.post(
    "/accounts/{account_id}/pins/{pin_id}/enqueue", summary="Enqueue a draft pin for publishing"
)
async def enqueue_pin(
    pin_id: str,
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> QueueItemOut:
    item = await service.enqueue_pin(pin_id, niche_id=account.niche_id, account_id=account.id)
    return QueueItemOut.model_validate(item, from_attributes=True)


@router.post("/accounts/{account_id}/pins/{pin_id}/cancel", summary="Cancel a queued pin")
async def cancel_pin(
    pin_id: str,
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> PinOut:
    pin = await service.cancel_pin(pin_id, niche_id=account.niche_id, account_id=account.id)
    return PinOut.model_validate(pin, from_attributes=True)


@router.get(
    "/accounts/{account_id}/pins/{pin_id}/attempts", summary="Publishing attempts for a pin"
)
async def pin_attempts(
    pin_id: str,
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
) -> list[PublishAttemptOut]:
    attempts = await service.list_attempts(pin_id, niche_id=account.niche_id, account_id=account.id)
    return [PublishAttemptOut.model_validate(a, from_attributes=True) for a in attempts]


# ---------------------------------------------------------------- queue
@router.get("/accounts/{account_id}/queue", summary="Pin queue for an account")
async def list_queue(
    account: PinterestAccount = Depends(require_account),
    state: str | None = Query(default=None),
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
) -> list[QueueItemOut]:
    items = await service.list_queue(account.id, niche_id=account.niche_id, state=state)
    return [QueueItemOut.model_validate(i, from_attributes=True) for i in items]


@router.post("/queue/publish-due", summary="Run the queue worker (claim + publish due pins)")
async def publish_due(
    limit: int = Query(default=10, ge=1, le=100),
    niche_id: str | None = Query(default=None, max_length=36),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
):
    return await service.publish_due(limit=limit, niche_id=niche_id)


# -------------------------------------------------------------- analytics
@router.post(
    "/accounts/{account_id}/analytics",
    summary="Upsert a per-account daily metric row",
    status_code=201,
)
async def upsert_analytics(
    payload: AnalyticsUpsert,
    account: PinterestAccount = Depends(require_account),
    _claims: TokenClaims = Depends(WRITE),
    service: PinterestService = Depends(get_pinterest_service),
) -> AnalyticsOut:
    row = await service.upsert_analytics(
        niche_id=account.niche_id,
        account_id=account.id,
        metric_date=payload.metric_date,
        impressions=payload.impressions,
        saves=payload.saves,
        clicks=payload.clicks,
        outbound_clicks=payload.outbound_clicks,
        engagement=payload.engagement,
    )
    return AnalyticsOut.model_validate(row, from_attributes=True)


@router.get("/accounts/{account_id}/analytics", summary="Per-account daily metrics")
async def list_analytics(
    account: PinterestAccount = Depends(require_account),
    limit: int = Query(default=30, ge=1, le=365),
    _claims: TokenClaims = Depends(READ),
    service: PinterestService = Depends(get_pinterest_service),
) -> list[AnalyticsOut]:
    rows = await service.list_analytics(account.id, niche_id=account.niche_id, limit=limit)
    return [AnalyticsOut.model_validate(r, from_attributes=True) for r in rows]
