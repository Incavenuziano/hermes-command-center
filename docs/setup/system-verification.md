# System Verification

Status: verified
Verified at: 2026-04-16 07:37:49 UTC
Verification scope: local WSL development/runtime baseline for Phase 0 / M0 foundation

## Host and runtime snapshot

- Host runtime: WSL2 on Windows host
- Kernel: Linux 6.6.87.2-microsoft-standard-WSL2 x86_64 GNU/Linux
- Python: 3.11.15
- Node: v22.22.0
- npm: 10.9.4
- SQLite: 3.50.4
- Git: git version 2.43.0

## Local security assumptions observed

- Running as root: no (`uid=1000`, user `danilo`)
- Default shell umask at verification time: `0002`
- Loopback port 8787: closed before manual startup
- Wildcard port 8787: closed before manual startup
- Current backend startup guardrails in code:
  - refuse root unless `HCC_ALLOW_ROOT=1`
  - refuse non-loopback bind unless `HCC_ALLOW_NON_LOOPBACK=1`
  - reject invalid `HCC_PORT` values outside `1..65535`

## Repository verification notes

- Backend stdlib HTTP skeleton exists and has automated tests under `tests/test_backend_app.py`
- Default operator mode is now trusted-local without mandatory login (`HCC_AUTH_ENABLED=0` by default)
- Cookie-based session login still exists as an optional path when explicit auth is enabled
- Runtime bootstrap now enforces restrictive process posture via `umask 077`
- Derived-state read APIs now exist for overview/event-feed surfaces
- Runtime-backed operator surfaces now read real Hermes sessions/processes/cron jobs from `~/.hermes`
- Minimal operator actions now exist for process termination and cron pause/resume/run requests
- A frontend shell is now served locally from `/` using static assets under `frontend/`
- Runtime event ingest is available through authenticated `POST /runtime/events`
- Event/read-model history is persisted locally under `.data/derived_state.json`
- Architecture/security/product baseline docs exist in `docs/`
- CI baseline is expected to run pytest, syntax compilation, and Phase 0 foundation verification

## Follow-up gaps still open after this verification

- Derived state is still in-memory only; durable local persistence is not implemented yet
- Event transport is still a minimal authenticated HTTP ingest path, not a richer stream/subscription system yet
- Secret storage implementation remains an ADR/baseline decision, not a shipped subsystem yet
