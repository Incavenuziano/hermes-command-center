# M3-03 — Read-only mode

This milestone adds a persistent operator-level read-only mode to the Command Center.

## Routes
- `GET /ops/read-only`
- `POST /ops/read-only`

## Current behavior
- read-only state persists under `.data/read-only-mode.json`
- when enabled, mutating operator routes now return `423 ops.read_only_mode`
- current guarded routes:
  - `POST /ops/processes/kill`
  - `POST /ops/cron/control`
  - `POST /ops/panic-stop`
- toggling read-only mode appends an audit entry (`ops.read_only`)

## Why this closes M3-03
The Command Center now has a real operator safety mode that preserves observability while blocking destructive or state-changing controls.

## Follow-on work
- extend guarding to future cron/process/files/terminal mutation routes automatically as those surfaces land
- surface read-only state prominently in the frontend during later M3 UI expansion
