"""Affiliate executor: records a reconciliation run in affiliate-service.

The affiliate-service owns networks, merchants, transactions, and the
reconciliation ledger (M5). The executor submits the reconciliation
metadata (network, report reference, expected/actual totals) to the frozen
``/reconciliations`` endpoint — comparison/reconciliation business logic
stays in affiliate-service.
"""

from atoz_automation_service.executors.base import (
    Executor,
    ExecutorContext,
    ExecutorResult,
    failure,
    success,
)


class AffiliateReconciliationExecutor(Executor):
    name = "affiliate.reconciliation"
    queue = "affiliate"

    async def execute(self, ctx: ExecutorContext) -> ExecutorResult:
        if not ctx.niche_id:
            return failure(error="reconciliation requires a niche scope", retryable=False)
        network_id = ctx.payload.get("network_id")
        if not network_id:
            return failure(error="payload.network_id is required", retryable=False)
        payload = {
            "network_id": network_id,
            "reported_at": ctx.payload.get("reported_at"),
            "expected_total_cents": int(ctx.payload.get("expected_total_cents", 0)),
            "actual_total_cents": int(ctx.payload.get("actual_total_cents", 0)),
            "report_ref": ctx.payload.get("report_ref"),
        }
        try:
            result = await ctx.siblings.request(
                "affiliate",
                "POST",
                "/api/v1/admin/reconciliations",
                niche_id=ctx.niche_id,
                payload=payload,
            )
        except Exception as exc:  # noqa: BLE001
            return failure(error=f"affiliate-service: {exc}", retryable=True)

        return success(
            summary=(
                f"reconciliation {result.get('id')} recorded "
                f"(delta {result.get('delta_cents', 0)} cents)"
            ),
            output_ref=result.get("id"),
            reconciliation_id=result.get("id"),
            delta_cents=result.get("delta_cents", 0),
        )
