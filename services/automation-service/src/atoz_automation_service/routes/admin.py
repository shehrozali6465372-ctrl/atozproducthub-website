"""Automation admin API (Task 20 / M10 foundation).

JWT RBAC ``automation:read`` / ``automation:write`` + optional
``X-Niche-Id`` tenancy header. Absent header = global records; present
header = strict niche scope. All mutations validate state transitions
server-side; run triggers honor the ``Idempotency-Key`` header for replay
safety. No AI functionality is exposed.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query

from atoz_automation_service.errors import ValidationError
from atoz_automation_service.executors.registry import ExecutorRegistry
from atoz_automation_service.routes.deps import (
    get_automation_service,
    get_executor_registry,
    get_niche_id,
    require_niche,
    require_permission,
)
from atoz_automation_service.schemas import (
    AiosJobCreate,
    AiosJobOut,
    AiosJobStatusIn,
    ExecutorOut,
    JobRunDetailOut,
    JobRunOut,
    NicheMirrorCreate,
    QueueEnqueueIn,
    QueueItemDetailOut,
    QueueItemOut,
    RuleCreate,
    RuleOut,
    RunJobRequest,
    RunOut,
    ScheduledJobCreate,
    ScheduledJobOut,
)
from atoz_automation_service.services import AutomationService
from atoz_backend_core.auth import TokenClaims

READ = require_permission("automation:read")
WRITE = require_permission("automation:write")

router = APIRouter(prefix="/api/v1/admin", tags=["admin-automation"])


# ------------------------------------------------------------------ niches
@router.get("/niches", summary="List niche mirrors")
async def list_niches(
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[dict]:
    return [
        {"id": n.id, "slug": n.slug, "name": n.name, "status": n.status}
        for n in await service.list_niches()
    ]


@router.post("/niches", summary="Create a niche mirror", status_code=201)
async def create_niche(
    payload: NicheMirrorCreate,
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    niche = await service.create_niche(name=payload.name, slug=payload.slug, status=payload.status)
    return {"id": niche.id, "slug": niche.slug, "name": niche.name, "status": niche.status}


# ------------------------------------------------------------------ rules
@router.get("/rules", summary="List automation rules in scope")
async def list_rules(
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[RuleOut]:
    rules = await service.list_rules(niche_id)
    return [RuleOut.model_validate(r) for r in rules]


@router.post("/rules", summary="Create an automation rule", status_code=201)
async def create_rule(
    payload: RuleCreate,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> RuleOut:
    rule = await service.create_rule(
        niche_id=niche_id,
        code=payload.code,
        trigger_type=payload.trigger_type,
        config=payload.config,
        run_as_user_id=payload.run_as_user_id,
    )
    return RuleOut.model_validate(rule)


@router.post("/rules/{rule_id}/enable", summary="Enable a rule")
async def enable_rule(
    rule_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> RuleOut:
    rule = await service.enable_rule(rule_id, niche_id)
    return RuleOut.model_validate(rule)


@router.post("/rules/{rule_id}/disable", summary="Disable a rule")
async def disable_rule(
    rule_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> RuleOut:
    rule = await service.disable_rule(rule_id, niche_id)
    return RuleOut.model_validate(rule)


@router.post("/rules/{rule_id}/trigger", summary="Trigger a rule run (idempotent)")
async def trigger_rule(
    rule_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    key = idempotency_key.strip() if idempotency_key else None
    run, created = await service.trigger_rule(
        rule_id=rule_id,
        niche_id=niche_id,
        triggered_by=_claims.subject,
        idempotency_key=key,
    )
    return {
        "run": RunOut.model_validate(run).model_dump(),
        "created": created,
    }


# ------------------------------------------------------------------- runs
@router.get("/runs", summary="List automation run history in scope")
async def list_runs(
    rule_id: str | None = Query(default=None, max_length=36),
    status: str | None = Query(default=None, pattern="^(running|success|failed)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[RunOut]:
    runs = await service.list_runs(
        niche_id, rule_id=rule_id, status=status, limit=limit, offset=offset
    )
    return [RunOut.model_validate(r) for r in runs]


@router.post("/runs/{run_id}/complete", summary="Complete a running rule")
async def complete_run(
    run_id: str,
    summary: str | None = Query(default=None, max_length=500),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> RunOut:
    run = await service.complete_run(run_id, niche_id, summary=summary)
    return RunOut.model_validate(run)


@router.post("/runs/{run_id}/fail", summary="Fail a running rule")
async def fail_run(
    run_id: str,
    error: str | None = Query(default=None, max_length=500),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> RunOut:
    run = await service.fail_run(run_id, niche_id, error=error)
    return RunOut.model_validate(run)


# ---------------------------------------------------------- scheduled jobs
@router.get("/scheduled-jobs", summary="List scheduled jobs in scope")
async def list_scheduled_jobs(
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[ScheduledJobOut]:
    jobs = await service.list_scheduled_jobs(niche_id)
    return [ScheduledJobOut.model_validate(j) for j in jobs]


@router.post("/scheduled-jobs", summary="Create a scheduled job", status_code=201)
async def create_scheduled_job(
    payload: ScheduledJobCreate,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> ScheduledJobOut:
    job = await service.create_scheduled_job(
        niche_id=niche_id,
        job_key=payload.job_key,
        cron_expr=payload.cron_expr,
        queue=payload.queue,
        handler=payload.handler,
        config=payload.config,
        next_run_at=payload.next_run_at,
    )
    return ScheduledJobOut.model_validate(job)


@router.post("/scheduled-jobs/{job_id}/enable", summary="Enable a scheduled job")
async def enable_job(
    job_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> ScheduledJobOut:
    job = await service.set_scheduled_job_status(job_id, niche_id, enabled=True)
    return ScheduledJobOut.model_validate(job)


@router.post("/scheduled-jobs/{job_id}/disable", summary="Disable a scheduled job")
async def disable_job(
    job_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> ScheduledJobOut:
    job = await service.set_scheduled_job_status(job_id, niche_id, enabled=False)
    return ScheduledJobOut.model_validate(job)


@router.post(
    "/scheduled-jobs/{job_id}/enqueue",
    summary="Queue one execution of a scheduled job",
    status_code=201,
)
async def enqueue_job(
    job_id: str,
    run_at: datetime | None = Query(default=None),
    payload: RunJobRequest | None = None,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    if payload is not None and payload.config:
        run_row, item = await service.enqueue_job_with_config(
            job_id, niche_id, run_at=run_at, config=payload.config
        )
    else:
        run_row, item = await service.enqueue_job(job_id, niche_id, run_at=run_at)
    return {
        "run": JobRunOut.model_validate(run_row).model_dump(),
        "queue_item": QueueItemOut.model_validate(item).model_dump(),
    }


@router.get("/job-runs", summary="List job run executions in scope")
async def list_job_runs(
    job_id: str | None = Query(default=None, max_length=36),
    status: str | None = Query(
        default=None, pattern="^(pending|running|success|failed|cancelled)$"
    ),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[JobRunOut]:
    runs = await service.list_job_runs(
        niche_id, job_id=job_id, status=status, limit=limit, offset=offset
    )
    return [JobRunOut.model_validate(r) for r in runs]


@router.post("/job-runs/{run_id}/start", summary="Start a pending job run")
async def start_job_run(
    run_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> JobRunOut:
    run = await service.start_job_run(run_id, niche_id)
    return JobRunOut.model_validate(run)


@router.post("/job-runs/{run_id}/complete", summary="Complete a running job run")
async def complete_job_run(
    run_id: str,
    output_ref: str | None = Query(default=None, max_length=500),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> JobRunOut:
    run = await service.complete_job_run(run_id, niche_id, output_ref=output_ref)
    return JobRunOut.model_validate(run)


@router.post("/job-runs/{run_id}/fail", summary="Fail (or retry) a running job run")
async def fail_job_run(
    run_id: str,
    error: str | None = Query(default=None, max_length=500),
    retry: bool = Query(default=True),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> JobRunOut:
    run = await service.fail_job_run(run_id, niche_id, error=error, retry=retry)
    return JobRunOut.model_validate(run)


@router.post("/job-runs/{run_id}/cancel", summary="Cancel a pending/running job run")
async def cancel_job_run(
    run_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> JobRunOut:
    run = await service.cancel_job_run(run_id, niche_id)
    return JobRunOut.model_validate(run)


@router.post("/job-runs/{run_id}/retry", summary="Retry a failed/cancelled job run")
async def retry_job_run(
    run_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    run_row, item = await service.retry_job_run(run_id, niche_id)
    return {
        "run": JobRunOut.model_validate(run_row).model_dump(),
        "queue_item": QueueItemOut.model_validate(item).model_dump(),
    }


@router.get("/jobs/runs", summary="List job runs with job key + niche slug")
async def list_job_runs_detailed(
    job_id: str | None = Query(default=None, max_length=36),
    status: str | None = Query(
        default=None, pattern="^(pending|running|success|failed|cancelled)$"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[JobRunDetailOut]:
    rows = await service.list_job_runs_detailed(
        niche_id, job_id=job_id, status=status, limit=limit, offset=offset
    )
    return [JobRunDetailOut.model_validate(r) for r in rows]


# ------------------------------------------------------------------ queue
@router.get("/queue", summary="List queue ledger items in scope")
async def list_queue(
    queue: str | None = Query(default=None, max_length=80),
    state: str | None = Query(default=None, pattern="^(queued|claimed|done|failed)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[QueueItemOut]:
    items = await service.list_queue(niche_id, queue=queue, state=state, limit=limit, offset=offset)
    return [QueueItemOut.model_validate(i) for i in items]


@router.get("/queue/detailed", summary="List queue ledger items with niche slug")
async def list_queue_detailed(
    queue: str | None = Query(default=None, max_length=80),
    state: str | None = Query(default=None, pattern="^(queued|claimed|done|failed)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[QueueItemDetailOut]:
    rows = await service.list_queue_aggregate(
        niche_id, queue=queue, state=state, limit=limit, offset=offset
    )
    return [QueueItemDetailOut.model_validate(r) for r in rows]


@router.post("/queue/enqueue", summary="Idempotent enqueue", status_code=201)
async def enqueue(
    payload: QueueEnqueueIn,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    item, created = await service.enqueue(
        niche_id=niche_id,
        queue=payload.queue,
        payload_ref=payload.payload_ref,
        run_at=payload.run_at,
        max_attempts=payload.max_attempts,
    )
    return {"item": QueueItemOut.model_validate(item).model_dump(), "created": created}


@router.post("/queue/{item_id}/claim", summary="Claim a queued item")
async def claim(
    item_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> QueueItemOut:
    item = await service.claim_queue_item(item_id, niche_id)
    return QueueItemOut.model_validate(item)


@router.post("/queue/{item_id}/complete", summary="Complete a claimed item")
async def complete(
    item_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> QueueItemOut:
    item = await service.complete_queue_item(item_id, niche_id)
    return QueueItemOut.model_validate(item)


@router.post("/queue/{item_id}/fail", summary="Fail (or retry with backoff) a claimed item")
async def fail(
    item_id: str,
    error: str | None = Query(default=None, max_length=500),
    retry: bool = Query(default=True),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> QueueItemOut:
    item = await service.fail_queue_item(item_id, niche_id, error=error, retry=retry)
    return QueueItemOut.model_validate(item)


@router.post("/queue/{item_id}/retry", summary="Requeue a failed queue item")
async def retry_queue_item(
    item_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> QueueItemOut:
    item = await service.retry_queue_item(item_id, niche_id)
    return QueueItemOut.model_validate(item)


@router.post("/queue/{item_id}/cancel", summary="Cancel a queued/claimed queue item")
async def cancel_queue_item(
    item_id: str,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> QueueItemOut:
    item = await service.cancel_queue_item(item_id, niche_id)
    return QueueItemOut.model_validate(item)


# --------------------------------------------------------------- executors
@router.get("/executors", summary="List registered business executors (read-only)")
async def list_executors(
    _claims: TokenClaims = Depends(READ),
    registry: ExecutorRegistry = Depends(get_executor_registry),
) -> list[ExecutorOut]:
    executors: list[ExecutorOut] = []
    for name in registry.names():
        executor = registry.get(name)
        if executor is not None:
            executors.append(ExecutorOut(name=executor.name, queue=executor.queue))
    return executors


# -------------------------------------------------------------- AI OS jobs
@router.get("/aios-jobs", summary="List AI OS Bridge correlation records")
async def list_aios_jobs(
    status: str | None = Query(
        default=None, pattern="^(pending|in_progress|succeeded|failed|cancelled)$"
    ),
    contract: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(READ),
    service: AutomationService = Depends(get_automation_service),
) -> list[AiosJobOut]:
    if niche_id is None:
        return []
    rows = await service.list_aios_jobs(
        niche_id, status=status, contract=contract, limit=limit, offset=offset
    )
    return [AiosJobOut.model_validate(r) for r in rows]


@router.post("/aios-jobs", summary="Create an AI OS job correlation record", status_code=201)
async def create_aios_job(
    payload: AiosJobCreate,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> dict:
    if niche_id is None:
        raise ValidationError("X-Niche-Id header is required for AI OS Bridge records.")
    row, created = await service.create_aios_job(
        niche_id=niche_id,
        job_id=payload.job_id,
        contract=payload.contract,
        direction=payload.direction,
        payload_ref=payload.payload_ref,
    )
    return {"job": AiosJobOut.model_validate(row).model_dump(), "created": created}


@router.post("/aios-jobs/status", summary="Advance an AI OS job status")
async def set_aios_job_status(
    payload: AiosJobStatusIn,
    niche_id: str | None = Depends(get_niche_id),
    _=Depends(require_niche),
    _claims: TokenClaims = Depends(WRITE),
    service: AutomationService = Depends(get_automation_service),
) -> AiosJobOut:
    if niche_id is None:
        raise ValidationError("X-Niche-Id header is required for AI OS Bridge records.")
    row = await service.set_aios_job_status(
        niche_id=niche_id,
        job_id=payload.job_id,
        contract=payload.contract,
        status=payload.status,
        error=payload.error,
    )
    return AiosJobOut.model_validate(row)
