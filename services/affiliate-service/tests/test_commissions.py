"""Commission lifecycle state machine tests (blueprint §5.13)."""

from atoz_affiliate_service.domain.commissions import NETWORK_STATUS_TO_COMMISSION, can_transition
from atoz_affiliate_service.domain.enums import CommissionStatus


def test_pending_transitions() -> None:
    assert can_transition(CommissionStatus.PENDING, CommissionStatus.APPROVED)
    assert can_transition(CommissionStatus.PENDING, CommissionStatus.REJECTED)
    assert not can_transition(CommissionStatus.PENDING, CommissionStatus.PAID)


def test_approved_transitions() -> None:
    assert can_transition(CommissionStatus.APPROVED, CommissionStatus.PAID)
    assert not can_transition(CommissionStatus.APPROVED, CommissionStatus.REJECTED)
    assert not can_transition(CommissionStatus.APPROVED, CommissionStatus.APPROVED)


def test_terminal_states() -> None:
    for state in (CommissionStatus.REJECTED, CommissionStatus.PAID):
        for target in CommissionStatus:
            assert not can_transition(state, target)


def test_network_status_map() -> None:
    assert NETWORK_STATUS_TO_COMMISSION["approved"] is CommissionStatus.APPROVED
    assert NETWORK_STATUS_TO_COMMISSION["rejected"] is CommissionStatus.REJECTED
    assert NETWORK_STATUS_TO_COMMISSION["paid"] is CommissionStatus.PAID
