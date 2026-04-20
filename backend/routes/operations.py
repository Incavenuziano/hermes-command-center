from __future__ import annotations

import time
from datetime import datetime, timezone

from approvals import approvals_store
from audit_log import audit_log_store
from auth import auth_manager
from config import AUTH_ENABLED, ENV, HOST, PORT, SERVICE_NAME
from cron_history import cron_history_store
from derived_state import derived_state_store
from gateway_runtime import gateway_runtime_store
from http_api import AuthenticationRequiredError, RequestValidationError, route
from read_only_mode import read_only_mode_store
from runtime_adapter import runtime_adapter

_SERVER_START = time.monotonic()
_APPROVAL_RISK_BY_KIND = {'db.migrate': 'high', 'shell.run': 'low', 'file.edit': 'medium'}


def _relative_time(iso: str | None) -> str:
    if not iso:
        return 'unknown'
    try:
        dt = datetime.fromisoformat(str(iso).replace('Z', '+00:00'))
        seconds = int((datetime.now(timezone.utc) - dt).total_seconds())
        if seconds < 0:
            return 'just now'
        if seconds < 60:
            return f'{seconds}s ago'
        if seconds < 3600:
            return f'{seconds // 60}m ago'
        if seconds < 86400:
            return f'{seconds // 3600}h ago'
        return f'{seconds // 86400}d ago'
    except Exception:
        return str(iso)


