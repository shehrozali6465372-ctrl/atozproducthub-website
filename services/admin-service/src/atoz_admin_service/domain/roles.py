"""Frozen RBAC catalog (Task 19 §1): permission codes + system role matrix.

Permission codes match the JWT ``perms`` claims enforced by every business
service (content:read/write, affiliate:read/write, pinterest:read/write,
seo:read/write, analytics:read/write, admin:read/write, automation:read/
write). The matrix is idempotently seeded into ``admin_db`` on startup so
system roles always exist; role membership is managed by operators.
"""

from dataclasses import dataclass

# (code, name, scope) — global/niche/account (Database Blueprint §5.19).
PERMISSION_CATALOG: tuple[tuple[str, str, str], ...] = (
    ("content:read", "Read content (articles, categories, tags)", "niche"),
    ("content:write", "Create/update/publish content", "niche"),
    ("affiliate:read", "Read affiliate catalog and revenue", "niche"),
    ("affiliate:write", "Manage affiliate catalog, links, reconciliation", "niche"),
    ("pinterest:read", "Read Pinterest accounts, boards, pins", "account"),
    ("pinterest:write", "Manage Pinterest accounts, boards, pin queue", "account"),
    ("seo:read", "Read SEO metadata, sitemaps, search", "niche"),
    ("seo:write", "Apply SEO metadata, rebuild sitemaps", "niche"),
    ("analytics:read", "Read analytics read models", "niche"),
    ("analytics:write", "Run analytics rollups", "niche"),
    ("admin:read", "Read admin/ops surfaces (audit, queues, users)", "global"),
    ("admin:write", "Manage operators, roles, settings, retries", "global"),
    ("automation:read", "Read automation rules and runs", "niche"),
    ("automation:write", "Manage automation rules and schedules", "niche"),
)

_ROLE_DEFS: dict[str, tuple[str, tuple[str, ...]]] = {
    "super_admin": (
        "Super Administrator",
        tuple(code for code, _name, _scope in PERMISSION_CATALOG),
    ),
    "admin": (
        "Administrator",
        (
            "content:read",
            "content:write",
            "affiliate:read",
            "affiliate:write",
            "pinterest:read",
            "pinterest:write",
            "seo:read",
            "seo:write",
            "analytics:read",
            "analytics:write",
            "admin:read",
            "admin:write",
            "automation:read",
            "automation:write",
        ),
    ),
    "editor": (
        "Content Editor",
        ("content:read", "content:write", "seo:read", "seo:write", "analytics:read"),
    ),
    "viewer": (
        "Read-only Viewer",
        (
            "content:read",
            "affiliate:read",
            "pinterest:read",
            "seo:read",
            "analytics:read",
            "admin:read",
            "automation:read",
        ),
    ),
    "pinterest_operator": (
        "Pinterest Operator",
        ("pinterest:read", "pinterest:write", "analytics:read"),
    ),
    "finance": (
        "Finance",
        ("affiliate:read", "affiliate:write", "analytics:read", "admin:read"),
    ),
}


@dataclass(frozen=True)
class RoleSeed:
    code: str
    name: str
    permissions: tuple[str, ...]
    is_system: bool = True


def role_seeds() -> tuple[RoleSeed, ...]:
    """System roles with their frozen permission sets."""
    return tuple(
        RoleSeed(code=code, name=name, permissions=perms, is_system=True)
        for code, (name, perms) in _ROLE_DEFS.items()
    )
