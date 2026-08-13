"""Repository layer for the admin module.

Every repository extends ``atoz_backend_core.repositories``. Scoped
repositories enforce Database Blueprint §4 tenancy server-side; the audit
ledger is append-only (no update/delete paths are exposed); the queue
ledger exposes explicit state transitions only.
"""

from collections.abc import Sequence

from sqlalchemy import func, select

from atoz_admin_service.domain.entities import (
    AdminNiche,
    AdminPreference,
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
    RolePermission,
    ScheduledJob,
    UserRole,
    WebhookLog,
)
from atoz_backend_core.repositories import SqlAlchemyRepository, SqlAlchemyUnitOfWork


class AdminNicheRepository(SqlAlchemyRepository[AdminNiche, str]):
    """Niches are a tenant-registry mirror — not niche-scoped themselves."""

    model = AdminNiche

    async def get_by_slug(self, slug: str) -> AdminNiche | None:
        result = await self._session.scalars(select(AdminNiche).where(AdminNiche.slug == slug))
        return result.first()

    async def slug_exists(self, slug: str, *, exclude_id: str | None = None) -> bool:
        stmt = select(AdminNiche.id).where(AdminNiche.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(AdminNiche.id != exclude_id)
        return (await self._session.scalars(stmt)).first() is not None


class AdminUserRepository(SqlAlchemyRepository[AdminUser, str]):
    """Operator identities; email/subject are globally unique."""

    model = AdminUser

    async def get_by_subject(self, subject: str) -> AdminUser | None:
        result = await self._session.scalars(select(AdminUser).where(AdminUser.subject == subject))
        return result.first()

    async def get_by_email(self, email: str) -> AdminUser | None:
        result = await self._session.scalars(select(AdminUser).where(AdminUser.email == email))
        return result.first()

    async def list_by_status(self, status: str | None = None) -> Sequence[AdminUser]:
        stmt = select(AdminUser).order_by(AdminUser.display_name)
        if status is not None:
            stmt = stmt.where(AdminUser.status == status)
        return (await self._session.scalars(stmt)).all()

    async def mark_login(self, user_id: str, *, mfa_enabled: bool) -> None:
        row = await self._session.get(AdminUser, user_id)
        if row is not None:
            from datetime import UTC, datetime

            row.last_login_at = datetime.now(UTC)
            row.mfa_enabled = mfa_enabled


class RoleRepository(SqlAlchemyRepository[Role, str]):
    """Global reference; roles are system-seeded and operator-managed."""

    model = Role

    async def get_by_code(self, code: str) -> Role | None:
        result = await self._session.scalars(select(Role).where(Role.code == code))
        return result.first()

    async def list_all(self) -> Sequence[Role]:
        return (await self._session.scalars(select(Role).order_by(Role.code))).all()


class PermissionRepository(SqlAlchemyRepository[Permission, str]):
    """Global reference; catalog is frozen by the domain module."""

    model = Permission

    async def get_by_code(self, code: str) -> Permission | None:
        result = await self._session.scalars(select(Permission).where(Permission.code == code))
        return result.first()

    async def list_all(self) -> Sequence[Permission]:
        return (await self._session.scalars(select(Permission).order_by(Permission.code))).all()


class RolePermissionRepository(SqlAlchemyRepository[RolePermission, str]):
    """Grants; idempotent on (role_id, permission_id)."""

    model = RolePermission

    async def permission_codes_for_role(self, role_id: str) -> list[str]:
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
            .order_by(Permission.code)
        )
        return list((await self._session.scalars(stmt)).all())

    async def grant(self, role_id: str, permission_id: str) -> None:
        exists = await self._session.scalars(
            select(RolePermission.id).where(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
            )
        )
        if exists.first() is None:
            from atoz_admin_service.uuids import uuid7

            self._session.add(
                RolePermission(id=uuid7(), role_id=role_id, permission_id=permission_id)
            )


