# HCC High-Fidelity Prototype Port Plan

> For Hermes: execute this as a faithful visual port of the supplied prototype onto the real HCC backend surfaces. Do not settle for a merely functional approximation.

Goal: rebuild the Hermes Command Center frontend so it is visually close to the reference prototype while preserving the current real backend contracts and operator flows.

Architecture: keep the current HCC backend and route contracts, but reconstruct the frontend around the prototype’s actual design system, shell, iconography, primitives, split layouts, and charts. Port visual language near-verbatim where possible; adapt only where real backend behavior requires it.

Tech stack: existing stdlib backend + frontend/index.html + frontend/styles.css + frontend/app.js, with optional small self-hosted static JS helpers if needed. No React UMD/Babel runtime transplant.

---

## Canonical references

Prototype source:
- `/tmp/hcc_frontend_review/Hermes Command Center.html`
- `/tmp/hcc_frontend_review/hermes/styles.css`
- `/tmp/hcc_frontend_review/hermes/icons.jsx`
- `/tmp/hcc_frontend_review/hermes/primitives.jsx`
- `/tmp/hcc_frontend_review/hermes/layout.jsx`
- `/tmp/hcc_frontend_review/hermes/pages_a.jsx`
- `/tmp/hcc_frontend_review/hermes/pages_b.jsx`
- `/tmp/hcc_frontend_review/hermes/pages_c.jsx`

Real HCC frontend to replace:
- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`
- `tests/test_command_center_features.py`

## Non-negotiable acceptance criteria

The new frontend must:
- match the prototype shell/layout hierarchy closely
- include a coherent SVG icon system across nav, actions, stats, and status
- be actually responsive on desktop/tablet/mobile breakpoints
- reintroduce real data-viz patterns, especially usage charts and sparklines
- use real backend data, not fake product data
- preserve current real HCC actions and contracts
- pass the current regression suite plus new fidelity-oriented tests
- be visually reviewable against the prototype in browser screenshots

The new frontend must NOT:
- stop at text-only cards and simple lists where the prototype has richer composed patterns
- remove real backend functionality to gain visual fidelity
- depend on React UMD/Babel in production runtime
- regress current routes or operator controls

---

## Task 1: Freeze the fidelity target in tests and docs

Objective: convert “make it look like the prototype” into pinned HTML/JS/CSS expectations so implementation cannot drift back to a low-fidelity approximation.

Files:
- Modify: `tests/test_command_center_features.py`
- Modify: `docs/plans/2026-04-17-hcc-high-fidelity-prototype-port.md`

Step 1: Write failing tests asserting prototype-driven markers exist in the real shell.

Add tests for presence of:
- Geist / Geist Mono font references
- real SVG icon containers or inline nav icons
- sidebar collapse control in footer
- status pill dot structure
- page subtitle/meta line
- reusable chart containers for dashboard/usage
- split-view containers for agents/sessions/cron/memory/documents
- timeline/feed row markers
- terminal/log styled output markers

Step 2: Run targeted test and confirm RED.

Run:
- `python -m pytest tests/test_command_center_features.py -q`

Expected: failure on missing prototype fidelity markers.

Step 3: Keep this plan updated as the single implementation contract.

Step 4: Re-run the same focused tests after each fidelity slice.

Step 5: Commit once the first fidelity marker slice is green.

---

## Task 2: Port the prototype token system and typography near-verbatim

Objective: replace the simplified current dark theme with the prototype’s semantic design-token structure.

Files:
- Modify: `frontend/styles.css`
- Test: `tests/test_command_center_features.py`

Step 1: Write failing tests for token/theme/font markers.

Assert CSS contains near-verbatim prototype structures such as:
- `--font-sans`
- `--font-mono`
- `:root[data-theme="premium"]`
- `:root[data-theme="mission"]`
- semantic tokens for accent/success/warning/danger
- shell token names like `--bg-deep`, `--bg-surface`, `--bg-panel`

Step 2: Run focused tests to verify RED.

Step 3: Port token definitions from prototype CSS into `frontend/styles.css`.

Specifically port/adapt:
- font variables
- radius variables
- transition variables
- premium theme token set
- mission theme token set
- base background/halo treatment
- typography and mono utility treatment

Step 4: Add the Google Fonts import for Geist / Geist Mono in the real HTML shell.

Files:
- Modify: `frontend/index.html`

Step 5: Run focused tests to verify GREEN.

Step 6: Run `node --check frontend/app.js` and keep CSS/HTML syntactically valid.

---

## Task 3: Port the icon system and shell chrome near-verbatim

Objective: eliminate text/emoji approximations and recreate the prototype shell components closely.

Files:
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`
- Modify: `frontend/app.js`
- Test: `tests/test_command_center_features.py`

