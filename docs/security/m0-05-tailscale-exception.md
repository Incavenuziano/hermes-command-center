# M0-05 Exception Record — Tailscale Trusted-Local Exposure

Date: 2026-04-16
Status: Accepted operator exception for current development/runtime phase

Context:
The official backlog and baseline security direction prefer authentication for non-loopback exposure. The current Hermes Command Center runtime is exposed only through the user's Tailscale network and was explicitly changed at the user's request to remove the login gate for this phase.

Exception:
- Current runtime allows trusted-local/no-login access on the Tailscale-exposed endpoint.
- This is an intentional deviation from the stricter default posture described in the original M0/M1 security direction.

Compensating controls currently in place:
- single-user product scope
- Tailscale access instead of public internet exposure
- loopback/local-first default still preserved in code paths unless explicitly overridden
- destructive actions are captured in append-only operator audit logging
- operator activity is visible through the unified SSE/event feed surfaces
- trusted-local non-loopback startup now also requires explicit `HCC_TRUST_TAILNET_ONLY=1`

Required follow-up:
- revisit before 1.0 release
- either restore auth for non-loopback exposure or formally codify a stricter tailnet-only exception model with additional controls
- current codified resolution is recorded in `docs/security/m1-auth-posture-exception.md`
