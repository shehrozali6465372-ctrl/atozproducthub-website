"""Pure aggregation tests: source derivation, bounce rate, distinct counts."""

from atoz_analytics_service.domain.entities import AnalyticsEventLedger
from atoz_analytics_service.services import aggregate_events, derive_traffic_source

from .fixtures import utc_dt


def _row(event_id: str, event_type: str, **overrides: object) -> AnalyticsEventLedger:
    base: dict = {
        "id": event_id,
        "event_id": event_id,
        "niche_id": "niche-1",
        "event_type": event_type,
        "source": "web",
        "traits_json": "{}",
        "occurred_at": utc_dt(2026, 8, 1, 12),
        "received_at": utc_dt(2026, 8, 1, 12),
    }
    base.update(overrides)
    return AnalyticsEventLedger(**base)


def test_derive_traffic_source_buckets() -> None:
    assert derive_traffic_source("https://www.pinterest.com/pin/1") == "pinterest"
    assert derive_traffic_source("https://www.google.com/search?q=x") == "google"
    assert derive_traffic_source("https://mail.google.com") == "email"
    assert derive_traffic_source(None) == "direct"
    assert derive_traffic_source("https://example.org") == "other"


def test_aggregation_counts_distinct_sessions_and_bounce() -> None:
    rows = [
        _row("a", "page_view", session_id="s1", user_pseudo_id="u1", referrer=None),
        _row(
            "b",
            "page_view",
            session_id="s1",
            user_pseudo_id="u1",
            referrer="https://www.pinterest.com",
        ),
        _row("c", "page_view", session_id="s2", user_pseudo_id="u2", referrer=None),
        _row("d", "session_start", session_id="s3", user_pseudo_id="u3", referrer=None),
    ]
    traffic, visitors, metrics = aggregate_events(rows)
    direct = traffic[("direct", None)]
    assert direct["pageviews"] == 2
    assert direct["sessions"] == 3  # s1 + s2 + s3 (session_start)
    assert direct["unique_visitors"] == 3
    pinterest = traffic[("pinterest", None)]
    assert pinterest["pageviews"] == 1
    # Bounce is global per session: s2 has exactly one page view -> bounced;
    # s1 has two page views across sources -> not bounced.
    assert direct["bounce_rate"] == round(1 / 3, 4)
    assert pinterest["bounce_rate"] == 0.0
    total_sessions = sum(t["sessions"] for t in traffic.values())
    assert total_sessions == 4
    assert metrics[("traffic.sessions", None)] == 4


def test_aggregation_isolation_by_account() -> None:
    account = "acct-a"
    rows = [
        _row("a", "pin_click", pinterest_account_id=account),
        _row("b", "pin_click", pinterest_account_id=account),
        _row("c", "pin_click", pinterest_account_id="acct-b"),
        _row("d", "affiliate_click", pinterest_account_id=None),
    ]
    _traffic, _visitors, metrics = aggregate_events(rows)
    assert metrics[("pinterest.pin_clicks", account)] == 2
    assert metrics[("pinterest.pin_clicks", "acct-b")] == 1
    assert metrics[("affiliate.clicks", None)] == 1
