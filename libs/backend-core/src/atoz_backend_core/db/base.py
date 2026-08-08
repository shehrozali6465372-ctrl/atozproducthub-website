"""ORM base and metadata (per-service models build on this in Phase 4+)."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all business-service models."""
