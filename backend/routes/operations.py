from __future__ import annotations

from auth import auth_manager
from derived_state import derived_state_store
from http_api import AuthenticationRequiredError, RequestValidationError, route
from runtime_adapter import runtime_adapter


def _require_authenticated(handler) -> None:
    session_id = handler.require_session_id()
    state = auth_manager.session_state(session_id)
    if not state.authenticated:
        raise AuthenticationRequiredError()


@route('GET', '/ops/overview', allow=('GET',))
def ops_overview(handler) -> None:
    _require_authenticated(handler)
    handler.send_data(derived_state_store.overview())


@route('GET', '/ops/events', allow=('GET',))
def ops_events(handler) -> None:
    _require_authenticated(handler)
    handler.send_data(derived_state_store.event_feed())


@route('GET', '/ops/session', allow=('GET',))
def ops_session(handler) -> None:
    _require_authenticated(handler)
    session_id = (handler.query_params.get('session_id') or [None])[0]
    if not session_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='session_id is required', details={'field': 'session_id'})
    session = runtime_adapter.get_session(session_id)
    if session is None:
        session = next((item for item in derived_state_store.overview().get('sessions', []) if item.get('session_id') == session_id), None)
    if session is None:
        raise RequestValidationError(status=404, code='ops.session_not_found', message='Session not found', details={'session_id': session_id})
    handler.send_data({'session': session})


@route('POST', '/ops/processes/kill', allow=('POST',))
def ops_process_kill(handler) -> None:
    _require_authenticated(handler)
    payload = handler.read_json_body()
    process_id = payload.get('process_id')
    if not isinstance(process_id, str) or not process_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='process_id is required', details={'field': 'process_id'})
    process = runtime_adapter.kill_process(process_id)
    event = derived_state_store.ingest_event({'kind': 'process.kill_requested', 'source': 'command-center', 'data': {'process_id': process_id, 'status': process.get('status')}})
    handler.send_data({'ok': True, 'process': process, 'event': event})


@route('POST', '/ops/cron/control', allow=('POST',))
def ops_cron_control(handler) -> None:
    _require_authenticated(handler)
    payload = handler.read_json_body()
    job_id = payload.get('job_id')
    action = payload.get('action')
    if not isinstance(job_id, str) or not job_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='job_id is required', details={'field': 'job_id'})
    if not isinstance(action, str) or not action:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='action is required', details={'field': 'action'})
    job = runtime_adapter.control_cron_job(job_id, action)
    event = derived_state_store.ingest_event({'kind': f'cron.{action}_requested', 'source': 'command-center', 'data': {'job_id': job_id, 'name': job.get('name'), 'status': job.get('status'), 'schedule': job.get('schedule')}})
    handler.send_data({'ok': True, 'job': job, 'event': event})
