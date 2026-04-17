from __future__ import annotations

import json

from auth import auth_manager
from derived_state import derived_state_store
from event_bus import event_bus_store
from http_api import AuthenticationRequiredError, RequestValidationError, route

HEARTBEAT_MS = 5000


def _require_authenticated(handler) -> None:
    session_id = handler.require_session_id()
    state = auth_manager.session_state(session_id)
    if not state.authenticated:
        raise AuthenticationRequiredError()


def _parse_last_event_id(handler) -> int | None:
    raw_value = handler.headers.get('Last-Event-ID')
    if not raw_value:
        raw_value = (handler.query_params.get('after_id') or [None])[0]
    if raw_value in (None, ''):
        return None
    try:
        parsed = int(str(raw_value))
    except ValueError as exc:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='Last-Event-ID must be an integer', details={'field': 'Last-Event-ID'}) from exc
    if parsed < 0:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='Last-Event-ID must be non-negative', details={'field': 'Last-Event-ID'})
    return parsed


def _encode_sse_frame(*, event: str, data: dict[str, object], event_id: int | None = None, retry_ms: int | None = None) -> str:
    lines: list[str] = []
    if retry_ms is not None:
        lines.append(f'retry: {retry_ms}')
    if event_id is not None:
        lines.append(f'id: {event_id}')
    lines.append(f'event: {event}')
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    for line in payload.splitlines() or ['{}']:
        lines.append(f'data: {line}')
    return '\n'.join(lines) + '\n\n'


@route('GET', '/ops/stream', allow=('GET',))
def ops_stream(handler) -> None:
    _require_authenticated(handler)
    after_id = _parse_last_event_id(handler)
    replay = event_bus_store.replay(after_id=after_id, limit=100)
    overview = derived_state_store.overview()
    body_parts = [
        _encode_sse_frame(
            event='health.snapshot',
            data={
                'service': overview.get('service'),
                'generated_at': overview.get('generated_at'),
                'counts': overview.get('counts', {}),
            },
            retry_ms=HEARTBEAT_MS,
        )
    ]
    for item in replay:
        body_parts.append(
            _encode_sse_frame(
                event=str(item['event_type']),
                event_id=int(item['event_id']),
                data={
                    'source': item['source'],
                    'channel': item['channel'],
                    'recorded_at': item['recorded_at'],
                    'payload': item['payload'],
                },
            )
        )
    body_parts.append(': heartbeat\n\n')
    body = ''.join(body_parts).encode('utf-8')
    handler.send_response(200)
    handler.send_header('Content-Type', 'text/event-stream; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.send_header('Connection', 'close')
    handler.send_header('X-Contract-Version', '2026-04-15')
    handler.send_header('X-Request-ID', handler._request_id())
    handler.end_headers()
    handler.wfile.write(body)
