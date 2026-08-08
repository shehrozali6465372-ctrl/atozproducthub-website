# Alembic migration template (per-service convention)

Every service owns its schema: `services/<service>/db/migrations/` holds that
service's Alembic environment. Copy `env.py.template` below into a new
service and wire `config` to the service settings.

## Convention

- One migration directory per service (no shared migration history).
- Migration files: `db/migrations/versions/<snake_case>.py`.
- `env.py` reads the database URL from the service settings
  (`DATABASE_URL`), never from committed config.
- Phase 4 (Database Implementation) adds the first real revision per
  service; M3 ships the environment template only.
