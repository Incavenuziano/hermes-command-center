# Approvals Backend

This document records the shipped M2-05 backend slice.

## Endpoints
- `GET /ops/approvals`
- `POST /ops/approvals`
- `POST /ops/approvals/resolve`

## Item shape
```json
{
  "id": "string",
  "kind": "clarify|approval|...",
  "title": "string",
  "summary": "string",
  "source": "string",
  "choices": ["..."],
  "status": "pending|resolved",
  "decision": null,
  "created_at": "ISO-8601",
  "resolved_at": null
}
```

## Persistence
- local file: `.data/approvals.json`

## Event integration
Approval lifecycle changes emit operational events:
- `approval.created`
- `approval.resolved`

This keeps approvals visible in the existing event feed and SSE stream.
