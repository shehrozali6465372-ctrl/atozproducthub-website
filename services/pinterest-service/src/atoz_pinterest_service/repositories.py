"""Repository layer for the Pinterest module.

Extends ``atoz_backend_core.repositories`` and enforces the Database
Blueprint §4 mandatory rules: every account-scoped query is scoped by BOTH
``niche_id`` and ``pinterest_account_id`` — an account-scoped query without
account context is impossible by construction, so Account A can never read
or mutate Account B's data (Task 16 rule).

``pinterest_pins`` is an append-only ledger: add/list/state-update only,
never row deletion.
"""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select

from atoz_backend_core.repositories import SqlAlchemyRepository, SqlAlchemyUnitOfWork
from atoz_pinterest_service.domain.entities import (
    BoardSection,
    PinPublishAttempt,
    PinQueueItem,
    PinterestAccount,
    PinterestAnalytics,
    PinterestBoard,
    PinterestNiche,
    PinterestPin,
    PinterestToken,
)
from atoz_pinterest_service.errors import AccountIsolationError


def _utcnow() -> datetime:
    return datetime.now(UTC)


class PinterestNicheRepository(SqlAlchemyRepository[PinterestNiche, str]):
    """Local tenant-registry mirror (ADR-0006) — the Pinterest tenancy root."""

    model = PinterestNiche

    async def get_by_slug(self, slug: str) -> PinterestNiche | None:
        result = await self._session.scalars(
            select(PinterestNiche).where(PinterestNiche.slug == slug)
        )
        return result.first()

    async def slug_exists(self, slug: str, *, exclude_id: str | None = None) -> bool:
        stmt = select(PinterestNiche.id).where(PinterestNiche.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(PinterestNiche.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_status(self, status: str | None = None) -> Sequence[PinterestNiche]:
        stmt = select(PinterestNiche).order_by(PinterestNiche.name)
        if status is not None:
            stmt = stmt.where(PinterestNiche.status == status)
        return (await self._session.scalars(stmt)).all()


class PinterestAccountRepository(SqlAlchemyRepository[PinterestAccount, str]):
    """Accounts are the root of Pinterest isolation (niche-scoped)."""

    model = PinterestAccount

    async def get_scoped(self, account_id: str, *, niche_id: str) -> PinterestAccount | None:
        if not account_id or not niche_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinterestAccount).where(
                PinterestAccount.id == account_id, PinterestAccount.niche_id == niche_id
            )
        )
        return result.first()

    async def get_by_name(self, name: str, *, niche_id: str) -> PinterestAccount | None:
        result = await self._session.scalars(
            select(PinterestAccount).where(
                PinterestAccount.name == name, PinterestAccount.niche_id == niche_id
            )
        )
        return result.first()

    async def name_exists(self, name: str, *, niche_id: str, exclude_id: str | None = None) -> bool:
        stmt = select(PinterestAccount.id).where(
            PinterestAccount.name == name, PinterestAccount.niche_id == niche_id
        )
        if exclude_id is not None:
            stmt = stmt.where(PinterestAccount.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_niche(self, niche_id: str) -> Sequence[PinterestAccount]:
        result = await self._session.scalars(
            select(PinterestAccount)
            .where(PinterestAccount.niche_id == niche_id)
            .order_by(PinterestAccount.name)
        )
        return result.all()

    async def list_connected(self) -> Sequence[PinterestAccount]:
        result = await self._session.scalars(
            select(PinterestAccount)
            .where(PinterestAccount.status.in_(["connected", "error"]))
            .order_by(PinterestAccount.name)
        )
        return result.all()


class PinterestTokenRepository(SqlAlchemyRepository[PinterestToken, str]):
    """One token record per account; VALUES live in Vault (blueprint §5.2)."""

    model = PinterestToken

    async def get_for_account(self, account_id: str, *, niche_id: str) -> PinterestToken | None:
        if not account_id or not niche_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinterestToken).where(
                PinterestToken.pinterest_account_id == account_id,
                PinterestToken.niche_id == niche_id,
            )
        )
        return result.first()


