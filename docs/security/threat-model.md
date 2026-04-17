# Hermes Command Center — Initial Threat Model

## Scope

This threat model covers the v1 single-user, multi-agent Hermes Command Center running locally or through secure remote access methods such as SSH tunnel or Tailscale.

## Security assumptions

- one trusted operator account
- Hermes runtime already exists and remains the source of truth
- Command Center is primarily loopback-bound
- remote exposure is deliberate, authenticated, and hardened
- attacker may gain browser-level access, filesystem-level local access, or network access if deployment is careless

## Assets

Primary assets:
- operator session/auth state
- Hermes runtime state
- Hermes secrets and channel credentials
- local filesystem roots exposed to UI
- cron definitions and outputs
- process controls
- profiles and profile-specific state
- audit log and derived state database
- Google integration tokens and any future third-party tokens

## Threat actors

- curious local user on same machine
- malicious webpage attempting browser-side attacks
- attacker on same LAN if app is exposed beyond loopback
- compromised browser session
- accidental misuse by operator
- compromised or buggy Hermes tool output that reaches the UI

## Threat surfaces

### 1. Authentication and sessions
Threats:
- password brute force
- stolen session cookie
- session fixation
- long-lived session leakage
- privilege escalation through profile switching

Controls:
- strong password hashing
- rate limiting and lockout
- session rotation on login
- idle timeout and max lifetime
- secure cookie flags
- optional WebAuthn/passkey
- re-auth for high-sensitivity actions

### 2. Browser and frontend
Threats:
- XSS through logs, markdown, skill content, or tool output
- CSRF on mutating routes
- clickjacking
- unsafe inline scripts
- overexposed browser permissions

Controls:
- strict CSP
- CSRF protections
- sanitized markdown rendering
- no permissive CORS
- frame blocking
- permissions policy
- safe rendering of runtime/tool content

### 3. Filesystem access
Threats:
- path traversal
- symlink escape
- preview of sensitive files
- reading special files or large files that cause denial-of-service

Controls:
- rooted path access only
- realpath validation
- denylist for sensitive patterns
- size caps for previews
- block special files and escaped symlinks

### 4. Process and terminal control
Threats:
- accidental destructive stop/kill
- hostile terminal usage
- privilege escalation through shell access
- unsafe process killing during incident response

Controls:
- structured process controls before shell access
- destructive confirmation and audit logging
- terminal opt-in with narrow scope
- no root-by-default runtime
- re-auth / approval for highly sensitive actions

### 5. Cron and automation
Threats:
- runaway jobs
- overlap storms
- missed-run explosions
- hidden cost growth
- destructive cron mutation without auditability

Controls:
- overlap policy
- max runtime
- missed-run policy
- cost circuit breaker
- audit log for cron mutations
- panic stop global control

### 6. Event transport
Threats:
- replay or stale approval events
- polling storms
- client desync
- malformed internal event data

Controls:
- unified SSE bus
- event IDs and reconnect policy
- approval tokens tied to exact action hashes
- bounded queues/backpressure behavior
- parser hardening and testing

### 7. Secrets and integrations
Threats:
- plaintext tokens in config or logs
- accidental git commit of secrets
- exposed example configs becoming real configs
- stolen third-party refresh tokens

Controls:
- secret storage strategy
- redaction in logs and responses
- gitleaks and CI checks
- no plaintext secret storage in SQLite or logs
- strict `.gitignore` and release review

### 8. Data integrity and recoverability
Threats:
- failed migrations
- corrupted SQLite state
- loss of audit trail
- inability to recover after bad release

Controls:
- migration framework
- backup-before-migrate
- WAL and safe SQLite settings
- backup/export/restore workflow
- append-only audit log discipline

## Highest-priority risks

1. runaway cost/token burn from agents or cron
2. accidental destructive action without sufficient approvals/auditability
3. filesystem escape or sensitive file preview leak
4. secret exposure through logs, config, or repo history
5. inconsistent/degraded runtime handling causing unsafe operator assumptions

## Required implementation consequences

This threat model implies the following work is mandatory early:
- secret storage
- audit log
- unified event bus
- approval-token binding
- cost circuit breaker
- panic stop
- filesystem sandbox hardening
- migration framework

## Review cadence

Update this threat model:
- before 1.0 release
- after any major architectural change
- when new high-risk integrations or execution surfaces are added
