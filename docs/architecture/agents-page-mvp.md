# M2-08 — Agents page MVP with multi-agent summaries/quick actions

This milestone adds a dedicated agents-facing surface to the stdlib frontend while reusing the existing runtime-backed overview data.

## What shipped
- dedicated `/agents` route serving the frontend shell
- explicit `Agents Page` section in the UI
- multi-agent summary cards sourced from `overview.data.agents`
- quick actions:
  - `Open Session` for a related active session
  - `Kill Process` for a running process

## Implementation notes
- route added in `backend/routes/frontend.py`
- rendering implemented in `frontend/app.js` via `renderAgentsPage(...)`
- navigation links added in the shell header so the page is discoverable
- MVP intentionally reuses existing overview/session/process surfaces instead of introducing a new backend contract

## Why this closes M2-08
The backlog called for an agents page MVP with multi-agent summaries and quick actions. The frontend now exposes a dedicated agents-oriented entry point and actionable controls without waiting for a richer multi-route SPA.
