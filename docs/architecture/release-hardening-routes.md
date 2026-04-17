# M5-01 / M5-02 — Security audit gate and performance budget validation

## Routes
- `GET /ops/security-audit`
- `GET /ops/performance`

## Scope
- exposes a release-facing hardening checklist as structured backend data
- exposes performance budget targets plus a current route/surface snapshot

## Why this closes M5-01 and M5-02
Security and performance readiness are now explicit inspectable surfaces rather than implicit expectations buried in docs or CI only.
