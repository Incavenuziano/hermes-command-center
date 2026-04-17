# Hermes Command Center — Next Official Issues (Execution Order)

This file opens the next tasks in the official backlog execution order after the current alignment audit.
Source of truth remains the official backlog PDF plus `docs/plans/2026-04-16-official-backlog-alignment.md`.

## Execution rule
Before expanding more dashboard/control-plane surface area, finish the remaining official M1 foundations that are still open or materially partial.

## Next issues to execute

### M2 entry unlocked
M2 is now complete. Continue in the official M3 order:

1. Backlog M0–M5 is now complete; next work should come from a new official backlog or post-1.0 priorities.
2. Re-run full regression and smoke checks before any deployment changes.
3. Consider switching branch-protected flow to actual PRs instead of admin bypass pushes.

## Notes
- Current dashboard/process/cron work remains useful, but should not be treated as completion of the official M1 foundation set.
- Any new operator action added before M1-11 should be considered a temporary risk until audit logging is in place.
