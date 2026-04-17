# ADR-0003 — Event Transport

## Status
Accepted

## Decision
Use SSE as the primary event transport for v1 unless a proven requirement forces broader bidirectional transport.

## Why
- simpler operationally than WebSockets
- fits single-user operator model well
- good for dashboard, approvals, chat events, process logs, and cron updates
- easier to inspect and debug

## Implications
- one unified event bus is preferred over per-feature polling
- event IDs, reconnection strategy, and heartbeat must be defined
- chat and operational surfaces should reuse the same transport model where practical
