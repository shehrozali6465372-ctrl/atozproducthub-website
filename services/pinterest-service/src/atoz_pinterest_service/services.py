"""Pinterest business service facade (M6).

Owns the business use cases: niche tenancy mirror, per-account management,
OAuth authorization-code connect/disconnect with state/CSRF protection,
token refresh via the Vault boundary, board sync, pin queue publishing with
idempotency + retry, and per-account analytics ingestion.

The service NEVER performs AI work: pin assets/copy arrive pre-authored
from the AI OS workflow and are stored as business data; publishing is pure
transport. No LLM/model SDKs are imported anywhere in this package.
"""

import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from atoz_backend_core.events.publisher import EventPublisher
from atoz_pinterest_service.config import Settings
from atoz_pinterest_service.domain import oauth as oauth_domain
from atoz_pinterest_service.domain import pins as pins_domain
from atoz_pinterest_service.domain.client import (
    PinterestApiClient,
    PinterestApiException,
)
from atoz_pinterest_service.domain.entities import (
    PinPublishAttempt,
    PinQueueItem,
    PinterestAccount,
    PinterestAnalytics,
    PinterestBoard,
    PinterestNiche,
    PinterestPin,
    PinterestToken,
)
from atoz_pinterest_service.domain.enums import (
    AccountStatus,
    BoardStatus,
    BoardSyncState,
    PinStatus,
    PublishAttemptStatus,
    QueueState,
    TokenStatus,
)
from atoz_pinterest_service.domain.events import (
    account_connected_event,
    account_disconnected_event,
    pin_failed_event,
    pin_published_event,
    pin_scheduled_event,
)
from atoz_pinterest_service.domain.rate_limits import PerAccountRateLimiter
from atoz_pinterest_service.domain.secrets import EnvSecretResolver, SecretResolver, TokenVault
from atoz_pinterest_service.errors import (
    DuplicateError,
    NotFoundError,
    OAuthError,
    RemoteApiError,
    ServiceUnavailableError,
    ValidationError,
)
from atoz_pinterest_service.repositories import PinterestUnitOfWork
from atoz_pinterest_service.uuids import uuid7

logger = logging.getLogger("atoz.pinterest.service")

_TOKEN_EXPIRY_MARGIN = 60  # refresh when access token has < 60s left


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


