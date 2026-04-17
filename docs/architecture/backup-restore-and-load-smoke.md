# M5-03 / M5-04 — Backup, restore, and load smoke routes

## Routes
- `POST /ops/state/export`
- `POST /ops/state/restore`
- `GET /ops/load-smoke`

## Scope
- export selected Command Center/Hermes state into a reproducible bundle directory
- restore from an explicit export path
- expose a lightweight repeatable load-smoke summary route for release validation

## Why this closes M5-03 and M5-04
Operational resilience now includes recoverability and repeatable smoke validation as first-class backend features.
