"""Commission status lifecycle (M5 scope).

Server-side state machine for ``revenue_transactions.status``:

    pending → approved → paid
    pending → rejected
    (rejected, paid are terminal)

Routes and services never inline transition logic; webhook ingestion maps
network statuses to pending/approved/rejected, and admin transitions move
approved → paid only through this module.
"""

from atoz_affiliate_service.domain.enums import CommissionStatus

TRANSITIONS: dict[CommissionStatus, set[CommissionStatus]] = {
    CommissionStatus.PENDING: {CommissionStatus.APPROVED, CommissionStatus.REJECTED},
    CommissionStatus.APPROVED: {CommissionStatus.PAID},
    CommissionStatus.REJECTED: set(),
    CommissionStatus.PAID: set(),
}


def can_transition(current: CommissionStatus, target: CommissionStatus) -> bool:
    """Whether ``current`` may move to ``target``."""
    return target in TRANSITIONS[current]


NETWORK_STATUS_TO_COMMISSION = {
    "pending": CommissionStatus.PENDING,
    "approved": CommissionStatus.APPROVED,
    "rejected": CommissionStatus.REJECTED,
    "paid": CommissionStatus.PAID,
}