def _format_time_short(iso: str | None) -> str:
    if not iso:
        return ''
    try:
        dt = datetime.fromisoformat(str(iso).replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
    except Exception:
        return str(iso)


def _map_agents_for_panel(agents: list[dict], sessions: list[dict]) -> list[dict]:
    agent_stats: dict[str, dict] = {}
    for s in sessions:
        aid = str(s.get('agent_id') or 'agent-main')
        stats = agent_stats.setdefault(aid, {'sessions': 0, 'tokens': 0, 'cost': 0.0, 'model': None})
        stats['sessions'] += 1
        stats['tokens'] += int(s.get('input_tokens') or 0) + int(s.get('output_tokens') or 0) + int(s.get('reasoning_tokens') or 0)
        stats['cost'] += float(s.get('actual_cost_usd') or 0.0)
        if s.get('model'):
            stats['model'] = s['model']
    result = []
    for agent in agents:
        aid = agent.get('agent_id', '')
        stats = agent_stats.get(aid, {})
        result.append({
            'id': aid,
            'role': agent.get('role', 'worker'),
            'status': agent.get('status', 'unknown'),
            'lastSeen': _relative_time(agent.get('last_seen_at')),
            'model': stats.get('model') or agent.get('model') or 'unknown',
            'sessions': stats.get('sessions', 0),
            'tokens24h': stats.get('tokens', 0),
            'cost24h': round(stats.get('cost', 0.0), 2),
            'avatar': aid[:2].upper() if aid else '??',
        })
    return result


def _map_sessions_for_panel(sessions: list[dict]) -> list[dict]:
    result = []
    for s in sessions:
        tokens = int(s.get('input_tokens') or 0) + int(s.get('output_tokens') or 0) + int(s.get('reasoning_tokens') or 0)
        result.append({
            'id': s.get('session_id', ''),
            'agent': str(s.get('agent_id') or s.get('source') or 'agent-main'),
            'status': s.get('status', 'unknown'),
            'platform': s.get('platform') or s.get('source') or 'cli',
            'title': s.get('title') or s.get('display_name') or s.get('session_id', ''),
            'msgs': 0,
            'started': _format_time_short(s.get('started_at')),
            'tokens': tokens,
        })
    return result


def _event_title(kind: str, source: str, data: dict) -> str:
    if kind == 'system.bootstrap':
        return 'System bootstrap \u00b7 ready'
    if kind.startswith('approval.'):
        action = kind.split('.', 1)[1] if '.' in kind else kind
        return f'Approval {action} \u00b7 {data.get("approval_id", "")}'
    if kind.startswith('session.'):
        action = kind.split('.', 1)[1] if '.' in kind else kind
        return f'Session {action} \u00b7 {data.get("session_id", "")}'
    if kind.startswith('process.'):
        action = kind.split('.', 1)[1] if '.' in kind else kind
        return f'Process {action} \u00b7 {data.get("process_id", "")}'
    if kind.startswith('cron.'):
        action = kind.split('.', 1)[1] if '.' in kind else kind
        name = data.get('name') or data.get('job_id', '')
        return f'{name} \u00b7 {action}'
    return f'{kind} \u00b7 {source}'


def _event_tone(kind: str) -> str:
    if 'error' in kind or 'fail' in kind or 'missed' in kind:
        return 'err'
    if 'warn' in kind or 'threshold' in kind or 'degraded' in kind:
        return 'warn'
    if 'completed' in kind or 'resolved' in kind or 'healthy' in kind:
        return 'ok'
    if 'requested' in kind or 'created' in kind or 'started' in kind:
        return 'acc'
    return ''


def _event_detail(data: dict) -> str:
    skip = {'agent_id', 'session_id', 'process_id', 'job_id', 'approval_id'}
    parts = []
    for key, val in data.items():
        if key in skip:
            continue
        if isinstance(val, str) and val:
            parts.append(val)
        elif isinstance(val, (int, float)):
            parts.append(f'{key}: {val}')
    return ' \u00b7 '.join(parts[:3]) if parts else ''


def _map_events_for_panel(events: list[dict]) -> list[dict]:
    result = []
    for e in events:
        kind = str(e.get('kind', ''))
        source = str(e.get('source', ''))
        data = e.get('data', {}) if isinstance(e.get('data'), dict) else {}
        result.append({
            't': _format_time_short(e.get('at')),
            'kind': kind,
            'source': source,
            'title': _event_title(kind, source, data),
            'tone': _event_tone(kind),
            'detail': _event_detail(data),
        })
    return result


def _map_cron_for_panel(jobs: list[dict]) -> list[dict]:
    result = []
    for j in jobs:
        result.append({
            'id': j.get('job_id', ''),
            'name': j.get('name', ''),
            'schedule': j.get('schedule', 'manual'),
            'next': j.get('next_run_at') or 'unknown',
            'last': j.get('last_status') or 'unknown',
            'enabled': bool(j.get('enabled', False)),
            'duration': '\u2014',
        })
    return result


def _map_approval_for_panel(item: dict) -> dict:
    return {
        'id': item.get('id'),
        'title': item.get('title'),
        'kind': item.get('kind'),
        'source': item.get('source'),
        'at': item.get('created_at'),
        'risk': _APPROVAL_RISK_BY_KIND.get(item.get('kind', ''), 'medium'),
        'preview': item.get('summary', ''),
        'choices': item.get('choices', []),
    }


def _system_health_panel() -> dict:
    uptime_secs = int(time.monotonic() - _SERVER_START)
    hours, remainder = divmod(uptime_secs, 3600)
    minutes = remainder // 60
    if hours >= 24:
        days, hours = divmod(hours, 24)
        uptime_str = f'{days}d {hours}h {minutes}m'
    else:
        uptime_str = f'{hours}h {minutes}m'
    return {
        'env': ENV,
        'bind': f'{HOST}:{PORT}',
        'auth': 'passkey + loopback' if AUTH_ENABLED else 'local-trusted',
        'uptime': uptime_str,
        'version': f'{SERVICE_NAME}/0.4',
    }


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
    overview = derived_state_store.overview()
    pending = approvals_store.list_items()
    mapped_approvals = [
        _map_approval_for_panel(item)
        for item in pending.get('items', [])
        if item.get('status') == 'pending'
    ]
    overview['approvals'] = mapped_approvals
    overview['system_health'] = _system_health_panel()
    panel = {
        'agents': _map_agents_for_panel(overview.get('agents', []), overview.get('sessions', [])),
        'sessions': _map_sessions_for_panel(overview.get('sessions', [])),
        'events': _map_events_for_panel(overview.get('events', [])),
        'approvals': mapped_approvals,
        'system_health': overview['system_health'],
        'service': overview.get('service'),
        'counts': overview.get('counts'),
        'generated_at': overview.get('generated_at'),
    }
    handler.send_panel_data(overview, panel=panel)


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


@route('GET', '/ops/gateway-runtime', allow=('GET',))
def ops_gateway_runtime(handler) -> None:
    _require_authenticated(handler)
    handler.send_data(gateway_runtime_store.get_state())


@route('POST', '/ops/gateway-runtime', allow=('POST',))
def ops_gateway_runtime_update(handler) -> None:
    _require_authenticated(handler)
    payload = handler.read_json_body()
    action = payload.get('action')
    if action not in {'kill', 'start'}:
        raise RequestValidationError(status=400, code='ops.invalid_action', message='Unsupported gateway action', details={'action': action})
    handler.send_data(gateway_runtime_store.set_action(action))


@route('GET', '/ops/cron/jobs', allow=('GET',))
def ops_cron_jobs(handler) -> None:
    _require_authenticated(handler)
    jobs = runtime_adapter.list_cron_jobs()
    handler.send_data({'items': jobs, 'count': len(jobs)})


@route('GET', '/runtime/cron/jobs', allow=('GET',))
def runtime_cron_jobs(handler) -> None:
    _require_authenticated(handler)
    jobs = runtime_adapter.list_cron_jobs()
    handler.send_panel_data(
        {'items': jobs, 'count': len(jobs)},
        panel={'jobs': _map_cron_for_panel(jobs), 'items': jobs, 'count': len(jobs)},
    )


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


@route('GET', '/ops/logs', allow=('GET',))
def ops_logs(handler) -> None:
    _require_authenticated(handler)
    limit_raw = (handler.query_params.get('limit') or [None])[0]
    limit = 50
    if limit_raw is not None:
        try:
            limit = int(limit_raw)
        except ValueError as exc:
            raise RequestValidationError(status=400, code='ops.invalid_request', message='limit must be an integer', details={'field': 'limit'}) from exc
    events = derived_state_store.event_feed(limit=limit)
    audit = audit_log_store.list_entries(limit=limit)
    items = _map_events_for_panel(events.get('items', []))
    for entry in audit.get('items', []):
        items.append({
            't': _format_time_short(entry.get('recorded_at')),
            'kind': f'audit.{entry.get("action_type", "unknown")}',
            'source': entry.get('actor_user', 'system'),
            'title': f'{entry.get("action_type", "")} \u00b7 {entry.get("target_type", "")}:{entry.get("target_id", "")}',
            'tone': 'ok' if entry.get('result') in ('enabled', 'executed', 'ok') else '',
            'detail': entry.get('result', ''),
        })
    handler.send_panel_data(
        {'events': events, 'audit': audit},
        panel={'items': items, 'count': len(items)},
    )


@route('GET', '/ops/agent', allow=('GET',))
def ops_agent_detail(handler) -> None:
    _require_authenticated(handler)
    agent_id = (handler.query_params.get('agent_id') or [None])[0]
    if not agent_id:
        raise RequestValidationError(status=400, code='ops.invalid_request', message='agent_id is required', details={'field': 'agent_id'})
    sessions = runtime_adapter.list_sessions()
    agent_sessions = [s for s in sessions if str(s.get('agent_id') or 'agent-main') == agent_id]
    if not agent_sessions:
        overview_agents = derived_state_store.overview().get('agents', [])
        match = next((a for a in overview_agents if a.get('agent_id') == agent_id), None)
        if match is None:
            raise RequestValidationError(status=404, code='ops.agent_not_found', message='Agent not found', details={'agent_id': agent_id})
    total_tokens = sum(int(s.get('input_tokens') or 0) + int(s.get('output_tokens') or 0) + int(s.get('reasoning_tokens') or 0) for s in agent_sessions)
    total_cost = sum(float(s.get('actual_cost_usd') or 0.0) for s in agent_sessions)
    models = list({s.get('model') for s in agent_sessions if s.get('model')})
    agent = {
        'agent_id': agent_id,
        'id': agent_id,
        'role': 'main' if agent_id == 'agent-main' else 'worker',
        'status': 'active' if any(s.get('status') == 'active' for s in agent_sessions) else 'idle',
        'model': models[0] if models else 'unknown',
        'models': models,
        'session_count': len(agent_sessions),
        'total_tokens': total_tokens,
        'total_cost_usd': round(total_cost, 4),
        'sessions': _map_sessions_for_panel(agent_sessions[:10]),
    }
    handler.send_panel_data(agent)
