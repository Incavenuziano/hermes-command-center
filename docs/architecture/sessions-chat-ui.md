# M2-07 — Sessions/chat UI with streaming and transcript handling

This milestone consumes the M2-04 backend transcript protocol and exposes a real sessions/chat operator view in the stdlib frontend.

## Scope shipped
- dashboard-integrated chat transcript panel
- transcript loading for the selected session
- live SSE subscription against `/ops/chat/stream`
- transcript re-render when `chat.message` events arrive
- session summary showing platform, model, and message count
- tool-call/result visibility in transcript cards

## Current UX
- first available session auto-loads on dashboard refresh
- clicking `Inspect` on a session now loads both:
  - raw session detail JSON
  - normalized chat transcript
- transcript panel shows:
  - stream status
  - session summary
  - ordered message cards
  - tool-call labels for assistant tool invocations
  - tool-result labels for tool messages

## Transport
- initial transcript load uses `GET /ops/chat/transcript`
- live updates use `EventSource` with `GET /ops/chat/stream`
- on each `chat.message`, the UI refreshes transcript state from the canonical transcript route

## Why this closes M2-07
The official item asked for sessions/chat UI with streaming and transcript handling. The frontend now consumes the real Hermes-native transcript contract and renders a practical chat operator view with live stream awareness.

## Follow-on opportunities
- better diff/incremental append instead of full transcript reload on each streamed message
- richer formatting for tool calls and tool outputs
- token/cost annotations if later exposed in transcript contract
- dedicated sessions route/page if M2/M3 scope grows beyond dashboard integration
