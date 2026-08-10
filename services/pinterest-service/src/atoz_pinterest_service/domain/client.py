"""Typed Pinterest API v5 client (business layer only).

Boards CRUD, board sections, pins create/read/delete, and bookmark
pagination. Handles 401/403/429/5xx, exponential backoff + jitter, and
per-account rate limiting by Pinterest's org_read/org_write categories —
one account's throttle never blocks another (Task 16 rule).

The client never performs AI work: it sends pre-authored pin assets and
copy that were created by the website/AI OS workflow and stored as business
data. It never calls any LLM provider.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from atoz_pinterest_service.domain.enums import RemoteErrorKind
from atoz_pinterest_service.domain.rate_limits import (
    PerAccountRateLimiter,
    backoff_delay,
    classify_http_error,
    is_retryable,
)

logger = logging.getLogger("atoz.pinterest.client")

CATEGORY_READ = "org_read"
CATEGORY_WRITE = "org_write"


class PinterestApiException(Exception):
    """Typed failure from the Pinterest API with a retry decision."""

    def __init__(
        self, kind: RemoteErrorKind, *, status_code: int | None = None, detail: str = ""
    ) -> None:
        super().__init__(detail or kind.value)
        self.kind = kind
        self.status_code = status_code
        self.detail = detail or kind.value
        self.retryable = is_retryable(kind)


@dataclass
class Page:
    """Bookmark-paginated Pinterest response (API v5)."""

    items: list[dict[str, Any]]
    bookmark: str | None = None


class PinterestApiClient:
    """HTTP client bound to one Pinterest account's access token.

    ``token_provider`` is an async callable returning the current access
    token; the service wires it so a 401 can trigger a token refresh and
    retry once.
    """

    def __init__(
        self,
        *,
        base_url: str,
        account_id: str,
        token_provider,
        rate_limiter: PerAccountRateLimiter | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 15.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._account_id = account_id
        self._token_provider = token_provider
        self._rate_limiter = rate_limiter or PerAccountRateLimiter(
            read_per_minute=600, write_per_minute=200
        )
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._base_backoff = base_backoff_seconds
        self._max_backoff = max_backoff_seconds
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout_seconds,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------ transport
    async def _request(
        self,
        method: str,
        path: str,
        *,
        category: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        allow_refresh: bool = True,
    ) -> httpx.Response:
        """Rate-limited, retried, refresh-aware request (single account)."""
        attempt = 0
        while True:
            await self._rate_limiter.acquire(self._account_id, category)
            token = await self._token_provider()
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
            try:
                response = await self._client.request(
                    method, path, params=params, json=json_body, headers=headers
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                kind = RemoteErrorKind.NETWORK
                if attempt >= self._max_retries:
                    raise PinterestApiException(kind, detail=f"transport error: {exc}") from exc
                await asyncio.sleep(
                    backoff_delay(
                        attempt=attempt, base=self._base_backoff, max_delay=self._max_backoff
                    )
                )
                attempt += 1
                continue

            kind = classify_http_error(response.status_code)

            if response.status_code == 401 and allow_refresh:
                # One refresh + retry: the token provider re-issues via the
                # refresh flow; the second 401 is a hard failure.
                try:
                    await self._token_provider(force_refresh=True)
                except Exception as exc:  # refresh failed — surface the original
                    raise PinterestApiException(
                        RemoteErrorKind.UNAUTHORIZED,
                        status_code=401,
                        detail=f"token refresh failed: {exc}",
                    ) from exc
                attempt += 1
                allow_refresh = False
                continue

            if kind in (RemoteErrorKind.RATE_LIMITED, RemoteErrorKind.SERVER_ERROR):
                if attempt >= self._max_retries:
                    raise PinterestApiException(
                        kind, status_code=response.status_code, detail=response.text[:500]
                    )
                delay = backoff_delay(
                    attempt=attempt, base=self._base_backoff, max_delay=self._max_backoff
                )
                if kind == RemoteErrorKind.RATE_LIMITED:
                    # Honor Pinterest's Retry-After when present.
                    retry_after = response.headers.get("retry-after")
                    if retry_after and retry_after.isdigit():
                        delay = max(delay, float(retry_after))
                await asyncio.sleep(delay)
                attempt += 1
                continue

            if 200 <= response.status_code < 300:
                return response
            raise PinterestApiException(
                kind, status_code=response.status_code, detail=response.text[:500]
            )

    async def _get_json(
        self, method: str, path: str, *, category: str, **kwargs: Any
    ) -> dict[str, Any]:
        response = await self._request(method, path, category=category, **kwargs)
        return response.json()

    # --------------------------------------------------------------- user
    async def get_user(self) -> dict[str, Any]:
        """Fetch the authenticated user (used at connect/callback time)."""
        return await self._get_json("GET", "/user_account", category=CATEGORY_READ)

    # -------------------------------------------------------------- boards
    async def list_boards(self, bookmark: str | None = None, page_size: int = 25) -> Page:
        params: dict[str, Any] = {"page_size": page_size}
        if bookmark:
            params["bookmark"] = bookmark
        data = await self._get_json("GET", "/boards", category=CATEGORY_READ, params=params)
        return Page(items=data.get("items", []), bookmark=data.get("bookmark"))

    async def create_board(self, *, name: str, description: str = "") -> dict[str, Any]:
        return await self._get_json(
            "POST",
            "/boards",
            category=CATEGORY_WRITE,
            json_body={"name": name, "description": description},
        )

    async def update_board(
        self, board_id: str, *, name: str, description: str = ""
    ) -> dict[str, Any]:
        return await self._get_json(
            "PATCH",
            f"/boards/{board_id}",
            category=CATEGORY_WRITE,
            json_body={"name": name, "description": description},
        )

    async def delete_board(self, board_id: str) -> None:
        await self._request("DELETE", f"/boards/{board_id}", category=CATEGORY_WRITE)

    # ------------------------------------------------------------ sections
    async def list_sections(
        self, board_id: str, bookmark: str | None = None, page_size: int = 25
    ) -> Page:
        params: dict[str, Any] = {"page_size": page_size}
        if bookmark:
            params["bookmark"] = bookmark
        data = await self._get_json(
            "GET", f"/boards/{board_id}/sections", category=CATEGORY_READ, params=params
        )
        return Page(items=data.get("items", []), bookmark=data.get("bookmark"))

    async def create_section(self, board_id: str, *, name: str) -> dict[str, Any]:
        return await self._get_json(
            "POST",
            f"/boards/{board_id}/sections",
            category=CATEGORY_WRITE,
            json_body={"name": name},
        )

    # ---------------------------------------------------------------- pins
    async def create_pin(
        self,
        *,
        board_id: str,
        media_source: str,
        title: str,
        description: str = "",
        link: str = "",
        alt_text: str | None = None,
        section_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a pin from a media source URL (image/video hosted by us).

        Only pre-authored content from the website/AI OS workflow is
        published — never third-party curated content (Task 16 rule).
        """
        body: dict[str, Any] = {
            "board_id": board_id,
            "media_source": {"source_type": "image_url", "url": media_source},
            "title": title,
            "description": description,
            "link": link,
        }
        if alt_text:
            body["alt_text"] = alt_text
        if section_id:
            body["section_id"] = section_id
        return await self._get_json("POST", "/pins", category=CATEGORY_WRITE, json_body=body)

    async def get_pin(self, pin_id: str) -> dict[str, Any]:
        return await self._get_json("GET", f"/pins/{pin_id}", category=CATEGORY_READ)

    async def list_pins(
        self, board_id: str | None = None, bookmark: str | None = None, page_size: int = 25
    ) -> Page:
        params: dict[str, Any] = {"page_size": page_size}
        if board_id:
            params["board_id"] = board_id
        if bookmark:
            params["bookmark"] = bookmark
        data = await self._get_json("GET", "/pins", category=CATEGORY_READ, params=params)
        return Page(items=data.get("items", []), bookmark=data.get("bookmark"))

    async def delete_pin(self, pin_id: str) -> None:
        await self._request("DELETE", f"/pins/{pin_id}", category=CATEGORY_WRITE)
