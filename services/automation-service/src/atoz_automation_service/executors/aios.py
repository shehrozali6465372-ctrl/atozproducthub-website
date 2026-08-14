"""AI OS executor: dispatches an approved job request through the Bridge.

automation-service contains zero AI logic. It reads the correlation record
(``aios_job_records``), submits the approved job request to the AI OS
Bridge (``/bridge/jobs`` — the bridge owns the AI OS client, contract
validation, retry, and circuit breaker), and the workflow records the
outcome in the correlation ledger. Payloads carry business references
only — never prompts or generated-content internals (Blueprint §5.29).
"""

from atoz_automation_service.executors.base import (
    Executor,
    ExecutorContext,
    ExecutorResult,
    failure,
    success,
)


class AiosDispatchExecutor(Executor):
    name = "aios.dispatch"
    queue = "aios"

    async def execute(self, ctx: ExecutorContext) -> ExecutorResult:
        if not ctx.niche_id:
            return failure(error="AI OS dispatch requires a niche scope", retryable=False)
        job_id = ctx.payload.get("job_id")
        contract = ctx.payload.get("contract")
        request = ctx.payload.get("request") or {}
        if not job_id or not contract:
            return failure(
                error="payload.job_id and payload.contract are required",
                retryable=False,
            )
        bridge_payload = {
            "job_id": job_id,
            "contract": contract,
            "niche_id": ctx.niche_id,
            "request": request,
        }
        headers: dict[str, str] = {}
        if ctx.settings.aios_bridge_internal_token:
            headers["X-Bridge-Token"] = ctx.settings.aios_bridge_internal_token
        try:
            result = await ctx.siblings.request(
                "aios-bridge",
                "POST",
                "/bridge/jobs",
                niche_id=None,  # bridge is transport-only; the request body carries scope
                payload=bridge_payload,
                headers=headers,
            )
        except Exception as exc:  # noqa: BLE001 — AI OS unavailable → retryable
            return failure(
                error=f"aios-bridge: {exc}",
                retryable=True,
                job_id=job_id,
                contract=contract,
            )

        aios_job_id = result.get("aios_job_id") or result.get("job_id")
        return success(
            summary=f"AI OS job submitted ({contract}), aios_job_id={aios_job_id}",
            output_ref=aios_job_id,
            job_id=job_id,
            contract=contract,
            aios_job_id=aios_job_id,
        )
