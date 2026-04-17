# Hermes Command Center — Next Official Issues (Execution Order)

This file opens the next tasks in the official backlog execution order after the current alignment audit.
Source of truth remains the official backlog PDF plus `docs/plans/2026-04-16-official-backlog-alignment.md`.

## Execution rule
Before expanding more dashboard/control-plane surface area, finish the remaining official M1 foundations that are still open or materially partial.

## Next issues to execute

### 1. M1-12 — Implement unified multiplexed SSE event bus
Status: OPEN
Priority: P1
Why next:
- official architectural requirement
- current UI relies on pull/read surfaces only
- SSE bus is foundation for dashboard freshness, approvals, chat stream, and process/cron updates

Scope:
- define SSE endpoint and event envelope
- assign event IDs and reconnect strategy
- multiplex health/runtime/cron/process/audit events on one stream
- keep idle overhead within performance budgets
- add smoke tests and reconnect behavior tests

Suggested deliverables:
- `backend/routes/events.py` or equivalent
- SSE contract doc update
- tests for initial connect, heartbeat, and event replay/reconnect behavior

### 2. M1-09 — Implement secret storage strategy
Status: OPEN
Priority: P1
Why next:
- ADR exists but implementation is not shipped
- official threat-model consequence
- should precede broader config/profile surfaces

Scope:
- choose concrete local secret storage mechanism matching ADR
- prevent sensitive values from leaking into logs/responses/plaintext state
- add bootstrap/setup rules for secret handling
- document degraded/fallback behavior where OS keyring is unavailable

Suggested deliverables:
- `backend/secrets.py` or equivalent
- tests for redaction and storage behavior
- doc update in security/setup docs

### 3. M1-03 / M1-07 follow-up — Resolve auth-gate divergence for non-loopback exposure
Status: OPEN (DECISION REQUIRED)
Priority: P1
Why next:
- current runtime intentionally diverges from official backlog default
- must either be corrected or explicitly documented/accepted as an exception

Scope:
- decide one of:
  - restore auth requirement for non-loopback exposure, or
  - keep Tailscale no-login mode but document it as an approved exception with compensating controls
- update docs/tests/startup rules accordingly

Suggested deliverables:
- decision record in docs
- config/default updates if needed
- tests for chosen posture

## After those M1 items
Proceed in official order into M2:
1. M2-05 approvals backend
2. M2-06 approvals UI
3. M2-04 Hermes-native chat streaming route/protocol
4. M2-07 sessions/chat UI
5. M2-02 dashboard completion against official scope

## Notes
- Current dashboard/process/cron work remains useful, but should not be treated as completion of the official M1 foundation set.
- Any new operator action added before M1-11 should be considered a temporary risk until audit logging is in place.
