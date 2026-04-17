# Hermes Command Center — Official Backlog Alignment

Source of truth: `Hermes Command Center — GitHub Backlog v2.pdf`
Canonical file used for extraction during this audit:
`/home/danilo/.hermes/cache/documents/doc_df9f36debcb3_Hermes Command Center — GitHub Backlog v2.pdf`

Status legend:
- DONE = materially implemented/documented already
- PARTIAL = started, but not yet aligned to official backlog acceptance criteria
- NOT STARTED = not meaningfully implemented yet
- DIVERGENT = work happened, but outside the official sequence or with behavior differing from the official backlog/defaults

Important correction:
The work done so far is not the official plan itself. The official roadmap is M0→M5 from the backlog PDF. Some implementation completed so far overlaps official backlog items, but some of it happened out of order and in one notable place diverged from the official default posture.

## High-level milestone status

- M0 — Foundation, Threat Model, and Performance Budgets: DONE (with one explicit accepted Tailscale auth exception recorded in docs)
- M1 — Secure Skeleton, Contracts, and Event Bus: DONE (with accepted Tailscale/trusted-tailnet auth exception)
- M2 — Dashboard, Chat MVP, and Approval-Safe Operation: PARTIAL (some dashboard/operator surface work landed early)
- M3 — Operator Control Plane and Cost Governance: PARTIAL (some cron/process controls landed early)
- M4 — Hermes Knowledge and Configuration Surfaces: NOT STARTED
- M5 — Hardening, Resilience, and 1.0 Release Readiness: NOT STARTED

## Official milestone/issue checklist

### M0 — Foundation, Threat Model, and Performance Budgets

- M0-01 Repository baseline and protections: DONE
  - Repo exists at `Incavenuziano/hermes-command-center`
  - `main` is published and protected with PR review requirement + conversation resolution
  - label taxonomy from the official backlog has been created
  - governance/security files exist locally and are pushed (`README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`, issue templates, PR template, `LICENSE`)
  - vulnerability alerts and automated security fixes were enabled via API
  - secret scanning and push protection are enabled for the public repo

- M0-02 Local project skeleton: DONE
  - `backend/`, `frontend/`, `docs/`, `tests/`, `scripts/`, `.github/` exist

- M0-03 System prerequisites and Hermes runtime assumptions: DONE
  - `docs/setup/system-verification.md` exists

- M0-04 Product vision and scope boundaries: DONE
  - `docs/product-vision.md` exists

- M0-05 Security baseline: DONE WITH ACCEPTED EXCEPTION
  - `docs/security/baseline.md` exists
  - exception recorded in `docs/security/m0-05-tailscale-exception.md`
  - divergence retained intentionally for the current Tailscale-exposed single-user runtime: trusted-local/no-login mode by explicit operator request

- M0-06 Token-efficiency / low-idle-cost rules: DONE
  - `docs/architecture/token-efficiency.md` exists

- M0-07 Initial ADRs / base strategy: DONE
  - present: `docs/architecture/adr-0001-base-strategy.md`
  - present: `docs/architecture/adr-0002-thin-control-plane.md`
  - present: `docs/architecture/adr-0003-event-transport.md`
  - present: `docs/architecture/adr-0004-contract-versioning.md`
  - present: `docs/architecture/adr-0005-secret-storage.md`

- M0-08 CI baseline quality gates: DONE
  - `.github/workflows/ci.yml` exists and runs backend tests, py_compile checks, and the Phase 0 verification script
  - the same checks were re-run locally and passed during this audit

- M0-09 Initial threat model: DONE
  - `docs/security/threat-model.md` exists

- M0-10 Supply-chain policy and SBOM plan: DONE
  - `docs/security/supply-chain.md` exists

- M0-11 Performance and resource budgets: DONE
  - `docs/architecture/performance-budgets.md` exists

### M1 — Secure Skeleton, Contracts, and Event Bus

- M1-01 Final frontend strategy: DONE
  - decision recorded in `docs/architecture/frontend-strategy.md`
  - minimal/no-build frontend selected with concrete tradeoff analysis against React/TypeScript and lightweight alternatives

