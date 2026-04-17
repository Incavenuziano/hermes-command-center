# M3-10 — Terminal strategy with explicit risk posture

This milestone makes the Command Center terminal stance explicit without enabling terminal access itself.

## Routes
- `GET /terminal`
- `GET /ops/terminal-policy`

## Current posture
The Command Center is intentionally in:
- `mode: disabled`
- `interactive_terminal_enabled: false`
- `risk_posture: explicit-deny-until-reviewed`

## Allowed controls
At this stage the operator surface allows only narrower controls that already exist elsewhere:
- kill process
- pause/resume cron
- inspect process and cron registry metadata

## Blocked terminal features
The following remain intentionally unavailable:
- PTY shell access
- stdin write/submit
- arbitrary command execution
- live terminal streaming

## Why the posture is explicit
Terminal features dramatically increase blast radius, secret exposure risk, and operator-footgun risk compared with the rest of the control plane.
Before any terminal surface is enabled, the Command Center should have a narrower threat model, stronger re-auth posture, and tighter audit semantics for interactive command sessions.

## Why this closes M3-10
The product now has an implemented and inspectable terminal strategy rather than scattered implied constraints. Operators can see that terminal access is intentionally disabled, what remains allowed, and which follow-on milestone must revisit the decision.
