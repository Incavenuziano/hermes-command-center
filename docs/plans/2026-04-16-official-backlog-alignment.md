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

- M0 — Foundation, Threat Model, and Performance Budgets: PARTIAL
- M1 — Secure Skeleton, Contracts, and Event Bus: PARTIAL
- M2 — Dashboard, Chat MVP, and Approval-Safe Operation: PARTIAL (some dashboard/operator surface work landed early)
- M3 — Operator Control Plane and Cost Governance: PARTIAL (some cron/process controls landed early)
- M4 — Hermes Knowledge and Configuration Surfaces: NOT STARTED
- M5 — Hardening, Resilience, and 1.0 Release Readiness: NOT STARTED

## Official milestone/issue checklist

### M0 — Foundation, Threat Model, and Performance Budgets

- M0-01 Repository baseline and protections: PARTIAL
  - Repo content and governance files exist locally (`README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS`)
  - GitHub-side settings like branch protection / labels / Dependabot were not verified from the local repo alone

- M0-02 Local project skeleton: DONE
  - `backend/`, `frontend/`, `docs/`, `tests/`, `scripts/`, `.github/` exist

- M0-03 System prerequisites and Hermes runtime assumptions: DONE
  - `docs/setup/system-verification.md` exists

- M0-04 Product vision and scope boundaries: DONE
  - `docs/product-vision.md` exists

- M0-05 Security baseline: PARTIAL + DIVERGENT
  - `docs/security/baseline.md` exists
  - divergence: official backlog says auth required for non-loopback exposure; current running app was intentionally changed to trusted-local/no-login by default for the Tailscale-exposed instance

- M0-06 Token-efficiency / low-idle-cost rules: DONE
  - `docs/architecture/token-efficiency.md` exists

- M0-07 Initial ADRs / base strategy: DONE
  - present: `docs/architecture/adr-0001-base-strategy.md`
  - present: `docs/architecture/adr-0002-thin-control-plane.md`
  - present: `docs/architecture/adr-0003-event-transport.md`
  - present: `docs/architecture/adr-0004-contract-versioning.md`
  - present: `docs/architecture/adr-0005-secret-storage.md`

- M0-08 CI baseline quality gates: PARTIAL
  - repository layout suggests CI baseline exists, but GitHub workflow coverage/behavior was not fully audited here

- M0-09 Initial threat model: DONE
  - `docs/security/threat-model.md` exists

- M0-10 Supply-chain policy and SBOM plan: DONE
  - `docs/security/supply-chain.md` exists

- M0-11 Performance and resource budgets: DONE
  - `docs/architecture/performance-budgets.md` exists

### M1 — Secure Skeleton, Contracts, and Event Bus

- M1-01 Final frontend strategy: PARTIAL
  - frontend exists and is working, but I have not yet verified that the explicit strategy decision doc matches the official issue intent

- M1-02 Backend application skeleton/config/SQLite setup: DONE
  - backend skeleton, config, stdlib HTTP, routes, tests, and use of Hermes SQLite runtime source are in place

- M1-03 Authentication and secure session lifecycle: PARTIAL + DIVERGENT
  - cookie/session auth exists
  - trusted-local bypass also exists and is currently the default
  - official M1 wording implies secure single-user auth lifecycle should be a central default; current runtime posture is looser because of the user-requested no-login mode

- M1-04 Browser hardening and CSRF protection: PARTIAL
  - CSRF exists for explicit-auth routes
  - broader browser hardening still needs full alignment to official issue scope

- M1-05 Canonical backend contracts for core surfaces: PARTIAL
  - standard data/error envelopes exist
  - contract versioning exists
  - likely still incomplete versus all official core surfaces

- M1-06 Hermes adapter layer for read-only summaries with degraded mode: DONE
  - `backend/runtime_adapter.py` reads real Hermes sessions/processes/cron state

- M1-07 Minimal frontend shell with auth gate / accessible layout: PARTIAL + DIVERGENT
  - frontend shell exists and is expanded
  - divergence: no auth gate in current default runtime posture

- M1-08 Health and smoke tests: DONE
  - health routes and test coverage exist

- M1-09 Secret storage strategy: PARTIAL
  - ADR exists (`adr-0005-secret-storage.md`)
  - shipped secret-storage subsystem not implemented

- M1-10 WebAuthn/passkey optional second factor: NOT STARTED

- M1-11 Append-only operator audit log: NOT STARTED
  - event feed exists, but this is not the same thing as an append-only audit log

- M1-12 Unified multiplexed SSE event bus: NOT STARTED
  - current implementation uses HTTP read surfaces and persisted events, not unified SSE

- M1-13 Schema migration framework: NOT STARTED / PARTIAL at best
  - no dedicated Command Center migration framework audited yet

- M1-14 Error taxonomy and standard error envelope: DONE
  - standard error envelope and error codes are already implemented

### M2 — Dashboard, Chat MVP, and Approval-Safe Operation

- M2-01 Zero-token dashboard data service: DONE / PARTIAL
  - dashboard data surfaces are zero-token and runtime-backed
  - may still need closer alignment with official M2 acceptance criteria

- M2-02 Dashboard page with health/agents/cron/approvals/recent events: PARTIAL
  - dashboard page exists with agents, sessions, processes, cron jobs, recent events
  - approvals surface is not implemented yet

- M2-03 Sessions and session list API: DONE
  - overview and session detail exist

- M2-04 Hermes-native chat streaming route and protocol: NOT STARTED

- M2-05 Approval and clarify queue backend: NOT STARTED

- M2-06 Approvals page and global pending-approvals tray: NOT STARTED

- M2-07 Sessions/chat UI with streaming and transcript handling: NOT STARTED

- M2-08 Agents page MVP with multi-agent summaries/quick actions: PARTIAL
  - agent summary appears in overview, but no dedicated agents page MVP yet

- M2-09 Regression tests for dashboard/chat/approvals/stream: PARTIAL
  - dashboard/regression tests exist
  - chat/approvals/stream not implemented yet

### M3 — Operator Control Plane and Cost Governance

- M3-01 Cost circuit breaker and per-agent telemetry: NOT STARTED

- M3-02 Panic stop global control: NOT STARTED

- M3-03 Read-only mode: NOT STARTED

- M3-04 Cron backend routes and normalized contracts: PARTIAL
  - minimal cron control exists (pause/resume/run)
  - likely not yet normalized to full official issue scope

- M3-05 Cron page with run history/output inspection/guarded actions: PARTIAL
  - cron UI exists in overview cards
  - no dedicated page/history/output inspection yet

- M3-06 Runs/activity timeline backend with retention and derived state: PARTIAL
  - event feed and persisted derived state exist
  - no full runs/activity backend yet

- M3-07 Runs/activity UI page with virtualization/drill-down: NOT STARTED

- M3-08 Process registry backend and guarded background-task controls: PARTIAL
  - process surface and kill control exist
  - no fully guarded registry backend aligned to official issue yet

- M3-09 Processes page before full terminal support: PARTIAL
  - process listing exists inside main dashboard
  - no dedicated processes page yet

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