class PinterestBoardRepository(SqlAlchemyRepository[PinterestBoard, str]):
    """Boards are account-scoped (blueprint §5.3)."""

    model = PinterestBoard

    async def get_scoped(
        self, board_id: str, *, niche_id: str, account_id: str
    ) -> PinterestBoard | None:
        if not board_id or not niche_id or not account_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinterestBoard).where(
                PinterestBoard.id == board_id,
                PinterestBoard.niche_id == niche_id,
                PinterestBoard.pinterest_account_id == account_id,
            )
        )
        return result.first()

    async def get_by_remote(
        self, remote_board_id: str, *, niche_id: str, account_id: str
    ) -> PinterestBoard | None:
        if not remote_board_id or not niche_id or not account_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinterestBoard).where(
                PinterestBoard.remote_board_id == remote_board_id,
                PinterestBoard.niche_id == niche_id,
                PinterestBoard.pinterest_account_id == account_id,
            )
        )
        return result.first()

    async def list_by_account(
        self, account_id: str, *, niche_id: str, status: str | None = None
    ) -> Sequence[PinterestBoard]:
        if not account_id or not niche_id:
            raise AccountIsolationError()
        stmt = (
            select(PinterestBoard)
            .where(
                PinterestBoard.pinterest_account_id == account_id,
                PinterestBoard.niche_id == niche_id,
            )
            .order_by(PinterestBoard.name)
        )
        if status is not None:
            stmt = stmt.where(PinterestBoard.status == status)
        return (await self._session.scalars(stmt)).all()


class BoardSectionRepository(SqlAlchemyRepository[BoardSection, str]):
    """Board sections are account-scoped (blueprint §5.3 extension)."""

    model = BoardSection

    async def get_scoped(
        self, section_id: str, *, niche_id: str, account_id: str
    ) -> BoardSection | None:
        if not section_id or not niche_id or not account_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(BoardSection).where(
                BoardSection.id == section_id,
                BoardSection.niche_id == niche_id,
                BoardSection.pinterest_account_id == account_id,
            )
        )
        return result.first()

    async def list_by_board(
        self, board_id: str, *, niche_id: str, account_id: str
    ) -> Sequence[BoardSection]:
        if not board_id or not niche_id or not account_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(BoardSection)
            .where(
                BoardSection.pinterest_board_id == board_id,
                BoardSection.niche_id == niche_id,
                BoardSection.pinterest_account_id == account_id,
            )
            .order_by(BoardSection.name)
        )
        return result.all()


class PinterestPinRepository(SqlAlchemyRepository[PinterestPin, str]):
    """Append-only pin ledger (blueprint §5.4) — no delete path."""

    model = PinterestPin

    async def get_scoped(
        self, pin_id: str, *, niche_id: str, account_id: str
    ) -> PinterestPin | None:
        if not pin_id or not niche_id or not account_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinterestPin).where(
                PinterestPin.id == pin_id,
                PinterestPin.niche_id == niche_id,
                PinterestPin.pinterest_account_id == account_id,
            )
        )
        return result.first()

    async def checksum_exists(self, checksum: str, *, niche_id: str, account_id: str) -> bool:
        if not checksum or not niche_id or not account_id:
            raise AccountIsolationError()
        stmt = select(PinterestPin.id).where(
            PinterestPin.checksum == checksum,
            PinterestPin.niche_id == niche_id,
            PinterestPin.pinterest_account_id == account_id,
        )
        return (await self._session.scalars(stmt)).first() is not None

    async def list_by_account(
        self,
        account_id: str,
        *,
        niche_id: str,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[PinterestPin]:
        if not account_id or not niche_id:
            raise AccountIsolationError()
        stmt = (
            select(PinterestPin)
            .where(
                PinterestPin.pinterest_account_id == account_id,
                PinterestPin.niche_id == niche_id,
            )
            .order_by(PinterestPin.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            stmt = stmt.where(PinterestPin.status == status)
        return (await self._session.scalars(stmt)).all()

    async def count_by_account_status(self, account_id: str, *, niche_id: str, status: str) -> int:
        if not account_id or not niche_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(func.count())
            .select_from(PinterestPin)
            .where(
                PinterestPin.pinterest_account_id == account_id,
                PinterestPin.niche_id == niche_id,
                PinterestPin.status == status,
            )
        )
        return int(result.one())


class PinQueueRepository(SqlAlchemyRepository[PinQueueItem, str]):
    """Durable pin queue (blueprint §5.4)."""

    model = PinQueueItem

    async def get_scoped(
        self, item_id: str, *, niche_id: str, account_id: str
    ) -> PinQueueItem | None:
        if not item_id or not niche_id or not account_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinQueueItem).where(
                PinQueueItem.id == item_id,
                PinQueueItem.niche_id == niche_id,
                PinQueueItem.pinterest_account_id == account_id,
            )
        )
        return result.first()

    async def get_by_pin(
        self, pin_id: str, *, niche_id: str, account_id: str
    ) -> PinQueueItem | None:
        if not pin_id or not niche_id or not account_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinQueueItem).where(
                PinQueueItem.pinterest_pin_id == pin_id,
                PinQueueItem.niche_id == niche_id,
                PinQueueItem.pinterest_account_id == account_id,
            )
        )
        return result.first()

    async def list_by_account(
        self, account_id: str, *, niche_id: str, state: str | None = None, limit: int = 100
    ) -> Sequence[PinQueueItem]:
        if not account_id or not niche_id:
            raise AccountIsolationError()
        stmt = (
            select(PinQueueItem)
            .where(
                PinQueueItem.pinterest_account_id == account_id,
                PinQueueItem.niche_id == niche_id,
            )
            .order_by(PinQueueItem.run_at)
            .limit(limit)
        )
        if state is not None:
            stmt = stmt.where(PinQueueItem.state == state)
        return (await self._session.scalars(stmt)).all()

    async def claim_due(self, *, limit: int, batch_size: int = 10) -> Sequence[PinQueueItem]:
        """Claim due queue items for a worker run (across accounts)."""
        now = _utcnow()
        result = await self._session.scalars(
            select(PinQueueItem)
            .where(
                PinQueueItem.state == "queued",
                PinQueueItem.run_at <= now,
            )
            .order_by(PinQueueItem.run_at)
            .limit(min(limit, batch_size))
        )
        items = result.all()
        for item in items:
            item.state = "claimed"
        return items


