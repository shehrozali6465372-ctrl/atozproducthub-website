"""Domain events for the automation module (API Contracts §11).

The automation service publishes business events only — never AI OS data.
Event codes are the frozen ``automation:*`` family; downstream modules
(admin ops, analytics) may consume them once Step 2 wires the scheduler.

Conforms to the ``name.vN`` envelope convention (backend-core events).
"""

from atoz_backend_core.events.envelope import EventEnvelope, new_event_id


def _envelope(
    event_type: str, *, niche_id: str | None, aggregate_id: str, payload: dict
) -> EventEnvelope:
    return EventEnvelope(
        type=event_type,
        event_id=new_event_id(),
        payload={"niche_id": niche_id, **payload},
        aggregate_id=aggregate_id,
    )


def rule_enabled_event(*, niche_id: str | None, rule_id: str, code: str) -> EventEnvelope:
    return _envelope(
        "automation:rule-enabled.v1",
        niche_id=niche_id,
        aggregate_id=rule_id,
        payload={"code": code},
    )


def rule_disabled_event(*, niche_id: str | None, rule_id: str, code: str) -> EventEnvelope:
    return _envelope(
        "automation:rule-disabled.v1",
        niche_id=niche_id,
        aggregate_id=rule_id,
        payload={"code": code},
    )


def run_started_event(
    *, niche_id: str | None, rule_id: str, run_id: str, triggered_by: str | None
) -> EventEnvelope:
    return _envelope(
        "automation:run-started.v1",
        niche_id=niche_id,
        aggregate_id=run_id,
        payload={"rule_id": rule_id, "triggered_by": triggered_by},
    )


def run_succeeded_event(*, niche_id: str | None, run_id: str, summary: str | None) -> EventEnvelope:
    return _envelope(
        "automation:run-succeeded.v1",
        niche_id=niche_id,
        aggregate_id=run_id,
        payload={"summary": summary},
    )


def run_failed_event(*, niche_id: str | None, run_id: str, error: str | None) -> EventEnvelope:
    return _envelope(
        "automation:run-failed.v1",
        niche_id=niche_id,
        aggregate_id=run_id,
        payload={"error": error},
    )


def job_enqueued_event(
    *, niche_id: str | None, job_id: str, run_id: str, queue: str, run_at: str
) -> EventEnvelope:
    return _envelope(
        "automation:job-enqueued.v1",
        niche_id=niche_id,
        aggregate_id=run_id,
        payload={"job_id": job_id, "queue": queue, "run_at": run_at},
    )


def job_queued_event(
    *, niche_id: str | None, queue_item_id: str, payload_ref: str, queue: str
) -> EventEnvelope:
    return _envelope(
        "automation:job-queued.v1",
        niche_id=niche_id,
        aggregate_id=queue_item_id,
        payload={"payload_ref": payload_ref, "queue": queue},
    )


def aios_job_created_event(
    *, niche_id: str, job_id: str, contract: str, direction: str
) -> EventEnvelope:
    return _envelope(
        "automation:aios-job-created.v1",
        niche_id=niche_id,
        aggregate_id=job_id,
        payload={"contract": contract, "direction": direction},
    )


def job_started_event(*, niche_id: str | None, run_id: str, job_id: str) -> EventEnvelope:
    return _envelope(
        "automation:job-started.v1",
        niche_id=niche_id,
        aggregate_id=run_id,
        payload={"scheduled_job_id": job_id},
    )


def job_succeeded_event(
    *, niche_id: str | None, run_id: str, job_id: str, output_ref: str | None
) -> EventEnvelope:
    return _envelope(
        "automation:job-succeeded.v1",
        niche_id=niche_id,
        aggregate_id=run_id,
        payload={"scheduled_job_id": job_id, "output_ref": output_ref},
    )


def job_failed_event(
    *, niche_id: str | None, run_id: str, job_id: str, error: str | None
) -> EventEnvelope:
    return _envelope(
        "automation:job-failed.v1",
        niche_id=niche_id,
        aggregate_id=run_id,
        payload={"scheduled_job_id": job_id, "error": error},
    )


def job_retry_scheduled_event(
    *, niche_id: str | None, run_id: str, job_id: str, next_run_at: str, attempts: int
) -> EventEnvelope:
    return _envelope(
        "automation:job-retry-scheduled.v1",
        niche_id=niche_id,
        aggregate_id=run_id,
        payload={
            "scheduled_job_id": job_id,
            "next_run_at": next_run_at,
            "attempts": attempts,
        },
    )


def aios_job_succeeded_event(*, niche_id: str, job_id: str, contract: str) -> EventEnvelope:
    return _envelope(
        "automation:aios-job-succeeded.v1",
        niche_id=niche_id,
        aggregate_id=job_id,
        payload={"contract": contract},
    )


def aios_job_failed_event(
    *, niche_id: str, job_id: str, contract: str, error: str | None
) -> EventEnvelope:
    return _envelope(
        "automation:aios-job-failed.v1",
        niche_id=niche_id,
        aggregate_id=job_id,
        payload={"contract": contract, "error": error},
    )