class UserRoleRepository(SqlAlchemyRepository[UserRole, str]):
    """Role assignments; unique per (user, role, niche)."""

    model = UserRole

    async def list_for_user(
        self, admin_user_id: str, *, active_only: bool = True
    ) -> Sequence[UserRole]:
        stmt = select(UserRole).where(UserRole.admin_user_id == admin_user_id)
        if active_only:
            stmt = stmt.where(UserRole.revoked_at.is_(None))
        return (await self._session.scalars(stmt.order_by(UserRole.assigned_at))).all()

    async def find_active(
        self, admin_user_id: str, role_id: str, niche_id: str | None
    ) -> UserRole | None:
        stmt = select(UserRole).where(
            UserRole.admin_user_id == admin_user_id,
            UserRole.role_id == role_id,
            UserRole.niche_id == niche_id,
            UserRole.revoked_at.is_(None),
        )
        return (await self._session.scalars(stmt)).first()

    async def revoke_all_for_user(self, admin_user_id: str) -> None:
        from datetime import UTC, datetime

        rows = await self._session.scalars(
            select(UserRole).where(UserRole.admin_user_id == admin_user_id)
        )
        for row in rows:
            if row.revoked_at is None:
                row.revoked_at = datetime.now(UTC)


class ApiKeyRepository(SqlAlchemyRepository[ApiKey, str]):
    """API keys store only the hash; raw keys are shown once at creation."""

    model = ApiKey

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        result = await self._session.scalars(select(ApiKey).where(ApiKey.key_hash == key_hash))
        return result.first()

    async def list_for_user(self, admin_user_id: str) -> Sequence[ApiKey]:
        return (
            await self._session.scalars(
                select(ApiKey)
                .where(ApiKey.admin_user_id == admin_user_id)
                .order_by(ApiKey.created_at)
            )
        ).all()


class AdminPreferenceRepository(SqlAlchemyRepository[AdminPreference, str]):
    model = AdminPreference

    async def get_for_user(self, admin_user_id: str) -> AdminPreference | None:
        result = await self._session.scalars(
            select(AdminPreference).where(AdminPreference.admin_user_id == admin_user_id)
        )
        return result.first()


class AuditLogRepository(SqlAlchemyRepository[AuditLog, str]):
    """Append-only: no update/delete paths exist on this repository."""

    model = AuditLog

    async def list_scoped(
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
        stmt = select(AuditLog).order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc())
        if niche_id is not None:
            stmt = stmt.where(AuditLog.niche_id == niche_id)
        if admin_user_id is not None:
            stmt = stmt.where(AuditLog.admin_user_id == admin_user_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)
        if request_id is not None:
            stmt = stmt.where(AuditLog.request_id == request_id)
        if start is not None:
            stmt = stmt.where(AuditLog.occurred_at >= start)
        if end is not None:
            stmt = stmt.where(AuditLog.occurred_at <= end)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_scoped(self, *, niche_id: str | None = None) -> int:
        stmt = select(func.count(AuditLog.id))
        if niche_id is not None:
            stmt = stmt.where(AuditLog.niche_id == niche_id)
        return int((await self._session.scalars(stmt)).one())


class NotificationRepository(SqlAlchemyRepository[Notification, str]):
    model = Notification

    async def list_for_recipient(
        self,
        recipient_id: str,
        *,
        status: str | None = None,
        niche_id: str | None = None,
        limit: int = 50,
    ) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.recipient_id == recipient_id)
            .order_by(Notification.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Notification.status == status)
        if niche_id is not None:
            stmt = stmt.where(Notification.niche_id == niche_id)
        return (await self._session.scalars(stmt.limit(limit))).all()

    async def count_open(self, recipient_id: str | None = None) -> int:
        stmt = select(func.count(Notification.id)).where(Notification.status == "unread")
        if recipient_id is not None:
            stmt = stmt.where(Notification.recipient_id == recipient_id)
        return int((await self._session.scalars(stmt)).one())

    async def mark_read(self, notification_id: str, recipient_id: str) -> Notification | None:
        row = await self._session.get(Notification, notification_id)
        if row is None or row.recipient_id != recipient_id:
            return None
        if row.status == "unread":
            from datetime import UTC, datetime

            row.status = "read"
            row.read_at = datetime.now(UTC)
        return row


