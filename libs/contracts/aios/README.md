# AI OS Bridge contracts (`libs/contracts/aios/`)

Versioned JSON Schemas for the **only** AI OS communication surface
(API Contracts §12). These schemas are validated by the AI OS Bridge client
before any request leaves the business layer and by bridge receivers before
any AI OS payload is accepted.

## Files

| Contract | File | Direction |
|----------|------|-----------|
| `AIOS.Content.Intake` | `content-intake.schema.json` | AI OS → Website |
| `AIOS.Job.Request` | `job-request.schema.json` | Website → AI OS |
| `AIOS.Job.Status` | `job-status.schema.json` | AI OS → Website (webhook) |
| `AIOS.SEO.Metadata` | `seo-metadata.schema.json` | AI OS → Website |
| `AIOS.Pinterest.Assets` | `pinterest-assets.schema.json` | AI OS → Website |
| `AIOS.Analytics.Insights` | `analytics-insights.schema.json` | AI OS → Website |
| `AIOS.Heartbeat` | `heartbeat.schema.json` | AI OS ↔ Website |

## Rules

- All contracts are `v1` at freeze; new fields are additive, breaking changes
  require a new version file and an ADR.
- The Bridge validates every message against its schema; invalid messages are
  rejected with `VALIDATION_FAILED` and never forwarded.
- These files carry **no business intelligence** — only message shapes.
