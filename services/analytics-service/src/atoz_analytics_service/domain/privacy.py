"""Privacy guard for the first-party collector (Task 18 §8).

The website is minimal-data by design (Database Blueprint §5.17 consent,
UI/UX design system §10): the collector rejects traits that would carry
personally-identifiable or credential material instead of storing it.
"""

from atoz_analytics_service.errors import ValidationError


def assert_no_sensitive_traits(traits: dict, *, sensitive_keys: list[str]) -> None:
    """Reject trait keys that would store PII or credentials."""
    lowered = {str(key).lower() for key in traits}
    for key in sensitive_keys:
        if key.lower() in lowered:
            raise ValidationError(f"Trait key '{key}' is not allowed (sensitive data exclusion).")
