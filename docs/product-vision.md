# Hermes Command Center — Product Vision

## Product definition

Hermes Command Center is a private, single-user, multi-agent operational command center for Hermes Agent.

It is not a SaaS control plane and not a multi-tenant product in v1.

## Target operator

One operator managing one or more Hermes agents/subagents, wanting:
- visibility into what Hermes is doing
- fast intervention when something needs approval or correction
- safe management of cron, sessions, processes, files, memory, skills, and profiles
- minimal token spend during passive monitoring

## Primary jobs-to-be-done

The operator must be able to:
- see whether Hermes is healthy quickly
- inspect active agents and sessions
- continue or intervene in live conversations
- approve or deny risky actions
- inspect and manage cron jobs
- inspect and control long-running work
- inspect memory, skills, files, and profiles without relying on terminal use
- detect incidents early and stop runaway behavior fast

## Non-goals for v1

- multi-tenant SaaS
- plugin marketplace sprawl
- default internet-exposed deployment
- hidden AI-driven token spend
- replacing Hermes as source of truth

## Product posture

- no telemetry
- no phone-home behavior
- no analytics by default
- no automatic update checks by default
- loopback/local-first operation by default

## Cost guardrails

Command Center must treat cost and token governance as first-class operational concerns.

That includes:
- passive views that never invoke models
- explicit operator gesture before any model invocation
- future per-agent/per-session/global cost controls
- visibility into burn rate and runaway behavior
