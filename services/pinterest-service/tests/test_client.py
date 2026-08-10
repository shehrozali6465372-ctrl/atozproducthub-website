"""PinterestApiClient tests: boards, pins, pagination, auth, retries.

The client talks to a mock transport; per-account rate limiting and
retry/backoff behavior are asserted without any network access.
"""

import json

from atoz_pinterest_service.domain.client import (
    PinterestApiClient,
    PinterestApiException,
)
from atoz_pinterest_service.domain.enums import RemoteErrorKind
from atoz_pinterest_service.domain.rate_limits import PerAccountRateLimiter, classify_http_error

from .fixtures import MockPinterestTransport

ACCOUNT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


async def _client(transport: MockPinterestTransport, *, token: str = "tok-1") -> PinterestApiClient:
    return PinterestApiClient(
        base_url="https://api.pinterest.test/v5",
        account_id=ACCOUNT,
        token_provider=lambda force_refresh=False: __import__("asyncio").sleep(0) or token,
        rate_limiter=PerAccountRateLimiter(read_per_minute=600, write_per_minute=200),
        timeout_seconds=5.0,
        max_retries=2,
        base_backoff_seconds=0.01,
        max_backoff_seconds=0.05,
        transport=transport,
    )


def _run(coro):
    import asyncio

    return asyncio.run(coro)


def test_list_boards_with_bookmark_pagination() -> None:
    transport = MockPinterestTransport()
    transport.boards = [{"id": "b1", "name": "Kitchen"}, {"id": "b2", "name": "Office"}]

    async def scenario() -> None:
        client = await _client(transport)
        try:
            page = await client.list_boards()
            assert [b["id"] for b in page.items] == ["b1", "b2"]
            assert page.bookmark is None
        finally:
            await client.close()

    _run(scenario())


def test_create_board_and_pin() -> None:
    transport = MockPinterestTransport()

    async def scenario() -> None:
        client = await _client(transport)
        try:
            board = await client.create_board(name="Travel", description="Gear")
            assert board["id"] == "b-1"
            pin = await client.create_pin(
                board_id=board["id"],
                media_source="https://media.example/pin.jpg",
                title="Pack light",
                link="https://atozproducthub.dev/landing/pack-light",
            )
            assert pin["id"] == "p-1"
            assert pin["board_id"] == "b-1"
            # The create payload uses our own hosted media + link only.
            body = json.loads(transport.requests[-1].content)
            assert body["media_source"]["url"] == "https://media.example/pin.jpg"
            assert body["link"] == "https://atozproducthub.dev/landing/pack-light"
        finally:
            await client.close()

    _run(scenario())


def test_429_retries_then_succeeds() -> None:
    transport = MockPinterestTransport()
    transport.add_failure(429, "rate limited")
    transport.add_failure(429, "rate limited")
    transport.boards = [{"id": "b1", "name": "Kitchen"}]

    async def scenario() -> None:
        client = await _client(transport)
        try:
            page = await client.list_boards()
            assert [b["id"] for b in page.items] == ["b1"]
            assert sum(1 for r in transport.requests if r.url.path == "/v5/boards") == 3
        finally:
            await client.close()

    _run(scenario())


def test_429_exhausts_retries_and_raises() -> None:
    transport = MockPinterestTransport()
    for _ in range(4):
        transport.add_failure(429, "rate limited")

    async def scenario() -> None:
        client = await _client(transport)
        try:
            try:
                await client.list_boards()
                raise AssertionError("expected PinterestApiException")
            except PinterestApiException as exc:
                assert exc.kind == RemoteErrorKind.RATE_LIMITED
                assert exc.retryable is True
        finally:
            await client.close()

    _run(scenario())


def test_403_is_non_retryable() -> None:
    transport = MockPinterestTransport()
    transport.add_failure(403, "forbidden")

    async def scenario() -> None:
        client = await _client(transport)
        try:
            try:
                await client.list_boards()
                raise AssertionError("expected PinterestApiException")
            except PinterestApiException as exc:
                assert exc.kind == RemoteErrorKind.FORBIDDEN
                assert exc.retryable is False
                assert sum(1 for r in transport.requests) == 1  # no retries
        finally:
            await client.close()

    _run(scenario())


def test_401_triggers_token_refresh_once() -> None:
    transport = MockPinterestTransport()
    transport.add_failure(401, "expired")
    transport.boards = [{"id": "b1", "name": "Kitchen"}]
    refreshes = {"count": 0}

    async def provider(force_refresh: bool = False) -> str:
        if force_refresh:
            refreshes["count"] += 1
            return "tok-2"
        return "tok-1"

    async def scenario() -> None:
        client = PinterestApiClient(
            base_url="https://api.pinterest.test/v5",
            account_id=ACCOUNT,
            token_provider=provider,
            rate_limiter=PerAccountRateLimiter(read_per_minute=600, write_per_minute=200),
            timeout_seconds=5.0,
            max_retries=2,
            base_backoff_seconds=0.01,
            max_backoff_seconds=0.05,
            transport=transport,
        )
        try:
            page = await client.list_boards()
            assert [b["id"] for b in page.items] == ["b1"]
            assert refreshes["count"] == 1
        finally:
            await client.close()

    _run(scenario())


def test_401_after_refresh_is_hard_failure() -> None:
    transport = MockPinterestTransport()
    transport.add_failure(401, "expired")
    transport.add_failure(401, "still expired")

    async def provider(force_refresh: bool = False) -> str:
        return "tok-new"

    async def scenario() -> None:
        client = PinterestApiClient(
            base_url="https://api.pinterest.test/v5",
            account_id=ACCOUNT,
            token_provider=provider,
            rate_limiter=PerAccountRateLimiter(read_per_minute=600, write_per_minute=200),
            timeout_seconds=5.0,
            max_retries=0,
            base_backoff_seconds=0.01,
            max_backoff_seconds=0.05,
            transport=transport,
        )
        try:
            try:
                await client.list_boards()
                raise AssertionError("expected PinterestApiException")
            except PinterestApiException as exc:
                assert exc.kind == RemoteErrorKind.UNAUTHORIZED
        finally:
            await client.close()

    _run(scenario())


def test_classify_http_error() -> None:
    assert classify_http_error(401) == RemoteErrorKind.UNAUTHORIZED
    assert classify_http_error(403) == RemoteErrorKind.FORBIDDEN
    assert classify_http_error(404) == RemoteErrorKind.NOT_FOUND
    assert classify_http_error(429) == RemoteErrorKind.RATE_LIMITED
    assert classify_http_error(500) == RemoteErrorKind.SERVER_ERROR
    assert classify_http_error(418) == RemoteErrorKind.VALIDATION
    assert classify_http_error(None) == RemoteErrorKind.NETWORK
