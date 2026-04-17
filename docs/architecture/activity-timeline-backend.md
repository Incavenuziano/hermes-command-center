# M3-06 — Runs/activity timeline backend with retention and derived state

This milestone exposes the existing persisted derived-event feed as an explicit activity timeline backend.

## Routes
- `GET /ops/activity`
- `GET /ops/events` (now supports the same filtering/limit contract)

## Supported query parameters
- `limit`
- `kind_prefix`

## Contract additions
- `retention.max_items`

## Retention
- current retained event count: 100 items
- retention metadata is returned with timeline responses so the UI can explain truncation behavior

## Why this closes M3-06
The activity timeline is now an explicit backend surface with retention semantics and filtering, rather than just an implicit recent-events helper.
