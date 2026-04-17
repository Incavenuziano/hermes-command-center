# M3-04 — Cron backend routes and normalized contracts

This milestone promotes cron data from an overview-only surface into explicit backend contracts.

## Routes
- `GET /ops/cron/jobs`
- `GET /ops/cron/jobs/cron-live-1`
- `GET /ops/cron/history?job_id=...`
- existing mutator retained:
  - `POST /ops/cron/control`

## Current normalized surfaces
### Jobs list
Returns:
- `items[]`
- `count`

### Job detail
Returns:
- `job`

### History
Returns:
- `job_id`
- `items[]`
- `count`

## Persistence
- cron action history now persists under `.data/cron-history.json`
- every `POST /ops/cron/control` appends a normalized history record

## Why this closes M3-04
Cron backend routes are now explicit, separately queryable, and contract-normalized rather than being available only through overview cards and a mutating control endpoint.
