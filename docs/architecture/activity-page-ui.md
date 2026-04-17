# M3-07 — Runs/activity UI page with virtualization and drill-down

This milestone adds a dedicated activity page for the retained operator/runtime event timeline exposed by `GET /ops/activity`.

## Route
- `GET /activity`

## UI scope
- dedicated `Activity Page` panel in the minimal frontend shell
- bounded timeline window backed by the existing retention-aware activity backend
- incremental `Load More Activity` control that increases the fetched window size instead of rendering an unbounded feed all at once
- per-item `Inspect Event` drill-down that renders the full event payload into a dedicated detail panel

## Virtualization posture
The frontend keeps the rendered list bounded to the currently requested window (`limit` on `/ops/activity`).
This is intentionally lightweight windowing rather than a complex virtual-scroll framework, consistent with the no-build frontend strategy.

## Drill-down behavior
- the newest returned item is shown by default in the drill-down panel
- selecting `Inspect Event` on any item replaces the drill-down payload with that event's normalized JSON

## Why this closes M3-07
The Command Center now has an explicit activity surface separate from the dashboard summary feed, with a bounded rendering window and event drill-down workflow aligned to the official milestone intent.
