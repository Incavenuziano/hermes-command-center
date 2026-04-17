# ADR-0002 — Thin Control Plane

## Status
Accepted

## Decision
Hermes Command Center is a thin control plane over Hermes Agent, not a replacement runtime.

## Rules
- Hermes remains source of truth for sessions, memory, skills, cron, profiles, and runtime execution state.
- Command Center may store derived state only.
- Derived state must be rebuildable without harming Hermes.
- UI-facing persistence is for indexes, caches, notifications, and auditability — not for becoming a second orchestration engine.

## Rationale
This keeps the product lightweight, reduces drift risk, and makes crashes of the UI/control plane survivable.
