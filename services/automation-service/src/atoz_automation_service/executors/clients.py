"""Service-to-service HTTP clients used by the executors.

The automation service is the orchestration layer: executors call the
owning sibling services' admin APIs with a short-lived service-account JWT
minted against each sibling's configured secret (production via Vault).
Tenancy is enforced by forwarding the item's ``niche_id`` as the
``X-Niche-Id`` header so sibling services apply their own server-side
isolation — no cross-niche leakage.

Notifications are best-effort: they never block or fail an execution, and
each outcome is notified at most once (no infinite notification retry).
"""

import logging
from typing import Any

import httpx

from atoz_automation_service.config import Settings
from atoz_backend_core.auth import create_access_token

logger = logging.getLogger("atoz.automation.executors.clients")


class SiblingRequestError(RuntimeError):
    """Sibling service returned an error status or was unreachable."""


class SiblingClients:
    """Typed HTTP clients for the sibling services (base URL + JWT)."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport
        self._clients: dict[str, httpx.AsyncClient] = {}

    def _endpoint(self, service: str) -> tuple[str, str, str]:
        """Return ``(base_url, jwt_secret, write_permission)`` for a service."""
        table: dict[str, tuple[str, str, str]] = {
            "admin": (
                self._settings.admin_base_url,
                self._settings.admin_jwt_secret,
                self._settings.admin_write_permission,
            ),
            "pinterest": (
                self._settings.pinterest_base_url,
                self._settings.pinterest_jwt_secret,
                self._settings.pinterest_write_permission,
            ),
            "seo": (
                self._settings.seo_base_url,
                self._settings.seo_jwt_secret,
                self._settings.seo_write_permission,
            ),
            "affiliate": (
                self._settings.affiliate_base_url,
                self._settings.affiliate_jwt_secret,
                self._settings.affiliate_write_permission,
            ),
            "analytics": (
                self._settings.analytics_base_url,
                self._settings.analytics_jwt_secret,
                self._settings.analytics_write_permission,
            ),
            "aios-bridge": (
                self._settings.aios_bridge_base_url,
                "",
                "",
            ),
        }
        try:
            return table[service]
        except KeyError as exc:
            raise ValueError(f"Unknown sibling service: {service!r}.") from exc

    def _client(self, service: str, base_url: str) -> httpx.AsyncClient:
        client = self._clients.get(service)
        if client is None:
            client = httpx.AsyncClient(
                base_url=base_url.rstrip("/"),
                timeout=self._settings.executor_timeout_seconds,
                transport=self._transport,
            )
            self._clients[service] = client
        return client

    def service_token(self, service: str) -> str | None:
        """Mint a service-account access token for a sibling (JWT RBAC)."""
        _base, secret, permission = self._endpoint(service)
        if not secret:
            return None
        return create_access_token(
            secret=secret,
            subject="automation-service",
            session_id=f"svc:{service}",
            permissions=(permission,),
        )

    async def request(
        self,
        service: str,
        method: str,
        path: str,
        *,
        niche_id: str | None = None,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Send an authenticated request to a sibling service."""
        base_url, _secret, _perm = self._endpoint(service)
        token = self.service_token(service)
        request_headers: dict[str, str] = {"Accept": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if niche_id:
            request_headers["X-Niche-Id"] = niche_id
        if headers:
            request_headers.update(headers)
        try:
            response = await self._client(service, base_url).request(
                method,
                path,
                headers=request_headers,
                json=payload,
                params=params,
            )
        except httpx.HTTPError as exc:
            raise SiblingRequestError(f"{service} unreachable: {exc}") from exc
        if response.status_code >= 400:
            detail = _error_detail(response)
            raise SiblingRequestError(
                f"{service} {method} {path} -> {response.status_code}: {detail}"
            )
        if response.status_code == 204 or not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    async def aclose(self) -> None:
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()


def _error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict):
            return str(body.get("detail") or body.get("title") or body)
        return str(body)
    except ValueError:
        return response.text[:300]


async def send_notification(
    siblings: SiblingClients,
    settings: Settings,
    *,
    kind: str,
    title: str,
    body: str = "",
    niche_id: str | None = None,
    action_ref: str | None = None,
    recipient_id: str | None = None,
) -> bool:
    """Best-effort notification via admin-service (at most once per outcome).

    Returns ``True`` when delivered, ``False`` when skipped (no recipient)
    or failed (logged, never raises — execution is not blocked by
    notification delivery).
    """
    recipient = recipient_id or settings.default_notification_recipient_id
    if not recipient:
        return False
    headers: dict[str, str] = {}
    if settings.admin_internal_token:
        headers["X-Internal-Token"] = settings.admin_internal_token
    try:
        await siblings.request(
            "admin",
            "POST",
            "/api/v1/admin/internal/notifications",
            niche_id=niche_id,
            headers=headers,
            payload={
                "recipient_id": recipient,
                "type": f"automation.{kind}",
                "title": title,
                "body": body,
                "niche_id": niche_id,
                "action_ref": action_ref,
            },
        )
        return True
    except Exception as exc:  # noqa: BLE001 — best-effort by contract
        logger.warning("notification skipped (%s): %s", kind, exc)
        return False
