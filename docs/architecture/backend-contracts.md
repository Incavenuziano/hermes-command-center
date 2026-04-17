# Canonical Backend Contracts

This document closes M1-05 for the currently shipped core backend surfaces.

## Contract version
- header: `X-Contract-Version`
- body meta: `meta.contract_version`
- current value: `2026-04-15`

## JSON success envelope
All core JSON routes return:
```json
{
  "data": {},
  "meta": {
    "request_id": "uuid",
    "contract_version": "2026-04-15"
  }
}
```

## JSON error envelope
All core JSON route failures return:
```json
{
  "error": {
    "code": "domain.error_code",
    "message": "Human-readable message",
    "details": {},
    "request_id": "uuid"
  },
  "meta": {
    "request_id": "uuid",
    "contract_version": "2026-04-15"
  }
}
```

## Core JSON surfaces covered
- `/health`
- `/ready`
- `/system/info`
- `/system/inspect`
- `/auth/login`
- `/auth/session`
- `/auth/logout`
- `/operators/me`
- `/runtime/events`
- `/ops/overview`
- `/ops/events`
- `/ops/audit`
- `/ops/session`
- `/ops/processes/kill`
- `/ops/cron/control`

## SSE surface
`GET /ops/stream` is the one non-JSON core surface.
It normalizes contract semantics via:
- `X-Contract-Version`
- `X-Request-ID`
- a first event named `contract.meta`

`contract.meta` payload:
```json
{
  "contract_version": "2026-04-15",
  "transport": "sse",
  "channel": "ops"
}
```

## Request identity
- every core surface returns `X-Request-ID`
- JSON routes mirror it into `meta.request_id`
- JSON error routes mirror it into `error.request_id`

## Security/header baseline
Core surfaces also carry the M1-04 browser/security headers.
