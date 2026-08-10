"""OAuth domain tests: state/CSRF, PKCE, authorize URL, callback parsing."""

from urllib.parse import parse_qs, urlparse

from atoz_pinterest_service.domain import oauth

SECRET = "test-secret"


def test_state_roundtrip_binds_account() -> None:
    state = oauth.new_state(SECRET, "account-1")
    assert oauth.verify_state(SECRET, state) == "account-1"


def test_state_verification_rejects_forged_state() -> None:
    state = oauth.new_state(SECRET, "account-1")
    # Tamper with the account id while keeping the original signature.
    forged = f"account-2:{state.split(':', 2)[1]}:{state.split(':', 2)[2]}"
    assert oauth.verify_state(SECRET, forged) is None


def test_state_verification_rejects_wrong_secret() -> None:
    state = oauth.new_state(SECRET, "account-1")
    assert oauth.verify_state("other-secret", state) is None


def test_state_verification_rejects_malformed() -> None:
    assert oauth.verify_state(SECRET, "garbage") is None
    assert oauth.verify_state(SECRET, "") is None


def test_pkce_verifier_and_challenge() -> None:
    verifier = oauth.new_code_verifier()
    assert 43 <= len(verifier) <= 128
    challenge = oauth.code_challenge(verifier)
    assert len(challenge) == 43
    assert oauth.code_challenge(verifier) == challenge  # deterministic


def test_authorize_url_contains_minimal_scopes_and_pkce() -> None:
    verifier = oauth.new_code_verifier()
    url = oauth.build_authorize_url(
        authorize_url="https://www.pinterest.com/oauth/",
        client_id="cid",
        redirect_uri="http://localhost:8400/oauth/callback",
        state="state-1",
        code_challenge_value=oauth.code_challenge(verifier),
        scopes=["boards:read", "boards:write", "pins:read", "pins:write"],
    )
    assert url.startswith("https://www.pinterest.com/oauth/?")
    assert "client_id=cid" in url
    assert "response_type=code" in url
    assert "state=state-1" in url
    assert "code_challenge_method=S256" in url
    # Minimum required scopes only — never more (values are URL-encoded,
    # so compare the decoded scope parameter).
    scope = parse_qs(urlparse(url).query)["scope"][0]
    assert scope == "boards:read boards:write pins:read pins:write"


def test_parse_callback_params() -> None:
    code, state, error = oauth.parse_callback_params({"code": "c1", "state": "s1"})
    assert (code, state, error) == ("c1", "s1", None)

    code, state, error = oauth.parse_callback_params({"error": "access_denied", "state": "s1"})
    assert (code, state, error) == ("", "s1", "access_denied")


def test_parse_callback_params_rejects_missing_fields() -> None:
    import pytest

    with pytest.raises(ValueError):
        oauth.parse_callback_params({})
    with pytest.raises(ValueError):
        oauth.parse_callback_params({"code": "c1"})
