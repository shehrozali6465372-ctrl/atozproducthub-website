"""Domain events emitted by the admin-service (Task 19 §4, §5).

The audit trail is the primary record; these events let automation and
notification consumers react without touching the ledger. No AI concepts.
"""

from atoz_backend_core.events.envelope import EventEnvelope


def audit_recorded_event(
    *, action: str, entity_type: str, entity_id: str, niche_id: str | None, actor: str | None
) -> EventEnvelope:
    """``admin:audit-recorded.v1`` — emitted after an audit row is appended."""
    return EventEnvelope(
        type="admin:audit-recorded.v1",
        event_id=f"{entity_type}:{entity_id}:{action}",
        payload={
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "niche_id": niche_id,
            "actor": actor,
        },
        aggregate_id=entity_id,
    )


def operation_recorded_event(
    *, operation: str, entity_type: str, entity_id: str, niche_id: str | None, status: str
) -> EventEnvelope:
    """``admin:operation-recorded.v1`` — emitted after an operation log row."""
    return EventEnvelope(
        type="admin:operation-recorded.v1",
        event_id=f"{operation}:{entity_id}",
        payload={
            "operation": operation,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "niche_id": niche_id,
            "status": status,
        },
        aggregate_id=entity_id,
    )
