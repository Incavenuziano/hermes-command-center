# ADR-0005 — Secret Storage Strategy

## Status
Accepted

## Decision
Secrets must not live casually in plaintext configuration files or logs.

Preferred order:
1. OS keychain/keyring integration
2. encrypted local secret store with operator-derived key
3. plaintext local file only as explicit last resort with warnings and strict permissions

## Applies to
- operator auth material
- integration tokens
- channel/gateway credentials
- future third-party refresh tokens

## Rationale
Hermes Command Center is a local control surface for sensitive capabilities; secret hygiene cannot be left implicit.
