# Hermes Command Center — Performance and Resource Budgets

## Purpose

These budgets define the acceptable baseline for a single-user, local-first operational console.

They exist so regressions are measurable rather than subjective.

## Target budgets (initial)

### Backend
- dashboard/status TTFB on localhost: <= 100 ms target, <= 200 ms acceptable
- ordinary read route latency on localhost: <= 200 ms target for common summaries
- idle backend CPU: <= 1% averaged over 5 minutes on a typical developer machine
- backend resident memory: <= 150 MB target before heavy optional features

### Frontend
- initial shell render on localhost: <= 500 ms target after HTML delivery
- bundle budget:
  - <= 150 KB gzip target if minimal/non-React approach
  - <= 250 KB gzip target if React/TypeScript approach is chosen
- no long-list full rendering beyond 200 items without virtualization

### Event transport
- SSE heartbeat overhead: <= 1 KB/minute idle per client connection
- reconnect should recover within a few seconds without full-page reload
- no feature-specific polling when unified event bus can satisfy the use case

### Operational behavior
- passive monitoring must consume zero model tokens
- passive monitoring must not trigger hidden summarization or analysis
- dashboard refresh must prefer incremental updates over full refetch

### Storage
- SQLite configured for WAL
- no unbounded log growth
- logs rotated before they exceed operationally reasonable size

## Enforcement guidance

- measure these budgets in M5 against real implementation
- prefer failing CI or at least warning when key budgets regress
- document any temporary waiver explicitly
