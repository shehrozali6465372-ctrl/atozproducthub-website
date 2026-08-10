"""OAuth 2.0 authorization-code flow endpoints (Pinterest).

- ``GET /oauth/authorize`` is not a browser route: the admin API starts the
  flow and returns the Pinterest authorization URL (state + PKCE already
  minted server-side). The operator opens that URL in the browser.
- ``GET /oauth/callback`` receives Pinterest's redirect with ``code`` +
  ``state``; the service verifies state (CSRF), exchanges the code, stores
  the token in the vault, and marks the account connected.

Token VALUES never appear in responses, logs, or the database.
"""

from fastapi import APIRouter, Depends, Request

from atoz_pinterest_service.routes.deps import get_pinterest_service
from atoz_pinterest_service.schemas import AccountOut
from atoz_pinterest_service.services import PinterestService

router = APIRouter(prefix="/oauth", tags=["pinterest-oauth"])


@router.get("/callback", summary="OAuth callback from Pinterest")
async def oauth_callback(
    request: Request,
    service: PinterestService = Depends(get_pinterest_service),
) -> AccountOut:
    query: dict[str, str] = {key: value for key, value in request.query_params.items()}
    account = await service.complete_connect(query_params=query)
    return AccountOut.model_validate(account, from_attributes=True)
