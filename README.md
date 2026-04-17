# Hermes Command Center

Hermes Command Center is a secure, lightweight, single-user, multi-agent operational command center for Hermes Agent.

It is designed to combine:
- the mission-control feel and operational breadth of openclaw-mission-control
- the Hermes-native integration quality and pragmatic architecture lessons of hermes-webui

Core principles:
- single-user first
- multi-agent aware from day one
- loopback/local-first by default
- no telemetry or phone-home by default
- zero LLM usage for dashboards and operational read surfaces
- Hermes remains the source of truth; Command Center stores derived state only
- destructive actions must be auditable
- runaway cost/token burn must be governable

## Repository structure

- `backend/` — backend app, adapters, contracts, security, event transport
- `frontend/` — UI shell and operator-facing surfaces
- `contracts/` — shared API/event contract references
- `docs/` — architecture, security, setup, and operating docs
- `tests/` — automated tests
- `scripts/` — local development and maintenance scripts
- `.github/` — CI, templates, and repository automation

## Current status

This repository is in early implementation.

The current focus is:
- Phase 0 foundation
- secure local skeleton
- documentation and architecture baselines
- initial backend/frontend structure
- backend control-plane bootstrap with health/readiness/system-info routes
- derived-state operational read APIs (`/ops/overview`, `/ops/events`)
- runtime-backed read APIs for sessions/processes/cron jobs plus session detail/action surfaces
- frontend shell served locally from `/`
- runtime event ingest path via `/runtime/events`
- durable event/read-model persistence under `.data/`

## Security posture

- bind to loopback by default
- authentication optional and disabled by default for the current single-user local/Tailscale deployment
- no plaintext secrets in logs or API responses
- path sandboxing is mandatory for file access
- high-risk actions require explicit safeguards and auditability

## Operational posture

- no telemetry
- no automatic phone-home behavior
- no hidden model invocations for passive monitoring
- event-first architecture preferred over polling

## References

Primary planning artifacts currently live in:
- local Hermes plans under `~/.hermes/plans/`
- Google Drive/Docs under the `Hermes` folder
- Obsidian vault references under the Hermes vault