- M1-02 Backend application skeleton/config/SQLite setup: DONE
  - backend skeleton, config, stdlib HTTP, routes, tests, and use of Hermes SQLite runtime source are in place

- M1-03 Authentication and secure session lifecycle: DONE WITH ACCEPTED EXCEPTION
  - cookie/session auth exists for explicit local-password mode
  - trusted-local bypass remains available by explicit operator request for the current Tailscale single-user runtime
  - non-loopback trusted-local startup now requires explicit `HCC_TRUST_TAILNET_ONLY=1`, and the exception is codified in `docs/security/m1-auth-posture-exception.md`

- M1-04 Browser hardening and CSRF protection: DONE
  - security headers now applied to JSON and static frontend responses
  - CSP, nosniff, frame denial, referrer policy, and permissions policy are documented in `docs/security/browser-hardening.md`
  - explicit-auth CSRF protections remain enforced, with trusted-local bypass limited to the accepted tailnet exception

- M1-05 Canonical backend contracts for core surfaces: DONE
  - canonical JSON success/error envelope and request-id semantics are documented in `docs/architecture/backend-contracts.md`
  - core JSON surfaces are normalized on the shared `send_data` / `send_error_envelope` contract
  - SSE core surface now emits `contract.meta` and shares contract/version/request-id semantics

- M1-06 Hermes adapter layer for read-only summaries with degraded mode: DONE
  - `backend/runtime_adapter.py` reads real Hermes sessions/processes/cron state

- M1-07 Minimal frontend shell with auth gate / accessible layout: DONE WITH ACCEPTED EXCEPTION
  - frontend shell exists and is expanded
  - auth gate remains bypassed only under the explicit trusted-tailnet single-user exception documented in `docs/security/m1-auth-posture-exception.md`

- M1-08 Health and smoke tests: DONE
  - health routes and test coverage exist

- M1-09 Secret storage strategy: DONE
  - implementation shipped in `backend/secrets_store.py`
  - resolution order now supports env override, optional OS keyring, and explicit plaintext fallback with `0600` permissions
  - `/system/info` exposes only redacted backend summaries, and setup/degraded behavior is documented in `docs/security/secret-storage.md`

- M1-10 WebAuthn/passkey optional second factor: DONE
  - optional passkey/WebAuthn backend shipped in `backend/passkeys.py` and `backend/routes/passkeys.py`
  - status, registration, and authentication ceremony endpoints are available under `/auth/passkeys/*`
  - current defaults, constraints, and security posture are documented in `docs/security/passkeys.md`

- M1-11 Append-only operator audit log: DONE
  - SQLite-backed append-only audit log implemented in `backend/audit_log.py`
  - destructive operator actions now append immutable records and expose them via `GET /ops/audit`
  - tests cover append/read behavior and SQLite-level tamper resistance triggers

- M1-12 Unified multiplexed SSE event bus: DONE
  - unified SSE stream implemented at `GET /ops/stream`
  - SQLite-backed event bus implemented in `backend/event_bus.py` with integer event IDs and replay via `Last-Event-ID`
  - health snapshot, operational events, and audit events now share one stream contract documented in `docs/architecture/sse-event-bus.md`

- M1-13 Schema migration framework: DONE
  - explicit migration manager shipped in `backend/migrations.py`
  - startup now applies Command Center-owned SQLite migrations before serving
  - migration behavior and operator expectations documented in `docs/architecture/schema-migrations.md`

- M1-14 Error taxonomy and standard error envelope: DONE
  - standard error envelope and error codes are already implemented

### M2 — Dashboard, Chat MVP, and Approval-Safe Operation

- M2-01 Zero-token dashboard data service: DONE / PARTIAL
  - dashboard data surfaces are zero-token and runtime-backed
  - may still need closer alignment with official M2 acceptance criteria

- M2-02 Dashboard page with health/agents/cron/approvals/recent events: DONE
  - dashboard page renders agents, sessions, processes, cron jobs, approvals, recent events, session detail, and chat transcript
  - explicit system health panel now consumes `/system/info` and `/health`
  - dashboard scope documented in `docs/architecture/dashboard-scope.md`

- M2-03 Sessions and session list API: DONE
  - overview and session detail exist

