"""Repository isolation tests: 10 accounts, composite uniqueness, no leakage.

The Database Blueprint mandates that an account-scoped query without account
context is impossible. These tests exercise the repository layer directly
with 10 simulated accounts across multiple niches.
"""

from .fixtures import MockPinterestTransport, build_repositories, connect_account, scenario


def _account_ids(accounts) -> set[str]:
    return {a.id for a in accounts}


def test_ten_accounts_coexist_without_leakage() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        # One niche with 10 accounts.
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        for index in range(10):
            await service.create_account(
                niche_id=niche.id, name=f"kitchenhub-{index}", username=f"user-{index}"
            )
        accounts = await service.list_accounts(niche.id)
        assert len(accounts) == 10
        assert len(_account_ids(accounts)) == 10

        # Each account sees only its own data.
        for account in accounts:
            boards = await service.list_boards(account.id, niche_id=niche.id)
            assert boards == []
            pins = await service.list_pins(account.id, niche_id=niche.id)
            assert pins == []

        # A second niche's accounts are invisible to the first niche.
        niche2 = await service.create_niche(name="Travel", slug="travel", status="active")
        travel_account = await service.create_account(niche_id=niche2.id, name="travelpicks")
        assert await service.get_account(travel_account.id, niche_id=niche.id) is None
        assert _account_ids(await service.list_accounts(niche.id)) == _account_ids(accounts)

    scenario(runner)


def test_account_name_unique_per_niche() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        await service.create_account(niche_id=niche.id, name="kitchenhub")
        try:
            await service.create_account(niche_id=niche.id, name="kitchenhub")
            raise AssertionError("expected duplicate error")
        except Exception as exc:
            assert "already exists" in str(exc)

    scenario(runner)


def test_same_name_allowed_in_different_niches() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories()
        n1 = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        n2 = await service.create_niche(name="Travel", slug="travel", status="active")
        a1 = await service.create_account(niche_id=n1.id, name="hub")
        a2 = await service.create_account(niche_id=n2.id, name="hub")
        assert a1.id != a2.id

    scenario(runner)


def test_account_scoped_query_requires_context() -> None:
    from atoz_pinterest_service.errors import AccountIsolationError
    from atoz_pinterest_service.repositories import PinterestAccountRepository

    async def runner() -> None:
        session_factory, _service = await build_repositories()

        async with session_factory() as session:
            repo = PinterestAccountRepository(session)
            try:
                await repo.get_scoped("", niche_id="")
                raise AssertionError("expected AccountIsolationError")
            except AccountIsolationError:
                pass

    scenario(runner)


def test_board_unique_remote_id_per_account() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories(transport=MockPinterestTransport())
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        a1 = await connect_account(service, niche_id=niche.id, name="hub-a")
        a2 = await connect_account(service, niche_id=niche.id, name="hub-b")
        # Same remote board id on two different accounts is legal.
        b1 = await service.create_board(niche_id=niche.id, account_id=a1.id, name="Kitchen Buys")
        b2 = await service.create_board(niche_id=niche.id, account_id=a2.id, name="Kitchen Buys")
        assert b1.remote_board_id != b2.remote_board_id
        assert [b.id for b in await service.list_boards(a1.id, niche_id=niche.id)] == [b1.id]
        assert [b.id for b in await service.list_boards(a2.id, niche_id=niche.id)] == [b2.id]
        # Cross-account reads are impossible.
        assert await service.get_board(b1.id, niche_id=niche.id, account_id=a2.id) is None

    scenario(runner)


def test_pin_checksum_dedupe_per_account() -> None:
    async def runner() -> None:
        session_factory, service = await build_repositories(transport=MockPinterestTransport())
        niche = await service.create_niche(name="Kitchen", slug="kitchen", status="active")
        a1 = await connect_account(service, niche_id=niche.id, name="hub-a")
        a2 = await connect_account(service, niche_id=niche.id, name="hub-b")
        board = await service.create_board(niche_id=niche.id, account_id=a1.id, name="Buys")
        board2 = await service.create_board(niche_id=niche.id, account_id=a2.id, name="Buys")
        await service.create_pin_draft(
            niche_id=niche.id,
            account_id=a1.id,
            board_id=board.id,
            title="Same content",
            destination_url="https://atozproducthub.dev/guide",
            media_ref="https://media.example/a.jpg",
        )
        # Same content on the SAME account is rejected (duplicate).
        try:
            await service.create_pin_draft(
                niche_id=niche.id,
                account_id=a1.id,
                board_id=board.id,
                title="Same content",
                destination_url="https://atozproducthub.dev/guide",
                media_ref="https://media.example/a.jpg",
            )
            raise AssertionError("expected duplicate error")
        except Exception as exc:
            assert "already exists" in str(exc)
        # Same content on a DIFFERENT account is allowed.
        pin2 = await service.create_pin_draft(
            niche_id=niche.id,
            account_id=a2.id,
            board_id=board2.id,
            title="Same content",
            destination_url="https://atozproducthub.dev/guide",
            media_ref="https://media.example/a.jpg",
        )
        assert pin2.status == "draft"

    scenario(runner)
