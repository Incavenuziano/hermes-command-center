# M1 Auth Posture Resolution — Trusted Tailnet Exception

Date: 2026-04-16
Status: Accepted for current single-user phase

## Decision
For the current Tailscale-exposed single-user runtime, Hermes Command Center keeps trusted-local/no-login access as an explicit exception instead of restoring mandatory login for non-loopback binds.

## Guardrails now enforced
- non-loopback bind still requires `HCC_ALLOW_NON_LOOPBACK=1`
- if auth is disabled and bind is non-loopback, startup now also requires `HCC_TRUST_TAILNET_ONLY=1`
- `/system/info` exposes the active security posture so the exception is inspectable
- append-only audit log records destructive operator actions
- unified SSE stream and audit feed make operator activity visible

## Why this is acceptable for now
- product scope is single-user
- access path is restricted to the operator's tailnet instead of public internet exposure
- the operator explicitly requested no-login local-trusted mode for this phase
- the runtime now refuses to start in this posture unless the tailnet-only exception is declared explicitly

## Remaining limits
- this is still weaker than the official secure-by-default auth posture for non-loopback exposure
- this exception must be revisited before 1.0 / M5 hardening
- public internet exposure without auth remains out of bounds
