"""Signed link-token tests (server-controlled redirect identifiers)."""

from atoz_affiliate_service.domain.tokens import (
    new_signed_token,
    token_from_signed,
    validate_signed_token,
)

SECRET = "unit-test-token-secret"


def test_new_signed_token_shape() -> None:
    signed = new_signed_token(secret=SECRET)
    assert "." in signed
    raw, signature = signed.rsplit(".", 1)
    assert raw and signature
    assert len(signature) == 32  # HMAC-SHA256 truncated hex


def test_validate_accepts_own_token() -> None:
    signed = new_signed_token(secret=SECRET)
    assert validate_signed_token(signed, secret=SECRET) == token_from_signed(signed)


def test_validate_rejects_tampered_token() -> None:
    signed = new_signed_token(secret=SECRET)
    raw = token_from_signed(signed)
    assert validate_signed_token(f"{raw}x.invalid", secret=SECRET) is None
    assert validate_signed_token(f"{raw}.ffffffffffffffffffffffffffffffff", secret=SECRET) is None


def test_validate_rejects_wrong_secret() -> None:
    signed = new_signed_token(secret=SECRET)
    assert validate_signed_token(signed, secret="other-secret") is None


def test_validate_rejects_malformed() -> None:
    assert validate_signed_token("no-dot-here", secret=SECRET) is None
    assert validate_signed_token("", secret=SECRET) is None
    assert validate_signed_token(".only-signature", secret=SECRET) is None
    assert validate_signed_token("raw.", secret=SECRET) is None


def test_tokens_are_unique() -> None:
    tokens = {new_signed_token(secret=SECRET) for _ in range(200)}
    assert len(tokens) == 200
