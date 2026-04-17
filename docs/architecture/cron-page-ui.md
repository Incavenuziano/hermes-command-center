# M3-05 — Cron page with run history/output inspection/guarded actions

This milestone adds a dedicated cron-oriented UI entrypoint on top of the normalized cron backend routes delivered in M3-04.

## What shipped
- dedicated `/cron` route in the stdlib frontend
- shell navigation link to the cron page
- `Cron Page` section showing normalized cron jobs
- `Cron Run History` section backed by `GET /ops/cron/history`
- `Cron Output Inspection` panel for inspecting selected job + history payloads
- guarded quick actions still flow through existing protected mutators:
  - run
  - pause
  - resume

## Data sources
- `GET /ops/cron/jobs`
- `GET /ops/cron/history`
- existing `POST /ops/cron/control`

## Why this closes M3-05
The project now has a dedicated cron-focused operator page with explicit run-history and inspection affordances rather than only overview cards.
