from __future__ import annotations

from config import AUTH_ENABLED, ENV, HOST, PORT, SERVICE_NAME, secret_backend_summary, security_posture_summary, to_jsonable
from contracts.system import ComponentStatus, SystemComponent, SystemHealth, SystemIdentity
from cost_controls import cost_circuit_breaker_store
from http_api import route
from runtime_adapter import runtime_adapter


_STATUS_MAP = {'degraded': 'warn', 'error': 'err'}


def _build_extended_checks() -> list[dict]:
    checks = [
        {'name': 'Runtime', 'status': 'ok', 'detail': f'http server ready · {HOST}:{PORT}'},
        {'name': 'Database', 'status': 'warn', 'detail': 'sqlite store not fully wired for health probing'},
        {'name': 'Event bus', 'status': 'warn', 'detail': 'event bus health not yet actively probed'},
    ]
    secret_info = secret_backend_summary()
    auth_secret_present = bool(secret_info.get('auth_local_password', {}).get('present'))
    checks.append(
        {
            'name': 'Secrets store',
            'status': 'ok' if auth_secret_present else 'warn',
            'detail': 'local auth secret present' if auth_secret_present else 'no local auth secret configured',
        }
    )
    checks.append(
        {
            'name': 'Auth posture',
            'status': 'ok' if AUTH_ENABLED else 'warn',
            'detail': 'local-password mode' if AUTH_ENABLED else 'trusted-local mode active',
        }
    )
    checks.append(
        {
            'name': 'Tailscale',
            'status': 'warn' if HOST != '127.0.0.1' else 'ok',
            'detail': f'bind {HOST}:{PORT}',
        }
    )
    try:
        breaker = cost_circuit_breaker_store.evaluate(totals={'actual_cost_usd': 0, 'total_tokens': 0})
        checks.append(
            {
                'name': 'Cost controls',
                'status': 'err' if breaker.get('tripped') else 'ok',
                'detail': 'breaker tripped' if breaker.get('tripped') else 'breaker healthy',
            }
        )
    except Exception:
        checks.append({'name': 'Cost controls', 'status': 'warn', 'detail': 'cost controls unavailable'})
    try:
        cron_jobs = runtime_adapter.list_cron_jobs()
        disabled = sum(1 for job in cron_jobs if not job.get('enabled'))
        checks.append(
            {
                'name': 'Cron registry',
                'status': 'warn' if disabled else 'ok',
                'detail': f'{disabled} job(s) disabled' if disabled else f'{len(cron_jobs)} job(s) registered',
            }
        )
    except Exception:
        checks.append({'name': 'Cron registry', 'status': 'warn', 'detail': 'cron registry unavailable'})
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
    has_err = any(check['status'] == 'err' for check in checks)
    has_warn = any(check['status'] == 'warn' for check in checks)
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
