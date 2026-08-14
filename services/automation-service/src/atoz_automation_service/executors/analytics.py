"""Analytics executor: runs daily rollups in analytics-service.

Rollup aggregation and read-model building live in analytics-service (M8).
The executor invokes the frozen ``/rollups`` endpoint for a date range with
the niche scope and reports how many rollup days were produced.
"""

from datetime import date

from atoz_automation_service.executors.base import (
    Executor,
    ExecutorContext,
    ExecutorResult,
    failure,
    success,
)


class AnalyticsRollupExecutor(Executor):
    name = "analytics.rollup"
    queue = "analytics"

    async def execute(self, ctx: ExecutorContext) -> ExecutorResult:
        if not ctx.niche_id:
            return failure(error="rollup requires a niche scope", retryable=False)
        from_date = ctx.payload.get("from_date") or date.today().isoformat()
        to_date = ctx.payload.get("to_date") or from_date
        try:
            result = await ctx.siblings.request(
                "analytics",
                "POST",
                "/api/v1/admin/rollups",
                niche_id=ctx.niche_id,
                params={"from_date": from_date, "to_date": to_date},
            )
        except Exception as exc:  # noqa: BLE001
            return failure(error=f"analytics-service: {exc}", retryable=True)

        days = len(result) if isinstance(result, list) else 0
        return success(
            summary=f"rollups completed for {days} day(s) ({from_date}..{to_date})",
            output_ref=f"rollup:{from_date}:{to_date}",
            days=days,
        )