- M2-04 Hermes-native chat streaming route and protocol: DONE
  - backend transcript normalization implemented in `backend/chat_protocol.py`
  - routes added in `backend/routes/chat.py`:
    - `GET /ops/chat/transcript?session_id=...`
    - `GET /ops/chat/stream?session_id=...&after_id=...`
  - protocol documented in `docs/architecture/chat-streaming-protocol.md`
  - transcript route reads real Hermes session files under `~/.hermes/sessions/session_<session_id>.json`
  - SSE stream emits `contract.meta`, `chat.session`, `chat.message`, and heartbeat with cursor support via `after_id` / `Last-Event-ID`

- M2-05 Approval and clarify queue backend: DONE
  - backend queue implemented in `backend/approvals.py` with routes in `backend/routes/approvals.py`
  - approval lifecycle persists locally and emits `approval.created` / `approval.resolved` events
  - contract and persistence are documented in `docs/architecture/approvals-backend.md`

- M2-06 Approvals page and global pending-approvals tray: DONE
  - approvals panel is integrated into the dashboard frontend and resolves queued items through `frontend/app.js`
  - pending approvals summary and quick-decision controls are shipped in the current minimal frontend
  - UI scope is documented in `docs/architecture/approvals-ui.md`

- M2-07 Sessions/chat UI with streaming and transcript handling: DONE
  - dashboard now includes a real `Chat Transcript` panel in `frontend/index.html`
  - frontend transcript/stream handling implemented in `frontend/app.js`
  - transcript cards render normalized messages, tool calls, and tool results
  - UI scope documented in `docs/architecture/sessions-chat-ui.md`

- M2-08 Agents page MVP with multi-agent summaries/quick actions: DONE
  - dedicated `/agents` shell route added in `backend/routes/frontend.py`
  - agents page renders runtime-backed agent summaries and quick actions in `frontend/app.js`
  - UI scope documented in `docs/architecture/agents-page-mvp.md`

- M2-09 Regression tests for dashboard/chat/approvals/stream: DONE
  - `tests/test_command_center_features.py` now covers frontend shell assets, approvals UI/backend, chat transcript+stream, agents page route, and unified stream behavior
  - regression coverage is exercised in the full `python -m pytest tests/ -q` suite

### M3 — Operator Control Plane and Cost Governance

- M3-01 Cost circuit breaker and per-agent telemetry: DONE
  - `GET /ops/costs` exposes runtime-derived totals and per-agent telemetry
  - `POST /ops/costs/circuit-breaker` persists breaker thresholds and evaluates tripped state
  - implementation/documentation live in `backend/routes/costs.py`, `backend/cost_controls.py`, and `docs/architecture/cost-governance.md`

- M3-02 Panic stop global control: DONE
  - `POST /ops/panic-stop` kills running processes and pauses enabled cron jobs
  - panic stop emits derived-state events and append-only audit records
  - behavior documented in `docs/architecture/cost-governance.md`

- M3-03 Read-only mode: DONE
  - persistent read-only state implemented in `backend/read_only_mode.py`
  - `GET/POST /ops/read-only` expose and update mode state
  - mutating operator routes now return `423 ops.read_only_mode` when the mode is enabled
  - behavior documented in `docs/architecture/read-only-mode.md`

- M3-04 Cron backend routes and normalized contracts: DONE
  - explicit cron routes now exist for list/detail/history in `backend/routes/operations.py`
  - cron action history persists in `backend/cron_history.py`
  - backend contract documented in `docs/architecture/cron-backend-contracts.md`

- M3-05 Cron page with run history/output inspection/guarded actions: DONE
  - dedicated `/cron` route added in `backend/routes/frontend.py`
  - frontend cron page consumes normalized cron jobs/history routes and exposes guarded actions
  - UI scope documented in `docs/architecture/cron-page-ui.md`

- M3-06 Runs/activity timeline backend with retention and derived state: DONE
  - `GET /ops/activity` now exposes a filtered/limited derived-state timeline backend
  - `GET /ops/events` shares the same filtering contract and retention metadata
  - retention/documentation recorded in `docs/architecture/activity-timeline-backend.md`

