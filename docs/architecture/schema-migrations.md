# Schema Migration Framework

This document records the shipped M1-13 migration strategy.

## Goals
- make Command Center-owned SQLite schema changes explicit
- ensure first-run initialization is reproducible
- ensure repeat startup is idempotent

## Current implementation
- module: `backend/migrations.py`
- bootstrap wiring: `backend/bootstrap.py`
- managed targets:
  - `audit_log` → `.data/audit-log.sqlite3`
  - `event_bus` → `.data/event-bus.sqlite3`

## Mechanism
Each managed SQLite database contains a `schema_migrations` table:
- `target` (primary key)
- `version`
- `updated_at`

Startup applies the current migration set before the HTTP server is created.

## Versioning
Current shipped versions:
- `audit_log`: `1`
- `event_bus`: `1`

## Safety properties
- first run creates the required tables and metadata
- repeat runs do not reapply already-current migrations
- migration state is local to each managed database

## Operator note
Future schema changes should be added as explicit migration functions in `backend/migrations.py` rather than embedded ad hoc inside feature modules.
