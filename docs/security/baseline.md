# Hermes Command Center — Security Baseline

## Default posture

- bind to `127.0.0.1` by default
- require authentication for non-loopback exposure
- refuse unsafe startup combinations where feasible
- run as non-root by default
- create local files with restrictive permissions (`umask 077` target posture)

## Browser security

- CSRF protection on mutating routes
- strict CSP
- no permissive CORS by default
- clickjacking protection
- secure cookie settings
- no inline/script policy shortcuts unless explicitly justified

## Secrets

- no plaintext secrets in API responses
- no plaintext secrets in logs
- no casual `.env` sprawl as de facto secret store
- secret storage strategy must be explicitly implemented and documented

## Filesystem access

- all file access must be rooted to explicit allowed roots
- path traversal must be blocked
- symlink escapes must be blocked
- sensitive file patterns must be denied by default

## Dangerous actions

- destructive or privileged actions must be auditable
- approvals must bind to the exact requested action
- process kill/stop and terminal behavior require explicit safeguards
- high-sensitivity profile switching must support re-auth

## Source-of-truth rule

Hermes remains the source of truth for runtime state.
Command Center may keep derived/cache state only.
