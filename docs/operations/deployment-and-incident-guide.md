# Deployment and Incident Guide

## Deployment
- run the backend locally or via Tailscale-exposed trusted environment
- verify `/health`, `/system/info`, and `/ops/security-audit`
- confirm full pytest suite is green before production use

## Operator Checks
- inspect `/ops/performance` for current budget posture
- inspect `/ops/gateway` for redacted delivery status
- verify read-only mode behavior before risky changes

## Incident Response
- use panic stop for runaway process/cron scenarios
- switch to read-only mode when the system must remain observable but frozen
- export state before invasive recovery with `/ops/state/export`
- restore from a known-good export with `/ops/state/restore`

## Troubleshooting
- if UI surfaces degrade, re-check `/health`, `/ops/overview`, `/ops/security-audit`
- if delivery channels misbehave, inspect `/ops/gateway`
- if state corruption is suspected, perform export, snapshot the workspace, then restore from a validated bundle
