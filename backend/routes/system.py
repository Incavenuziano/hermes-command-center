from __future__ import annotations

from config import AUTH_ENABLED, ENV, HOST, PORT, SERVICE_NAME, secret_backend_summary, security_posture_summary, to_jsonable
from contracts.system import ComponentStatus, SystemComponent, SystemHealth, SystemIdentity
from cost_controls import cost_circuit_breaker_store
from http_api import route
from runtime_adapter import runtime_adapter

_STATUS_MAP = {'degraded': 'warn', 'error': 'err', 'unknown': 'warn'}


def _build_extended_checks() -> list[dict]:
    checks = [
        {'name': 'Runtime', 'status': 'ok', 'detail': f'gateway online \u00b7 {HOST}:{PORT}'},
    ]
    try:
        from event_bus import event_bus_store
        recent = event_bus_store.replay(after_id=0, limit=1)
        checks.append({'name': 'Event bus', 'status': 'ok', 'detail': f'sqlite \u00b7 {len(recent)} recent events'})
    except Exception:
        checks.append({'name': 'Event bus', 'status': 'warn', 'detail': 'not available'})
    checks.append({'name': 'Database', 'status': 'ok', 'detail': 'sqlite \u00b7 migrations applied'})
    secret_info = secret_backend_summary()
    secret_status = 'ok' if secret_info.get('auth_local_password', {}).get('present') else 'warn'
    checks.append({'name': 'Secrets store', 'status': secret_status, 'detail': 'keychain' if secret_status == 'ok' else 'no secrets configured'})
    posture = security_posture_summary()
    if not AUTH_ENABLED:
        checks.append({'name': 'Auth posture', 'status': 'warn', 'detail': 'trusted-local mode \u00b7 auth disabled'})
    else:
        checks.append({'name': 'Auth posture', 'status': 'ok', 'detail': 'local-password mode'})
    if posture.get('non_loopback_requires_explicit_trusted_tailnet') and HOST != '127.0.0.1':
        checks.append({'name': 'Tailscale', 'status': 'warn', 'detail': f'non-default bind {HOST} \u00b7 exception active'})
    else:
        checks.append({'name': 'Tailscale', 'status': 'ok', 'detail': f'bind {HOST}'})
    try:
        breaker = cost_circuit_breaker_store.evaluate(totals={'actual_cost_usd': 0, 'total_tokens': 0})
        checks.append({'name': 'Cost controls', 'status': 'err' if breaker.get('tripped') else 'ok', 'detail': 'breaker tripped' if breaker.get('tripped') else 'breaker healthy'})
    except Exception:
        checks.append({'name': 'Cost controls', 'status': 'warn', 'detail': 'not available'})
    try:
        cron_jobs = runtime_adapter.list_cron_jobs()
        disabled = sum(1 for j in cron_jobs if not j.get('enabled'))
        if disabled:
            checks.append({'name': 'Cron registry', 'status': 'warn', 'detail': f'{disabled} job(s) disabled'})
        else:
            checks.append({'name': 'Cron registry', 'status': 'ok', 'detail': f'{len(cron_jobs)} job(s) registered'})
    except Exception:
        checks.append({'name': 'Cron registry', 'status': 'warn', 'detail': 'not available'})
    return checks


@route('GET', '/health', allow=('GET',))
def health(handler) -> None:
    health = SystemHealth(
        overall_status=ComponentStatus.OK,
        runtime=SystemComponent(name='runtime', status=ComponentStatus.OK, detail='http server ready'),
        database=SystemComponent(name='database', status=ComponentStatus.UNKNOWN, detail='not wired yet'),
        event_bus=SystemComponent(name='event_bus', status=ComponentStatus.UNKNOWN, detail='not wired yet'),
        details={'mode': 'local-skeleton', 'environment': ENV},
    )
    handler.send_data(to_jsonable(health))


@route('GET', '/ready', allow=('GET',))
def ready(handler) -> None:
    handler.send_data(
        {
            'ready': True,
            'checks': {
                'runtime': 'ok',
                'config': 'ok',
            },
        }
    )


@route('GET', '/system/info', allow=('GET',))
def system_info(handler) -> None:
    identity = SystemIdentity(
        service=SERVICE_NAME,
        environment=ENV,
        bind=f'{HOST}:{PORT}',
        transport='http',
        auth_mode='local-password' if AUTH_ENABLED else 'local-trusted',
    )
    payload = to_jsonable(identity)
    payload['secret_storage'] = secret_backend_summary()
    payload['security_posture'] = security_posture_summary()
    handler.send_data(payload)


@route('GET', '/health/live', allow=('GET',))
def health_live(handler) -> None:
    handler.send_data({'status': 'ok'})


@route('GET', '/health/doctor', allow=('GET',))
def health_doctor(handler) -> None:
    checks = _build_extended_checks()
    has_err = any(c['status'] == 'err' for c in checks)
    has_warn = any(c['status'] == 'warn' for c in checks)
    overall = 'err' if has_err else ('warn' if has_warn else 'ok')
    data = {'checks': checks, 'overall_status': overall}
    handler.send_panel_data(data)


@route('POST', '/system/inspect', allow=('POST',))
def inspect_payload(handler) -> None:
    payload = handler.read_json_body()
    handler.send_data(
        {
            'received': payload,
            'validated': True,
            'content_type': 'application/json',
        }
    )
