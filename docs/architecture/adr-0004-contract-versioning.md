# ADR-0004 — Contract Versioning

## Status
Accepted

## Decision
Backend contracts will be versioned intentionally, even though frontend and backend initially evolve together in one repository.

## Rules
- contracts should have documented versions
- breaking changes require explicit note in docs/ADR or changelog
- response metadata or headers may expose contract version where useful
- deprecation should be explicit before removal when practical

## Rationale
This reduces future pain if the UI, automation, or alternate clients ever consume Command Center APIs directly.
