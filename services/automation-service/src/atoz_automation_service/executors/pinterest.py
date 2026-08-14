"""Pinterest executor: triggers pin publishing in pinterest-service.

The pinterest-service owns pin queues, accounts, rate limits, and
publishing attempts (M6). This executor only calls its worker entry point
(``/queue/publish-due``) with the item's niche scope — no Pinterest logic is
duplicated here. Only safe/idempotent work is retried (rate-limit and
transient failures are re-queued by the owning service).
"""

from atoz_automation_service.executors.base import (
    Executor,
    ExecutorContext,
    ExecutorResult,
    failure,
    success,
)


class PinterestExecutor(Executor):
    name = "pinterest.publish_due"
    queue = "pinterest"

    async def execute(self, ctx: ExecutorContext) -> ExecutorResult:
        params: dict[str, object] = {"limit": int(ctx.payload.get("limit", 10))}
        if ctx.niche_id:
            params["niche_id"] = ctx.niche_id
        try:
            result = await ctx.siblings.request(
                "pinterest",
                "POST",
                "/api/v1/admin/queue/publish-due",
                niche_id=ctx.niche_id,
                params=params,
            )
        except Exception as exc:  # noqa: BLE001 — sibling errors become retryable failures
            return failure(error=f"pinterest-service: {exc}", retryable=True)

        outcomes = result if isinstance(result, list) else result.get("outcomes", [])
        published = sum(1 for o in outcomes if o.get("status") == "published")
        failed = sum(1 for o in outcomes if o.get("status") == "failed")
        summary = f"pins published: {published}, failed: {failed}"
        if failed and not published:
            return failure(
                error="pinterest publish failed for all due pins",
                retryable=True,
                summary=summary,
                published=published,
                failed=failed,
            )
        return success(
            summary=summary,
            output_ref=f"pins:{published}",
            published=published,
            failed=failed,
        )
