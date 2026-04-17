# M4-07 / M4-08 — Profiles backend with re-auth rules and profiles page

## Backend
- `GET /ops/profiles`
- exposes active profile, normalized profile list, and per-profile `requires_reauth`

## UI
- `GET /profiles`
- dedicated Profiles Page with list + detail drill-down

## Notes
This milestone makes re-auth posture inspectable to the operator before any higher-risk profile switching workflow is implemented.
