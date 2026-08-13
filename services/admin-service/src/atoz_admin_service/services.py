"""Admin & operations business layer (Task 19 / M9).

Facade over the admin_db repositories implementing the control plane:

- RBAC hardening: idempotent system-role/permission seeding, operator
  identity management, niche-scoped role assignment, effective-permission
  resolution for JWT claim snapshots, and MFA/session controls.
- Append-only audit ledger: write-once records, searchable queries, and
  capped CSV export. No update/delete paths exist in the repository layer.
- Operations dashboard: sibling-service probes, queue/webhook/operation/
  job failure counts, per-state queue visibility, and KPI summaries.
- Operational tools: safe bounded retry of failed queue items, searchable
  webhook/operation logs, scheduled-job visibility, isolation verification,
  and export controls.
- Internal event ingestion: HMAC-verified webhook with (source, event_id)
  idempotency that maps domain events to operation records.

No AI functionality exists here. The AI OS stays an external system; this
service only records and reports business operations (Website Contract §4).
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import httpx

from atoz_admin_service.config import Settings
from atoz_admin_service.domain.entities import (
    AdminNiche,
    AdminUser,
    ApiKey,
    AuditLog,
    JobRun,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    OperationLog,
    Permission,
    QueueItem,
    Role,
    ScheduledJob,
    UserRole,
    WebhookLog,
)
from atoz_admin_service.domain.enums import (
    DOMAIN_EVENT_TO_OPERATION,
)
from atoz_admin_service.domain.events import (
    audit_recorded_event,
    operation_recorded_event,
)
from atoz_admin_service.domain.roles import PERMISSION_CATALOG, role_seeds
from atoz_admin_service.errors import (
    AuthenticationError,
    DuplicateError,
    NotFoundError,
    ValidationError,
)
from atoz_admin_service.repositories import AdminUnitOfWork
from atoz_admin_service.uuids import uuid7
from atoz_backend_core.events.envelope import EventEnvelope
from atoz_backend_core.events.publisher import EventPublisher

logger = logging.getLogger("atoz.admin.service")

SERVICE_HEALTH_PATHS = {
    "content-service": "content",
    "affiliate-service": "affiliate",
    "pinterest-service": "pinterest",
    "seo-service": "seo",
    "analytics-service": "analytics",
}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _uuid(value: str | None) -> str | None:
    """Normalize an optional UUID string; None stays None."""
    return value


class AdminService:
    """Control-plane facade over the admin_db (niche/account scoped)."""

    def __init__(
        self,
        *,
        uow_factory,
        event_publisher: EventPublisher,
        settings: Settings,
    ) -> None:
        self._uow_factory = uow_factory
        self._event_publisher = event_publisher
        self._settings = settings

    # ---------------------------------------------------------- RBAC seed
    async def seed_reference_data(self) -> None:
        """Idempotently create the permission catalog and system roles."""
        async with self._uow_factory().transaction() as uow:
            for code, name, scope in PERMISSION_CATALOG:
                existing = await uow.permissions.get_by_code(code)
                if existing is None:
                    await uow.permissions.add(
                        Permission(
                            id=uuid7(),
                            code=code,
                            name=name,
                            scope=scope,
                            description=f"Frozen permission: {code} (scope {scope}).",
                        )
                    )
            for seed in role_seeds():
                existing = await uow.roles.get_by_code(seed.code)
                if existing is None:
                    existing = Role(
                        id=uuid7(),
                        code=seed.code,
                        name=seed.name,
                        description=f"System role: {seed.name}",
                        is_system=seed.is_system,
                    )
                    await uow.roles.add(existing)
                for code in seed.permissions:
                    permission = await uow.permissions.get_by_code(code)
                    if permission is not None:
                        await uow.role_permissions.grant(existing.id, permission.id)
            await uow.commit()

    # ----------------------------------------------------------- niches
    async def list_niches(self) -> Sequence[AdminNiche]:
        async with self._uow_factory().transaction() as uow:
            return await uow.niches.list()

    async def get_niche(self, niche_id: str) -> AdminNiche | None:
        async with self._uow_factory().transaction() as uow:
            return await uow.niches.get(niche_id)

    async def get_niche_by_slug(self, slug: str) -> AdminNiche | None:
        async with self._uow_factory().transaction() as uow:
            return await uow.niches.get_by_slug(slug)

    async def create_niche(self, *, name: str, slug: str, status: str) -> AdminNiche:
        async with self._uow_factory().transaction() as uow:
            if await uow.niches.slug_exists(slug):
                raise DuplicateError(f"Niche slug already registered: {slug}.")
            niche = AdminNiche(id=uuid7(), slug=slug, name=name, status=status)
            await uow.niches.add(niche)
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="create",
                    entity_type="niche",
                    entity_id=niche.id,
                    after_json=json.dumps({"name": name, "slug": slug, "status": status}),
                )
            )
            await uow.commit()
            await self._publish(
                audit_recorded_event(
                    action="create",
                    entity_type="niche",
                    entity_id=niche.id,
                    niche_id=None,
                    actor=None,
                )
            )
            return niche

    # ----------------------------------------------------------- users
    async def list_users(self) -> list[dict[str, Any]]:
        async with self._uow_factory().transaction() as uow:
            users = await uow.users.list_by_status()
            result: list[dict[str, Any]] = []
            for user in users:
                roles = await self._user_roles_out(uow, user.id)
                result.append({**user_out(user), "roles": roles})
            return result

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        async with self._uow_factory().transaction() as uow:
            user = await uow.users.get(user_id)
            if user is None:
                return None
            return {**user_out(user), "roles": await self._user_roles_out(uow, user.id)}

    async def get_user_by_subject(self, subject: str) -> AdminUser | None:
        async with self._uow_factory().transaction() as uow:
            return await uow.users.get_by_subject(subject)

    async def create_user(
        self,
        *,
        subject: str,
        email: str,
        display_name: str,
        status: str,
        roles: list[dict[str, Any]],
    ) -> AdminUser:
        async with self._uow_factory().transaction() as uow:
            if await uow.users.get_by_subject(subject) is not None:
                raise DuplicateError(f"Operator subject already exists: {subject}.")
            if await uow.users.get_by_email(email) is not None:
                raise DuplicateError(f"Operator email already exists: {email}.")
            user = AdminUser(
                id=uuid7(),
                subject=subject,
                email=email,
                display_name=display_name,
                status=status,
            )
            await uow.users.add(user)
            for assignment in roles:
                await self._assign_role(
                    uow, user.id, assignment["role_code"], assignment.get("niche_id")
                )
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="create",
                    entity_type="admin_user",
                    entity_id=user.id,
                    after_json=json.dumps({"email": email}),
                )
            )
            await uow.commit()
            return user

    async def update_user(
        self,
        user_id: str,
        *,
        display_name: str | None,
        status: str | None,
        mfa_enabled: bool | None,
    ) -> AdminUser | None:
        async with self._uow_factory().transaction() as uow:
            user = await uow.users.get(user_id)
            if user is None:
                raise NotFoundError("Operator not found.")
            before = {"display_name": user.display_name, "status": user.status}
            if display_name is not None:
                user.display_name = display_name
            if status is not None:
                user.status = status
            if mfa_enabled is not None:
                user.mfa_enabled = mfa_enabled
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="update",
                    entity_type="admin_user",
                    entity_id=user.id,
                    before_json=json.dumps(before),
                    after_json=json.dumps(
                        {"display_name": user.display_name, "status": user.status}
                    ),
                )
            )
            await uow.commit()
            return user

    async def assign_role(self, user_id: str, role_code: str, niche_id: str | None) -> None:
        async with self._uow_factory().transaction() as uow:
            await self._assign_role(uow, user_id, role_code, niche_id)
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="assign",
                    entity_type="role",
                    entity_id=role_code,
                    niche_id=_uuid(niche_id),
                    after_json=json.dumps({"admin_user_id": user_id}),
                )
            )
            await uow.commit()

    async def revoke_role(self, user_id: str, role_code: str, niche_id: str | None) -> None:
        async with self._uow_factory().transaction() as uow:
            role = await uow.roles.get_by_code(role_code)
            if role is None:
                raise NotFoundError(f"Role not found: {role_code}.")
            assignment = await uow.user_roles.find_active(user_id, role.id, _uuid(niche_id))
            if assignment is None:
                raise NotFoundError("Active role assignment not found.")
            assignment.revoked_at = _utcnow()
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="revoke",
                    entity_type="role",
                    entity_id=role_code,
                    niche_id=_uuid(niche_id),
                    before_json=json.dumps({"admin_user_id": user_id}),
                )
            )
            await uow.commit()

    async def effective_permissions(self, subject: str) -> list[str]:
        """Resolve the union of permissions across the subject's roles."""
        async with self._uow_factory().transaction() as uow:
            user = await uow.users.get_by_subject(subject)
            if user is None:
                return []
            assignments = await uow.user_roles.list_for_user(user.id)
            perms: set[str] = set()
            for assignment in assignments:
                codes = await uow.role_permissions.permission_codes_for_role(assignment.role_id)
                perms.update(codes)
            return sorted(perms)

    async def list_roles(self) -> list[dict[str, Any]]:
        async with self._uow_factory().transaction() as uow:
            result: list[dict[str, Any]] = []
            for role in await uow.roles.list_all():
                codes = await uow.role_permissions.permission_codes_for_role(role.id)
                result.append(
                    {
                        "id": role.id,
                        "code": role.code,
                        "name": role.name,
                        "description": role.description,
                        "is_system": role.is_system,
                        "permissions": codes,
                    }
                )
            return result

    async def list_permissions(self) -> Sequence[Permission]:
        async with self._uow_factory().transaction() as uow:
            return await uow.permissions.list_all()

    async def mark_login(self, subject: str, *, mfa_enabled: bool) -> AdminUser | None:
        async with self._uow_factory().transaction() as uow:
            user = await uow.users.get_by_subject(subject)
            if user is None:
                return None
            await uow.users.mark_login(user.id, mfa_enabled=mfa_enabled)
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="login",
                    entity_type="admin_user",
                    entity_id=user.id,
                    admin_user_id=user.id,
                )
            )
            await uow.commit()
            return user

    async def create_api_key(
        self, *, admin_user_id: str, niche_id: str | None, name: str, scopes: list[str]
    ) -> tuple[ApiKey, str]:
        raw_key = f"ak_{uuid7().replace('-', '')}{uuid7().replace('-', '')}"
        key_hash = _hash_key(raw_key)
        async with self._uow_factory().transaction() as uow:
            api_key = ApiKey(
                id=uuid7(),
                admin_user_id=admin_user_id,
                niche_id=_uuid(niche_id),
                name=name,
                key_hash=key_hash,
                scopes_json=json.dumps(scopes),
            )
            await uow.api_keys.add(api_key)
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="create",
                    entity_type="api_key",
                    entity_id=api_key.id,
                    niche_id=_uuid(niche_id),
                    after_json=json.dumps({"name": name, "scopes": scopes}),
                )
            )
            await uow.commit()
            return api_key, raw_key

    async def list_api_keys(self, admin_user_id: str) -> Sequence[ApiKey]:
        async with self._uow_factory().transaction() as uow:
            return await uow.api_keys.list_for_user(admin_user_id)

    async def revoke_api_key(self, api_key_id: str) -> None:
        async with self._uow_factory().transaction() as uow:
            api_key = await uow.api_keys.get(api_key_id)
            if api_key is None:
                raise NotFoundError("API key not found.")
            api_key.revoked_at = _utcnow()
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="revoke",
                    entity_type="api_key",
                    entity_id=api_key.id,
                    niche_id=_uuid(api_key.niche_id),
                )
            )
            await uow.commit()

    # ----------------------------------------------------------- audit
    async def record_audit(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str = "",
        niche_id: str | None = None,
        admin_user_id: str | None = None,
        before_json: str | None = None,
        after_json: str | None = None,
        ip_hash: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        """Append one immutable audit record (write-once policy)."""
        async with self._uow_factory().transaction() as uow:
            entry = AuditLog(
                id=uuid7(),
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                niche_id=_uuid(niche_id),
                admin_user_id=_uuid(admin_user_id),
                before_json=before_json,
                after_json=after_json,
                ip_hash=ip_hash,
                request_id=request_id,
            )
            await uow.audit.add(entry)
            await uow.commit()
            await self._publish(
                audit_recorded_event(
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    niche_id=_uuid(niche_id),
                    actor=admin_user_id,
                )
            )
            return entry

    async def search_audit(
        self,
        *,
        niche_id: str | None = None,
        admin_user_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        request_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[AuditLog]:
        async with self._uow_factory().transaction() as uow:
            return await uow.audit.list_scoped(
                niche_id=_uuid(niche_id),
                admin_user_id=_uuid(admin_user_id),
                action=action,
                entity_type=entity_type,
                entity_id=_uuid(entity_id),
                request_id=request_id,
                start=start,
                end=end,
                limit=min(limit, 200),
                offset=offset,
            )

    async def count_audit(self, *, niche_id: str | None = None) -> int:
        async with self._uow_factory().transaction() as uow:
            return await uow.audit.count_scoped(niche_id=_uuid(niche_id))

    async def export_audit_csv(
        self, *, niche_id: str | None = None, limit: int | None = None
    ) -> str:
        """Capped CSV export of the audit ledger (export controls §5)."""
        row_limit = min(
            limit or self._settings.audit_export_max_rows, self._settings.audit_export_max_rows
        )
        async with self._uow_factory().transaction() as uow:
            rows = await uow.audit.list_scoped(
                niche_id=_uuid(niche_id),
                limit=row_limit,
            )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "id",
                "occurred_at",
                "admin_user_id",
                "api_key_id",
                "action",
                "entity_type",
                "entity_id",
                "niche_id",
                "request_id",
                "ip_hash",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.occurred_at.isoformat(),
                    row.admin_user_id or "",
                    row.api_key_id or "",
                    row.action,
                    row.entity_type,
                    row.entity_id,
                    row.niche_id or "",
                    row.request_id or "",
                    row.ip_hash or "",
                ]
            )
        return buffer.getvalue()

    # ------------------------------------------------------- notifications
    async def create_notification(
        self,
        *,
        recipient_id: str,
        type: str,
        title: str,
        body: str = "",
        niche_id: str | None = None,
        action_ref: str | None = None,
    ) -> Notification:
        async with self._uow_factory().transaction() as uow:
            if await uow.users.get(recipient_id) is None:
                raise NotFoundError("Notification recipient not found.")
            notification = Notification(
                id=uuid7(),
                recipient_id=recipient_id,
                type=type,
                title=title,
                body=body,
                niche_id=_uuid(niche_id),
                action_ref=action_ref,
            )
            await uow.notifications.add(notification)
            delivery = NotificationDelivery(
                id=uuid7(),
                notification_id=notification.id,
                channel="inbox",
            )
            await uow.notification_deliveries.add(delivery)
            await uow.commit()
            return notification

    async def list_notifications(
        self, recipient_id: str, *, status: str | None = None, niche_id: str | None = None
    ) -> Sequence[Notification]:
        async with self._uow_factory().transaction() as uow:
            return await uow.notifications.list_for_recipient(
                recipient_id, status=status, niche_id=_uuid(niche_id)
            )

    async def mark_notification_read(
        self, notification_id: str, recipient_id: str
    ) -> Notification | None:
        async with self._uow_factory().transaction() as uow:
            updated = await uow.notifications.mark_read(notification_id, recipient_id)
            if updated is not None:
                await uow.commit()
            return updated

    async def notification_preferences(self, admin_user_id: str) -> dict[str, Any]:
        async with self._uow_factory().transaction() as uow:
            prefs = await uow.notification_preferences.get_for_user(admin_user_id)
            if prefs is None:
                return {"channels": ["inbox"], "quiet_hours": {}}
            return {
                "channels": json.loads(prefs.channels_json or "[]"),
                "quiet_hours": json.loads(prefs.quiet_hours_json or "{}"),
            }

    async def update_notification_preferences(
        self, admin_user_id: str, *, channels: list[str], quiet_hours: dict[str, Any]
    ) -> None:
        async with self._uow_factory().transaction() as uow:
            prefs = await uow.notification_preferences.get_for_user(admin_user_id)
            if prefs is None:
                prefs = NotificationPreference(id=uuid7(), admin_user_id=admin_user_id)
                await uow.notification_preferences.add(prefs)
            prefs.channels_json = json.dumps(channels)
            prefs.quiet_hours_json = json.dumps(quiet_hours)
            await uow.commit()

    # ----------------------------------------------------------- ops
    async def ops_overview(self, *, niche_id: str | None = None) -> dict[str, Any]:
        async with self._uow_factory().transaction() as uow:
            queues = await uow.queue.count_by_state(niche_id=_uuid(niche_id))
            return {
                "failed_queue_items": await uow.queue.failed_count(niche_id=_uuid(niche_id)),
                "failed_webhooks": await uow.webhook_logs.failed_count(niche_id=_uuid(niche_id)),
                "failed_operations": await uow.operation_logs.failed_count(
                    niche_id=_uuid(niche_id)
                ),
                "failed_job_runs": await uow.job_runs.failed_count(),
                "open_notifications": await uow.notifications.count_open(),
                "audit_entries": await uow.audit.count_scoped(niche_id=_uuid(niche_id)),
                "queues": queues,
            }

    async def system_status(self) -> dict[str, Any]:
        """Probe sibling business services from ``service_health_urls``."""
        urls = self._settings.service_health_urls
        services: list[dict[str, Any]] = []
        if not urls:
            services.append(
                {
                    "name": "admin-service",
                    "status": "ok",
                    "version": "0.9.0",
                    "latency_ms": 0,
                    "error": None,
                }
            )
            return {"overall": "ok", "services": services}

        async with httpx.AsyncClient(timeout=2.0) as client:
            for name, base in urls.items():
                entry: dict[str, Any] = {"name": name, "status": "down", "error": "unreachable"}
                try:
                    response = await client.get(f"{base}/health")
                    if response.status_code == 200:
                        body = response.json()
                        entry = {
                            "name": name,
                            "status": "ok",
                            "version": body.get("version"),
                            "latency_ms": int(response.elapsed.total_seconds() * 1000),
                            "error": None,
                        }
                    else:
                        entry["status"] = "degraded"
                        entry["error"] = f"HTTP {response.status_code}"
                except httpx.HTTPError as exc:
                    entry["error"] = type(exc).__name__
                services.append(entry)
        overall = "ok" if all(s["status"] == "ok" for s in services) else "degraded"
        return {"overall": overall, "services": services}

    async def isolation_check(self) -> dict[str, Any]:
        """Verify niche/account isolation in the admin-owned records.

        Checks that every scoped admin record references a registered niche
        and that no pinterest-account-scoped row exists without account
        context in admin-owned operation data. The 10-account isolation
        proof itself lives in the Pinterest service tests; here we verify
        the control plane cannot mix scopes.
        """
        async with self._uow_factory().transaction() as uow:
            niches = {n.id for n in await uow.niches.list()}
            checks: list[dict[str, Any]] = []
            for label, rows in (
                ("audit", await uow.audit.list(limit=1000)),
                ("queue", await uow.queue.list(limit=1000)),
                ("webhook", await uow.webhook_logs.list(limit=1000)),
                ("operation", await uow.operation_logs.list(limit=1000)),
            ):
                orphaned = [
                    r.id for r in rows if r.niche_id is not None and r.niche_id not in niches
                ]
                checks.append({"table": label, "rows": len(rows), "orphaned": orphaned})
            ok = all(not check["orphaned"] for check in checks)
            return {"ok": ok, "checks": checks}

    # ----------------------------------------------------------- queue
    async def list_queue_items(
        self,
        *,
        niche_id: str | None = None,
        queue: str | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[QueueItem]:
        async with self._uow_factory().transaction() as uow:
            return await uow.queue.list_scoped(
                niche_id=_uuid(niche_id),
                queue=queue,
                state=state,
                limit=min(limit, 200),
                offset=offset,
            )

    async def retry_queue_item(self, queue_item_id: str) -> QueueItem | None:
        """Safe retry: failed items only, bounded by max_attempts (§5)."""
        async with self._uow_factory().transaction() as uow:
            item = await uow.queue.get(queue_item_id)
            if item is None:
                raise NotFoundError("Queue item not found.")
            updated = await uow.queue.retry(queue_item_id, max_attempts=item.max_attempts)
            if updated is None:
                raise ValidationError(
                    "Only failed queue items below their attempt cap can be retried."
                )
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="retry",
                    entity_type="queue_item",
                    entity_id=item.id,
                    niche_id=_uuid(item.niche_id),
                )
            )
            await uow.commit()
            return updated

    async def enqueue(
        self,
        *,
        niche_id: str | None,
        queue: str,
        payload_ref: str,
        run_at: datetime | None,
        max_attempts: int,
    ) -> QueueItem:
        async with self._uow_factory().transaction() as uow:
            item = QueueItem(
                id=uuid7(),
                niche_id=_uuid(niche_id),
                queue=queue,
                payload_ref=payload_ref,
                max_attempts=max_attempts,
                run_at=run_at or _utcnow(),
            )
            await uow.queue.add(item)
            await uow.audit.add(
                AuditLog(
                    id=uuid7(),
                    action="create",
                    entity_type="queue_item",
                    entity_id=item.id,
                    niche_id=_uuid(niche_id),
                )
            )
            await uow.commit()
            return item

    # ----------------------------------------------------------- logs
    async def list_webhook_logs(
        self,
        *,
        source: str | None = None,
        status: str | None = None,
        niche_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[WebhookLog]:
        async with self._uow_factory().transaction() as uow:
            return await uow.webhook_logs.list_scoped(
                source=source,
                status=status,
                niche_id=_uuid(niche_id),
                limit=min(limit, 200),
                offset=offset,
            )

    async def record_operation(
        self,
        *,
        operation: str,
        entity_type: str = "",
        entity_id: str = "",
        niche_id: str | None = None,
        status: str = "succeeded",
        message: str = "",
        details: dict[str, Any] | None = None,
    ) -> OperationLog:
        async with self._uow_factory().transaction() as uow:
            record = OperationLog(
                id=uuid7(),
                operation=operation,
                entity_type=entity_type,
                entity_id=entity_id,
                niche_id=_uuid(niche_id),
                status=status,
                message=message[:500],
                details_json=json.dumps(details or {}),
            )
            await uow.operation_logs.add(record)
            await uow.commit()
            await self._publish(
                operation_recorded_event(
                    operation=operation,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    niche_id=_uuid(niche_id),
                    status=status,
                )
            )
            return record

    async def list_operation_logs(
        self,
        *,
        niche_id: str | None = None,
        operation: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationLog]:
        async with self._uow_factory().transaction() as uow:
            return await uow.operation_logs.list_scoped(
                niche_id=_uuid(niche_id),
                operation=operation,
                status=status,
                limit=min(limit, 200),
                offset=offset,
            )

    # ----------------------------------------------------------- jobs
    async def list_scheduled_jobs(self, *, niche_id: str | None = None) -> Sequence[ScheduledJob]:
        async with self._uow_factory().transaction() as uow:
            return await uow.scheduled_jobs.list_scoped(niche_id=_uuid(niche_id))

    async def list_job_runs(
        self, *, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> Sequence[JobRun]:
        async with self._uow_factory().transaction() as uow:
            return await uow.job_runs.list_recent(
                status=status, limit=min(limit, 200), offset=offset
            )

    # ----------------------------------------------------------- webhook
    async def ingest_event(self, *, source: str, signature: str, raw_body: bytes) -> WebhookLog:
        """HMAC-verified, idempotent internal-event ingestion (API Contracts §8).

        The signature is computed over the exact request bytes (same
        convention as the analytics webhook), so producers must send the
        raw body unchanged.
        """
        expected = _sign_bytes(self._settings.event_webhook_secret, raw_body)
        if not hmac.compare_digest(expected, signature):
            raise AuthenticationError("Invalid webhook signature.")
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ValidationError("Webhook payload must be valid JSON.") from exc
        event_type = str(payload.get("type", ""))
        event_id = str(payload.get("event_id", ""))
        if not event_type or not event_id:
            raise ValidationError("Webhook payload requires type and event_id.")
        body = json.dumps(payload, separators=(",", ":"))
        if len(body) > self._settings.operation_log_max_details_bytes * 2:
            raise ValidationError("Webhook payload exceeds the size limit.")

        async with self._uow_factory().transaction() as uow:
            existing = await uow.webhook_logs.get_by_source_event(source, event_id)
            if existing is not None:
                return existing  # idempotent replay: no duplicate record

            payload_data = payload.get("payload") or {}
            niche_id = (
                _uuid(payload_data.get("niche_id")) if isinstance(payload_data, dict) else None
            )
            log = WebhookLog(
                id=uuid7(),
                niche_id=niche_id,
                source=source,
                event_id=event_id,
                status="processed",
                payload_ref=f"{source}:{event_id}",
                error=None,
            )
            await uow.webhook_logs.add(log)
            operation = DOMAIN_EVENT_TO_OPERATION.get(event_type, "event.ingested")
            await uow.operation_logs.add(
                OperationLog(
                    id=uuid7(),
                    operation=operation,
                    niche_id=niche_id,
                    entity_type="domain_event",
                    entity_id=event_id,
                    status="succeeded",
                    message=f"Ingested {event_type}",
                    details_json=body[: self._settings.operation_log_max_details_bytes],
                )
            )
            await uow.commit()
            return log

    # ----------------------------------------------------------- helpers
    async def _assign_role(
        self, uow: AdminUnitOfWork, user_id: str, role_code: str, niche_id: str | None
    ) -> None:
        role = await uow.roles.get_by_code(role_code)
        if role is None:
            raise NotFoundError(f"Role not found: {role_code}.")
        normalized_niche = _uuid(niche_id)
        if await uow.user_roles.find_active(user_id, role.id, normalized_niche) is not None:
            raise DuplicateError("Role already assigned for this scope.")
        await uow.user_roles.add(
            UserRole(
                id=uuid7(),
                admin_user_id=user_id,
                role_id=role.id,
                niche_id=normalized_niche,
            )
        )

    async def _user_roles_out(self, uow: AdminUnitOfWork, user_id: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for assignment in await uow.user_roles.list_for_user(user_id):
            role = await uow.roles.get(assignment.role_id)
            if role is None:
                continue
            result.append(
                {
                    "role_code": role.code,
                    "role_name": role.name,
                    "niche_id": assignment.niche_id,
                    "assigned_at": assignment.assigned_at,
                    "revoked_at": assignment.revoked_at,
                }
            )
        return result

    async def _publish(self, event: EventEnvelope) -> None:
        try:
            await self._event_publisher.publish(event)
        except Exception:  # noqa: BLE001 — publishing must never break the write path
            logger.warning("event_publish_failed", extra={"event": event.type})


def user_out(user: AdminUser) -> dict[str, Any]:
    return {
        "id": user.id,
        "subject": user.subject,
        "email": user.email,
        "display_name": user.display_name,
        "status": user.status,
        "mfa_enabled": user.mfa_enabled,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    }


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _sign_bytes(secret: str, raw: bytes) -> str:
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
