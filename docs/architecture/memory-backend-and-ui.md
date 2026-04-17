# M4-01 / M4-02 — Memory backend routes and memory page

## Backend
- `GET /ops/memory`
- source: `memory.json` under Hermes home
- aggregates `memory` and `user` scopes into a single summary surface
- exposes per-scope counts and normalized item previews

## UI
- `GET /memory`
- dedicated Memory Page with list + detail drill-down

## Notes
This keeps the Command Center on inspect-first semantics: summaries are readable and explorable, but there is no direct memory mutation surface yet.
