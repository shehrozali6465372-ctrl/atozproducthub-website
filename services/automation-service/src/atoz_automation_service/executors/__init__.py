"""Executor package: registry + built-in business executors."""

from atoz_automation_service.executors.affiliate import AffiliateReconciliationExecutor
from atoz_automation_service.executors.aios import AiosDispatchExecutor
from atoz_automation_service.executors.analytics import AnalyticsRollupExecutor
from atoz_automation_service.executors.base import (
    Executor,
    ExecutorContext,
    ExecutorError,
    ExecutorResult,
    failure,
    success,
)
from atoz_automation_service.executors.pinterest import PinterestExecutor
from atoz_automation_service.executors.registry import ExecutorRegistry
from atoz_automation_service.executors.seo import SeoSitemapExecutor

BUILTIN_EXECUTORS = (
    PinterestExecutor(),
    SeoSitemapExecutor(),
    AffiliateReconciliationExecutor(),
    AnalyticsRollupExecutor(),
    AiosDispatchExecutor(),
)


def build_default_registry() -> ExecutorRegistry:
    """Registry with all Step 2 executors registered."""
    registry = ExecutorRegistry()
    for executor in BUILTIN_EXECUTORS:
        registry.register(executor)
    return registry


__all__ = [
    "Executor",
    "ExecutorContext",
    "ExecutorResult",
    "ExecutorError",
    "ExecutorRegistry",
    "build_default_registry",
    "AffiliateReconciliationExecutor",
    "AnalyticsRollupExecutor",
    "AiosDispatchExecutor",
    "PinterestExecutor",
    "SeoSitemapExecutor",
]
