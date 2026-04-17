# Unified SSE Event Bus

This document records the M1-12 event-stream contract for Hermes Command Center.

## Endpoint
- `GET /ops/stream`

## Authentication
- follows the same operator auth posture as other `/ops/*` routes
- in the current trusted-local Tailscale posture, the route is reachable without a login cookie because the runtime resolves to the trusted local operator session

## Transport
- content type: `text/event-stream; charset=utf-8`
- cache policy: `no-store`
- reconnect hint: `retry: 5000`
- heartbeat frame: `: heartbeat`

## Replay / reconnect
- clients may send `Last-Event-ID: <integer>`
- clients may also use `?after_id=<integer>` for manual inspection/debugging
- the server replays only events with `event_id > Last-Event-ID`

## Stream contents
One stream multiplexes:
- `health.snapshot`
- operational/runtime events persisted from `derived_state_store.ingest_event(...)`
- audit events emitted when append-only operator audit records are written

## Event envelope
Each persisted event frame uses:
- `id: <event_id>`
- `event: <event_type>`
- `data: <json>`

JSON payload shape:
```json
{
  "source": "command-center",
  "channel": "ops",
  "recorded_at": "2026-04-16T23:59:59Z",
  "payload": {}
}
```

`health.snapshot` is emitted first on connect and includes a lightweight service/counts summary.

## Current implementation notes
- persistence: `backend/event_bus.py` using SQLite under `.data/event-bus.sqlite3`
- route: `backend/routes/events.py`
- current stream response is finite per request: snapshot + replay buffer + heartbeat, then close
- this is sufficient for reconnect-safe MVP semantics while keeping idle cost and complexity low
