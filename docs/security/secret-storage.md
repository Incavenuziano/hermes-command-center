# Secret Storage Strategy Implementation

This document records the shipped M1-09 behavior.

## Resolution order
Hermes Command Center resolves secrets in this order:
1. environment variable override
2. OS keyring via Python `keyring` module when available
3. local plaintext fallback file only when explicitly enabled
4. hardcoded development default only where the current project still requires one for bootstrap

## Current implementation
- module: `backend/secrets_store.py`
- local fallback path: `.data/secrets.json`
- local fallback is disabled unless `HCC_ALLOW_PLAINTEXT_SECRETS=1`
- when plaintext fallback is used, the file is written with mode `0600`

## Current shipped secret bindings
- `auth.local_password`
  - env override: `HCC_AUTH_PASSWORD`
  - current bootstrap default: `dev-password`

## Redaction rules
- system surfaces must expose only redacted summaries
- `/system/info` reports backend/presence/redacted preview only
- raw secret values must not be returned by HTTP routes

## Degraded mode
If OS keyring is unavailable:
- reads continue from environment variables
- writes may fall back to `.data/secrets.json` only with explicit operator opt-in
- without opt-in, attempts to write plaintext secrets raise an error

## Operator notes
- for real deployments, prefer environment override or OS keyring
- plaintext fallback exists only as a constrained last resort for single-user local operation
- rotate any secret that was ever pasted into chat, logs, or shell history
