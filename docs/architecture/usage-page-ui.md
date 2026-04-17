# Usage Page UI

## Goal

Turn `/usage` into a real operational page instead of a placeholder.

## Backend surface

- `GET /ops/usage`

The route aggregates:
- cost totals from live Hermes sessions
- per-agent breakdown
- circuit breaker state
- performance snapshot
- load smoke snapshot
- top sessions by cost/token weight

## UI sections

The current page exposes:
- summary KPI list
- circuit breaker update form
- usage detail drill-down panel
- per-agent breakdown list

## Operator value

This page is intended to answer:
- how much token/cost usage is happening now?
- is the circuit breaker healthy or tripped?
- which agent is consuming the most resources?
- which sessions dominate spend?
- does the current build still fit the expected performance envelope?

## Current integrations

- `GET /ops/usage`
- `POST /ops/costs/circuit-breaker`

## MVP interaction pattern

- page load fetches `/ops/usage`
- breaker form posts updated thresholds to `/ops/costs/circuit-breaker`
- page then re-fetches `/ops/usage` and re-renders in place

## Notes

This page intentionally prefers:
- compact textual metrics
- operator-safe drill-down
- no heavy charting dependency yet

Charts can be added later if the data volume justifies them.
