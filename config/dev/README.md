# dev

Non-secret environment settings for `dev`. See `env.template`.

- Secrets are never committed; use Vault (`infra/secrets/`) or the deploy pipeline.
- Phase 3 (M3) ships the templates; deployments consume them from Phase 13 onward.
