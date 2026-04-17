from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import build_app  # noqa: E402
import json as _json
import sqlite3
from pathlib import Path as _Path


def _start_test_server():
    server = build_app(host='127.0.0.1', port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.05)
    return server, thread


def _request(server, path: str, method: str = 'GET', *, json_body: dict | None = None, raw_body: bytes | None = None, headers: dict[str, str] | None = None):
    url = f'http://127.0.0.1:{server.server_address[1]}{path}'
    request_headers = dict(headers or {})
    body = raw_body
    if json_body is not None:
        body = json.dumps(json_body).encode('utf-8')
        request_headers.setdefault('Content-Type', 'application/json')
    request = urllib.request.Request(url, method=method, data=body, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = response.read()
            content_type = response.headers.get('Content-Type', '')
            parsed = json.loads(payload.decode('utf-8')) if 'application/json' in content_type else payload.decode('utf-8')
            return response.status, response.headers, parsed
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        content_type = exc.headers.get('Content-Type', '')
        parsed = json.loads(payload.decode('utf-8')) if 'application/json' in content_type else payload.decode('utf-8')
        return exc.code, exc.headers, parsed


def _login(server):
    status, headers, payload = _request(server, '/auth/login', method='POST', json_body={'password': 'dev-password'})
    assert status == 200
    cookie = headers['Set-Cookie'].split(';', 1)[0]
    csrf_token = payload['data']['csrf_token']
    return cookie, csrf_token


def _write_runtime_fixture(base: _Path) -> None:
    (base / 'sessions').mkdir(parents=True, exist_ok=True)
    (base / 'cron').mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(base / 'state.db')
    db.execute(
        'CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT NOT NULL, user_id TEXT, model TEXT, model_config TEXT, system_prompt TEXT, parent_session_id TEXT, started_at REAL NOT NULL, ended_at REAL, end_reason TEXT, message_count INTEGER DEFAULT 0, tool_call_count INTEGER DEFAULT 0, input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0, cache_read_tokens INTEGER DEFAULT 0, cache_write_tokens INTEGER DEFAULT 0, reasoning_tokens INTEGER DEFAULT 0, billing_provider TEXT, billing_base_url TEXT, billing_mode TEXT, estimated_cost_usd REAL, actual_cost_usd REAL, cost_status TEXT, cost_source TEXT, pricing_version TEXT, title TEXT)'
    )
    db.execute(
        "INSERT INTO sessions (id, source, user_id, model, started_at, ended_at, title) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('sess-live-1', 'telegram', 'u1', 'gpt-5.4', 1000.0, None, 'Live session'),
    )
    db.commit()
    db.close()
    (base / 'sessions' / 'sessions.json').write_text(_json.dumps({
        'agent:main:telegram:dm:416112154': {
            'session_key': 'agent:main:telegram:dm:416112154',
            'session_id': 'sess-live-1',
            'updated_at': '2026-04-16T20:00:00',
            'display_name': 'D',
            'platform': 'telegram',
            'chat_type': 'dm',
        }
    }), encoding='utf-8')
    (base / 'processes.json').write_text(_json.dumps([
        {
            'session_id': 'proc-live-1',
            'command': 'python worker.py',
            'pid': 999999,
            'cwd': '/tmp/runtime',
            'started_at': 1001.0,
            'task_id': 'sess-live-1',
            'session_key': 'agent:main:telegram:dm:416112154',
            'notify_on_complete': False,
            'watch_patterns': [],
        }
    ]), encoding='utf-8')
    (base / 'cron' / 'jobs.json').write_text(_json.dumps({
        'jobs': [
            {
                'id': 'cron-live-1',
                'name': 'Daily Scan',
                'schedule_display': '0 7 * * *',
                'enabled': True,
                'state': 'scheduled',
                'next_run_at': '2026-04-17T07:00:00-03:00',
                'last_run_at': None,
                'last_status': None,
            }
        ],
        'updated_at': '2026-04-16T20:00:00-03:00'
    }), encoding='utf-8')


def test_ops_overview_is_available_without_authentication():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/overview')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['service'] == 'hermes-command-center'


def test_ops_overview_returns_derived_state_summary():
    server, thread = _start_test_server()
    try:
        cookie, _ = _login(server)
        status, _, payload = _request(server, '/ops/overview', headers={'Cookie': cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['service'] == 'hermes-command-center'
    assert payload['data']['counts']['sessions'] >= 1
    assert payload['data']['counts']['agents'] >= 1
    assert payload['data']['counts']['processes'] >= 1
    assert payload['data']['counts']['cron_jobs'] >= 1
    assert payload['data']['events']


def test_ops_events_returns_recent_event_feed():
    server, thread = _start_test_server()
    try:
        cookie, _ = _login(server)
        status, _, payload = _request(server, '/ops/events', headers={'Cookie': cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['items']
    assert payload['data']['items'][0]['kind']
    assert payload['data']['items'][0]['source']


def test_frontend_shell_is_served_from_root():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/html')
    assert 'Hermes Command Center' in body
    assert '/static/app.js' in body


def test_frontend_javascript_bundle_is_served():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/static/app.js')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'javascript' in headers['Content-Type']
    assert 'fetchOverview' in body


def test_runtime_event_ingest_requires_valid_csrf_token():
    server, thread = _start_test_server()
    try:
        cookie, _ = _login(server)
        status, _, payload = _request(
            server,
            '/runtime/events',
            method='POST',
            headers={'Cookie': cookie, 'Content-Type': 'application/json'},
            json_body={'kind': 'process.started', 'source': 'hermes-runtime', 'data': {'process_id': 'proc-new'}},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 403
    assert payload['error']['code'] == 'auth.csrf_token_required'


def test_runtime_adapter_populates_overview_from_live_hermes_files(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setattr('os.kill', lambda pid, sig: (_ for _ in ()).throw(ProcessLookupError()))

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/overview')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['counts']['sessions'] == 1
    assert payload['data']['counts']['processes'] == 1
    assert payload['data']['counts']['cron_jobs'] == 1
    assert payload['data']['sessions'][0]['session_id'] == 'sess-live-1'
    assert payload['data']['processes'][0]['process_id'] == 'proc-live-1'
    assert payload['data']['processes'][0]['status'] == 'exited'
    assert payload['data']['cron_jobs'][0]['job_id'] == 'cron-live-1'


def test_session_detail_route_returns_single_runtime_session(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/session?session_id=sess-live-1')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['session']['session_id'] == 'sess-live-1'
    assert payload['data']['session']['title'] == 'Live session'
    assert payload['data']['session']['source'] == 'telegram'


def test_process_kill_action_updates_runtime_event_feed(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    killed = {}

    def fake_kill(pid, sig):
        killed['pid'] = pid
        killed['sig'] = sig

    monkeypatch.setattr('os.kill', fake_kill)

    server, thread = _start_test_server()
    try:
        kill_status, _, kill_payload = _request(server, '/ops/processes/kill', method='POST', json_body={'process_id': 'proc-live-1'})
        events_status, _, events_payload = _request(server, '/ops/events')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert kill_status == 200
    assert kill_payload['data']['ok'] is True
    assert killed['pid'] == 999999
    assert events_status == 200
    assert events_payload['data']['items'][0]['kind'] == 'process.kill_requested'


def test_cron_control_pause_updates_jobs_file_and_event_feed(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))

    server, thread = _start_test_server()
    try:
        pause_status, _, pause_payload = _request(server, '/ops/cron/control', method='POST', json_body={'job_id': 'cron-live-1', 'action': 'pause'})
        jobs = _json.loads((runtime_home / 'cron' / 'jobs.json').read_text(encoding='utf-8'))
        events_status, _, events_payload = _request(server, '/ops/events')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert pause_status == 200
    assert pause_payload['data']['job']['status'] == 'paused'
    assert jobs['jobs'][0]['enabled'] is False
    assert jobs['jobs'][0]['state'] == 'paused'
    assert events_status == 200
    assert events_payload['data']['items'][0]['kind'] == 'cron.pause_requested'


def test_runtime_event_log_persists_across_backend_restart(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setattr('os.kill', lambda pid, sig: None)

    server, thread = _start_test_server()
    try:
        _request(server, '/ops/processes/kill', method='POST', json_body={'process_id': 'proc-live-1'})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/events')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert any(item['kind'] == 'process.kill_requested' for item in payload['data']['items'])


def test_runtime_event_ingest_updates_derived_state_and_feed():
    server, thread = _start_test_server()
    try:
        cookie, csrf_token = _login(server)
        ingest_status, _, ingest_payload = _request(
            server,
            '/runtime/events',
            method='POST',
            headers={'Cookie': cookie, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token},
            json_body={
                'kind': 'session.started',
                'source': 'hermes-runtime',
                'data': {'session_id': 'session-test-42', 'agent_id': 'agent-main', 'status': 'running'},
            },
        )
        overview_status, _, overview_payload = _request(server, '/ops/overview', headers={'Cookie': cookie})
        events_status, _, events_payload = _request(server, '/ops/events', headers={'Cookie': cookie})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert ingest_status == 200
    assert ingest_payload['data']['accepted'] is True
    assert overview_status == 200
    session_ids = {item['session_id'] for item in overview_payload['data']['sessions']}
    assert 'session-test-42' in session_ids
    assert events_status == 200
    assert events_payload['data']['items'][0]['kind'] == 'session.started'
    assert events_payload['data']['items'][0]['source'] == 'hermes-runtime'
