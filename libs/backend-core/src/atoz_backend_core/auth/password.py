"""Password hashing (Argon2 via pwdlib)."""

from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password with Argon2id (pwdlib recommended settings)."""
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its stored hash."""
    return _password_hash.verify(password, hashed)
