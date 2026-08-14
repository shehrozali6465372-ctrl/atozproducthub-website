"""Admin & operations API (Task 19 / M9).

JWT RBAC (``admin:read`` / ``admin:write`` and per-module permissions) plus
optional ``X-Niche-Id`` tenancy. The audit ledger is read-only here (append
happens through the service layer on every mutation); exports are capped by
the export-control setting. No AI functionality exists on this surface.
"""

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import PlainTextResponse

from atoz_admin_service.routes.deps import (
    get_admin_service,
    get_niche_id,
    require_mfa_verified,
    require_permission,
)
from atoz_admin_service.schemas import (
    AdminUserCreate,
    AdminUserUpdate,
    ApiKeyCreate,
    AuditLogIn,
    AuditLogOut,
    IsolationCheckOut,
    JobRunOut,
    NotificationCreate,
    NotificationOut,
    NotificationPreferenceUpdate,
    OperationLogIn,
    OperationLogOut,
    OpsOverviewOut,
    PermissionOut,
    QueueEnqueueIn,
    QueueItemOut,
    RoleAssignIn,
    ScheduledJobOut,
    SystemStatusOut,
    WebhookLogOut,
)
from atoz_admin_service.services import AdminService

ADMIN_READ = require_permission("admin:read")
ADMIN_WRITE = require_permission("admin:write")
MFA_WRITE = require_mfa_verified("admin:write")

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ------------------------------------------------------------------ RBAC
@router.get("/roles", summary="List system + custom roles with permission sets")
async def list_roles(
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[dict]:
    return await service.list_roles()


@router.get("/permissions", summary="List the frozen permission catalog")
async def list_permissions(
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[PermissionOut]:
    perms = await service.list_permissions()
    return [PermissionOut.model_validate(p, from_attributes=True) for p in perms]


@router.get("/users", summary="List operators with their role assignments")
async def list_users(
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[dict]:
    return await service.list_users()


@router.post("/users", summary="Create an operator", status_code=201)
async def create_user(
    payload: AdminUserCreate,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    user = await service.create_user(
        subject=payload.subject,
        email=payload.email,
        display_name=payload.display_name,
        status=payload.status,
        roles=[{"role_code": r.role_code, "niche_id": r.niche_id} for r in payload.roles],
    )
    detail = await service.get_user(user.id)
    assert detail is not None
    return detail


@router.get("/users/{user_id}", summary="Operator detail with roles")
async def get_user(
    user_id: str,
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    user = await service.get_user(user_id)
    if user is None:
        from atoz_admin_service.errors import NotFoundError

        raise NotFoundError("Operator not found.")
    return user


@router.patch("/users/{user_id}", summary="Update operator profile/status/MFA flag")
async def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    user = await service.update_user(
        user_id,
        display_name=payload.display_name,
        status=payload.status,
        mfa_enabled=payload.mfa_enabled,
    )
    assert user is not None
    detail = await service.get_user(user.id)
    assert detail is not None
    return detail


@router.post(
    "/users/{user_id}/roles", summary="Assign a role (optionally niche-scoped)", status_code=201
)
async def assign_role(
    user_id: str,
    payload: RoleAssignIn,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    await service.assign_role(user_id, payload.role_code, payload.niche_id)
    return {"ok": True}


@router.post("/users/{user_id}/roles/revoke", summary="Revoke a role assignment")
async def revoke_role(
    user_id: str,
    payload: RoleAssignIn,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    await service.revoke_role(user_id, payload.role_code, payload.niche_id)
    return {"ok": True}


@router.post(
    "/users/{user_id}/api-keys", summary="Issue an automation API key (shown once)", status_code=201
)
async def create_api_key(
    user_id: str,
    payload: ApiKeyCreate,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    api_key, raw_key = await service.create_api_key(
        admin_user_id=user_id,
        niche_id=payload.niche_id,
        name=payload.name,
        scopes=payload.scopes,
    )
    return {
        "id": api_key.id,
        "admin_user_id": api_key.admin_user_id,
        "niche_id": api_key.niche_id,
        "name": api_key.name,
        "scopes": api_key.scopes_json,
        "raw_key": raw_key,
    }


@router.post("/mfa/provision", summary="Provision TOTP enrollment for the caller")
async def provision_mfa(
    _claims=Depends(ADMIN_READ),
) -> dict:
    from atoz_backend_core.auth.mfa import MfaService

    provision = MfaService().provision(_claims.subject)
    return {
        "subject": provision.subject,
        "otpauth_uri": provision.otpauth_uri,
        "secret_ref": f"vault:mfa/{_claims.subject}",
        "note": (
            "Verification ships with the Authentication milestone; "
            "enable the operator MFA flag once enrolled."
        ),
    }


# ------------------------------------------------------------- sessions
@router.post("/sessions/{session_id}/revoke", summary="Revoke an operator session")
async def revoke_session(
    session_id: str,
    request: Request,
    _claims=Depends(MFA_WRITE),
) -> dict:
    from atoz_admin_service.routes.deps import get_session_manager

    manager = get_session_manager(request)
    await manager.revoke(session_id)
    return {"ok": True}


# --------------------------------------------------------------- audit
@router.get("/audit", summary="Search the append-only audit ledger")
async def search_audit(
    action: str | None = Query(default=None, max_length=60),
    entity_type: str | None = Query(default=None, max_length=60),
    entity_id: str | None = Query(default=None, max_length=36),
    admin_user_id: str | None = Query(default=None, max_length=36),
    request_id: str | None = Query(default=None, max_length=100),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[AuditLogOut]:
    rows = await service.search_audit(
        niche_id=niche_id,
        admin_user_id=admin_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        request_id=request_id,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
    )
    return [AuditLogOut.model_validate(r, from_attributes=True) for r in rows]


@router.post(
    "/audit", summary="Append an audit record (server-side actor metadata)", status_code=201
)
async def record_audit(
    payload: AuditLogIn,
    request: Request,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> AuditLogOut:
    claims = _claims
    entry = await service.record_audit(
        action=payload.action,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        niche_id=payload.niche_id,
        admin_user_id=claims.subject,
        before_json=payload.before_json,
        after_json=payload.after_json,
        ip_hash=payload.ip_hash,
        request_id=request.headers.get("X-Request-ID"),
    )
    return AuditLogOut.model_validate(entry, from_attributes=True)


@router.get("/audit/export", summary="Capped CSV export of the audit ledger")
async def export_audit(
    niche_id: str | None = Depends(get_niche_id),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> Response:
    csv_content = await service.export_audit_csv(niche_id=niche_id)
    return PlainTextResponse(
        csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit.csv"},
    )


# --------------------------------------------------------------- ops
@router.get("/ops/overview", summary="Operations KPI summary (failures, queues, audit)")
async def ops_overview(
    niche_id: str | None = Depends(get_niche_id),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> OpsOverviewOut:
    return OpsOverviewOut(**await service.ops_overview(niche_id=niche_id))


@router.get("/ops/status", summary="System status: probe sibling business services")
async def system_status(
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> SystemStatusOut:
    status = await service.system_status()
    return SystemStatusOut(**status)


@router.get("/ops/isolation", summary="Verify niche/account isolation in admin-owned records")
async def isolation_check(
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> IsolationCheckOut:
    result = await service.isolation_check()
    return IsolationCheckOut(**result)


# --------------------------------------------------------------- queue
@router.get("/queue", summary="Queue visibility with state/queue/niche filters")
async def list_queue(
    queue: str | None = Query(default=None, max_length=80),
    state: str | None = Query(default=None, pattern="^(queued|claimed|done|failed)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[QueueItemOut]:
    rows = await service.list_queue_items(
        niche_id=niche_id, queue=queue, state=state, limit=limit, offset=offset
    )
    return [QueueItemOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/queue", summary="Enqueue a durable work item", status_code=201)
async def enqueue(
    payload: QueueEnqueueIn,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> QueueItemOut:
    item = await service.enqueue(
        niche_id=payload.niche_id,
        queue=payload.queue,
        payload_ref=payload.payload_ref,
        run_at=payload.run_at,
        max_attempts=payload.max_attempts,
    )
    return QueueItemOut.model_validate(item, from_attributes=True)


@router.post("/queue/{queue_item_id}/retry", summary="Safe retry of a failed queue item")
async def retry_queue(
    queue_item_id: str,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> QueueItemOut:
    item = await service.retry_queue_item(queue_item_id)
    return QueueItemOut.model_validate(item, from_attributes=True)


# --------------------------------------------------------------- logs
@router.get("/logs/webhooks", summary="Searchable webhook delivery records")
async def list_webhook_logs(
    source: str | None = Query(default=None, max_length=30),
    status: str | None = Query(default=None, pattern="^(received|processed|failed|ignored)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[WebhookLogOut]:
    rows = await service.list_webhook_logs(
        source=source, status=status, niche_id=niche_id, limit=limit, offset=offset
    )
    return [WebhookLogOut.model_validate(r, from_attributes=True) for r in rows]


@router.get("/logs/operations", summary="Searchable business operation records")
async def list_operation_logs(
    operation: str | None = Query(default=None, max_length=80),
    status: str | None = Query(default=None, pattern="^(started|succeeded|failed)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[OperationLogOut]:
    rows = await service.list_operation_logs(
        niche_id=niche_id, operation=operation, status=status, limit=limit, offset=offset
    )
    return [OperationLogOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/logs/operations", summary="Record a business operation (internal tooling)")
async def record_operation(
    payload: OperationLogIn,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> OperationLogOut:
    record = await service.record_operation(
        operation=payload.operation,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        niche_id=payload.niche_id,
        status=payload.status,
        message=payload.message,
        details=payload.details,
    )
    return OperationLogOut.model_validate(record, from_attributes=True)


# --------------------------------------------------------------- jobs
@router.get("/jobs", summary="Scheduled job definitions")
async def list_jobs(
    niche_id: str | None = Depends(get_niche_id),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[ScheduledJobOut]:
    rows = await service.list_scheduled_jobs(niche_id=niche_id)
    return [ScheduledJobOut.model_validate(r, from_attributes=True) for r in rows]


@router.get("/jobs/runs", summary="Recent job execution records")
async def list_job_runs(
    status: str | None = Query(
        default=None, pattern="^(pending|running|success|failed|cancelled)$"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[JobRunOut]:
    rows = await service.list_job_runs(status=status, limit=limit, offset=offset)
    return [JobRunOut.model_validate(r, from_attributes=True) for r in rows]


# ------------------------------------------------------- notifications
@router.get("/notifications", summary="Notifications for the caller")
async def list_notifications(
    status: str | None = Query(default=None, pattern="^(unread|read|actioned)$"),
    niche_id: str | None = Depends(get_niche_id),
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> list[NotificationOut]:
    rows = await service.list_notifications(_claims.subject, status=status, niche_id=niche_id)
    return [NotificationOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/notifications", summary="Create a notification for an operator", status_code=201)
async def create_notification(
    payload: NotificationCreate,
    _claims=Depends(MFA_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> NotificationOut:
    notification = await service.create_notification(
        recipient_id=payload.recipient_id,
        type=payload.type,
        title=payload.title,
        body=payload.body,
        niche_id=payload.niche_id,
        action_ref=payload.action_ref,
    )
    return NotificationOut.model_validate(notification, from_attributes=True)


@router.post(
    "/internal/notifications",
    summary="Create a notification from a service account (internal channel)",
    status_code=201,
)
async def create_internal_notification(
    payload: NotificationCreate,
    request: Request,
    _claims=Depends(ADMIN_WRITE),
    service: AdminService = Depends(get_admin_service),
) -> NotificationOut:
    """Service-account notification delivery (automation executors).

    Requires a service JWT carrying ``admin:write`` (minted against the
    shared admin secret) and, when ``INTERNAL_TOKEN`` is configured, the
    matching ``X-Internal-Token`` header. MFA is intentionally not required:
    this channel is for machine-to-machine delivery, never human sessions.
    """
    settings = request.app.state.settings
    if settings.internal_token:
        presented = request.headers.get("X-Internal-Token", "")
        if presented != settings.internal_token:
            from atoz_admin_service.errors import PermissionDeniedError

            raise PermissionDeniedError("Invalid internal token.")
    notification = await service.create_notification(
        recipient_id=payload.recipient_id,
        type=payload.type,
        title=payload.title,
        body=payload.body,
        niche_id=payload.niche_id,
        action_ref=payload.action_ref,
    )
    return NotificationOut.model_validate(notification, from_attributes=True)


@router.post("/notifications/{notification_id}/read", summary="Mark a notification read")
async def mark_notification_read(
    notification_id: str,
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> NotificationOut:
    updated = await service.mark_notification_read(notification_id, _claims.subject)
    if updated is None:
        from atoz_admin_service.errors import NotFoundError

        raise NotFoundError("Notification not found.")
    return NotificationOut.model_validate(updated, from_attributes=True)


@router.get("/notifications/preferences", summary="Notification delivery preferences")
async def get_preferences(
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    return await service.notification_preferences(_claims.subject)


@router.put("/notifications/preferences", summary="Update notification preferences")
async def put_preferences(
    payload: NotificationPreferenceUpdate,
    _claims=Depends(ADMIN_READ),
    service: AdminService = Depends(get_admin_service),
) -> dict:
    await service.update_notification_preferences(
        _claims.subject, channels=payload.channels, quiet_hours=payload.quiet_hours
    )
    return await service.notification_preferences(_claims.subject)
