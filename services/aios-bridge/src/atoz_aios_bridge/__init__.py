"""AI OS Bridge — the ONLY AI OS contact point in the business layer.

Transport only: request validation, contract validation, retry with
exponential backoff, timeout, heartbeat, and authentication. No prompts,
no models, no generation, no learning, no memory — ever (Website
Architecture Contract §4.2).

All AI OS traffic uses the frozen contracts in ``libs/contracts/aios/``.
"""

__version__ = "0.3.0"