class NotificationPreferenceRepository(SqlAlchemyRepository[NotificationPreference, str]):
    model = NotificationPreference

    async def get_for_user(self, admin_user_id: str) -> NotificationPreference | None:
        result = await self._session.scalars(
            select(NotificationPreference).where(
                NotificationPreference.admin_user_id == admin_user_id
            )
        )
        return result.first()


class NotificationDeliveryRepository(SqlAlchemyRepository[NotificationDelivery, str]):
    model = NotificationDelivery


class QueueItemRepository(SqlAlchemyRepository[QueueItem, str]):
    """Durable queue ledger with explicit state transitions (Blueprint §5.23)."""

    model = QueueItem

    async def list_scoped(
        self,
        *,
        niche_id: str | None = None,
        queue: str | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[QueueItem]:
        stmt = select(QueueItem).order_by(QueueItem.run_at.desc())
        if niche_id is not None:
            stmt = stmt.where(QueueItem.niche_id == niche_id)
        if queue is not None:
            stmt = stmt.where(QueueItem.queue == queue)
        if state is not None:
            stmt = stmt.where(QueueItem.state == state)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def count_by_state(self, *, niche_id: str | None = None) -> dict[str, int]:
        stmt = select(QueueItem.state, func.count(QueueItem.id)).group_by(QueueItem.state)
        if niche_id is not None:
            stmt = stmt.where(QueueItem.niche_id == niche_id)
        return {state: int(count) for state, count in (await self._session.execute(stmt)).all()}

    async def failed_count(self, *, niche_id: str | None = None) -> int:
        stmt = select(func.count(QueueItem.id)).where(QueueItem.state == "failed")
        if niche_id is not None:
            stmt = stmt.where(QueueItem.niche_id == niche_id)
        return int((await self._session.scalars(stmt)).one())

    async def mark_claimed(self, queue_item_id: str) -> QueueItem | None:
        row = await self._session.get(QueueItem, queue_item_id)
        if row is not None and row.state == "queued":
            row.state = "claimed"
            row.attempts += 1
        return row

    async def complete(self, queue_item_id: str) -> QueueItem | None:
        from datetime import UTC, datetime

        row = await self._session.get(QueueItem, queue_item_id)
        if row is not None and row.state == "claimed":
            row.state = "done"
            row.completed_at = datetime.now(UTC)
            row.error = None
        return row

    async def fail(self, queue_item_id: str, *, error: str) -> QueueItem | None:
        from datetime import UTC, datetime

        row = await self._session.get(QueueItem, queue_item_id)
        if row is not None and row.state == "claimed":
            row.state = "failed"
            row.error = error[:500]
            row.completed_at = datetime.now(UTC)
        return row

    async def retry(self, queue_item_id: str, *, max_attempts: int) -> QueueItem | None:
        """Safe retry: only failed items, bounded by max_attempts."""
        from datetime import UTC, datetime

        row = await self._session.get(QueueItem, queue_item_id)
        if row is None or row.state != "failed":
            return None
        if row.attempts >= max_attempts:
            return None
        row.state = "queued"
        row.error = None
        row.completed_at = None
        row.run_at = datetime.now(UTC)
        return row


class WebhookLogRepository(SqlAlchemyRepository[WebhookLog, str]):
    """Idempotent on (source, event_id); failures are searchable."""

    model = WebhookLog

    async def get_by_source_event(self, source: str, event_id: str) -> WebhookLog | None:
        result = await self._session.scalars(
            select(WebhookLog).where(WebhookLog.source == source, WebhookLog.event_id == event_id)
        )
        return result.first()

    async def list_scoped(
        self,
        *,
        source: str | None = None,
        status: str | None = None,
        niche_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[WebhookLog]:
        stmt = select(WebhookLog).order_by(WebhookLog.received_at.desc())
        if source is not None:
            stmt = stmt.where(WebhookLog.source == source)
        if status is not None:
            stmt = stmt.where(WebhookLog.status == status)
        if niche_id is not None:
            stmt = stmt.where(WebhookLog.niche_id == niche_id)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def failed_count(self, *, niche_id: str | None = None) -> int:
        stmt = select(func.count(WebhookLog.id)).where(WebhookLog.status == "failed")
        if niche_id is not None:
            stmt = stmt.where(WebhookLog.niche_id == niche_id)
        return int((await self._session.scalars(stmt)).one())


class OperationLogRepository(SqlAlchemyRepository[OperationLog, str]):
    model = OperationLog

    async def list_scoped(
        self,
        *,
        niche_id: str | None = None,
        operation: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[OperationLog]:
        stmt = select(OperationLog).order_by(OperationLog.occurred_at.desc())
        if niche_id is not None:
            stmt = stmt.where(OperationLog.niche_id == niche_id)
        if operation is not None:
            stmt = stmt.where(OperationLog.operation == operation)
        if status is not None:
            stmt = stmt.where(OperationLog.status == status)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def failed_count(self, *, niche_id: str | None = None) -> int:
        stmt = select(func.count(OperationLog.id)).where(OperationLog.status == "failed")
        if niche_id is not None:
            stmt = stmt.where(OperationLog.niche_id == niche_id)
        return int((await self._session.scalars(stmt)).one())


class ScheduledJobRepository(SqlAlchemyRepository[ScheduledJob, str]):
    model = ScheduledJob

    async def list_scoped(self, *, niche_id: str | None = None) -> Sequence[ScheduledJob]:
        stmt = select(ScheduledJob).order_by(ScheduledJob.job_key)
        if niche_id is not None:
            stmt = stmt.where(ScheduledJob.niche_id == niche_id)
        return (await self._session.scalars(stmt)).all()


class JobRunRepository(SqlAlchemyRepository[JobRun, str]):
    model = JobRun

    async def list_recent(
        self, *, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> Sequence[JobRun]:
        stmt = select(JobRun).order_by(JobRun.run_at.desc())
        if status is not None:
            stmt = stmt.where(JobRun.status == status)
        return (await self._session.scalars(stmt.limit(limit).offset(offset))).all()

    async def failed_count(self) -> int:
        stmt = select(func.count(JobRun.id)).where(JobRun.status == "failed")
        return int((await self._session.scalars(stmt)).one())


class AdminUnitOfWork(SqlAlchemyUnitOfWork):
    """Transaction boundary exposing all admin repositories (ADR-0009)."""

    # Repository attributes are wired lazily by ``SqlAlchemyUnitOfWork._open``;
    # declared here so typed service helpers can rely on them.
    niches: AdminNicheRepository
    users: AdminUserRepository
    roles: RoleRepository
    permissions: PermissionRepository
    role_permissions: RolePermissionRepository
    user_roles: UserRoleRepository
    api_keys: ApiKeyRepository
    preferences: AdminPreferenceRepository
    audit: AuditLogRepository
    notifications: NotificationRepository
    notification_preferences: NotificationPreferenceRepository
    notification_deliveries: NotificationDeliveryRepository
    queue: QueueItemRepository
    webhook_logs: WebhookLogRepository
    operation_logs: OperationLogRepository
    scheduled_jobs: ScheduledJobRepository
    job_runs: JobRunRepository

    @classmethod
    def build(cls, session_factory) -> "AdminUnitOfWork":
        return cls(
            session_factory,
            repositories={
                "niches": AdminNicheRepository,
                "users": AdminUserRepository,
                "roles": RoleRepository,
                "permissions": PermissionRepository,
                "role_permissions": RolePermissionRepository,
                "user_roles": UserRoleRepository,
                "api_keys": ApiKeyRepository,
                "preferences": AdminPreferenceRepository,
                "audit": AuditLogRepository,
                "notifications": NotificationRepository,
                "notification_preferences": NotificationPreferenceRepository,
                "notification_deliveries": NotificationDeliveryRepository,
                "queue": QueueItemRepository,
                "webhook_logs": WebhookLogRepository,
                "operation_logs": OperationLogRepository,
                "scheduled_jobs": ScheduledJobRepository,
                "job_runs": JobRunRepository,
            },
        )
