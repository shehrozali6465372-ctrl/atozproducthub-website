"""Pinterest module enumerations (string constants, portable across DBs).

Lifecycle values follow Database Blueprint §5.2–5.4 and the M6 scope:
accounts are per-niche, pins move draft → queued → publishing → published
(with failed/cancelled states), and every account-scoped record carries
``pinterest_account_id`` for strict isolation.
"""

from enum import StrEnum


class AccountStatus(StrEnum):
    """Pinterest account registration lifecycle."""

    DRAFT = "draft"
    PENDING_OAUTH = "pending_oauth"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class TokenStatus(StrEnum):
    """OAuth token record lifecycle (token VALUES live in Vault)."""

    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ROTATED = "rotated"


class BoardSyncState(StrEnum):
    """Board ↔ Pinterest sync state."""

    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    ERROR = "error"


class BoardStatus(StrEnum):
    """Board availability lifecycle."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class PinStatus(StrEnum):
    """Pin ledger lifecycle (blueprint §5.4 append-only ledger)."""

    DRAFT = "draft"
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"
    CANCELLED = "cancelled"


class QueueState(StrEnum):
    """pin_queue_items durable state machine (blueprint §5.4)."""

    QUEUED = "queued"
    CLAIMED = "claimed"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PublishAttemptStatus(StrEnum):
    """Complete publishing attempt record states."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYABLE = "retryable"
    CANCELLED = "cancelled"


class RemoteErrorKind(StrEnum):
    """Classified Pinterest API error kinds for retry decisions."""

    UNAUTHORIZED = "unauthorized"  # 401 — token expired/revoked
    FORBIDDEN = "forbidden"  # 403 — scope/permission
    RATE_LIMITED = "rate_limited"  # 429 — per-category budget
    SERVER_ERROR = "server_error"  # 5xx — retryable
    NETWORK = "network"  # transport — retryable
    NOT_FOUND = "not_found"  # 404 — pin/board missing
    VALIDATION = "validation"  # 4xx other — non-retryable
