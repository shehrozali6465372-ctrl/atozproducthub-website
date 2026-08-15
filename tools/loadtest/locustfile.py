"""Locust load profile for AtozProductHub (M11 Phase G — dev-only).

Usage:
    pip install locust
    locust -f tools/loadtest/locustfile.py --host https://staging.atozproducthub.dev

Mixed reader/operator traffic: article pages, search, affiliate product
pages, affiliate redirects, and admin reads. The profile targets the public
surface and the API; publish/webhook paths are exercised by the queue
reliability tests instead (they must not be load-tested against external
providers).
"""

from locust import HttpUser, between, task


class HealthUser(HttpUser):
    """Probe traffic: healthz/health/ready (scenario 1 in baselines.yml)."""

    wait_time = between(0.5, 2.0)

    @task(1)
    def healthz(self) -> None:
        self.client.get("/healthz", name="healthz")

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="health")

    @task(1)
    def ready(self) -> None:
        self.client.get("/ready", name="ready")


class ReaderUser(HttpUser):
    """Typical reader mix: browse articles, search, view products."""

    wait_time = between(1.0, 5.0)

    @task(5)
    def article_page(self) -> None:
        self.client.get("/articles/atoz-product-hub-guide", name="article_page")

    @task(3)
    def category_page(self) -> None:
        self.client.get("/categories/kitchen", name="category_page")

    @task(4)
    def search(self) -> None:
        self.client.get("/search?q=blender", name="search")

    @task(4)
    def product_page(self) -> None:
        self.client.get("/products/best-blender-2026", name="product_page")

    @task(2)
    def affiliate_collection(self) -> None:
        self.client.get("/collections/kitchen-buying-guides", name="collection")


class OperatorUser(HttpUser):
    """Admin/operator read traffic against the API (RBAC enforced)."""

    wait_time = between(2.0, 10.0)

    @task(3)
    def analytics_summary(self) -> None:
        self.client.get("/api/v1/admin/analytics/summary", name="admin_analytics")

    @task(2)
    def queue_visibility(self) -> None:
        self.client.get("/api/v1/admin/ops/overview", name="admin_ops")

    @task(1)
    def audit_search(self) -> None:
        self.client.get("/api/v1/admin/audit?limit=20", name="admin_audit")


class AnalyticsIngestionUser(HttpUser):
    """First-party analytics event ingestion (mock payloads only)."""

    wait_time = between(1.0, 4.0)

    @task(1)
    def collect_event(self) -> None:
        self.client.post(
            "/api/v1/collect/event",
            json={
                "event_id": "loadtest",
                "event_type": "page_view",
                "page_url": "/articles/loadtest",
                "session_id": "loadtest",
                "user_pseudo_id": "loadtest",
            },
            name="collect_event",
        )


class AutomationQueueUser(HttpUser):
    """Operator reads for queue/job visibility (RBAC enforced)."""

    wait_time = between(2.0, 6.0)

    @task(2)
    def scheduled_jobs(self) -> None:
        self.client.get("/api/v1/admin/scheduled-jobs", name="admin_scheduled_jobs")

    @task(1)
    def job_runs(self) -> None:
        self.client.get("/api/v1/admin/job-runs?limit=20", name="admin_job_runs")
