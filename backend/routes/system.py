from __future__ import annotations

from config import AUTH_ENABLED, ENV, HOST, PORT, SERVICE_NAME, to_jsonable
from contracts.system import ComponentStatus, SystemComponent, SystemHealth, SystemIdentity
from http_api import route


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
    handler.send_data(to_jsonable(identity))


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
