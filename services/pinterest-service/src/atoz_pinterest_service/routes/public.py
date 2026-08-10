"""Public read API for the Pinterest module.

Read-only: landing pages and pin/board discovery by niche slug. No
mutations, no token data, no account secrets (Task 16 rule). Published pins
only — drafts, queues, and internal states are never exposed.
"""

from fastapi import APIRouter, Depends, Query

from atoz_pinterest_service.domain.entities import PinterestNiche
from atoz_pinterest_service.routes.deps import (
    get_pinterest_service,
    resolve_public_niche,
)
from atoz_pinterest_service.schemas import Page, PublicAccountOut, PublicBoardOut, PublicPinOut
from atoz_pinterest_service.services import PinterestService

router = APIRouter(prefix="/api/v1/public", tags=["public-pinterest"])


def _public_pin(pin, board_name: str, account_name: str) -> PublicPinOut:
    return PublicPinOut(
        id=pin.id,
        slug=pin.id,
        title=pin.title,
        description=pin.description,
        board=board_name,
        account_name=account_name,
        destination_url=pin.destination_url,
        pin_url=pin.pin_url,
        published_at=pin.published_at,
        saves="",
    )


@router.get("/accounts", summary="List connected Pinterest accounts for a niche")
async def list_accounts(
    niche: PinterestNiche = Depends(resolve_public_niche),
    service: PinterestService = Depends(get_pinterest_service),
) -> list[PublicAccountOut]:
    accounts = await service.list_accounts(niche.id)
    return [
        PublicAccountOut(id=a.id, name=a.name, username=a.username, status=a.status)
        for a in accounts
        if a.status == "connected"
    ]


@router.get("/boards", summary="List boards for a niche (optionally per account)")
async def list_boards(
    niche: PinterestNiche = Depends(resolve_public_niche),
    account_id: str | None = Query(default=None),
    service: PinterestService = Depends(get_pinterest_service),
) -> list[PublicBoardOut]:
    accounts = [a for a in await service.list_accounts(niche.id) if a.status == "connected"]
    if account_id:
        accounts = [a for a in accounts if a.id == account_id]
    boards: list[PublicBoardOut] = []
    for account in accounts:
        for board in await service.list_boards(account.id, niche_id=niche.id):
            if board.status == "active":
                boards.append(
                    PublicBoardOut(
                        id=board.id,
                        remote_board_id=board.remote_board_id,
                        name=board.name,
                        description=board.description,
                    )
                )
    return boards


@router.get("/pins", summary="Published pins for a niche (optionally per account)")
async def list_pins(
    niche: PinterestNiche = Depends(resolve_public_niche),
    account_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    service: PinterestService = Depends(get_pinterest_service),
) -> Page[PublicPinOut]:
    pins = await service.public_pins(niche_id=niche.id, account_id=account_id, limit=limit)
    account_names: dict[str, str] = {}
    board_names: dict[str, str] = {}
    for account in await service.list_accounts(niche.id):
        account_names[account.id] = account.name
        for board in await service.list_boards(account.id, niche_id=niche.id):
            board_names[board.id] = board.name
    items = [
        _public_pin(
            pin,
            board_name=board_names.get(pin.pinterest_board_id or "", ""),
            account_name=account_names.get(pin.pinterest_account_id, ""),
        )
        for pin in pins
    ]
    return Page[PublicPinOut](items=items, page=1, page_size=limit, total=len(items))
