# Hermes Command Center — Next Official Issues (Execution Order)

This file opens the next tasks in the official backlog execution order after the current alignment audit.
Source of truth remains the official backlog PDF plus `docs/plans/2026-04-16-official-backlog-alignment.md`.

## Execution rule
Before expanding more dashboard/control-plane surface area, finish the remaining official M1 foundations that are still open or materially partial.

## Next issues to execute

### 1. M1-04 — Browser hardening and CSRF protection alignment
Status: OPEN
Priority: P1
Why next:
- explicit-auth CSRF exists, but broader browser hardening still needs formal closure

### 2. M1-05 — Canonical backend contracts for core surfaces
Status: OPEN
Priority: P1
Why next:
- contracts exist, but all official core surfaces should be reaudited/normalized after the recent M1 additions

### 3. M1-10 — WebAuthn/passkey optional second factor
Status: OPEN
Priority: P2
Why next:
- still part of official M1 scope, but lower leverage than hardening/contracts alignment for the current single-user phase

## After those M1 items
Proceed in official order into M2:
1. M2-05 approvals backend
2. M2-06 approvals UI
3. M2-04 Hermes-native chat streaming route/protocol
4. M2-07 sessions/chat UI
5. M2-02 dashboard completion against official scope

## Notes
- Current dashboard/process/cron work remains useful, but should not be treated as completion of the official M1 foundation set.
- Any new operator action added before M1-11 should be considered a temporary risk until audit logging is in place.