class PinPublishAttemptRepository(SqlAlchemyRepository[PinPublishAttempt, str]):
    """Complete publish attempt records — append-only."""

    model = PinPublishAttempt

    async def list_by_pin(
        self, pin_id: str, *, niche_id: str, account_id: str
    ) -> Sequence[PinPublishAttempt]:
        if not pin_id or not niche_id or not account_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinPublishAttempt)
            .where(
                PinPublishAttempt.pinterest_pin_id == pin_id,
                PinPublishAttempt.niche_id == niche_id,
                PinPublishAttempt.pinterest_account_id == account_id,
            )
            .order_by(PinPublishAttempt.attempt_no)
        )
        return result.all()


class PinterestAnalyticsRepository(SqlAlchemyRepository[PinterestAnalytics, str]):
    """Per-account daily Pinterest metrics — business data only."""

    model = PinterestAnalytics

    async def get_for_date(
        self, account_id: str, *, niche_id: str, metric_date: str
    ) -> PinterestAnalytics | None:
        if not account_id or not niche_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinterestAnalytics).where(
                PinterestAnalytics.pinterest_account_id == account_id,
                PinterestAnalytics.niche_id == niche_id,
                PinterestAnalytics.metric_date == metric_date,
            )
        )
        return result.first()

    async def list_by_account(
        self, account_id: str, *, niche_id: str, limit: int = 30
    ) -> Sequence[PinterestAnalytics]:
        if not account_id or not niche_id:
            raise AccountIsolationError()
        result = await self._session.scalars(
            select(PinterestAnalytics)
            .where(
                PinterestAnalytics.pinterest_account_id == account_id,
                PinterestAnalytics.niche_id == niche_id,
            )
            .order_by(PinterestAnalytics.metric_date.desc())
            .limit(limit)
        )
        return result.all()


class PinterestUnitOfWork(SqlAlchemyUnitOfWork):
    """Typed unit of work for the Pinterest module."""

    @classmethod
    def build(cls, session_factory) -> "PinterestUnitOfWork":
        return cls(
            session_factory,
            repositories={
                "niches": PinterestNicheRepository,
                "accounts": PinterestAccountRepository,
                "tokens": PinterestTokenRepository,
                "boards": PinterestBoardRepository,
                "sections": BoardSectionRepository,
                "pins": PinterestPinRepository,
                "queue": PinQueueRepository,
                "attempts": PinPublishAttemptRepository,
                "analytics": PinterestAnalyticsRepository,
            },
        )
