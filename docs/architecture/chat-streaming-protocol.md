# M2-04 — Hermes-native chat streaming route/protocol

This document defines the backend-native chat transcript surfaces used by Hermes Command Center before the dedicated sessions/chat UI is built.

## Goals
- expose real Hermes session transcripts from `~/.hermes/sessions/session_<session_id>.json`
- normalize message records into a stable Command Center contract
- provide both pull and streaming read surfaces so UI work in M2-07 can build on a fixed protocol

## Routes

### `GET /ops/chat/transcript?session_id=<id>`
Returns a canonical JSON envelope:

```json
{
  "data": {
    "session": {
      "session_id": "...",
      "model": "...",
      "platform": "telegram",
      "started_at": "...",
      "updated_at": "...",
      "message_count": 4
    },
    "items": [
      {
        "message_id": 1,
        "role": "user",
        "content": "hello",
        "tool_call_id": null,
        "tool_calls": [],
        "finish_reason": null
      }
    ],
    "count": 4,
    "last_message_id": 4
  },
  "meta": {
    "request_id": "...",
    "contract_version": "2026-04-15"
  }
}
```

### `GET /ops/chat/stream?session_id=<id>&after_id=<n>`
Returns finite SSE output with:
1. `contract.meta`
2. `chat.session`
3. one `chat.message` event per normalized message after the cursor
4. final heartbeat comment

The route also accepts `Last-Event-ID` as an SSE cursor equivalent.

## Message normalization rules
- source of truth is the Hermes session file `messages[]`
- `message_id` is a stable 1-based ordinal position in that file
- `role` is preserved from Hermes (`user`, `assistant`, `tool`, etc.)
- `content` remains raw string content
- `tool_call_id` is preserved for tool result messages
- `tool_calls[]` is normalized to lightweight metadata:
  - `id`
  - `type`
  - `name`
  - `arguments`
- `finish_reason` is preserved when present
- reasoning internals are intentionally not exposed in this MVP contract

## Current behavior
- read-only backend surface only; no transcript mutation yet
- finite SSE response mirrors the pragmatic M1 event-bus pattern used elsewhere in the MVP
- authentication follows the current trusted-local / operator session rules already used across `/ops/*`

## Why this closes M2-04
M2-04 was scoped to route/protocol, not full sessions/chat UX. This ships the Hermes-native transcript contract and a streaming transport that M2-07 can consume directly.
