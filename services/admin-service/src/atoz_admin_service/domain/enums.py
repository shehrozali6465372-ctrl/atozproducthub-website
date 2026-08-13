"""Enums for the admin & operations layer (Task 19 §1, §4, §5).

Mirrors Database Blueprint §5.17–§5.26 states and the frozen event codes
(12-api-contracts.md §8). No AI concepts exist here.
"""

from enum import StrEnum


class AdminUserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class PermissionScope(StrEnum):
    GLOBAL = "global"
    NICHE = "niche"
    ACCOUNT = "account"


class AuditAction(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ASSIGN = "assign"
    REVOKE = "revoke"
    LOGIN = "login"
    LOGOUT = "logout"
    ENABLE = "enable"
    DISABLE = "disable"
    RETRY = "retry"
    EXPORT = "export"
    SETTINGS_CHANGE = "settings.change"
    APPROVE = "approve"
    REJECT = "reject"


class EntityType(StrEnum):
    ADMIN_USER = "admin_user"
    ROLE = "role"
    PERMISSION = "permission"
    API_KEY = "api_key"
    PREFERENCE = "preference"
    AUDIT_LOG = "audit_log"
    NOTIFICATION = "notification"
    QUEUE_ITEM = "queue_item"
    WEBHOOK_LOG = "webhook_log"
    OPERATION_LOG = "operation_log"
    SCHEDULED_JOB = "scheduled_job"
    JOB_RUN = "job_run"
    NICHE = "niche"
    SETTING = "setting"


class QueueState(StrEnum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    DONE = "done"
    FAILED = "failed"


class JobRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WebhookStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"
    FAILED = "failed"
    IGNORED = "ignored"


class OperationStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class NotificationStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
    ACTIONED = "actioned"


class NotificationType(StrEnum):
    APPROVAL_REQUEST = "approval.request"
    FAILURE = "failure"
    REPORT_READY = "report.ready"
    SYSTEM = "system"


# Internal domain event types consumed by the webhook (API Contracts §8).
DOMAIN_EVENT_TO_OPERATION: dict[str, str] = {
    "content:published.v1": "content.publish",
    "content:updated.v1": "content.update",
    "content:unpublished.v1": "content.unpublish",
    "pin:published.v1": "pinterest.pin_publish",
    "pin:failed.v1": "pinterest.pin_failed",
    "product:ingested.v1": "affiliate.product_ingest",
    "product:removed.v1": "affiliate.product_remove",
    "affiliate:click.v1": "affiliate.click",
    "revenue:attributed.v1": "affiliate.revenue_attributed",
    "seo:sitemap-rebuilt.v1": "seo.sitemap_rebuilt",
    "analytics:rollup-completed.v1": "analytics.rollup",
}
