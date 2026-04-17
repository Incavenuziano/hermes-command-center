from __future__ import annotations

from http_api import route
from release_hardening import release_hardening


@route('GET', '/ops/security-audit', allow=('GET',))
def ops_security_audit(handler) -> None:
    handler.send_data(release_hardening.security_audit())


@route('GET', '/ops/performance', allow=('GET',))
def ops_performance(handler) -> None:
    handler.send_data(release_hardening.performance_snapshot())


@route('POST', '/ops/state/export', allow=('POST',))
def ops_state_export(handler) -> None:
    handler.read_json_body()
    handler.send_data(release_hardening.export_state())


@route('POST', '/ops/state/restore', allow=('POST',))
def ops_state_restore(handler) -> None:
    payload = handler.read_json_body()
    handler.send_data(release_hardening.restore_state(str(payload.get('export_path') or '')))


@route('GET', '/ops/load-smoke', allow=('GET',))
def ops_load_smoke(handler) -> None:
    handler.send_data(release_hardening.load_smoke())
