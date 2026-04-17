# M1 Runtime Integration Plan

> For Hermes: use TDD on each slice; verify with targeted pytest, then full suite, then real curl against the running Tailscale instance.

Goal: turn Hermes Command Center from bootstrap/demo state into a real operator surface backed by Hermes runtime data and minimal operational controls.

Architecture:
- Add a runtime adapter layer in backend that reads Hermes live state from ~/.hermes (state.db, sessions/sessions.json, processes.json, cron/jobs.json).
- Keep stdlib HTTP routes thin; routes call adapter/read-model helpers.
- Persist the derived event/read model to .data so the Command Center survives restart with last known state and action events.

Planned M1 slices:
1. M1.1 Runtime-backed read model
   - Replace bootstrap-only overview with data derived from Hermes runtime sources.
   - Sessions from state.db + sessions/sessions.json
   - Processes from processes.json + PID liveness checks
   - Cron jobs from cron/jobs.json

2. M1.2 Detail/read routes
   - Add read routes for sessions, processes, cron jobs, and a single-session detail view.
   - Keep exact routes (no framework router); use query params where needed.

3. M1.3 Minimal operator actions
   - Kill a tracked background process by process_id.
   - Pause/resume/run cron jobs by job_id.
   - Return action events into the event feed.

4. M1.4 Durable derived state
   - Persist event feed / last-known runtime snapshot under backend .data.
   - Reload on backend start so the UI retains recent operational history.

5. M1.5 Frontend expansion
   - Replace tiny overview with tables/cards for sessions, processes, cron jobs.
   - Add refresh + action buttons for kill/pause/resume/run.
   - Add a session detail panel.

Verification commands:
- python -m pytest tests/test_command_center_features.py -q
- python -m pytest tests/test_backend_app.py -q
- python -m pytest tests/ -q
- python -m py_compile backend/*.py backend/routes/*.py
- curl --noproxy '*' http://100.65.45.58:8788/ops/overview
