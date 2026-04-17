# M3-09 — Processes page before full terminal support

This milestone adds a dedicated processes page on top of the explicit process registry backend from M3-08.

## Route
- `GET /processes`

## UI scope
- dedicated `Processes Page` route in the minimal frontend shell
- process registry list backed by `GET /ops/processes`
- process detail drill-down panel for the selected registry item
- guarded kill action backed by `POST /ops/processes/control`

## Current operator posture
The page is intentionally limited to read/inspect plus the already-guarded kill action.
It does not expose terminal I/O, stdin, log streaming, or arbitrary process controls yet.
Those concerns remain deferred until the explicit terminal-risk milestone.

## Why this closes M3-09
The process surface is now promoted from a dashboard subsection to a dedicated operator page, while still keeping the interaction model narrow and consistent with the pre-terminal risk posture required by the official backlog.
