"""AI OS adapters: transport signing and verification.

Only message authentication — never content intelligence.
"""

from atoz_aios_bridge.adapters.signing import AiosSigner, verify_signature

__all__ = ["AiosSigner", "verify_signature"]
