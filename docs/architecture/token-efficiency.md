# Hermes Command Center — Token Efficiency Rules

## Core rule

Operational read surfaces must not invoke LLMs.

This includes:
- dashboard
- approvals
- logs
- timeline/activity
- process views
- file browser
- status/health views
- cron summaries

## Model invocation policy

A model may only be invoked when triggered by an explicit operator action.

Disallowed in v1:
- hidden summarization
- AI tooltips
- AI autocomplete for ordinary forms
- AI validation helpers
- background “smart” analysis by default

## Event transport

Prefer event-driven incremental updates over polling.

## Rendering and payload rules

- paginate large datasets
- truncate large payloads server-side
- use virtualization for long lists
- use caching and ETags for GET surfaces
- keep passive monitoring cheap in CPU, memory, and tokens

## Cost control principle

UI efficiency is not enough; future runtime controls must also govern cost at the agent/session/global level.
