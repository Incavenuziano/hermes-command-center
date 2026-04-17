# Frontend Strategy

Status: accepted for current architecture phase
Date: 2026-04-16
Related backlog issue: M1-01

## Decision

Use a minimal/no-build frontend as the default Hermes Command Center strategy for the current product phase.

Chosen stack:
- server-served HTML
- plain CSS
- plain JavaScript modules/files
- stdlib HTTP backend serving static assets directly
- no SPA framework requirement in the current phase

## Why this was selected

Hermes Command Center has unusually strong constraints:
- single-user deployment
- local-first / loopback-first posture
- zero LLM usage for dashboard and operational read surfaces
- strong preference for low idle CPU, low memory, low complexity, and minimal token/cost burn
- mission-control UX matters, but initial reliability and inspectability matter more than frontend abstraction comfort

Given those constraints, the current no-build frontend is the lightest viable option that still supports a serious control-plane UX.

## Options considered

### 1. Minimal / no-build frontend

Description:
- HTML + CSS + vanilla JS served directly from the backend
- optional incremental enhancement without introducing a full framework runtime

Pros:
- lowest bundle size
- fastest startup and lowest local TTI overhead
- easiest to inspect/debug in a local control-plane product
- no frontend build pipeline required for basic progress
- trivial backend/static serving integration
- easy SSE integration through native `EventSource`
- smallest dependency and supply-chain footprint
- best fit for current stdlib-backend phase

Cons:
- more manual DOM/state management over time
- harder to scale to very complex UI composition if the product grows substantially
- developer ergonomics weaker than React/TypeScript for large interactive surfaces

Assessment:
- best current fit

### 2. Restrained React + TypeScript

Description:
- React app with TypeScript, likely Vite-based, but kept intentionally small

Pros:
- strong component model
- better large-surface maintainability
- stronger typing and developer tooling
- easier stateful chat/dashboard views once the product grows

Cons:
- larger JS/runtime footprint
- higher build/dev complexity
- more dependency churn and supply-chain exposure
- stronger risk of overbuilding early
- more effort to stay disciplined on token-free / low-idle mission-control surfaces

Assessment:
- viable later, not justified as the current default

### 3. Lightweight alternative such as HTMX or Preact

Description:
- introduce a smaller abstraction layer while avoiding full React weight

Pros:
- lighter than React
- can improve ergonomics over pure vanilla JS
- HTMX can reduce custom JS for some server-driven interactions
- Preact offers a component model with smaller runtime

Cons:
- still adds another dependency/runtime model
- can create architectural ambiguity during the early phase
- HTMX is less natural for rich streaming/control-plane interactions than explicit event/state handling
- Preact still pushes the project toward SPA-style complexity earlier than necessary

Assessment:
- reasonable fallback if vanilla becomes too costly before a React-level migration is warranted

## Performance tradeoff summary

### Bundle size
- Minimal/no-build: lowest possible; near-zero framework overhead
- HTMX/Preact: low to moderate
- React/TypeScript: highest of the options considered

### Time to interactive under local budgets
- Minimal/no-build: best expected outcome
- HTMX/Preact: acceptable
- React/TypeScript: acceptable but worst of the set

### Accessibility burden
- Minimal/no-build: explicit/manual but fully controllable
- HTMX/Preact: moderate
- React/TypeScript: good ecosystem support, but still requires discipline

### Code-splitting
- Minimal/no-build: manual, route/file based
- HTMX/Preact: possible with some tooling
- React/TypeScript: strongest tooling support

### SSE integration
- Minimal/no-build: straightforward via native browser APIs
- HTMX/Preact: workable
- React/TypeScript: workable, but not meaningfully better at this phase

### Developer ergonomics
- Minimal/no-build: weakest for large UI complexity, strongest for immediate clarity
- HTMX/Preact: middle ground
- React/TypeScript: strongest for large app ergonomics

## Decision boundary for revisiting

Revisit this decision if one or more of these becomes true:
- multiple dedicated pages with dense cross-component state become hard to maintain
- streaming chat/approvals/timeline surfaces create excessive manual UI state code
- testability of the frontend becomes materially worse than the performance savings justify
- the operator UX requires more component reuse than the no-build approach handles cleanly

## Current rule

Until one of those triggers is reached:
- keep the frontend minimal/no-build
- prefer server-served static assets
- avoid introducing a JS framework by default
- use native browser features first (`fetch`, `EventSource`, accessible semantic HTML)
- keep the dependency/supply-chain surface minimal
