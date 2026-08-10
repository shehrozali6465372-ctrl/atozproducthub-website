"""PinterestService business tests: OAuth connect, refresh, boards, pins,
queue publishing, retry/failure, analytics, and cross-account isolation.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

from atoz_pinterest_service.domain import oauth
from atoz_pinterest_service.errors import DuplicateError, NotFoundError, OAuthError

from .fixtures import (
    MockPinterestTransport,
    build_repositories,
    make_settings,
    scenario,
)


async def _connected_account(service, transport, *, niche_id: str, name: str = "hub"):
    account = await service.create_account(niche_id=niche_id, name=name)
    authorize_url = await service.start_connect(account.id, niche_id=niche_id)
    assert "pinterest.com/oauth/" in authorize_url
    state = parse_qs(urlparse(authorize_url).query)["state"][0]
    assert oauth.verify_state(make_settings().oauth_state_secret, state) == account.id
    return await service.complete_connect(query_params={"code": "auth-code-1", "state": state})


def test_oauth_connect_flow_with_mock_token_exchange() -> None:
    async def runner() -> None:
        _session_factory, service = await build_repositories(transport=MockPinterestTransport())
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, MockPinterestTransport(), niche_id=niche.id)
        assert account.status == "connected"
        assert account.remote_user_id == "u-1"
        assert account.username == "mock-user"
        # Token record exists with a vault ref; no token value in the DB.
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            token = await unit.tokens.get_for_account(account.id, niche_id=niche.id)
            assert token is not None
            assert token.vault_ref.startswith("vault://pinterest/accounts/")
            assert token.status == "active"
            assert "access_token" not in str(token.vault_ref)

    scenario(runner)


def test_oauth_callback_rejects_forged_state() -> None:
    async def runner() -> None:
        _session_factory, service = await build_repositories()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await service.create_account(niche_id=niche.id, name="hub")
        await service.start_connect(account.id, niche_id=niche.id)
        try:
            await service.complete_connect(
                query_params={"code": "c", "state": oauth.new_state("wrong-secret", account.id)}
            )
            raise AssertionError("expected OAuthError")
        except OAuthError:
            pass

    scenario(runner)


def test_oauth_callback_rejects_denied() -> None:
    async def runner() -> None:
        _session_factory, service = await build_repositories()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await service.create_account(niche_id=niche.id, name="hub")
        state = oauth.new_state(make_settings().oauth_state_secret, account.id)
        try:
            await service.complete_connect(query_params={"error": "access_denied", "state": state})
            raise AssertionError("expected OAuthError")
        except OAuthError:
            pass

    scenario(runner)


def test_disconnect_revokes_token() -> None:
    async def runner() -> None:
        _session_factory, service = await build_repositories(transport=MockPinterestTransport())
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, MockPinterestTransport(), niche_id=niche.id)
        disconnected = await service.disconnect_account(account.id, niche_id=niche.id)
        assert disconnected.status == "disconnected"
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            token = await unit.tokens.get_for_account(account.id, niche_id=niche.id)
            assert token.status == "revoked"
            assert token.revoked_at is not None

    scenario(runner)


def test_token_refresh_when_expired() -> None:
    async def runner() -> None:
        transport = MockPinterestTransport()
        _session_factory, service = await build_repositories(transport=transport)
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, transport, niche_id=niche.id)
        # Force the vault payload to be expired, then resolve a token.
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            token = await unit.tokens.get_for_account(account.id, niche_id=niche.id)
            vault_ref = token.vault_ref
        await service._vault.write(  # noqa: SLF001
            vault_ref,
            {
                "access_token": "expired-token",
                "refresh_token": "mock-refresh-token",
                "expires_in": "3600",
                "expires_at": str((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
            },
        )
        provider = await service._token_provider_for(account)  # noqa: SLF001
        token_value = await provider()
        assert token_value == "mock-access-token"  # refreshed via mock endpoint
        # The token record's expiry was updated.
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            token = await unit.tokens.get_for_account(account.id, niche_id=niche.id)
            assert token.rotated_at is not None
            # SQLite returns naive datetimes; compare in the same tz domain.
            assert token.access_expires_at > datetime.now(UTC).replace(tzinfo=None)

    scenario(runner)


def test_sync_boards_and_publish_pin_lifecycle() -> None:
    async def runner() -> None:
        transport = MockPinterestTransport()
        transport.boards = [{"id": "b-remote-1", "name": "Kitchen Buys", "description": "Guides"}]
        _session_factory, service = await build_repositories(transport=transport)
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, transport, niche_id=niche.id)

        boards = await service.sync_boards(account.id, niche_id=niche.id)
        assert len(boards) == 1
        board = boards[0]
        assert board.remote_board_id == "b-remote-1"
        assert board.sync_state == "synced"

        pin = await service.create_pin_draft(
            niche_id=niche.id,
            account_id=account.id,
            board_id=board.id,
            title="Kitchen gadgets worth buying",
            destination_url="https://atozproducthub.dev/landing/kitchen-buys",
            media_ref="https://media.example/kitchen.jpg",
            description="Our honest 2026 list",
        )
        assert pin.status == "draft"

        item = await service.enqueue_pin(pin.id, niche_id=niche.id, account_id=account.id)
        assert item.state == "queued"
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            stored = await unit.pins.get_scoped(pin.id, niche_id=niche.id, account_id=account.id)
            assert stored.status == "queued"

        outcomes = await service.publish_due()
        assert outcomes == [{"pin_id": pin.id, "status": "published", "remote_pin_id": "p-1"}]

        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            stored = await unit.pins.get_scoped(pin.id, niche_id=niche.id, account_id=account.id)
            assert stored.status == "published"
            assert stored.remote_pin_id == "p-1"
            assert stored.published_at is not None
            queue = await unit.queue.get_by_pin(pin.id, niche_id=niche.id, account_id=account.id)
            assert queue.state == "done"
            attempts = await unit.attempts.list_by_pin(
                pin.id, niche_id=niche.id, account_id=account.id
            )
            assert len(attempts) == 1
            assert attempts[0].status == "success"
            assert attempts[0].remote_pin_id == "p-1"

    scenario(runner)


def test_publish_retryable_failure_keeps_queue_for_later() -> None:
    async def runner() -> None:
        transport = MockPinterestTransport()
        transport.boards = [{"id": "b-1", "name": "Buys"}]
        _session_factory, service = await build_repositories(transport=transport)
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, transport, niche_id=niche.id)
        boards = await service.sync_boards(account.id, niche_id=niche.id)
        pin = await service.create_pin_draft(
            niche_id=niche.id,
            account_id=account.id,
            board_id=boards[0].id,
            title="Retry me",
            destination_url="https://atozproducthub.dev/x",
            media_ref="https://media.example/x.jpg",
        )
        await service.enqueue_pin(pin.id, niche_id=niche.id, account_id=account.id)
        # Exhaust the client's internal 429 retries so the failure surfaces
        # to the service as a retryable publish outcome.
        for _ in range(3):
            transport.add_failure(429, "rate limited")
        outcomes = await service.publish_due()
        assert outcomes[0]["status"] == "retryable"
        # Pin stays publishing; queue item reset to queued for a later run.
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            stored = await unit.pins.get_scoped(pin.id, niche_id=niche.id, account_id=account.id)
            assert stored.status == "publishing"
            queue = await unit.queue.get_by_pin(pin.id, niche_id=niche.id, account_id=account.id)
            assert queue.state == "queued"
            assert queue.attempts == 1
            attempts = await unit.attempts.list_by_pin(
                pin.id, niche_id=niche.id, account_id=account.id
            )
            assert attempts[0].status == "retryable"
            assert attempts[0].error_kind == "rate_limited"

    scenario(runner)


def test_publish_permanent_failure_marks_failed() -> None:
    async def runner() -> None:
        transport = MockPinterestTransport()
        transport.boards = [{"id": "b-1", "name": "Buys"}]
        _session_factory, service = await build_repositories(transport=transport)
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, transport, niche_id=niche.id)
        boards = await service.sync_boards(account.id, niche_id=niche.id)
        pin = await service.create_pin_draft(
            niche_id=niche.id,
            account_id=account.id,
            board_id=boards[0].id,
            title="Fail me",
            destination_url="https://atozproducthub.dev/f",
            media_ref="https://media.example/f.jpg",
        )
        await service.enqueue_pin(pin.id, niche_id=niche.id, account_id=account.id)
        transport.add_failure(403, "forbidden")
        outcomes = await service.publish_due()
        assert outcomes[0]["status"] == "failed"
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            stored = await unit.pins.get_scoped(pin.id, niche_id=niche.id, account_id=account.id)
            assert stored.status == "failed"
            queue = await unit.queue.get_by_pin(pin.id, niche_id=niche.id, account_id=account.id)
            assert queue.state == "failed"
            attempts = await unit.attempts.list_by_pin(
                pin.id, niche_id=niche.id, account_id=account.id
            )
            assert attempts[0].status == "failed"
            assert attempts[0].error_kind == "forbidden"

    scenario(runner)


def test_cancel_queued_pin() -> None:
    async def runner() -> None:
        _session_factory, service = await build_repositories(transport=MockPinterestTransport())
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, MockPinterestTransport(), niche_id=niche.id)
        board = await service.create_board(niche_id=niche.id, account_id=account.id, name="Buys")
        pin = await service.create_pin_draft(
            niche_id=niche.id,
            account_id=account.id,
            board_id=board.id,
            title="Cancel me",
            destination_url="https://atozproducthub.dev/c",
            media_ref="https://media.example/c.jpg",
        )
        await service.enqueue_pin(pin.id, niche_id=niche.id, account_id=account.id)
        cancelled = await service.cancel_pin(pin.id, niche_id=niche.id, account_id=account.id)
        assert cancelled.status == "cancelled"
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            queue = await unit.queue.get_by_pin(pin.id, niche_id=niche.id, account_id=account.id)
            assert queue.state == "cancelled"

    scenario(runner)


def test_duplicate_enqueue_rejected() -> None:
    async def runner() -> None:
        _session_factory, service = await build_repositories(transport=MockPinterestTransport())
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, MockPinterestTransport(), niche_id=niche.id)
        board = await service.create_board(niche_id=niche.id, account_id=account.id, name="Buys")
        pin = await service.create_pin_draft(
            niche_id=niche.id,
            account_id=account.id,
            board_id=board.id,
            title="Once",
            destination_url="https://atozproducthub.dev/o",
            media_ref="https://media.example/o.jpg",
        )
        await service.enqueue_pin(pin.id, niche_id=niche.id, account_id=account.id)
        try:
            await service.enqueue_pin(pin.id, niche_id=niche.id, account_id=account.id)
            raise AssertionError("expected DuplicateError")
        except DuplicateError:
            pass

    scenario(runner)


def test_cross_account_isolation_in_publish() -> None:
    async def runner() -> None:
        transport = MockPinterestTransport()
        transport.boards = [{"id": "b-1", "name": "Buys"}]
        _session_factory, service = await build_repositories(transport=transport)
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account_a = await _connected_account(service, transport, niche_id=niche.id, name="hub-a")
        account_b = await service.create_account(niche_id=niche.id, name="hub-b")

        # Account B has no boards and cannot touch A's board.
        assert await service.list_boards(account_b.id, niche_id=niche.id) == []
        board_a = (await service.sync_boards(account_a.id, niche_id=niche.id))[0]
        assert (
            await service.get_board(board_a.id, niche_id=niche.id, account_id=account_b.id) is None
        )

        # Creating a pin under B with A's board id fails.
        try:
            await service.create_pin_draft(
                niche_id=niche.id,
                account_id=account_b.id,
                board_id=board_a.id,
                title="Cross account",
                destination_url="https://atozproducthub.dev/x",
                media_ref="https://media.example/x.jpg",
            )
            raise AssertionError("expected NotFoundError")
        except NotFoundError:
            pass

        # Mutations on A's pin from B are impossible.
        pin = await service.create_pin_draft(
            niche_id=niche.id,
            account_id=account_a.id,
            board_id=board_a.id,
            title="A pin",
            destination_url="https://atozproducthub.dev/a",
            media_ref="https://media.example/a.jpg",
        )
        try:
            await service.enqueue_pin(pin.id, niche_id=niche.id, account_id=account_b.id)
            raise AssertionError("expected NotFoundError")
        except NotFoundError:
            pass

    scenario(runner)


def test_analytics_upsert_is_account_scoped() -> None:
    async def runner() -> None:
        _session_factory, service = await build_repositories(transport=MockPinterestTransport())
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, MockPinterestTransport(), niche_id=niche.id)
        row = await service.upsert_analytics(
            niche_id=niche.id,
            account_id=account.id,
            metric_date="2026-08-10",
            impressions=1200,
            saves=340,
            clicks=90,
            outbound_clicks=25,
            engagement=180,
        )
        assert row.impressions == 1200
        rows = await service.list_analytics(account.id, niche_id=niche.id)
        assert len(rows) == 1
        # Upsert updates the same row (unique account+date).
        await service.upsert_analytics(
            niche_id=niche.id, account_id=account.id, metric_date="2026-08-10", impressions=1300
        )
        rows = await service.list_analytics(account.id, niche_id=niche.id)
        assert len(rows) == 1
        assert rows[0].impressions == 1300

    scenario(runner)


def test_delete_account_disconnects_softly() -> None:
    async def runner() -> None:
        transport = MockPinterestTransport()
        _session_factory, service = await build_repositories(transport=transport)
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, transport, niche_id=niche.id)
        await service.delete_account(account.id, niche_id=niche.id)
        stored = await service.get_account(account.id, niche_id=niche.id)
        assert stored.status == "disconnected"
        async with service._uow_factory().transaction() as unit:  # noqa: SLF001
            token = await unit.tokens.get_for_account(account.id, niche_id=niche.id)
            assert token.status == "revoked"

    scenario(runner)


def test_account_status_summary() -> None:
    async def runner() -> None:
        transport = MockPinterestTransport()
        _session_factory, service = await build_repositories(transport=transport)
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        account = await _connected_account(service, transport, niche_id=niche.id)
        summary = await service.account_status(account.id, niche_id=niche.id)
        assert summary["name"] == "hub"
        assert summary["status"] == "connected"
        assert summary["token_status"] == "active"
        assert summary["board_count"] == 0
        assert summary["pin_counts"]["published"] == 0

    scenario(runner)
