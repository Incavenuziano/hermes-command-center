# M3-01/M3-02 — Cost governance and panic stop

## M3-01 cost circuit breaker and per-agent telemetry

Shipped backend surfaces:
- `GET /ops/costs`
- `POST /ops/costs/circuit-breaker`

Implementation notes:
- telemetry is derived from real Hermes session cost/token fields in `state.db`
- `backend/runtime_adapter.py` now carries token/cost fields through session summaries
- `backend/cost_controls.py` persists breaker configuration under `.data/cost-circuit-breaker.json`
- `backend/routes/costs.py` computes totals plus per-agent summaries and breaker state

Current totals exposed:
- session_count
- input_tokens
- output_tokens
- reasoning_tokens
- total_tokens
- estimated_cost_usd
- actual_cost_usd

Breaker config supported:
- `max_actual_cost_usd`
- `max_total_tokens`

Current breaker reasons:
- `cost_limit_exceeded`
- `token_limit_exceeded`

## M3-02 panic stop global control

Shipped backend surface:
- `POST /ops/panic-stop`

Current behavior:
- kills all running processes visible through the runtime adapter
- pauses all enabled cron jobs
- emits process/cron events into the derived state feed
- appends a global audit entry (`ops.panic_stop`)

## Validation
- focused TDD for `/ops/costs`, breaker update, and `/ops/panic-stop`
- full suite green after implementation
