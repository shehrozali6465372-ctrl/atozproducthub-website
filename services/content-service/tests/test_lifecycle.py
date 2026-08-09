"""Lifecycle state-machine tests (server-side validation rules)."""

import pytest

from atoz_content_service.domain.enums import ArticleStatus
from atoz_content_service.domain.lifecycle import TRANSITIONS, can_transition, transition


def test_full_lifecycle_path() -> None:
    assert can_transition(ArticleStatus.DRAFT, "submit")
    assert transition(ArticleStatus.DRAFT, "submit") == ArticleStatus.REVIEW
    assert can_transition(ArticleStatus.REVIEW, "approve")
    assert transition(ArticleStatus.REVIEW, "approve") == ArticleStatus.PUBLISHED
    assert can_transition(ArticleStatus.PUBLISHED, "unpublish")
    assert transition(ArticleStatus.PUBLISHED, "unpublish") == ArticleStatus.UNPUBLISHED
    assert can_transition(ArticleStatus.UNPUBLISHED, "publish")
    assert transition(ArticleStatus.UNPUBLISHED, "publish") == ArticleStatus.PUBLISHED
    assert can_transition(ArticleStatus.PUBLISHED, "archive")
    assert transition(ArticleStatus.PUBLISHED, "archive") == ArticleStatus.ARCHIVED
    assert can_transition(ArticleStatus.ARCHIVED, "restore")
    assert transition(ArticleStatus.ARCHIVED, "restore") == ArticleStatus.DRAFT


def test_reject_sends_review_back_to_draft() -> None:
    assert transition(ArticleStatus.REVIEW, "reject") == ArticleStatus.DRAFT


def test_republish_applies_from_published() -> None:
    assert transition(ArticleStatus.PUBLISHED, "publish") == ArticleStatus.PUBLISHED


def test_invalid_transitions_raise() -> None:
    with pytest.raises(ValueError, match="Invalid lifecycle action"):
        transition(ArticleStatus.DRAFT, "approve")
    with pytest.raises(ValueError, match="Invalid lifecycle action"):
        transition(ArticleStatus.REVIEW, "unpublish")
    with pytest.raises(ValueError, match="Invalid lifecycle action"):
        transition(ArticleStatus.ARCHIVED, "submit")
    with pytest.raises(ValueError, match="Unknown lifecycle action"):
        transition(ArticleStatus.DRAFT, "explode")


def test_every_transition_is_defined() -> None:
    statuses = set(ArticleStatus)
    for targets in TRANSITIONS.values():
        assert targets  # no empty maps
        assert set(targets.values()) <= statuses
        assert set(targets.keys()) <= statuses
