"""RBAC: roles, permissions, and FastAPI dependencies.

Infrastructure only — concrete roles/permissions for business modules are
registered by services (Phase 5+). M3 ships the mechanism and tests.
"""

from dataclasses import dataclass
from typing import Protocol

from fastapi import Depends, HTTPException, Request, status


class AuthContext(Protocol):
    subject: str
    permissions: tuple[str, ...]
    session_id: str


@dataclass(frozen=True)
class Role:
    name: str
    permissions: frozenset[str] = frozenset()


class RoleRegistry:
    """Named role → permission set (in-memory; persisted in Phase 5)."""

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}

    def register(self, role: Role) -> None:
        self._roles[role.name] = role

    def permissions_for(self, role_names: list[str] | tuple[str, ...]) -> frozenset[str]:
        perms: set[str] = set()
        for name in role_names:
            role = self._roles.get(name)
            if role:
                perms.update(role.permissions)
        return frozenset(perms)


def get_auth_context(request: Request) -> AuthContext:
    """Resolve the authenticated context attached by the gateway middleware."""
    context = getattr(request.state, "auth", None)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return context


def require_permissions(*required: str):
    """FastAPI dependency: require all listed permissions."""

    def dependency(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
        missing = [perm for perm in required if perm not in context.permissions]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return context

    return dependency