- M3-07 Runs/activity UI page with virtualization/drill-down: DONE
  - dedicated `/activity` route added in `backend/routes/frontend.py`
  - frontend activity page renders a bounded timeline window from `GET /ops/activity`
  - drill-down panel inspects normalized event payloads without leaving the page
  - UI scope documented in `docs/architecture/activity-page-ui.md`

- M3-08 Process registry backend and guarded background-task controls: DONE
  - explicit process registry routes now exist for list/detail/control in `backend/routes/operations.py`
  - process entries now expose background-task metadata such as `notify_on_complete` and `watch_patterns`
  - guarded control endpoint currently accepts only explicit supported actions and rejects unsupported ones with `ops.invalid_action`
  - backend scope documented in `docs/architecture/process-registry-backend.md`

- M3-09 Processes page before full terminal support: DONE
  - dedicated `/processes` route added in `backend/routes/frontend.py`
  - frontend processes page consumes the explicit process registry backend from M3-08
  - process detail drill-down and guarded kill action are available without exposing terminal features
  - UI scope documented in `docs/architecture/processes-page-ui.md`

- M3-10 Terminal strategy with explicit risk posture: NOT STARTED / PARTIAL doc-only
  - security docs mention posture, but no implemented terminal surface strategy for Command Center

### M4 — Hermes Knowledge and Configuration Surfaces

- M4-01 Memory backend routes and summaries: NOT STARTED
- M4-02 Memory page: NOT STARTED
- M4-03 Skills backend routes and metadata views: NOT STARTED
- M4-04 Skills browser UI: NOT STARTED
- M4-05 Safe files/workspace backend: NOT STARTED
- M4-06 Files/workspace browser UI: NOT STARTED
- M4-07 Profiles backend with re-auth rules: NOT STARTED
- M4-08 Profiles page: NOT STARTED
- M4-09 Gateway/channels backend status views with redaction: NOT STARTED
- M4-10 Channels/gateway UI page: NOT STARTED

### M5 — Hardening, Resilience, and 1.0 Release Readiness

- M5-01 Final security audit and regression gate: NOT STARTED
- M5-02 Performance budget validation/optimization: NOT STARTED
- M5-03 Backup/export/restore for Command Center state: NOT STARTED
- M5-04 Load and stress smoke tests: NOT STARTED
- M5-05 Deployment/operator/incident/troubleshooting docs: NOT STARTED / PARTIAL docs-only
- M5-06 1.0 release checklist/demo/release hygiene: NOT STARTED

## What is actually done today in practical terms

Implemented already:
- local repo skeleton and docs foundation
- system verification docs
- product vision/security/threat model/supply-chain/performance docs
- backend stdlib HTTP skeleton
- health/ready/system routes
- contract versioning and standard error envelopes
- trusted-local + optional explicit auth cookie flow
- CSRF on explicit-auth mutating routes
- runtime adapter reading real Hermes runtime state
- dashboard/overview with real sessions/processes/cron jobs
- session detail route
- minimal process kill and cron pause/resume/run controls
- persisted event feed/read model
- working UI exposed over Tailscale
- automated tests currently passing locally

## Divergences that should be corrected or explicitly accepted

1. Auth posture divergence
- Official backlog/security baseline direction: auth required for non-loopback exposure
- Current runtime: no-login trusted-local mode exposed on Tailscale by explicit user request
- This is a conscious deviation and should be tracked as such

2. Sequence divergence
- Some M2/M3-ish operator surface work landed before finishing official M1 items such as audit log, SSE bus, WebAuthn, approvals, and stronger auth posture

3. Event-feed vs audit-log gap
- Persisted events exist, but that is not yet a true append-only operator audit log

## Recommended realignment order from here

1. Finish remaining M1 security/control-plane foundations first:
- M1-11 append-only audit log
- M1-12 unified SSE event bus
- M1-09 actual secret-storage implementation
- revisit M1-03/M1-07 auth posture decision and document exception if keeping no-login-on-tailnet

2. Then resume M2 in official order:
- approvals backend + UI
- chat streaming protocol + UI
- dedicated dashboard completion

3. Then continue M3 with cost governance and panic-stop before expanding more surface area
