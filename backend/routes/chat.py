from __future__ import annotations

from auth import auth_manager
from chat_protocol import chat_transcript_store
from config import CONTRACT_VERSION
from http_api import AuthenticationRequiredError, RequestValidationError, SECURITY_HEADERS, route
from routes.events import HEARTBEAT_MS, _encode_sse_frame


def _require_authenticated(handler) -> None:
    session_id = handler.require_session_id()
    state = auth_manager.session_state(session_id)
    if not state.authenticated:
        raise AuthenticationRequiredError()


def _required_session_id(handler) -> str:
    session_id = (handler.query_params.get('session_id') or [None])[0]
    if not session_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='session_id is required', details={'field': 'session_id'})
    return session_id


def _parse_after_id(handler) -> int:
    raw_value = handler.headers.get('Last-Event-ID')
    if not raw_value:
        raw_value = (handler.query_params.get('after_id') or ['0'])[0]
    try:
        after_id = int(str(raw_value))
    except ValueError as exc:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='after_id must be an integer', details={'field': 'after_id'}) from exc
    if after_id < 0:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='after_id must be non-negative', details={'field': 'after_id'})
    return after_id


@route('GET', '/ops/chat/transcript', allow=('GET',))
def ops_chat_transcript(handler) -> None:
    _require_authenticated(handler)
    session_id = _required_session_id(handler)
    handler.send_data(chat_transcript_store.transcript(session_id))


@route('GET', '/ops/chat/stream', allow=('GET',))
def ops_chat_stream(handler) -> None:
    _require_authenticated(handler)
    session_id = _required_session_id(handler)
    after_id = _parse_after_id(handler)
    transcript = chat_transcript_store.transcript(session_id)
    body_parts = [
        _encode_sse_frame(
            event='contract.meta',
            data={'contract_version': CONTRACT_VERSION, 'transport': 'sse', 'channel': 'chat'},
            retry_ms=HEARTBEAT_MS,
        ),
        _encode_sse_frame(event='chat.session', data=transcript['session']),
    ]
    for item in transcript['items']:
        if int(item['message_id']) <= after_id:
            continue
        body_parts.append(_encode_sse_frame(event='chat.message', event_id=int(item['message_id']), data=item))
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
