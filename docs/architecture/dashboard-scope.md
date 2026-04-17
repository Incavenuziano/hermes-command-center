# M2-02 — Dashboard completion against official scope

This milestone closes the core dashboard surface expected for the M2 control-plane MVP.

## Dashboard surfaces now present
- agents summary cards
- sessions list
- processes list with operator actions
- cron jobs list with operator actions
- approvals panel
- recent events panel
- explicit system health panel
- session detail panel
- chat transcript panel with streaming awareness

## Health/system closure
The remaining gap for this milestone was making the system/health surface explicit in the dashboard itself rather than only indirectly visible through the ops overview snapshot.

The dashboard now loads:
- `GET /system/info`
- `GET /health`

And renders a dedicated `System Health` panel with:
- service
- bind
- auth mode
- overall status
- runtime status
- event-bus status

## Why this closes M2-02
The dashboard now visibly covers the official operational surfaces called out in the backlog: health, agents, cron, approvals, and recent events, while preserving the already-built sessions/processes/chat operator context.

## Notes
- this remains a no-build stdlib frontend
- the dashboard is intentionally integrated rather than split into multiple routes/pages at this stage
- later milestones can still refine layout or add dedicated pages without reopening the MVP dashboard scope
