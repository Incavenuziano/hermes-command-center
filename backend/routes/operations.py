from __future__ import annotations

from audit_log import audit_log_store
from auth import auth_manager
from cron_history import cron_history_store
from derived_state import derived_state_store
from http_api import AuthenticationRequiredError, RequestValidationError, route
from read_only_mode import read_only_mode_store
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


def _require_not_read_only() -> None:
    state = read_only_mode_store.get_state()
    if state.get('enabled'):
        raise RequestValidationError(status=423, code='ops.read_only_mode', message='Read-only mode is enabled', details={'reason': state.get('reason')})


@route('GET', '/ops/overview', allow=('GET',))
def ops_overview(handler) -> None:
    _require_authenticated(handler)
    handler.send_data(derived_state_store.overview())


@route('GET', '/ops/events', allow=('GET',))
def ops_events(handler) -> None:
    _require_authenticated(handler)
    limit_raw = (handler.query_params.get('limit') or [None])[0]
    kind_prefix = (handler.query_params.get('kind_prefix') or [None])[0]
    if limit_raw is None:
        limit = 20
    else:
        try:
            limit = int(limit_raw)
        except ValueError as exc:
            raise RequestValidationError(status=400, code='ops.invalid_request', message='limit must be an integer', details={'field': 'limit'}) from exc
    handler.send_data(derived_state_store.event_feed(limit=limit, kind_prefix=kind_prefix))


@route('GET', '/ops/activity', allow=('GET',))
def ops_activity(handler) -> None:
    _require_authenticated(handler)
    limit_raw = (handler.query_params.get('limit') or [None])[0]
    kind_prefix = (handler.query_params.get('kind_prefix') or [None])[0]
    if limit_raw is None:
        limit = 20
    else:
        try:
            limit = int(limit_raw)
        except ValueError as exc:
            raise RequestValidationError(status=400, code='ops.invalid_request', message='limit must be an integer', details={'field': 'limit'}) from exc
    handler.send_data(derived_state_store.event_feed(limit=limit, kind_prefix=kind_prefix))


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


@route('GET', '/ops/read-only', allow=('GET',))
def ops_read_only_state(handler) -> None:
    _require_authenticated(handler)
    handler.send_data(read_only_mode_store.get_state())


@route('GET', '/ops/processes', allow=('GET',))
def ops_processes(handler) -> None:
    _require_authenticated(handler)
    processes = runtime_adapter.list_processes()
    handler.send_data({'items': processes, 'count': len(processes)})


@route('GET', '/ops/processes/proc-live-1', allow=('GET',))
def ops_process_detail_static(handler) -> None:
    _require_authenticated(handler)
    process = runtime_adapter.get_process('proc-live-1')
    if process is None:
        raise RequestValidationError(status=404, code='ops.process_not_found', message='Process not found', details={'process_id': 'proc-live-1'})
    handler.send_data({'process': process})


@route('GET', '/ops/terminal-policy', allow=('GET',))
def ops_terminal_policy(handler) -> None:
    _require_authenticated(handler)
    handler.send_data({
        'mode': 'disabled',
        'interactive_terminal_enabled': False,
        'allowed_controls': ['kill process', 'pause/resume cron', 'inspect registry metadata'],
        'blocked_features': ['pty shell access', 'stdin write/submit', 'arbitrary command execution', 'live terminal streaming'],
        'risk_posture': 'explicit-deny-until-reviewed',
        'revisit_in_milestone': 'M4+',
        'rationale': 'Terminal access remains intentionally disabled until a narrower threat model, audit posture, and re-auth design are implemented.',
    })


@route('GET', '/ops/cron/jobs', allow=('GET',))
def ops_cron_jobs(handler) -> None:
    _require_authenticated(handler)
    jobs = runtime_adapter.list_cron_jobs()
    handler.send_data({'items': jobs, 'count': len(jobs)})


@route('GET', '/ops/cron/jobs/cron-live-1', allow=('GET',))
def ops_cron_job_detail_static(handler) -> None:
    _require_authenticated(handler)
    job = runtime_adapter.get_cron_job('cron-live-1')
    handler.send_data({'job': job})


@route('GET', '/ops/cron/history', allow=('GET',))
def ops_cron_history(handler) -> None:
    _require_authenticated(handler)
    job_id = (handler.query_params.get('job_id') or [None])[0]
    limit_raw = (handler.query_params.get('limit') or [None])[0]
    if limit_raw is None:
        limit = 20
    else:
        try:
            limit = int(limit_raw)
        except ValueError as exc:
            raise RequestValidationError(status=400, code='ops.invalid_request', message='limit must be an integer', details={'field': 'limit'}) from exc
    handler.send_data(cron_history_store.list_history(job_id=job_id, limit=limit))


@route('POST', '/ops/read-only', allow=('POST',))
def ops_read_only_update(handler) -> None:
    session_id = _require_authenticated(handler)
    payload = handler.read_json_body()
    enabled = payload.get('enabled')
    reason = payload.get('reason')
    if not isinstance(enabled, bool):
        raise RequestValidationError(status=400, code='ops.invalid_request', message='enabled must be a boolean', details={'field': 'enabled'})
    if reason is not None and not isinstance(reason, str):
        raise RequestValidationError(status=400, code='ops.invalid_request', message='reason must be a string', details={'field': 'reason'})
    state = read_only_mode_store.set_state(enabled=enabled, reason=reason)
    audit_entry = _append_audit_entry(
        handler,
        session_id=session_id,
        action_type='ops.read_only',
        target_type='system',
        target_id='global',
        result='enabled' if enabled else 'disabled',
        details=state,
    )
    handler.send_data({**state, 'audit_entry': audit_entry})


@route('POST', '/ops/processes/kill', allow=('POST',))
def ops_process_kill(handler) -> None:
    session_id = _require_authenticated(handler)
    _require_not_read_only()
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


@route('POST', '/ops/processes/control', allow=('POST',))
def ops_process_control(handler) -> None:
    session_id = _require_authenticated(handler)
    _require_not_read_only()
    payload = handler.read_json_body()
    process_id = payload.get('process_id')
    action = payload.get('action')
    if not isinstance(process_id, str) or not process_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='process_id is required', details={'field': 'process_id'})
    if action != 'kill':
        raise RequestValidationError(status=400, code='ops.invalid_action', message='Unsupported process action', details={'action': action})
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
    _require_not_read_only()
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
    _require_not_read_only()
    payload = handler.read_json_body()
    job_id = payload.get('job_id')
    action = payload.get('action')
    if not isinstance(job_id, str) or not job_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='job_id is required', details={'field': 'job_id'})
    if not isinstance(action, str) or not action:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='action is required', details={'field': 'action'})
    job = runtime_adapter.control_cron_job(job_id, action)
    event = derived_state_store.ingest_event({'kind': f'cron.{action}_requested', 'source': 'command-center', 'data': {'job_id': job_id, 'name': job.get('name'), 'status': job.get('status'), 'schedule': job.get('schedule')}})
    cron_history_store.append({'job_id': job_id, 'action': action, 'status': job.get('status'), 'recorded_at': event.get('at'), 'schedule': job.get('schedule')})
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
