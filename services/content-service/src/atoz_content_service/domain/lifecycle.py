"""Server-side article lifecycle state machine (M4 requirement).

Statuses: draft → review → published → archived (plus unpublished for the
blueprint's withdrawal flow and restore back to draft).

Rules are enforced here — routes and services never inline transition
logic, so the state machine is testable in isolation and identical across
every entry point.
"""

from atoz_content_service.domain.enums import ArticleStatus

# action -> {(from_status): to_status}
TRANSITIONS: dict[str, dict[ArticleStatus, ArticleStatus]] = {
    "submit": {ArticleStatus.DRAFT: ArticleStatus.REVIEW},
    "approve": {ArticleStatus.REVIEW: ArticleStatus.PUBLISHED},
    "reject": {ArticleStatus.REVIEW: ArticleStatus.DRAFT},
    "publish": {
        ArticleStatus.DRAFT: ArticleStatus.PUBLISHED,
        ArticleStatus.UNPUBLISHED: ArticleStatus.PUBLISHED,
        # Re-publish: applies the latest draft version to the published
        # snapshot (ADR-0004 immutable-snapshot flow).
        ArticleStatus.PUBLISHED: ArticleStatus.PUBLISHED,
    },
    "unpublish": {
        ArticleStatus.PUBLISHED: ArticleStatus.UNPUBLISHED,
    },
    "archive": {
        ArticleStatus.PUBLISHED: ArticleStatus.ARCHIVED,
        ArticleStatus.UNPUBLISHED: ArticleStatus.ARCHIVED,
    },
    "restore": {ArticleStatus.ARCHIVED: ArticleStatus.DRAFT},
}


def can_transition(current: ArticleStatus, action: str) -> bool:
    """Whether ``action`` is legal from ``current``."""
    targets = TRANSITIONS.get(action)
    return targets is not None and current in targets


def transition(current: ArticleStatus, action: str) -> ArticleStatus:
    """Return the target status or raise ``ValueError`` with a clear message."""
    targets = TRANSITIONS.get(action)
    if targets is None:
        raise ValueError(f"Unknown lifecycle action {action!r}.")
    target = targets.get(current)
    if target is None:
        raise ValueError(
            f"Invalid lifecycle action {action!r} for article status {current.value!r}."
        )
    return target
