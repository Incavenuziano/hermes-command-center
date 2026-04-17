from __future__ import annotations

from audit_log import audit_log_store
from auth import auth_manager
from derived_state import derived_state_store
from http_api import AuthenticationRequiredError, RequestValidationError, route
from runtime_adapter import runtime_adapter


def _session_actor(handler, session_id: str) -> dict[str, str]:
    state = auth_manager.session_state(session_id)
    return {
        'session_id': session_id,
        'user': state.user,
        'auth_mode': state.auth_mode,
    }


def _append_audit_entry(
    handler,
    *,
    session_id: str,
    action_type: str,
    target_type: str,
    target_id: str,
    result: str,
    details: dict[str, object],
) -> dict[str, object]:
    actor = _session_actor(handler, session_id)
    return audit_log_store.append_entry(
        actor_session_id=actor['session_id'],
        actor_user=actor['user'],
        auth_mode=actor['auth_mode'],
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        result=result,
        details=details,
    )


def _require_authenticated(handler) -> str:
    session_id = handler.require_session_id()
    state = auth_manager.session_state(session_id)
    if not state.authenticated:
        raise AuthenticationRequiredError()
    return session_id


@route('GET', '/ops/overview', allow=('GET',))
def ops_overview(handler) -> None:
    _require_authenticated(handler)
    handler.send_data(derived_state_store.overview())


@route('GET', '/ops/events', allow=('GET',))
def ops_events(handler) -> None:
    _require_authenticated(handler)
    handler.send_data(derived_state_store.event_feed())


@route('GET', '/ops/audit', allow=('GET',))
def ops_audit(handler) -> None:
    _require_authenticated(handler)
    limit = (handler.query_params.get('limit') or [None])[0]
    if limit is None:
        bounded_limit = 20
    else:
        try:
            bounded_limit = int(limit)
        except ValueError as exc:
            raise RequestValidationError(status=400, code='ops.invalid_request', message='limit must be an integer', details={'field': 'limit'}) from exc
    handler.send_data(audit_log_store.list_entries(limit=bounded_limit))


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
    session_id = _require_authenticated(handler)
    payload = handler.read_json_body()
    process_id = payload.get('process_id')
    if not isinstance(process_id, str) or not process_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='process_id is required', details={'field': 'process_id'})
    process = runtime_adapter.kill_process(process_id)
    event = derived_state_store.ingest_event({'kind': 'process.kill_requested', 'source': 'command-center', 'data': {'process_id': process_id, 'status': process.get('status')}})
    audit_entry = _append_audit_entry(
        handler,
        session_id=session_id,
        action_type='process.kill',
        target_type='process',
        target_id=process_id,
        result=str(process.get('status') or 'unknown'),
        details={'process': process, 'event_kind': event['kind']},
    )
    handler.send_data({'ok': True, 'process': process, 'event': event, 'audit_entry': audit_entry})


@route('POST', '/ops/panic-stop', allow=('POST',))
def ops_panic_stop(handler) -> None:
    session_id = _require_authenticated(handler)
    handler.read_json_body()
    stopped_processes = []
    paused_jobs = []
    for process in runtime_adapter.list_processes():
        if process.get('status') != 'running':
            continue
        process_id = process.get('process_id')
        if not isinstance(process_id, str):
            continue
        stopped_processes.append(runtime_adapter.kill_process(process_id))
        derived_state_store.ingest_event({'kind': 'process.kill_requested', 'source': 'command-center', 'data': {'process_id': process_id, 'status': stopped_processes[-1].get('status')}})
    for job in runtime_adapter.list_cron_jobs():
        if not job.get('enabled'):
            continue
        job_id = job.get('job_id')
        if not isinstance(job_id, str):
            continue
        paused_jobs.append(runtime_adapter.control_cron_job(job_id, 'pause'))
        derived_state_store.ingest_event({'kind': 'cron.pause_requested', 'source': 'command-center', 'data': {'job_id': job_id, 'name': paused_jobs[-1].get('name'), 'status': paused_jobs[-1].get('status'), 'schedule': paused_jobs[-1].get('schedule')}})
    audit_entry = _append_audit_entry(
        handler,
        session_id=session_id,
        action_type='ops.panic_stop',
        target_type='system',
        target_id='global',
        result='executed',
        details={'stopped_processes': len(stopped_processes), 'paused_cron_jobs': len(paused_jobs)},
    )
    handler.send_data({'ok': True, 'stopped_processes': len(stopped_processes), 'paused_cron_jobs': len(paused_jobs), 'audit_entry': audit_entry})


@route('POST', '/ops/cron/control', allow=('POST',))
def ops_cron_control(handler) -> None:
    session_id = _require_authenticated(handler)
    payload = handler.read_json_body()
    job_id = payload.get('job_id')
    action = payload.get('action')
    if not isinstance(job_id, str) or not job_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='job_id is required', details={'field': 'job_id'})
    if not isinstance(action, str) or not action:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='action is required', details={'field': 'action'})
    job = runtime_adapter.control_cron_job(job_id, action)
    event = derived_state_store.ingest_event({'kind': f'cron.{action}_requested', 'source': 'command-center', 'data': {'job_id': job_id, 'name': job.get('name'), 'status': job.get('status'), 'schedule': job.get('schedule')}})
    audit_entry = _append_audit_entry(
        handler,
        session_id=session_id,
        action_type=f'cron.{action}',
        target_type='cron_job',
        target_id=job_id,
        result=str(job.get('status') or 'unknown'),
        details={'job': job, 'event_kind': event['kind']},
    )
    handler.send_data({'ok': True, 'job': job, 'event': event, 'audit_entry': audit_entry})
