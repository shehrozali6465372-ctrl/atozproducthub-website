# automation-service — schema migrations

Alembic environment for `automation_db` with its own version table
(`alembic_version_automation`) so the stream coexists with content,
affiliate, pinterest, seo, analytics, and admin streams on the same
physical database (M5 fix).

**Ownership (ADR-0010):** this stream creates `automation_niches`,
`automation_rules`, `automation_runs`, and `aios_job_records` only. The
Platform tables `scheduled_jobs`, `job_runs`, and `queue_items` are created
by the admin-service stream (ADR-0009) and are never re-created here.
