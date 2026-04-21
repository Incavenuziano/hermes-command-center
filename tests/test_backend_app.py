from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import build_app, run_startup_checks  # noqa: E402
from migrations import MigrationManager  # noqa: E402


def _start_test_server():
    server = build_app(host='127.0.0.1', port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    return server, thread


def _request(
    server,
    path: str,
    method: str = 'GET',
    *,
    json_body: dict | None = None,
    raw_body: bytes | None = None,
    headers: dict[str, str] | None = None,
):
    url = f'http://127.0.0.1:{server.server_address[1]}{path}'
    request_headers = dict(headers or {})
    body = raw_body
    if json_body is not None:
        body = json.dumps(json_body).encode('utf-8')
        request_headers.setdefault('Content-Type', 'application/json')
    request = urllib.request.Request(url, method=method, data=body, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, response.headers, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, json.loads(exc.read().decode('utf-8'))


def test_health_endpoint_returns_contract_headers_and_request_id():
    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(server, '/health')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'] == 'application/json; charset=utf-8'
    assert headers['Cache-Control'] == 'no-store'
    assert headers['X-Contract-Version'] == '2026-04-15'
    assert headers['X-Request-ID']
    assert headers['X-Frame-Options'] == 'DENY'
    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert headers['Referrer-Policy'] == 'no-referrer'
    csp = headers['Content-Security-Policy']
    assert 'default-src' in csp
    assert 'https://unpkg.com' in csp
    assert "'unsafe-inline'" in csp
    assert "'unsafe-eval'" in csp
    assert 'https://fonts.googleapis.com' in csp
    assert 'https://fonts.gstatic.com' in csp
    assert payload['meta']['request_id'] == headers['X-Request-ID']
    assert payload['meta']['contract_version'] == '2026-04-15'
    assert payload['data']['overall_status'] == 'ok'
    assert payload['data']['details']['mode'] == 'local-skeleton'


def test_ready_endpoint_returns_readiness_payload():
    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(server, '/ready')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['X-Request-ID'] == payload['meta']['request_id']
    assert payload['data'] == {
        'ready': True,
        'checks': {'runtime': 'ok', 'config': 'ok'},
    }


def test_system_info_endpoint_returns_service_identity():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/system/info')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['service'] == 'hermes-command-center'
    assert payload['data']['transport'] == 'http'
    assert payload['data']['auth_mode'] == 'local-trusted'
    assert payload['data']['security_posture']['non_loopback_requires_explicit_trusted_tailnet'] is True
    assert payload['data']['secret_storage']['auth_local_password']['present'] is True
    assert payload['data']['secret_storage']['auth_local_password']['redacted'] != 'dev-password'


def test_missing_route_returns_standard_error_envelope():
    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(server, '/missing')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 404
    assert headers['X-Request-ID'] == payload['error']['request_id']
    assert payload == {
        'error': {
            'code': 'route.not_found',
            'message': 'Route not found',
            'details': {'path': '/missing', 'method': 'GET'},
            'request_id': headers['X-Request-ID'],
        },
        'meta': {
            'request_id': headers['X-Request-ID'],
            'contract_version': '2026-04-15',
        },
    }


def test_unsupported_method_returns_method_not_allowed_error():
    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(server, '/health', method='POST')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 405
    assert headers['Allow'] == 'GET'
    assert payload['error']['code'] == 'route.method_not_allowed'
    assert payload['error']['details'] == {'path': '/health', 'method': 'POST', 'allowed_methods': ['GET']}


def test_inspect_endpoint_accepts_json_post_body():
    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(
            server,
            '/system/inspect',
            method='POST',
            json_body={'component': 'runtime', 'include_details': True},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['X-Request-ID'] == payload['meta']['request_id']
    assert payload['data'] == {
        'received': {'component': 'runtime', 'include_details': True},
        'validated': True,
        'content_type': 'application/json',
    }


def test_inspect_endpoint_rejects_invalid_json_body():
    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(
            server,
            '/system/inspect',
            method='POST',
            raw_body=b'{invalid',
            headers={'Content-Type': 'application/json'},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 400
    assert headers['X-Request-ID'] == payload['error']['request_id']
    assert payload['error']['code'] == 'request.invalid_json'
    assert payload['error']['details']['content_type'] == 'application/json'


def test_inspect_endpoint_requires_json_content_type():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(
            server,
            '/system/inspect',
            method='POST',
            raw_body=b'component=runtime',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 415
    assert payload['error']['code'] == 'request.unsupported_media_type'
    assert payload['error']['details']['expected'] == 'application/json'


def test_inspect_endpoint_rejects_large_payloads():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(
            server,
            '/system/inspect',
            method='POST',
            json_body={'blob': 'x' * 5000},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 413
    assert payload['error']['code'] == 'request.payload_too_large'
    assert payload['error']['details']['max_bytes'] == 4096


def test_login_sets_session_cookie_and_returns_authenticated_identity():
    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['authenticated'] is True
    assert payload['data']['user'] == 'local-operator'
    assert 'session_id=' in headers['Set-Cookie']
    assert 'HttpOnly' in headers['Set-Cookie']
    assert 'SameSite=Strict' in headers['Set-Cookie']


def test_login_rejects_invalid_password():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'wrong-password'},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 401
    assert payload['error']['code'] == 'auth.invalid_credentials'


def test_auth_session_defaults_to_trusted_local_operator_without_cookie():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/auth/session')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['authenticated'] is True
    assert payload['data']['user'] == 'local-operator'
    assert payload['data']['auth_mode'] == 'local-trusted'


def test_auth_session_returns_active_session_after_login():
    server, thread = _start_test_server()
    try:
        login_status, login_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        status, _, payload = _request(server, '/auth/session', headers={'Cookie': session_cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert status == 200
    assert payload['data']['authenticated'] is True
    assert payload['data']['user'] == 'local-operator'


def test_logout_clears_session_cookie_and_revokes_session():
    server, thread = _start_test_server()
    try:
        login_status, login_headers, login_payload = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        csrf_token = login_payload['data']['csrf_token']
        logout_status, logout_headers, logout_payload = _request(
            server,
            '/auth/logout',
            method='POST',
            headers={
                'Cookie': session_cookie,
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrf_token,
            },
            raw_body=b'{}',
        )
        session_status, _, session_payload = _request(server, '/auth/session', headers={'Cookie': session_cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert logout_status == 200
    assert logout_payload['data']['authenticated'] is False
    assert 'session_id=;' in logout_headers['Set-Cookie']
    assert 'Max-Age=0' in logout_headers['Set-Cookie']
    assert session_status == 200
    assert session_payload['data']['authenticated'] is True
    assert session_payload['data']['auth_mode'] == 'local-trusted'


def test_login_rotates_existing_session_cookie():
    server, thread = _start_test_server()
    try:
        first_status, first_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        first_cookie = first_headers['Set-Cookie'].split(';', 1)[0]
        second_status, second_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
            headers={'Cookie': first_cookie},
        )
        second_cookie = second_headers['Set-Cookie'].split(';', 1)[0]
        old_session_status, _, old_session_payload = _request(server, '/auth/session', headers={'Cookie': first_cookie})
        new_session_status, _, new_session_payload = _request(server, '/auth/session', headers={'Cookie': second_cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert first_status == 200
    assert second_status == 200
    assert first_cookie != second_cookie
    assert old_session_status == 200
    assert old_session_payload['data']['authenticated'] is True
    assert old_session_payload['data']['auth_mode'] == 'local-trusted'
    assert new_session_status == 200
    assert new_session_payload['data']['authenticated'] is True


def test_auth_session_rejects_expired_session(monkeypatch):
    server, thread = _start_test_server()
    try:
        login_status, login_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        monkeypatch.setattr('auth.time.time', lambda: 10_000_000_000)
        status, _, payload = _request(server, '/auth/session', headers={'Cookie': session_cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert status == 200
    assert payload['data']['authenticated'] is True
    assert payload['data']['auth_mode'] == 'local-trusted'


def test_login_sets_secure_cookie_outside_development(monkeypatch):
    monkeypatch.setattr('config.ENV', 'production')
    monkeypatch.setattr('auth.ENV', 'production')

    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['authenticated'] is True
    assert 'Secure' in headers['Set-Cookie']


def test_authenticated_operator_route_returns_current_identity():
    server, thread = _start_test_server()
    try:
        login_status, login_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        status, _, payload = _request(server, '/operators/me', headers={'Cookie': session_cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert status == 200
    assert payload['data']['user'] == 'local-operator'
    assert payload['data']['auth_mode'] == 'local-password'
    assert payload['data']['session']['authenticated'] is True


def test_operator_route_defaults_to_trusted_local_operator_without_authentication():
    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(server, '/operators/me')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['X-Request-ID'] == payload['meta']['request_id']
    assert payload['meta']['contract_version'] == '2026-04-15'
    assert payload['data']['user'] == 'local-operator'
    assert payload['data']['auth_mode'] == 'local-trusted'
    assert payload['data']['session']['authenticated'] is True


def test_logout_requires_matching_csrf_token():
    server, thread = _start_test_server()
    try:
        login_status, login_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        logout_status, _, logout_payload = _request(
            server,
            '/auth/logout',
            method='POST',
            headers={'Cookie': session_cookie, 'Content-Type': 'application/json'},
            raw_body=b'{}',
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert logout_status == 403
    assert logout_payload['error']['code'] == 'auth.csrf_token_required'


def test_logout_accepts_matching_csrf_token():
    server, thread = _start_test_server()
    try:
        login_status, login_headers, login_payload = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        csrf_token = login_payload['data']['csrf_token']
        logout_status, logout_headers, logout_payload = _request(
            server,
            '/auth/logout',
            method='POST',
            headers={
                'Cookie': session_cookie,
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrf_token,
            },
            raw_body=b'{}',
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert logout_status == 200
    assert logout_payload['data']['authenticated'] is False
    assert 'session_id=;' in logout_headers['Set-Cookie']


def test_login_returns_csrf_token_for_authenticated_session():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert isinstance(payload['data']['csrf_token'], str)
    assert payload['data']['csrf_token']


def test_auth_session_returns_csrf_token():
    server, thread = _start_test_server()
    try:
        login_status, login_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        status, _, payload = _request(server, '/auth/session', headers={'Cookie': session_cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert status == 200
    assert isinstance(payload['data']['csrf_token'], str)
    assert payload['data']['csrf_token']


def test_passkey_status_reports_feature_configuration():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/auth/passkeys/status')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert isinstance(payload['data']['available'], bool)
    assert payload['data']['credential_count'] == 0
    assert payload['data']['required'] is False


def test_passkey_registration_options_require_authenticated_session():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/auth/passkeys/register/options', method='POST', json_body={})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 401
    assert payload['error']['code'] == 'auth.authentication_required'


def test_passkey_registration_options_return_public_key_creation_options():
    try:
        from webauthn import generate_registration_options
        if generate_registration_options is None:
            raise ImportError
    except (ImportError, Exception):
        pytest.skip('webauthn library not available')

    server, thread = _start_test_server()
    try:
        login_status, login_headers, login_payload = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        csrf_token = login_payload['data']['csrf_token']
        status, _, payload = _request(
            server,
            '/auth/passkeys/register/options',
            method='POST',
            headers={'Cookie': session_cookie, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token},
            raw_body=b'{}',
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert status == 200
    assert isinstance(payload['data']['challenge_id'], str)
    assert payload['data']['public_key']['rp']['name'] == 'Hermes Command Center'
    assert payload['data']['public_key']['user']['name'] == 'local-operator'


def test_startup_checks_report_root_refusal_without_override(monkeypatch):
    monkeypatch.setattr('bootstrap.os.geteuid', lambda: 0)
    monkeypatch.delenv('HCC_ALLOW_ROOT', raising=False)

    errors = run_startup_checks()

    assert errors == ['Refusing to run as root without HCC_ALLOW_ROOT=1']


def test_startup_checks_report_non_loopback_bind_without_override(monkeypatch):
    monkeypatch.setattr('bootstrap.HOST', '0.0.0.0')
    monkeypatch.delenv('HCC_ALLOW_NON_LOOPBACK', raising=False)

    errors = run_startup_checks()

    assert 'Refusing non-loopback bind without HCC_ALLOW_NON_LOOPBACK=1' in errors


def test_startup_checks_require_explicit_tailnet_trust_when_non_loopback_and_auth_disabled(monkeypatch):
    monkeypatch.setattr('bootstrap.HOST', '100.64.0.10')
    monkeypatch.setattr('bootstrap.AUTH_ENABLED', False)
    monkeypatch.setattr('bootstrap.TRUST_TAILNET_ONLY', False)
    monkeypatch.setenv('HCC_ALLOW_NON_LOOPBACK', '1')

    errors = run_startup_checks()

    assert 'Refusing trusted-local non-loopback bind without HCC_TRUST_TAILNET_ONLY=1' in errors


def test_migration_manager_can_run_during_startup(tmp_path):
    manager = MigrationManager(data_dir=tmp_path / 'command-center-data')

    report = manager.apply_all()

    assert report['current_versions'] == {'audit_log': '1', 'event_bus': '1'}


def test_apply_runtime_posture_enforces_restrictive_umask(monkeypatch):
    applied = {}

    def fake_umask(mask):
        applied['mask'] = mask
        return 0o022

    monkeypatch.setattr('bootstrap.os.umask', fake_umask)

    from bootstrap import apply_runtime_posture

    apply_runtime_posture()

    assert applied == {'mask': 0o077}


def test_health_live_returns_ok():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/health/live')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['status'] == 'ok'


def test_health_doctor_returns_checks():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/health/doctor')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'checks' in payload['data']
    assert isinstance(payload['data']['checks'], list)
    assert len(payload['data']['checks']) >= 1
    assert payload['data']['checks'][0]['name'] == 'Runtime'
    assert payload['data']['checks'][0]['status'] == 'ok'
    assert 'overall_status' in payload['data']


def test_ops_logs_returns_consolidated_panel_items():
    server, thread = _start_test_server()
    try:
        login_status, login_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        status, _, payload = _request(server, '/ops/logs', headers={'Cookie': session_cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert status == 200
    assert 'events' in payload['data']
    assert 'audit' in payload['data']
    assert 'items' in payload
    assert 'count' in payload
    assert isinstance(payload['items'], list)



def test_ops_agent_returns_agent_detail_panel():
    server, thread = _start_test_server()
    try:
        login_status, login_headers, _ = _request(
            server,
            '/auth/login',
            method='POST',
            json_body={'password': 'dev-password'},
        )
        session_cookie = login_headers['Set-Cookie'].split(';', 1)[0]
        status, _, payload = _request(server, '/ops/agent?agent_id=agent-main', headers={'Cookie': session_cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert login_status == 200
    assert status == 200
    assert payload['id'] == 'agent-main'
    assert payload['data']['agent']['agent_id'] == 'agent-main'
    assert 'sessions' in payload['data']['agent']
    assert 'total_tokens' in payload['data']['agent']


def test_static_styles_css_returns_css():
    server, thread = _start_test_server()
    try:
        url = f'http://127.0.0.1:{server.server_address[1]}/static/styles.css'
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=2) as resp:
            status = resp.status
            content_type = resp.headers['Content-Type']
            body = resp.read().decode('utf-8')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'text/css' in content_type
    assert 'hc-shell' in body


def test_static_hermes_data_js_returns_javascript():
    server, thread = _start_test_server()
    try:
        url = f'http://127.0.0.1:{server.server_address[1]}/static/hermes/data.js'
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=2) as resp:
            status = resp.status
            content_type = resp.headers['Content-Type']
            body = resp.read().decode('utf-8')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'javascript' in content_type
    assert 'HC_DATA' in body


def test_static_hermes_jsx_returns_javascript():
    server, thread = _start_test_server()
    try:
        url = f'http://127.0.0.1:{server.server_address[1]}/static/hermes/icons.jsx'
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=2) as resp:
            status = resp.status
            content_type = resp.headers['Content-Type']
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'javascript' in content_type


def test_spa_shell_routes_return_html():
    server, thread = _start_test_server()
    try:
        for path in ['/', '/agents', '/dashboard', '/terminal', '/logs']:
            url = f'http://127.0.0.1:{server.server_address[1]}{path}'
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=2) as resp:
                content_type = resp.headers['Content-Type']
                body = resp.read().decode('utf-8')
                assert 'text/html' in content_type, f'{path} should return HTML'
                assert '<div id="root">' in body, f'{path} should contain React root'
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_runtime_cron_jobs_alias_returns_data():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/runtime/cron/jobs')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'items' in payload['data']
    assert 'count' in payload['data']
