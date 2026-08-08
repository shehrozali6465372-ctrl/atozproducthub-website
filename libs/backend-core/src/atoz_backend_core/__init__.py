"""AtozProductHub shared backend foundation (ADR-0003).

Infrastructure primitives only: configuration, logging, middleware, database
connections, repository patterns, events, workers, authentication, security,
and observability. No business logic and no AI behavior.
"""

from atoz_backend_core.version import __version__

__all__ = ["__version__"]
