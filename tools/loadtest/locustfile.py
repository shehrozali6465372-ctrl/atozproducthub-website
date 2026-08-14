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