Step 1: Write failing tests for:
- nav icon markers
- collapse button
- brand SVG/icon marker
- search icon marker
- status-pill dot marker
- refresh/start/kill icon usage

Step 2: Run focused tests and verify RED.

Step 3: Rebuild shell structure to mirror prototype more closely.

Port/adapt:
- brand block
- nav sections/items with icon + label + badge
- operator footer with collapse control
- topbar breadcrumb
- search input with icon + kbd hint
- gateway status pill with dot
- mono clock/status metadata where appropriate
- page header title + subtitle + action cluster

Step 4: Implement the prototype SVG icon registry inside the real frontend JS.

Step 5: Update nav/action rendering to use icons instead of text-only shell affordances.

Step 6: Run focused tests and confirm GREEN.

---

## Task 4: Introduce reusable prototype primitives in the real frontend

Objective: stop page-by-page ad hoc cards and create the real primitive layer the prototype depends on.

Files:
- Modify: `frontend/styles.css`
- Modify: `frontend/app.js`
- Test: `tests/test_command_center_features.py`

Step 1: Write failing tests for primitive markers/function names.

Add expectations for real frontend support of:
- panel
- stat card
- tag/badge tones
- progress bar
- sparkline
- split view
- key-value grid
- timeline feed item

Step 2: Run focused tests and verify RED.

Step 3: Implement reusable JS render helpers and CSS classes for:
- `renderIcon(...)`
- `buildPanel(...)`
- `buildStatCard(...)`
- `buildTag(...)`
- `buildProgressBar(...)`
- `buildSparkline(...)`
- `buildKeyValueGrid(...)`
- `buildTimelineItem(...)`

Step 4: Convert existing page renderers to use these helpers instead of generic item cards where the prototype expects richer composition.

Step 5: Run focused tests and verify GREEN.

---

## Task 5: Rebuild Dashboard and Usage to high-fidelity parity first

Objective: land the highest-value, highest-visibility prototype parity surfaces first.

Files:
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`
- Modify: `frontend/app.js`
- Modify if needed: `backend/usage_surface.py`
- Test: `tests/test_command_center_features.py`

Step 1: Write failing tests for:
- usage chart container
- usage breakdown bars/sparklines
- dashboard stat cards with icon/sparkline support
- live activity feed/timeline markers
- richer top-agents and cron highlight layouts

Step 2: Run focused tests and verify RED.

Step 3: Recreate dashboard using prototype patterns:
- Stat cards instead of plain count tiles
- timeline/feed treatment for live activity
- richer panels for top agents and cron overview
- better header/action hierarchy

Step 4: Recreate usage using prototype patterns:
- main usage chart
- summary stat cards with sparks where feasible
- breaker panel styled like prototype controls
- agent distribution bars
- top sessions ranking with stronger visual hierarchy

Step 5: If current `/ops/usage` lacks chart-friendly time-series data, add the minimum backend shape necessary without inventing fake data.

Step 6: Run focused tests and verify GREEN.

---

## Task 6: Rebuild split-view detail pages near-verbatim

Objective: port the prototype’s strongest operational pattern: list/detail workspaces.

Files:
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`
- Modify: `frontend/app.js`
- Test: `tests/test_command_center_features.py`

Pages in this task:
- Agents
- Sessions / Chat
- Activity
- Cron
- Memory
- Documents

Step 1: Write failing tests for split-view markers and richer detail structures.

Step 2: Run focused tests and verify RED.

Step 3: Implement reusable split-view layout classes matching prototype behavior.

Step 4: Port Agents page patterns:
- better rows with avatar/status
- richer detail panel
- recent sessions table/list pattern

Step 5: Port Sessions/Chat patterns:
- transcript visual structure
- message hierarchy
- tool-call/attachment treatment
- inspector/detail side

Step 6: Port Activity patterns:
- vertical timeline feed
- detail drilldown panel
- stronger filter affordances

Step 7: Port Cron patterns:
- jobs list/table hierarchy
- history/detail workspace
- better action grouping

