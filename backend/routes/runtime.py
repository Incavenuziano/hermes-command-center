from __future__ import annotations

from auth import auth_manager
from derived_state import derived_state_store
from http_api import AuthenticationRequiredError, RequestValidationError, route


@route('POST', '/runtime/events', allow=('POST',))
def runtime_events(handler) -> None:
    payload = handler.read_json_body()
    session_id = handler.require_csrf_token(auth_manager.is_valid_csrf_token)
    state = auth_manager.session_state(session_id)
    if not state.authenticated:
        raise AuthenticationRequiredError()

    kind = payload.get('kind')
    source = payload.get('source')
    data = payload.get('data', {})
    if not isinstance(kind, str) or not kind:
        raise RequestValidationError(status=400, code='runtime.invalid_event', message='kind is required', details={'field': 'kind'})
    if not isinstance(source, str) or not source:
        raise RequestValidationError(status=400, code='runtime.invalid_event', message='source is required', details={'field': 'source'})
    if not isinstance(data, dict):
        raise RequestValidationError(status=400, code='runtime.invalid_event', message='data must be an object', details={'field': 'data'})

    event = derived_state_store.ingest_event({'kind': kind, 'source': source, 'data': data})
    handler.send_data({'accepted': True, 'event': event})
