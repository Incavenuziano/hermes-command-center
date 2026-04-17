# Approvals UI

This document records the shipped M2-06 UI slice.

## Current UI behavior
- dashboard now includes an `Approvals` panel
- pending items show choice buttons for quick resolution
- resolved items show the final decision
- the approvals summary shows pending-count state

## Data source
- `GET /ops/approvals`
- `POST /ops/approvals/resolve`

## Current scope
This is a dashboard-integrated approvals surface, not yet a standalone full workflow console.
It is sufficient for the current M2 approvals UI milestone in the shipped minimal frontend.
