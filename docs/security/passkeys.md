# Optional Passkey / WebAuthn Second Factor

This document records the shipped M1-10 implementation.

## Scope
Passkeys are optional for the current single-user Hermes Command Center runtime.
They are not required for default trusted-tailnet operation.

## Backend surfaces
- `GET /auth/passkeys/status`
- `POST /auth/passkeys/register/options`
- `POST /auth/passkeys/register/verify`
- `POST /auth/passkeys/authenticate/options`
- `POST /auth/passkeys/authenticate/verify`

## Current behavior
- feature status is inspectable without exposing secret material
- passkey enrollment requires an explicit password-authenticated session plus CSRF token
- registration/authentication ceremonies use the Python `webauthn` library when available
- enrolled credential metadata is stored locally in `.data/passkeys.json`

## Defaults
- RP ID: `localhost` unless overridden by `HCC_WEBAUTHN_RP_ID`
- RP name: `Hermes Command Center` unless overridden by `HCC_WEBAUTHN_RP_NAME`
- origin: `http://localhost` unless overridden by `HCC_WEBAUTHN_ORIGIN`

## Security posture
- passkeys are optional, not mandatory
- enrollment is stricter than trusted-local browsing: it requires a real local-password session
- if the WebAuthn dependency is unavailable, the passkey routes return explicit unavailability instead of silently degrading