Step 8: Port Memory/Documents patterns if still placeholders or low-fidelity.

Step 9: Run focused tests and verify GREEN.

---

## Task 7: Rebuild Terminal, Logs, and Doctor with prototype-grade operational styling

Objective: restore the most “command center” feeling surfaces with high-fidelity visual treatment.

Files:
- Modify: `frontend/index.html`
- Modify: `frontend/styles.css`
- Modify: `frontend/app.js`
- Test: `tests/test_command_center_features.py`

Step 1: Write failing tests for:
- terminal console container markers
- log stream viewer markers
- doctor summary/data table markers
- status tones and monospace output styling markers

Step 2: Run focused tests and verify RED.

Step 3: Port terminal treatment:
- black console surface
- colored line semantics
- mono text and cursor treatment

Step 4: Port logs treatment:
- structured stream rows
- colored severity markers
- filter controls with stronger visual grouping

Step 5: Port doctor treatment:
- summary cards
- diagnostic table styling
- better key/value and status semantics

Step 6: Run focused tests and verify GREEN.

---

## Task 8: Make responsiveness real, not symbolic

Objective: ensure the rebuilt frontend works credibly on desktop, tablet, and mobile, unlike the current simplified adaptation.

Files:
- Modify: `frontend/styles.css`
- Modify: `frontend/index.html` if necessary
- Test: `tests/test_command_center_features.py`

Step 1: Write failing tests for responsive marker classes and shell states.

Step 2: Run focused tests and verify RED.

Step 3: Port prototype-responsive behavior:
- shell collapse behavior
- sidebar treatment on smaller breakpoints
- stacked page-header actions
- grid collapse for stat cards and split panes
- searchable topbar behavior on narrower widths

Step 4: Ensure no page becomes unusable under tablet/mobile widths.

Step 5: Run focused tests and verify GREEN.

---

## Task 9: Visual verification against the reference prototype

Objective: prove the result is close to the supplied frontend, not just internally “nicer”.

Files:
- Optional docs update: `docs/architecture/` or `docs/plans/`

Step 1: Start the HCC locally.

Run:
- `HCC_HOST=127.0.0.1 HCC_PORT=8787 python backend/app.py`

Step 2: Use browser and/or screenshot comparison to inspect:
- shell
- dashboard
- usage
- agents
- sessions/chat
- activity
- cron
- doctor
- logs

Step 3: Compare directly against the prototype source behavior and hierarchy.

Checklist:
- same overall shell proportions and hierarchy
- real icons everywhere expected
- visible charts/data viz where prototype has them
- split layouts visually comparable
- status pills/tags/badges look intentional and systematized
- responsive layout survives practical viewport changes

Step 4: Fix visual mismatches that materially break fidelity.

Step 5: Re-run tests.

Commands:
- `python -m pytest tests/test_command_center_features.py -q`
- `python -m pytest tests/ -q`
- `python -m py_compile backend/usage_surface.py tests/test_command_center_features.py`
- `node --check frontend/app.js`

---

## Task 10: Commit, publish, validate on real instance

Objective: deploy the rebuilt frontend and validate it operationally.

Files:
- no new product files required beyond implementation changes

Step 1: Review git diff.

Step 2: Run independent review.

Step 3: Commit with a message similar to:
- `feat: port HCC frontend to high-fidelity prototype design`

Step 4: Push to `main`.

Step 5: Restart/publish the validated HCC instance.

Step 6: Verify live routes and browser rendering on:
- local loopback
- published tailnet instance if applicable

---

## Implementation notes

- High-fidelity means prototype-driven visual reconstruction, not “admin page with nicer CSS”.
- Reuse current backend contracts aggressively; add backend shape only when a real chart or visual primitive truly needs it.
- Prefer small helper abstractions in `frontend/app.js` over another round of one-off page render code.
- If a self-hosted static helper file becomes necessary (for icons/charts/primitives), create it under the existing frontend static surface and update tests accordingly.
- Keep current route markers stable when possible so we don’t create avoidable backend/frontend regressions.

## Verification baseline for every slice

Always run:
- `python -m pytest tests/test_command_center_features.py -q`
- `python -m pytest tests/ -q`
- `python -m py_compile backend/usage_surface.py tests/test_command_center_features.py`
- `node --check frontend/app.js`

And for visual slices, also perform browser validation on the real pages.