class PinterestService:
    """Facade over the Pinterest business layer (one service per app)."""

    def __init__(
        self,
        *,
        uow_factory,
        event_publisher: EventPublisher,
        settings: Settings,
        secret_resolver: SecretResolver | None = None,
        token_vault: TokenVault | None = None,
        rate_limiter: PerAccountRateLimiter | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._events = event_publisher
        self._settings = settings
        self._secrets = secret_resolver or EnvSecretResolver()
        self._vault = token_vault
        self._limiter = rate_limiter or PerAccountRateLimiter(
            read_per_minute=settings.rate_limit_read_per_minute,
            write_per_minute=settings.rate_limit_write_per_minute,
        )
        self._http = http_client or httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    @staticmethod
    def build_uow(session_factory) -> PinterestUnitOfWork:
        """Build a UoW with the Pinterest module repositories."""
        return PinterestUnitOfWork.build(session_factory)

    # ------------------------------------------------------------ lifecycle
    async def close(self) -> None:
        await self._http.aclose()

    # ----------------------------------------------------------------- niche
    async def create_niche(self, *, name: str, slug: str, status: str = "draft") -> PinterestNiche:
        async with self._uow_factory().transaction() as unit:
            if await unit.niches.slug_exists(slug):
                raise DuplicateError("A niche with this slug already exists.")
            niche = PinterestNiche(id=uuid7(), name=name, slug=slug, status=status)
            await unit.niches.add(niche)
            return niche

    async def update_niche(
        self,
        niche_id: str,
        *,
        name: str | None = None,
        slug: str | None = None,
        status: str | None = None,
    ) -> PinterestNiche:
        async with self._uow_factory().transaction() as unit:
            niche = await unit.niches.get(niche_id)
            if niche is None:
                raise NotFoundError("Niche not found.")
            if slug is not None and slug != niche.slug:
                if await unit.niches.slug_exists(slug, exclude_id=niche_id):
                    raise DuplicateError("A niche with this slug already exists.")
                niche.slug = slug
            if name is not None:
                niche.name = name
            if status is not None:
                niche.status = status
            return niche

    async def get_niche(self, niche_id: str) -> PinterestNiche | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.get(niche_id)

    async def get_niche_by_slug(self, slug: str) -> PinterestNiche | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.get_by_slug(slug)

    async def list_niches(self, *, status: str | None = None) -> Sequence[PinterestNiche]:
        async with self._uow_factory().transaction() as unit:
            return await unit.niches.list_by_status(status)

    # -------------------------------------------------------------- accounts
    async def create_account(
        self, *, niche_id: str, name: str, username: str = ""
    ) -> PinterestAccount:
        async with self._uow_factory().transaction() as unit:
            if await unit.accounts.name_exists(name, niche_id=niche_id):
                raise DuplicateError("An account with this name already exists in this niche.")
            account = PinterestAccount(
                id=uuid7(),
                niche_id=niche_id,
                name=name,
                username=username,
                status=AccountStatus.DRAFT.value,
            )
            await unit.accounts.add(account)
            return account

    async def update_account(
        self,
        account_id: str,
        *,
        niche_id: str,
        name: str | None = None,
        username: str | None = None,
    ) -> PinterestAccount:
        async with self._uow_factory().transaction() as unit:
            account = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if account is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            if name is not None and name != account.name:
                if await unit.accounts.name_exists(name, niche_id=niche_id, exclude_id=account_id):
                    raise DuplicateError("An account with this name already exists in this niche.")
                account.name = name
            if username is not None:
                account.username = username
            return account

    async def get_account(self, account_id: str, *, niche_id: str) -> PinterestAccount | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.accounts.get_scoped(account_id, niche_id=niche_id)

    async def list_accounts(self, niche_id: str) -> Sequence[PinterestAccount]:
        async with self._uow_factory().transaction() as unit:
            return await unit.accounts.list_by_niche(niche_id)

    async def delete_account(self, account_id: str, *, niche_id: str) -> None:
        """Soft-remove an account: disconnect tokens and mark it disconnected.

        Account-scoped child rows are never deleted (audit trail); the
        account leaves the active working set.
        """
        async with self._uow_factory().transaction() as unit:
            account = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if account is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            token = await unit.tokens.get_for_account(account_id, niche_id=niche_id)
            if token is not None:
                token.status = TokenStatus.REVOKED.value
                token.revoked_at = _utcnow()
            account.status = AccountStatus.DISCONNECTED.value
            account.error = ""
            await self._events.publish(
                account_disconnected_event(account_id=account.id, niche_id=niche_id)
            )

    # ----------------------------------------------------------------- oauth
    async def start_connect(self, account_id: str, *, niche_id: str) -> str:
        """Begin OAuth: mint state + PKCE, store on the account, return the
        Pinterest authorization URL (never a token)."""
        async with self._uow_factory().transaction() as unit:
            account = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if account is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            state = oauth_domain.new_state(self._settings.oauth_state_secret, account.id)
            verifier = oauth_domain.new_code_verifier()
            account.oauth_state = state
            account.code_verifier = verifier
            account.status = AccountStatus.PENDING_OAUTH.value
            account.error = ""
        return oauth_domain.build_authorize_url(
            authorize_url=self._settings.oauth_authorize_url,
            client_id=self._settings.oauth_client_id,
            redirect_uri=self._settings.oauth_redirect_uri,
            state=state,
            code_challenge_value=oauth_domain.code_challenge(verifier),
            scopes=self._settings.oauth_scopes,
        )

    async def complete_connect(self, *, query_params: dict[str, str]) -> PinterestAccount:
        """OAuth callback: verify state/CSRF, exchange the code, store the
        token in the vault, mark the account connected."""
        try:
            code, state, error = oauth_domain.parse_callback_params(query_params)
        except ValueError as exc:
            raise OAuthError(str(exc)) from exc
        if error:
            raise OAuthError(f"Pinterest denied authorization: {error}")
        if not state:
            raise OAuthError("OAuth callback missing 'state' parameter.")
        account_id = oauth_domain.verify_state(self._settings.oauth_state_secret, state)
        if account_id is None:
            raise OAuthError("OAuth state verification failed (CSRF).")

        async with self._uow_factory().transaction() as unit:
            account = await unit.accounts.get(account_id)
            if account is None:
                raise OAuthError("Unknown Pinterest account.")
            if account.oauth_state != state:
                raise OAuthError("OAuth state mismatch.")
            if not account.code_verifier:
                raise OAuthError("OAuth flow was not started for this account.")
            verifier = account.code_verifier
            account.code_verifier = ""
            account.oauth_state = ""

            token_payload = await self._exchange_code(code, verifier)
            vault_ref = f"vault://pinterest/accounts/{account.id}/token"
            if self._vault is not None:
                await self._vault.write(vault_ref, token_payload)

            existing = await unit.tokens.get_for_account(account.id, niche_id=account.niche_id)
            access_expires = _utcnow() + timedelta(
                seconds=int(token_payload.get("expires_in", 3600))
            )
            if existing is not None:
                existing.vault_ref = vault_ref
                existing.scopes = token_payload.get("scope", " ".join(self._settings.oauth_scopes))
                existing.status = TokenStatus.ACTIVE.value
                existing.access_expires_at = access_expires
                existing.rotated_at = _utcnow()
                existing.revoked_at = None
                token = existing
            else:
                token = PinterestToken(
                    id=uuid7(),
                    niche_id=account.niche_id,
                    pinterest_account_id=account.id,
                    vault_ref=vault_ref,
                    scopes=token_payload.get("scope", " ".join(self._settings.oauth_scopes)),
                    status=TokenStatus.ACTIVE.value,
                    access_expires_at=access_expires,
                )
                await unit.tokens.add(token)

            account.status = AccountStatus.CONNECTED.value
            account.connected_at = _utcnow()
            account.error = ""
            account.scopes = token.scopes

        # Verify identity + record remote user id (best-effort, outside txn).
        try:
            client = await self._client_for_account(account)
            user = await client.get_user()
            async with self._uow_factory().transaction() as unit:
                stored = await unit.accounts.get_scoped(account.id, niche_id=account.niche_id)
                if stored is not None:
                    stored.remote_user_id = str(user.get("id", ""))
                    stored.username = str(user.get("username", ""))
                    account = stored
        except PinterestApiException as exc:
            logger.warning(
                "oauth_user_verify_failed", extra={"account_id": account.id, "kind": exc.kind.value}
            )
        await self._events.publish(
            account_connected_event(account_id=account.id, niche_id=account.niche_id)
        )
        return account

    async def disconnect_account(self, account_id: str, *, niche_id: str) -> PinterestAccount:
        """Disconnect: revoke the token record and mark the account disconnected."""
        async with self._uow_factory().transaction() as unit:
            account = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if account is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            token = await unit.tokens.get_for_account(account_id, niche_id=niche_id)
            if token is not None:
                token.status = TokenStatus.REVOKED.value
                token.revoked_at = _utcnow()
            account.status = AccountStatus.DISCONNECTED.value
            account.error = ""
            await self._events.publish(
                account_disconnected_event(account_id=account.id, niche_id=niche_id)
            )
            return account

    async def _exchange_code(self, code: str, verifier: str) -> dict[str, str]:
        """Exchange the authorization code for tokens at Pinterest."""
        client_secret = await self._secrets.get(self._settings.oauth_client_secret_ref)
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._settings.oauth_redirect_uri,
            "client_id": self._settings.oauth_client_id,
            "client_secret": client_secret,
            "code_verifier": verifier,
        }
        return await self._token_request(data)

    async def _refresh_tokens(self, refresh_token: str) -> dict[str, str]:
        client_secret = await self._secrets.get(self._settings.oauth_client_secret_ref)
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._settings.oauth_client_id,
            "client_secret": client_secret,
        }
        return await self._token_request(data)

    async def _token_request(self, data: dict[str, str]) -> dict[str, str]:
        try:
            response = await self._http.post(self._settings.oauth_token_url, data=data)
        except httpx.HTTPError as exc:
            raise OAuthError(f"Token endpoint unreachable: {exc}") from exc
        if response.status_code >= 400:
            raise OAuthError(
                f"Pinterest token endpoint rejected the request: {response.status_code}"
            )
        payload = response.json()
        if "access_token" not in payload:
            raise OAuthError("Token response missing access_token.")
        return {
            "access_token": str(payload["access_token"]),
            "refresh_token": str(payload.get("refresh_token", "")),
            "expires_in": str(payload.get("expires_in", "3600")),
            "scope": str(payload.get("scope", "")),
        }

    # ----------------------------------------------------------------- token
    async def _token_provider_for(self, account: PinterestAccount):
        """Build the async token provider the API client uses per account."""

        async def provider(force_refresh: bool = False) -> str:
            token, payload = await self._load_token(account, force_refresh=force_refresh)
            return str(payload["access_token"])

        return provider

    async def _load_token(
        self, account: PinterestAccount, *, force_refresh: bool = False
    ) -> tuple[PinterestToken, dict[str, str]]:
        """Read the current access token, refreshing when expired."""
        if self._vault is None:
            raise ServiceUnavailableError("Token vault is not configured.")
        async with self._uow_factory().transaction() as unit:
            token = await unit.tokens.get_for_account(account.id, niche_id=account.niche_id)
            if token is None:
                raise NotFoundError("No token record for this Pinterest account.")
            vault_ref = token.vault_ref
        payload = await self._vault.read(vault_ref)
        access = payload.get("access_token", "")
        if not access:
            raise ServiceUnavailableError("Token material is missing from the vault.")
        expires_at = payload.get("expires_at")
        expired = (
            force_refresh
            or expires_at is None
            or float(expires_at) - _utcnow().timestamp() < _TOKEN_EXPIRY_MARGIN
        )
        if not expired:
            return token, payload
        refresh_token = payload.get("refresh_token", "")
        if not refresh_token:
            raise ServiceUnavailableError("No refresh token available; reconnect the account.")
        fresh = await self._refresh_tokens(refresh_token)
        fresh["expires_at"] = str(_utcnow().timestamp() + int(fresh.get("expires_in", "3600")))
        if fresh.get("refresh_token"):
            # Pinterest may rotate the refresh token; keep the newest.
            fresh["refresh_token"] = fresh["refresh_token"]
        else:
            fresh["refresh_token"] = refresh_token
        await self._vault.write(vault_ref, fresh)
        async with self._uow_factory().transaction() as unit:
            stored = await unit.tokens.get_for_account(account.id, niche_id=account.niche_id)
            if stored is not None:
                stored.access_expires_at = _utcnow() + timedelta(
                    seconds=int(fresh.get("expires_in", "3600"))
                )
                stored.rotated_at = _utcnow()
                stored.status = TokenStatus.ACTIVE.value
        return token, fresh

    # ---------------------------------------------------------------- client
    async def _client_for_account(self, account: PinterestAccount) -> PinterestApiClient:
        """Create a typed client bound to this account (per-account limits)."""
        provider = await self._token_provider_for(account)
        return PinterestApiClient(
            base_url=self._settings.pinterest_api_base,
            account_id=account.id,
            token_provider=provider,
            rate_limiter=self._limiter,
            timeout_seconds=self._settings.request_timeout_seconds,
            max_retries=self._settings.max_retries,
            base_backoff_seconds=self._settings.base_backoff_seconds,
            max_backoff_seconds=self._settings.max_backoff_seconds,
        )

    # ---------------------------------------------------------------- boards
    async def sync_boards(self, account_id: str, *, niche_id: str) -> Sequence[PinterestBoard]:
        """Sync boards from Pinterest into the account-scoped ledger."""
        async with self._uow_factory().transaction() as unit:
            account = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if account is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            if account.status not in (AccountStatus.CONNECTED.value, AccountStatus.ERROR.value):
                raise ValidationError("Account is not connected.")
        client = await self._client_for_account(account)
        try:
            bookmark: str | None = None
            remote_boards: list[dict[str, Any]] = []
            while True:
                page = await client.list_boards(bookmark=bookmark)
                remote_boards.extend(page.items)
                bookmark = page.bookmark
                if not bookmark:
                    break
        except PinterestApiException as exc:
            raise RemoteApiError(
                f"Board sync failed: {exc.detail}", retryable=exc.retryable
            ) from exc
        finally:
            await client.close()

        async with self._uow_factory().transaction() as unit:
            stored = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if stored is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            for item in remote_boards:
                remote_id = str(item.get("id", ""))
                if not remote_id:
                    continue
                board = await unit.boards.get_by_remote(
                    remote_id, niche_id=niche_id, account_id=account_id
                )
                if board is None:
                    board = PinterestBoard(
                        id=uuid7(),
                        niche_id=niche_id,
                        pinterest_account_id=account_id,
                        remote_board_id=remote_id,
                        name=str(item.get("name", "")),
                        description=str(item.get("description", "")),
                        status=BoardStatus.ACTIVE.value,
                        sync_state=BoardSyncState.SYNCED.value,
                        last_sync_at=_utcnow(),
                    )
                    await unit.boards.add(board)
                else:
                    board.name = str(item.get("name", board.name))
                    board.description = str(item.get("description", board.description))
                    board.sync_state = BoardSyncState.SYNCED.value
                    board.last_sync_at = _utcnow()
            return await unit.boards.list_by_account(account_id, niche_id=niche_id)

    async def list_boards(self, account_id: str, *, niche_id: str) -> Sequence[PinterestBoard]:
        async with self._uow_factory().transaction() as unit:
            if await unit.accounts.get_scoped(account_id, niche_id=niche_id) is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            return await unit.boards.list_by_account(account_id, niche_id=niche_id)

    async def get_board(
        self, board_id: str, *, niche_id: str, account_id: str
    ) -> PinterestBoard | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.boards.get_scoped(board_id, niche_id=niche_id, account_id=account_id)

    async def create_board(
        self, *, niche_id: str, account_id: str, name: str, description: str = ""
    ) -> PinterestBoard:
        """Create a board on Pinterest and record it (account-scoped)."""
        async with self._uow_factory().transaction() as unit:
            account = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if account is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            if account.status not in (AccountStatus.CONNECTED.value, AccountStatus.ERROR.value):
                raise ValidationError("Account is not connected.")
        client = await self._client_for_account(account)
        try:
            remote = await client.create_board(name=name, description=description)
        except PinterestApiException as exc:
            raise RemoteApiError(
                f"Board creation failed: {exc.detail}", retryable=exc.retryable
            ) from exc
        finally:
            await client.close()
        remote_id = str(remote.get("id", ""))
        async with self._uow_factory().transaction() as unit:
            existing = await unit.boards.get_by_remote(
                remote_id, niche_id=niche_id, account_id=account_id
            )
            if existing is not None:
                return existing
            board = PinterestBoard(
                id=uuid7(),
                niche_id=niche_id,
                pinterest_account_id=account_id,
                remote_board_id=remote_id,
                name=name,
                description=description,
                status=BoardStatus.ACTIVE.value,
                sync_state=BoardSyncState.SYNCED.value,
                last_sync_at=_utcnow(),
            )
            await unit.boards.add(board)
            return board

    # ------------------------------------------------------------------ pins
    async def create_pin_draft(
        self,
        *,
        niche_id: str,
        account_id: str,
        board_id: str,
        title: str,
        destination_url: str,
        media_ref: str,
        description: str = "",
        link: str = "",
        article_id: str | None = None,
        scheduled_at: datetime | None = None,
        utms: dict[str, str] | None = None,
    ) -> PinterestPin:
        """Register a pin intent (draft). Duplicate intents are rejected by
        the deterministic checksum (idempotency + duplicate prevention)."""
        async with self._uow_factory().transaction() as unit:
            board = await unit.boards.get_scoped(board_id, niche_id=niche_id, account_id=account_id)
            if board is None:
                raise NotFoundError("Board not found for this account/niche.")
            checksum = pins_domain.pin_checksum(
                account_id=account_id,
                board_id=board_id,
                title=title,
                destination_url=destination_url,
            )
            if await unit.pins.checksum_exists(checksum, niche_id=niche_id, account_id=account_id):
                raise DuplicateError("A pin with this content already exists for the account.")
            pin = PinterestPin(
                id=uuid7(),
                niche_id=niche_id,
                pinterest_account_id=account_id,
                pinterest_board_id=board_id,
                article_id=article_id,
                media_ref=media_ref,
                destination_url=destination_url,
                title=title,
                description=description,
                link=link or destination_url,
                status=PinStatus.DRAFT.value,
                scheduled_at=scheduled_at,
                utms_json=__import__("json").dumps(utms or {}),
                checksum=checksum,
            )
            await unit.pins.add(pin)
            return pin

    async def enqueue_pin(
        self, pin_id: str, *, niche_id: str, account_id: str, run_at: datetime | None = None
    ) -> PinQueueItem:
        """Move a draft pin into the durable queue (draft → queued)."""
        async with self._uow_factory().transaction() as unit:
            pin = await unit.pins.get_scoped(pin_id, niche_id=niche_id, account_id=account_id)
            if pin is None:
                raise NotFoundError("Pin not found for this account/niche.")
            if (
                await unit.queue.get_by_pin(pin_id, niche_id=niche_id, account_id=account_id)
                is not None
            ):
                raise DuplicateError("This pin is already in the queue.")
            if pin.status != PinStatus.DRAFT.value:
                raise ValidationError("Only draft pins can be enqueued.")
            item = PinQueueItem(
                id=uuid7(),
                niche_id=niche_id,
                pinterest_account_id=account_id,
                pinterest_pin_id=pin.id,
                state=QueueState.QUEUED.value,
                run_at=run_at or _utcnow(),
            )
            await unit.queue.add(item)
            pin.status = PinStatus.QUEUED.value
            await self._events.publish(
                pin_scheduled_event(
                    pin_id=pin.id,
                    account_id=account_id,
                    niche_id=niche_id,
                    run_at=_to_iso(item.run_at) or "",
                )
            )
            return item

    async def cancel_pin(self, pin_id: str, *, niche_id: str, account_id: str) -> PinterestPin:
        """Cancel a queued/draft pin (queued → cancelled)."""
        async with self._uow_factory().transaction() as unit:
            pin = await unit.pins.get_scoped(pin_id, niche_id=niche_id, account_id=account_id)
            if pin is None:
                raise NotFoundError("Pin not found for this account/niche.")
            if pin.status in (PinStatus.PUBLISHED.value, PinStatus.PUBLISHING.value):
                raise ValidationError("Published or in-flight pins cannot be cancelled.")
            item = await unit.queue.get_by_pin(pin_id, niche_id=niche_id, account_id=account_id)
            if item is not None and item.state in (
                QueueState.QUEUED.value,
                QueueState.CLAIMED.value,
            ):
                item.state = QueueState.CANCELLED.value
                item.completed_at = _utcnow()
            pin.status = PinStatus.CANCELLED.value
            return pin

    async def publish_due(
        self, *, limit: int = 10, niche_id: str | None = None
    ) -> list[dict[str, str]]:
        """Worker entry point: claim due queue items and publish them.

        ``niche_id`` optionally scopes the run to one niche (automation
        executor); otherwise it claims across accounts (M6 behavior).
        Returns a summary of outcomes (idempotent-safe, per-account limits).
        """
        async with self._uow_factory().transaction() as unit:
            items = await unit.queue.claim_due(
                limit=limit,
                batch_size=self._settings.queue_batch_size,
                niche_id=niche_id,
            )
            snapshot = [
                (item.id, item.pinterest_pin_id, item.pinterest_account_id, item.niche_id)
                for item in items
            ]
        outcomes: list[dict[str, str]] = []
        for item_id, pin_id, account_id, niche_id in snapshot:
            try:
                outcome = await self._publish_one(
                    pin_id=pin_id, niche_id=niche_id, account_id=account_id, queue_item_id=item_id
                )
                outcomes.append(outcome)
            except Exception as exc:  # worker must never die on one pin
                logger.exception(
                    "pin_publish_unhandled", extra={"pin_id": pin_id, "account_id": account_id}
                )
                outcomes.append({"pin_id": pin_id, "status": "failed", "error": str(exc)})
        return outcomes

    async def _publish_one(
        self, *, pin_id: str, niche_id: str, account_id: str, queue_item_id: str | None = None
    ) -> dict[str, str]:
        """Publish one pin: record the attempt, call Pinterest, update ledgers.

        Only safe operations are retried: idempotent failures (rate limit,
        server, network) reset the queue item for a later run while the pin
        stays ``publishing``; permanent failures move the pin to ``failed``.
        """
        async with self._uow_factory().transaction() as unit:
            pin = await unit.pins.get_scoped(pin_id, niche_id=niche_id, account_id=account_id)
            if pin is None:
                return {"pin_id": pin_id, "status": "failed", "error": "pin not found"}
            account = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if account is None:
                return {"pin_id": pin_id, "status": "failed", "error": "account not found"}
            if pin.status not in (PinStatus.QUEUED.value, PinStatus.PUBLISHING.value):
                return {"pin_id": pin_id, "status": "skipped", "error": f"pin state {pin.status}"}
            if account.status not in (AccountStatus.CONNECTED.value, AccountStatus.ERROR.value):
                pin.status = PinStatus.FAILED.value
                return {"pin_id": pin_id, "status": "failed", "error": "account not connected"}
            pin.status = PinStatus.PUBLISHING.value
            item = None
            if queue_item_id:
                item = await unit.queue.get_scoped(
                    queue_item_id, niche_id=niche_id, account_id=account_id
                )
            attempts = await unit.attempts.list_by_pin(
                pin_id, niche_id=niche_id, account_id=account_id
            )
            attempt_no = (attempts[-1].attempt_no if attempts else 0) + 1
            attempt = PinPublishAttempt(
                id=uuid7(),
                niche_id=niche_id,
                pinterest_account_id=account_id,
                pinterest_pin_id=pin.id,
                pin_queue_item_id=item.id if item else None,
                status=PublishAttemptStatus.PENDING.value,
                attempt_no=attempt_no,
                started_at=_utcnow(),
            )
            await unit.attempts.add(attempt)
            attempt_id = attempt.id
            board_id = pin.pinterest_board_id
            media_ref = pin.media_ref
            title = pin.title
            description = pin.description
            link = pin.link

        client = await self._client_for_account(account)
        try:
            remote = await client.create_pin(
                board_id=board_id or "",
                media_source=media_ref,
                title=title,
                description=description,
                link=link,
            )
        except PinterestApiException as exc:
            retryable = exc.retryable
            kind = exc.kind.value
            detail = exc.detail
            http_status = exc.status_code
            outcome_status = pins_domain.attempt_status_for_error(
                retryable=retryable,
                attempts=attempt_no,
                max_attempts=self._settings.publish_retry_attempts,
            )
            async with self._uow_factory().transaction() as unit:
                attempt = await unit.attempts.get(attempt_id)
                if attempt is not None:
                    attempt.status = outcome_status
                    attempt.error_kind = kind
                    attempt.error_detail = detail[:500]
                    attempt.http_status = http_status
                    attempt.completed_at = _utcnow()
                stored_pin = await unit.pins.get_scoped(
                    pin_id, niche_id=niche_id, account_id=account_id
                )
                if stored_pin is not None:
                    if outcome_status == PublishAttemptStatus.FAILED.value:
                        stored_pin.status = PinStatus.FAILED.value
                    # retryable: pin stays ``publishing``; queue resets below
                if item is not None:
                    stored_item = await unit.queue.get_scoped(
                        item.id, niche_id=niche_id, account_id=account_id
                    )
                    if stored_item is not None:
                        stored_item.attempts = attempt_no
                        if outcome_status == PublishAttemptStatus.FAILED.value:
                            stored_item.state = QueueState.FAILED.value
                            stored_item.completed_at = _utcnow()
                            stored_item.error = detail[:500]
                        else:
                            stored_item.state = QueueState.QUEUED.value
                            stored_item.run_at = _utcnow() + timedelta(minutes=5 * attempt_no)
            if outcome_status == PublishAttemptStatus.FAILED.value:
                await self._events.publish(
                    pin_failed_event(
                        pin_id=pin_id, account_id=account_id, niche_id=niche_id, error=detail[:300]
                    )
                )
            return {
                "pin_id": pin_id,
                "status": outcome_status,
                "error": detail[:200],
                "attempt": str(attempt_no),
            }

        finally:
            await client.close()

        remote_pin_id = str(remote.get("id", ""))
        pin_url = str(remote.get("link", ""))
        async with self._uow_factory().transaction() as unit:
            attempt = await unit.attempts.get(attempt_id)
            if attempt is not None:
                attempt.status = PublishAttemptStatus.SUCCESS.value
                attempt.remote_pin_id = remote_pin_id
                attempt.http_status = 200
                attempt.completed_at = _utcnow()
            stored_pin = await unit.pins.get_scoped(
                pin_id, niche_id=niche_id, account_id=account_id
            )
            if stored_pin is not None:
                stored_pin.status = PinStatus.PUBLISHED.value
                stored_pin.remote_pin_id = remote_pin_id
                stored_pin.pin_url = pin_url
                stored_pin.published_at = _utcnow()
            if item is not None:
                stored_item = await unit.queue.get_scoped(
                    item.id, niche_id=niche_id, account_id=account_id
                )
                if stored_item is not None:
                    stored_item.state = QueueState.DONE.value
                    stored_item.attempts = attempt_no
                    stored_item.completed_at = _utcnow()
                    stored_item.error = ""
        await self._events.publish(
            pin_published_event(
                pin_id=pin_id, account_id=account_id, niche_id=niche_id, remote_pin_id=remote_pin_id
            )
        )
        return {"pin_id": pin_id, "status": "published", "remote_pin_id": remote_pin_id}

    async def list_pins(
        self,
        account_id: str,
        *,
        niche_id: str,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[PinterestPin]:
        async with self._uow_factory().transaction() as unit:
            if await unit.accounts.get_scoped(account_id, niche_id=niche_id) is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            return await unit.pins.list_by_account(
                account_id, niche_id=niche_id, status=status, limit=limit, offset=offset
            )

    async def list_queue(
        self, account_id: str, *, niche_id: str, state: str | None = None
    ) -> Sequence[PinQueueItem]:
        async with self._uow_factory().transaction() as unit:
            if await unit.accounts.get_scoped(account_id, niche_id=niche_id) is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            return await unit.queue.list_by_account(account_id, niche_id=niche_id, state=state)

    async def list_attempts(
        self, pin_id: str, *, niche_id: str, account_id: str
    ) -> Sequence[PinPublishAttempt]:
        async with self._uow_factory().transaction() as unit:
            pin = await unit.pins.get_scoped(pin_id, niche_id=niche_id, account_id=account_id)
            if pin is None:
                raise NotFoundError("Pin not found for this account/niche.")
            return await unit.attempts.list_by_pin(pin_id, niche_id=niche_id, account_id=account_id)

    async def account_status(self, account_id: str, *, niche_id: str) -> dict[str, Any]:
        """Per-account rate-limit/status summary (admin dashboard)."""
        async with self._uow_factory().transaction() as unit:
            account = await unit.accounts.get_scoped(account_id, niche_id=niche_id)
            if account is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            token = await unit.tokens.get_for_account(account_id, niche_id=niche_id)
            counts = {
                status: await unit.pins.count_by_account_status(
                    account_id, niche_id=niche_id, status=status
                )
                for status in ("queued", "publishing", "published", "failed")
            }
            board_count = len(await unit.boards.list_by_account(account_id, niche_id=niche_id))
            return {
                "account_id": account.id,
                "niche_id": account.niche_id,
                "name": account.name,
                "status": account.status,
                "connected_at": _to_iso(account.connected_at),
                "rate_limit_status": account.rate_limit_status,
                "last_rate_limit_at": _to_iso(account.last_rate_limit_at),
                "token_status": token.status if token else None,
                "token_expires_at": _to_iso(token.access_expires_at if token else None),
                "board_count": board_count,
                "pin_counts": counts,
            }

    # -------------------------------------------------------------- analytics
    async def upsert_analytics(
        self,
        *,
        niche_id: str,
        account_id: str,
        metric_date: str,
        impressions: int = 0,
        saves: int = 0,
        clicks: int = 0,
        outbound_clicks: int = 0,
        engagement: int = 0,
    ) -> PinterestAnalytics:
        """Ingest a per-account daily Pinterest business metric row.

        Business data only — no AI analytics engine (Task 16 rule); AI OS
        insights remain read-only through the AI OS Bridge.
        """
        async with self._uow_factory().transaction() as unit:
            if await unit.accounts.get_scoped(account_id, niche_id=niche_id) is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            existing = await unit.analytics.get_for_date(
                account_id, niche_id=niche_id, metric_date=metric_date
            )
            if existing is not None:
                existing.impressions = impressions
                existing.saves = saves
                existing.clicks = clicks
                existing.outbound_clicks = outbound_clicks
                existing.engagement = engagement
                return existing
            row = PinterestAnalytics(
                id=uuid7(),
                niche_id=niche_id,
                pinterest_account_id=account_id,
                metric_date=metric_date,
                impressions=impressions,
                saves=saves,
                clicks=clicks,
                outbound_clicks=outbound_clicks,
                engagement=engagement,
            )
            await unit.analytics.add(row)
            return row

    async def list_analytics(
        self, account_id: str, *, niche_id: str, limit: int = 30
    ) -> Sequence[PinterestAnalytics]:
        async with self._uow_factory().transaction() as unit:
            if await unit.accounts.get_scoped(account_id, niche_id=niche_id) is None:
                raise NotFoundError("Pinterest account not found in this niche.")
            return await unit.analytics.list_by_account(account_id, niche_id=niche_id, limit=limit)

    # --------------------------------------------------------------- public
    async def public_account(self, niche_id: str, account_id: str) -> PinterestAccount | None:
        async with self._uow_factory().transaction() as unit:
            return await unit.accounts.get_scoped(account_id, niche_id=niche_id)

    async def public_pins(
        self, *, niche_id: str, account_id: str | None = None, limit: int = 100
    ) -> Sequence[PinterestPin]:
        """Read-only published pins for public landing pages (never mutations)."""
        async with self._uow_factory().transaction() as unit:
            if account_id:
                if await unit.accounts.get_scoped(account_id, niche_id=niche_id) is None:
                    raise NotFoundError("Pinterest account not found in this niche.")
                return await unit.pins.list_by_account(
                    account_id, niche_id=niche_id, status=PinStatus.PUBLISHED.value, limit=limit
                )
            # Aggregate across accounts requires a niche-wide query: the
            # repository is account-scoped by design, so iterate accounts.
            accounts = await unit.accounts.list_by_niche(niche_id)
            pins: list[PinterestPin] = []
            for account in accounts:
                if account.status != AccountStatus.CONNECTED.value:
                    continue
                pins.extend(
                    await unit.pins.list_by_account(
                        account.id, niche_id=niche_id, status=PinStatus.PUBLISHED.value, limit=limit
                    )
                )
            return pins[:limit]
