# M3-08 — Process registry backend and guarded background-task controls

This milestone promotes the existing runtime-backed process view into an explicit operator-facing backend surface with guarded controls.

## Routes
- `GET /ops/processes`
- `GET /ops/processes/proc-live-1`
- `POST /ops/processes/control`
- existing compatibility route retained: `POST /ops/processes/kill`

## Registry contract
Each process entry now exposes:
- `process_id`
- `pid`
- `command`
- `cwd`
- `task_id`
- `session_key`
- `notify_on_complete`
- `watch_patterns`
- `status`
- `started_at`
- `updated_at`

## Guarded controls
`POST /ops/processes/control` currently accepts only:
- `action: "kill"`

Any other process action is rejected with:
- HTTP `400`
- `code: ops.invalid_action`

This keeps the control plane explicit and narrow before broader terminal/stdin support exists.

## Audit and event behavior
Successful guarded controls:
- append immutable operator audit records
- emit `process.kill_requested` into the retained activity/event timeline

## Why this closes M3-08
The process surface is no longer only an overview fragment plus an ad hoc kill action. It is now a first-class registry backend with explicit contracts and a guarded action boundary suitable for the next dedicated processes page milestone.
