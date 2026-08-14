"""SEO executor: rebuilds one sitemap group in seo-service.

Sitemap generation/sharding/XML lives in seo-service (M7). The executor
just invokes the frozen rebuild endpoint with the niche scope and reports
shard counts. A niche scope is mandatory (sitemaps are niche-scoped).
"""

from atoz_automation_service.executors.base import (
    Executor,
    ExecutorContext,
    ExecutorResult,
    failure,
    success,
)

DEFAULT_GROUP = "articles"


class SeoSitemapExecutor(Executor):
    name = "seo.sitemap_rebuild"
    queue = "seo"

    async def execute(self, ctx: ExecutorContext) -> ExecutorResult:
        group = str(ctx.payload.get("group") or DEFAULT_GROUP)[:80]
        if not ctx.niche_id:
            return failure(error="sitemap rebuild requires a niche scope", retryable=False)
        try:
            result = await ctx.siblings.request(
                "seo",
                "POST",
                f"/api/v1/admin/sitemaps/{group}/rebuild",
                niche_id=ctx.niche_id,
            )
        except Exception as exc:  # noqa: BLE001
            return failure(error=f"seo-service: {exc}", retryable=True)

        shard_count = int(result.get("shard_count", 0))
        return success(
            summary=f"sitemap group '{group}' rebuilt ({shard_count} shards)",
            output_ref=result.get("shards") and str(result["shards"]),
            group=group,
            shard_count=shard_count,
        )
