"""MFA placeholders (Phase 5 wires real TOTP + enrollment flows).

M3 ships provisioning (secret + otpauth URI) and the verify interface;
verification itself is intentionally unimplemented until the auth milestone.
"""

import base64
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MfaProvision:
    subject: str
    secret: str
    otpauth_uri: str
    issuer: str


class MfaService:
    """TOTP placeholder: provisioning works; verification lands in Phase 5."""

    def __init__(self, issuer: str = "AtozProductHub") -> None:
        self._issuer = issuer

    def provision(self, subject: str) -> MfaProvision:
        secret = base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")
        uri = (
            f"otpauth://totp/{self._issuer}:{subject}"
            f"?secret={secret}&issuer={self._issuer}&algorithm=SHA1&digits=6&period=30"
        )
        return MfaProvision(subject=subject, secret=secret, otpauth_uri=uri, issuer=self._issuer)

    def verify(self, subject: str, secret: str, code: str) -> bool:
        """Placeholder — real TOTP verification ships with Phase 5."""
        raise NotImplementedError("TOTP verification lands in Phase 5 (Authentication).")
