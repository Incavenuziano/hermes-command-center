from __future__ import annotations

import json

from auth import auth_manager
from config import CONTRACT_VERSION
from derived_state import derived_state_store
from event_bus import event_bus_store
from http_api import AuthenticationRequiredError, RequestValidationError, SECURITY_HEADERS, route

HEARTBEAT_MS = 5000


def _map_event_tone(kind: str) -> str:
    if kind.startswith('approval.'):
        return 'acc'
    if kind.endswith('.failed') or kind.endswith('.error') or kind.endswith('.missed'):
        return 'err'
    if kind.endswith('.completed') or kind.endswith('.ok'):
        return 'ok'
    return ''


def _event_title(kind: str, source: str, data: dict) -> str:
    if kind == 'system.bootstrap':
        return 'System bootstrap · ready'
    if kind.startswith('approval.'):
        action = kind.split('.', 1)[1]
        return f"Approval {action} · {data.get('approval_id', '')}"
    if kind.startswith('session.'):
        action = kind.split('.', 1)[1]
        return f"Session {action} · {data.get('session_id', '')}"
    if kind.startswith('process.'):
        action = kind.split('.', 1)[1]
        return f"Process {action} · {data.get('process_id', '')}"
    if kind.startswith('cron.'):
        action = kind.split('.', 1)[1]
        name = data.get('name') or data.get('job_id', '')
        return f'{name} · {action}'
    return f'{kind} · {source}'


def _event_detail(data: dict) -> str:
    skip = {'agent_id', 'session_id', 'process_id', 'job_id', 'approval_id'}
    parts: list[str] = []
    for key, val in data.items():
        if key in skip:
            continue
        if isinstance(val, str) and val:
            parts.append(val)
        elif isinstance(val, (int, float)):
            parts.append(f'{key}: {val}')
    return ' · '.join(parts[:3]) if parts else ''


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
            event='contract.meta',
            data={'contract_version': CONTRACT_VERSION, 'transport': 'sse', 'channel': 'ops'},
            retry_ms=HEARTBEAT_MS,
        ),
        _encode_sse_frame(
            event='health.snapshot',
            data={
                'service': overview.get('service'),
                'generated_at': overview.get('generated_at'),
                'counts': overview.get('counts', {}),
            },
        )
    ]
    for item in replay:
        event_type = str(item['event_type'])
        source_name = item['source']
        payload_data = item['payload'] if isinstance(item.get('payload'), dict) else {}
        body_parts.append(
            _encode_sse_frame(
                event=event_type,
                event_id=int(item['event_id']),
                data={
                    'source': source_name,
                    'channel': item['channel'],
                    'recorded_at': item['recorded_at'],
                    'payload': payload_data,
                },
            )
        )
        body_parts.append(
            _encode_sse_frame(
                event='activity',
                event_id=int(item['event_id']),
                data={
                    't': item['recorded_at'],
                    'kind': event_type,
                    'source': source_name,
                    'title': _event_title(event_type, source_name, payload_data),
                    'tone': _map_event_tone(event_type),
                    'detail': _event_detail(payload_data),
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
    handler.send_header('X-Contract-Version', CONTRACT_VERSION)
    handler.send_header('X-Request-ID', handler._request_id())
    for header_name, header_value in SECURITY_HEADERS.items():
        handler.send_header(header_name, header_value)
    handler.end_headers()
    handler.wfile.write(body)
