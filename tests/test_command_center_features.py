from __future__ import annotations

import json
import os
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import build_app  # noqa: E402


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


def _write_runtime_fixture(base: Path) -> None:
    (base / 'sessions').mkdir(parents=True, exist_ok=True)
    (base / 'cron').mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(base / 'state.db')
    db.execute(
        'CREATE TABLE sessions (id TEXT PRIMARY KEY, source TEXT NOT NULL, user_id TEXT, model TEXT, model_config TEXT, system_prompt TEXT, parent_session_id TEXT, started_at REAL NOT NULL, ended_at REAL, end_reason TEXT, message_count INTEGER DEFAULT 0, tool_call_count INTEGER DEFAULT 0, input_tokens INTEGER DEFAULT 0, output_tokens INTEGER DEFAULT 0, cache_read_tokens INTEGER DEFAULT 0, cache_write_tokens INTEGER DEFAULT 0, reasoning_tokens INTEGER DEFAULT 0, billing_provider TEXT, billing_base_url TEXT, billing_mode TEXT, estimated_cost_usd REAL, actual_cost_usd REAL, cost_status TEXT, cost_source TEXT, pricing_version TEXT, title TEXT)'
    )
    db.execute(
        "INSERT INTO sessions (id, source, user_id, model, started_at, ended_at, title, input_tokens, output_tokens, reasoning_tokens, estimated_cost_usd, actual_cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('sess-live-1', 'telegram', 'u1', 'gpt-5.4', 1000.0, None, 'Live session', 120, 80, 10, 1.10, 1.25),
    )
    db.commit()
    db.close()
    (base / 'sessions' / 'sessions.json').write_text(json.dumps({
        'agent:main:telegram:dm:416112154': {
            'session_key': 'agent:main:telegram:dm:416112154',
            'session_id': 'sess-live-1',
            'updated_at': '2026-04-16T20:00:00',
            'display_name': 'D',
            'platform': 'telegram',
            'chat_type': 'dm',
        }
    }), encoding='utf-8')
    (base / 'sessions' / 'session_sess-live-1.json').write_text(json.dumps({
        'session_id': 'sess-live-1',
        'model': 'gpt-5.4',
        'platform': 'telegram',
        'session_start': '2026-04-16T20:00:00',
        'last_updated': '2026-04-16T20:05:00',
        'message_count': 4,
        'messages': [
            {'role': 'user', 'content': 'hello'},
            {'role': 'assistant', 'content': 'Hi there.'},
            {
                'role': 'assistant',
                'content': '',
                'finish_reason': 'tool_calls',
                'tool_calls': [
                    {
                        'id': 'call-1',
                        'type': 'function',
                        'function': {
                            'name': 'terminal',
                            'arguments': '{"command":"pwd"}',
                        },
                    }
                ],
            },
            {'role': 'tool', 'tool_call_id': 'call-1', 'content': '{"output":"/tmp"}'},
        ],
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    (base / 'processes.json').write_text(json.dumps([
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
    (base / 'cron' / 'jobs.json').write_text(json.dumps({
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
    (base / 'memory.json').write_text(json.dumps({
        'memory': [
            {'id': 'mem-1', 'text': 'Use isolated Hermes Obsidian vault', 'updated_at': '2026-04-16T18:00:00Z'},
        ],
        'user': [
            {'id': 'user-1', 'text': 'Danilo prefers practical end-to-end validation', 'updated_at': '2026-04-16T18:05:00Z'},
        ],
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    (base / 'skills' / 'command-center-demo-skill').mkdir(parents=True, exist_ok=True)
    (base / 'skills' / 'command-center-demo-skill' / 'SKILL.md').write_text('# Demo Skill\n\nUsed for test coverage.\n', encoding='utf-8')
    (base / 'workspace' / 'notes').mkdir(parents=True, exist_ok=True)
    (base / 'workspace' / 'notes' / 'daily.md').write_text('# Daily\n\nHermes workspace note.\n', encoding='utf-8')
    (base / 'profiles.json').write_text(json.dumps({
        'active_profile_id': 'default',
        'profiles': [
            {'id': 'default', 'label': 'Default Operator', 'sensitivity': 'standard', 'requires_reauth': False},
            {'id': 'production', 'label': 'Production Operator', 'sensitivity': 'high', 'requires_reauth': True},
        ],
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    (base / 'gateway.json').write_text(json.dumps({
        'gateway': {'status': 'connected', 'transport': 'telegram', 'bot_token': '123456:super-secret-token'},
        'channels': [
            {'id': 'telegram:416112154', 'label': 'Danilo DM', 'platform': 'telegram', 'delivery_state': 'connected', 'secret': 'chat-secret-value'},
        ],
    }, ensure_ascii=False, indent=2), encoding='utf-8')


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


def test_frontend_shell_uses_sidebar_navigation_and_header_controls():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/html')
    assert 'sidebar-toggle' in body
    assert 'global-search' in body
    assert 'gateway-runtime-button' in body
    assert 'gateway-runtime-status' in body
    assert 'Visão Geral' in body
    assert 'Agentes' in body
    assert 'Trabalhos' in body
    assert 'Conhecimento' in body
    assert 'Sistema' in body
    assert 'Dashboard' in body
    assert 'Usage' in body
    assert 'Conversar' in body
    assert 'Calendario' in body
    assert 'API&#x27;s' in body or 'API\'s' in body or 'API’s' in body or 'API&apos;s' in body


def test_agents_page_is_served_with_same_frontend_shell():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/agents')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/html')
    assert 'Agents Page' in body
    assert 'agents-page-list' in body


def test_cron_page_is_served_with_run_history_and_output_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/cron')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/html')
    assert 'Cron Page' in body
    assert 'cron-page-list' in body
    assert 'cron-run-history' in body
    assert 'cron-output-inspection' in body


def test_activity_page_is_served_with_timeline_virtualization_and_drill_down_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/activity')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/html')
    assert 'Activity Page' in body
    assert 'activity-page-list' in body
    assert 'activity-drilldown' in body
    assert 'activity-window-summary' in body
    assert 'Load More Activity' in body


def test_processes_page_is_served_with_registry_and_detail_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/processes')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/html')
    assert 'Processes Page' in body
    assert 'processes-page-list' in body
    assert 'processes-page-detail' in body
    assert 'processes-page-summary' in body


def test_terminal_strategy_page_is_served_with_risk_posture_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/terminal')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/html')
    assert 'Terminal Strategy' in body
    assert 'terminal-policy-summary' in body
    assert 'terminal-policy-list' in body
    assert 'terminal-policy-detail' in body


def test_memory_page_is_served_with_summary_and_detail_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/memory')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'Memory Page' in body
    assert 'memory-page-list' in body
    assert 'memory-page-detail' in body


def test_skills_page_is_served_with_browser_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/skills')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'Skills Page' in body
    assert 'skills-page-list' in body
    assert 'skills-page-detail' in body


def test_files_page_is_served_with_workspace_browser_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/files')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'Files Page' in body
    assert 'files-page-list' in body
    assert 'files-page-detail' in body


def test_profiles_page_is_served_with_reauth_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/profiles')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'Profiles Page' in body
    assert 'profiles-page-list' in body
    assert 'profiles-page-detail' in body


def test_channels_page_is_served_with_gateway_panels():
    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/channels')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert 'Channels Page' in body
    assert 'channels-page-list' in body
    assert 'channels-page-detail' in body


def test_new_navigation_placeholder_routes_are_served():
    expected = {
        '/usage': 'Usage',
        '/chat': 'Conversar',
        '/sessions': 'Sessões',
        '/tasks': 'Tarefas',
        '/calendar': 'Calendario',
        '/integrations': 'Integrações',
        '/skill': 'Skill',
        '/database': 'DataBase',
        '/apis': 'API',
        '/hooks': 'Segurança Hooks',
        '/preferences': 'Preferencias',
        '/doctor': 'Doctor',
        '/logs': 'Logs',
        '/tailscale': 'Tailscale',
        '/config': 'Config',
    }

    server, thread = _start_test_server()
    try:
        for path, marker in expected.items():
            status, _, body = _request(server, path)
            assert status == 200, path
            assert marker in body, path
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


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
    assert 'renderApprovals' in body
    assert '/ops/approvals' in body
    assert 'renderSystemHealth' in body
    assert '/system/info' in body
    assert '/health' in body
    assert 'renderChatTranscript' in body
    assert '/ops/chat/transcript' in body
    assert '/ops/chat/stream' in body
    assert 'chat-stream-status' in body
    assert 'renderAgentsPage' in body
    assert 'agents-page-list' in body
    assert 'renderCronPage' in body
    assert '/ops/cron/jobs' in body
    assert '/ops/cron/history' in body
    assert 'cron-run-history' in body
    assert 'renderActivityPage' in body
    assert '/ops/activity' in body
    assert 'activity-page-list' in body
    assert 'activity-drilldown' in body
    assert 'activity-load-more' in body
    assert 'renderProcessesPage' in body
    assert '/ops/processes' in body
    assert '/ops/processes/control' in body
    assert 'processes-page-list' in body
    assert 'processes-page-detail' in body
    assert 'renderTerminalPolicyPage' in body
    assert '/ops/terminal-policy' in body
    assert 'terminal-policy-summary' in body
    assert 'terminal-policy-list' in body
    assert 'terminal-policy-detail' in body
    assert 'renderMemoryPage' in body
    assert '/ops/memory' in body
    assert 'memory-page-list' in body
    assert 'renderSkillsPage' in body
    assert '/ops/skills' in body
    assert 'skills-page-list' in body
    assert 'renderFilesPage' in body
    assert '/ops/files' in body
    assert 'files-page-list' in body
    assert 'renderProfilesPage' in body
    assert '/ops/profiles' in body
    assert 'profiles-page-list' in body
    assert 'renderChannelsPage' in body
    assert '/ops/gateway' in body
    assert 'channels-page-list' in body
    assert 'sidebar-toggle' in body
    assert 'global-search' in body
    assert '/ops/gateway-runtime' in body
    assert 'toggleSidebar' in body
    assert 'renderCurrentPage' in body


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
        jobs = json.loads((runtime_home / 'cron' / 'jobs.json').read_text(encoding='utf-8'))
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


def test_cost_telemetry_and_circuit_breaker_status_are_exposed(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    data_dir = tmp_path / 'command-center-data'
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(data_dir))

    server, thread = _start_test_server()
    try:
        initial_status, _, initial_payload = _request(server, '/ops/costs')
        update_status, _, update_payload = _request(
            server,
            '/ops/costs/circuit-breaker',
            method='POST',
            json_body={'max_actual_cost_usd': 1.0, 'max_total_tokens': 150},
        )
        final_status, _, final_payload = _request(server, '/ops/costs')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert initial_status == 200
    assert initial_payload['data']['totals']['actual_cost_usd'] == 1.25
    assert initial_payload['data']['totals']['total_tokens'] == 210
    assert initial_payload['data']['agents'][0]['agent_id'] == 'agent-main'
    assert initial_payload['data']['agents'][0]['actual_cost_usd'] == 1.25
    assert update_status == 200
    assert update_payload['data']['circuit_breaker']['tripped'] is True
    assert final_status == 200
    assert final_payload['data']['circuit_breaker']['tripped'] is True
    assert 'cost_limit_exceeded' in final_payload['data']['circuit_breaker']['reasons']
    assert 'token_limit_exceeded' in final_payload['data']['circuit_breaker']['reasons']


def test_panic_stop_kills_processes_and_pauses_cron_jobs(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    killed = []

    def fake_kill(pid, sig):
        if sig != 0:
            killed.append(pid)

    monkeypatch.setattr('os.kill', fake_kill)

    server, thread = _start_test_server()
    try:
        stop_status, _, stop_payload = _request(server, '/ops/panic-stop', method='POST', json_body={})
        overview_status, _, overview_payload = _request(server, '/ops/overview')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert stop_status == 200
    assert stop_payload['data']['stopped_processes'] == 1
    assert stop_payload['data']['paused_cron_jobs'] == 1
    assert killed == [999999]
    assert overview_status == 200
    assert overview_payload['data']['processes'][0]['status'] == 'termination_requested'
    assert overview_payload['data']['cron_jobs'][0]['status'] == 'paused'


def test_read_only_mode_blocks_mutating_operator_routes(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setattr('os.kill', lambda pid, sig: None)

    server, thread = _start_test_server()
    try:
        mode_status, _, mode_payload = _request(server, '/ops/read-only', method='POST', json_body={'enabled': True, 'reason': 'maintenance'})
        kill_status, _, kill_payload = _request(server, '/ops/processes/kill', method='POST', json_body={'process_id': 'proc-live-1'})
        cron_status, _, cron_payload = _request(server, '/ops/cron/control', method='POST', json_body={'job_id': 'cron-live-1', 'action': 'pause'})
        panic_status, _, panic_payload = _request(server, '/ops/panic-stop', method='POST', json_body={})
        read_status, _, read_payload = _request(server, '/ops/read-only')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert mode_status == 200
    assert mode_payload['data']['enabled'] is True
    assert kill_status == 423
    assert kill_payload['error']['code'] == 'ops.read_only_mode'
    assert cron_status == 423
    assert cron_payload['error']['code'] == 'ops.read_only_mode'
    assert panic_status == 423
    assert panic_payload['error']['code'] == 'ops.read_only_mode'
    assert read_status == 200
    assert read_payload['data']['enabled'] is True
    assert read_payload['data']['reason'] == 'maintenance'


def test_cron_backend_routes_expose_normalized_list_detail_and_history(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))

    server, thread = _start_test_server()
    try:
        list_status, _, list_payload = _request(server, '/ops/cron/jobs')
        detail_status, _, detail_payload = _request(server, '/ops/cron/jobs/cron-live-1')
        history_status, _, history_payload = _request(server, '/ops/cron/history?job_id=cron-live-1')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert list_status == 200
    assert list_payload['data']['count'] == 1
    assert list_payload['data']['items'][0]['job_id'] == 'cron-live-1'
    assert detail_status == 200
    assert detail_payload['data']['job']['job_id'] == 'cron-live-1'
    assert detail_payload['data']['job']['status'] == 'scheduled'
    assert history_status == 200
    assert history_payload['data']['job_id'] == 'cron-live-1'
    assert history_payload['data']['count'] >= 0


def test_runs_activity_timeline_supports_retention_and_kind_filter(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setattr('os.kill', lambda pid, sig: None)

    server, thread = _start_test_server()
    try:
        _request(server, '/ops/processes/kill', method='POST', json_body={'process_id': 'proc-live-1'})
        _request(server, '/ops/cron/control', method='POST', json_body={'job_id': 'cron-live-1', 'action': 'pause'})
        timeline_status, _, timeline_payload = _request(server, '/ops/activity?kind_prefix=cron.&limit=5')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert timeline_status == 200
    assert timeline_payload['data']['count'] >= 1
    assert all(item['kind'].startswith('cron.') for item in timeline_payload['data']['items'])
    assert timeline_payload['data']['retention']['max_items'] == 100


def test_process_registry_backend_exposes_list_detail_and_guarded_controls(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setattr('os.kill', lambda pid, sig: None)

    server, thread = _start_test_server()
    try:
        list_status, _, list_payload = _request(server, '/ops/processes')
        detail_status, _, detail_payload = _request(server, '/ops/processes/proc-live-1')
        invalid_status, _, invalid_payload = _request(
            server,
            '/ops/processes/control',
            method='POST',
            json_body={'process_id': 'proc-live-1', 'action': 'pause'},
        )
        control_status, _, control_payload = _request(
            server,
            '/ops/processes/control',
            method='POST',
            json_body={'process_id': 'proc-live-1', 'action': 'kill'},
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert list_status == 200
    assert list_payload['data']['count'] == 1
    assert list_payload['data']['items'][0]['process_id'] == 'proc-live-1'
    assert list_payload['data']['items'][0]['notify_on_complete'] is False
    assert list_payload['data']['items'][0]['watch_patterns'] == []
    assert detail_status == 200
    assert detail_payload['data']['process']['process_id'] == 'proc-live-1'
    assert detail_payload['data']['process']['task_id'] == 'sess-live-1'
    assert invalid_status == 400
    assert invalid_payload['error']['code'] == 'ops.invalid_action'
    assert control_status == 200
    assert control_payload['data']['process']['process_id'] == 'proc-live-1'
    assert control_payload['data']['event']['kind'] == 'process.kill_requested'
    assert control_payload['data']['audit_entry']['action']['type'] == 'process.kill'


def test_terminal_policy_backend_exposes_disabled_terminal_risk_posture():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/terminal-policy')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['mode'] == 'disabled'
    assert payload['data']['interactive_terminal_enabled'] is False
    assert 'pty shell access' in payload['data']['blocked_features']
    assert 'kill process' in payload['data']['allowed_controls']
    assert payload['data']['revisit_in_milestone'] == 'M4+'


def test_memory_backend_exposes_summary_counts_and_items(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/memory')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['counts']['memory'] == 1
    assert payload['data']['counts']['user'] == 1
    assert payload['data']['items'][0]['scope'] in {'memory', 'user'}


def test_skills_backend_exposes_metadata_views(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/skills')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['count'] == 1
    assert payload['data']['items'][0]['skill_id'] == 'command-center-demo-skill'


def test_files_backend_exposes_safe_workspace_listing_and_preview(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/files')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['count'] >= 1
    assert payload['data']['items'][0]['path']
    assert payload['data']['items'][0]['preview']


def test_profiles_backend_exposes_reauth_rules(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/profiles')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['active_profile_id'] == 'default'
    assert any(item['requires_reauth'] for item in payload['data']['items'])


def test_gateway_backend_exposes_redacted_channel_status(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/gateway')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['gateway']['status'] == 'connected'
    assert payload['data']['gateway']['bot_token_redacted'].endswith('oken')
    assert payload['data']['channels'][0]['secret_redacted'].startswith('***')


def test_security_audit_gate_exposes_overall_regression_status():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/security-audit')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['overall_status'] in {'pass', 'warn'}
    assert payload['data']['checks']
    assert payload['data']['checks'][0]['name']


def test_performance_budget_route_exposes_targets_and_current_snapshot():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/performance')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['budgets']['max_frontend_requests_on_load'] >= 1
    assert payload['data']['snapshot']['route_count'] >= 1


def test_backup_export_and_restore_round_trip(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    export_dir = tmp_path / 'exports'
    monkeypatch.setenv('HCC_EXPORT_DIR', str(export_dir))

    server, thread = _start_test_server()
    try:
        export_status, _, export_payload = _request(server, '/ops/state/export', method='POST', json_body={})
        restore_status, _, restore_payload = _request(server, '/ops/state/restore', method='POST', json_body={'export_path': export_payload['data']['export_path']})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert export_status == 200
    assert export_payload['data']['file_count'] >= 1
    assert Path(export_payload['data']['export_path']).exists()
    assert restore_status == 200
    assert restore_payload['data']['restored'] is True


def test_load_smoke_route_exposes_repeatable_summary():
    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/load-smoke')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['requests_executed'] >= 1
    assert payload['data']['failures'] == 0


def test_release_manifest_and_operator_docs_exist():
    release_doc = PROJECT_ROOT / 'docs' / 'release' / 'release-readiness.md'
    operator_doc = PROJECT_ROOT / 'docs' / 'operations' / 'deployment-and-incident-guide.md'

    assert release_doc.exists()
    assert operator_doc.exists()
    assert 'Release Checklist' in release_doc.read_text(encoding='utf-8')
    assert 'Incident Response' in operator_doc.read_text(encoding='utf-8')


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


def test_operator_actions_are_appended_to_audit_log_and_exposed_via_ops_audit(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setattr('os.kill', lambda pid, sig: None)

    server, thread = _start_test_server()
    try:
        kill_status, _, kill_payload = _request(server, '/ops/processes/kill', method='POST', json_body={'process_id': 'proc-live-1'})
        cron_status, _, cron_payload = _request(server, '/ops/cron/control', method='POST', json_body={'job_id': 'cron-live-1', 'action': 'pause'})
        audit_status, audit_headers, audit_payload = _request(server, '/ops/audit?limit=5')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert kill_status == 200
    assert cron_status == 200
    assert kill_payload['data']['audit_entry']['action']['type'] == 'process.kill'
    assert cron_payload['data']['audit_entry']['action']['type'] == 'cron.pause'
    assert audit_status == 200
    assert audit_headers['X-Request-ID'] == audit_payload['meta']['request_id']
    assert audit_payload['meta']['contract_version'] == '2026-04-15'
    assert audit_payload['data']['count'] == 2
    assert [item['action']['type'] for item in audit_payload['data']['items']] == ['cron.pause', 'process.kill']
    assert audit_payload['data']['items'][0]['actor']['auth_mode'] == 'local-trusted'
    assert audit_payload['data']['items'][0]['action']['target_type'] == 'cron_job'


def test_audit_log_is_append_only_at_sqlite_layer(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    data_dir = tmp_path / 'command-center-data'
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(data_dir))
    monkeypatch.setattr('os.kill', lambda pid, sig: None)

    server, thread = _start_test_server()
    try:
        kill_status, _, kill_payload = _request(server, '/ops/processes/kill', method='POST', json_body={'process_id': 'proc-live-1'})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert kill_status == 200
    db_path = data_dir / 'audit-log.sqlite3'
    assert db_path.exists()

    with sqlite3.connect(db_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE operator_audit_log SET result = 'mutated' WHERE entry_id = 1")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute('DELETE FROM operator_audit_log WHERE entry_id = 1')
        row = conn.execute('SELECT COUNT(*) FROM operator_audit_log').fetchone()

    assert row[0] == 1
    assert kill_payload['data']['audit_entry']['action']['result'] == 'termination_requested'


def test_sse_stream_returns_event_stream_with_ids_and_heartbeat(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setattr('os.kill', lambda pid, sig: None)

    server, thread = _start_test_server()
    try:
        _request(server, '/ops/processes/kill', method='POST', json_body={'process_id': 'proc-live-1'})
        status, headers, body = _request(server, '/ops/stream')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/event-stream')
    assert headers['X-Contract-Version'] == '2026-04-15'
    assert headers['X-Request-ID']
    assert headers['X-Frame-Options'] == 'DENY'
    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert 'retry: 5000' in body
    assert 'event: contract.meta' in body
    assert 'event: health.snapshot' in body
    assert 'event: process.kill_requested' in body
    assert 'id: ' in body
    assert ': heartbeat' in body


def test_sse_stream_replays_only_events_after_last_event_id(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setattr('os.kill', lambda pid, sig: None)

    server, thread = _start_test_server()
    try:
        first_status, _, first_payload = _request(server, '/ops/processes/kill', method='POST', json_body={'process_id': 'proc-live-1'})
        _request(server, '/ops/cron/control', method='POST', json_body={'job_id': 'cron-live-1', 'action': 'pause'})
        last_event_id = first_payload['data']['event']['event_id']
        stream_status, _, stream_body = _request(server, '/ops/stream', headers={'Last-Event-ID': str(last_event_id)})
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert first_status == 200
    assert stream_status == 200
    assert 'event: cron.pause_requested' in stream_body
    assert 'event: process.kill_requested' not in stream_body


def test_chat_transcript_route_returns_normalized_messages_from_hermes_session_file(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))

    server, thread = _start_test_server()
    try:
        status, headers, payload = _request(server, '/ops/chat/transcript?session_id=sess-live-1')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['X-Request-ID'] == payload['meta']['request_id']
    assert payload['data']['session']['session_id'] == 'sess-live-1'
    assert payload['data']['session']['message_count'] == 4
    assert payload['data']['count'] == 4
    assert payload['data']['items'][0]['message_id'] == 1
    assert payload['data']['items'][0]['role'] == 'user'
    assert payload['data']['items'][1]['content'] == 'Hi there.'
    assert payload['data']['items'][2]['tool_calls'][0]['name'] == 'terminal'
    assert payload['data']['items'][3]['tool_call_id'] == 'call-1'


def test_chat_stream_route_emits_contract_and_message_events_with_cursor_support(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))

    server, thread = _start_test_server()
    try:
        status, headers, body = _request(server, '/ops/chat/stream?session_id=sess-live-1&after_id=2')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert headers['Content-Type'].startswith('text/event-stream')
    assert headers['X-Contract-Version'] == '2026-04-15'
    assert headers['X-Request-ID']
    assert 'event: contract.meta' in body
    assert 'event: chat.session' in body
    assert 'event: chat.message' in body
    assert 'id: 3' in body
    assert 'id: 4' in body
    assert 'id: 1' not in body
    assert 'id: 2' not in body
    assert ': heartbeat' in body


def test_chat_ui_contract_has_session_summary_and_tool_call_labels(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))

    server, thread = _start_test_server()
    try:
        status, _, payload = _request(server, '/ops/chat/transcript?session_id=sess-live-1')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert status == 200
    assert payload['data']['session']['platform'] == 'telegram'
    assert payload['data']['session']['model'] == 'gpt-5.4'
    assert payload['data']['items'][2]['tool_calls'][0]['name'] == 'terminal'
    assert payload['data']['items'][3]['role'] == 'tool'


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


def test_approvals_backend_queues_and_resolves_items(tmp_path, monkeypatch):
    runtime_home = tmp_path / 'hermes-home'
    _write_runtime_fixture(runtime_home)
    monkeypatch.setenv('HCC_HERMES_HOME', str(runtime_home))
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))

    server, thread = _start_test_server()
    try:
        list_status, _, list_payload = _request(server, '/ops/approvals')
        create_status, _, create_payload = _request(
            server,
            '/ops/approvals',
            method='POST',
            json_body={
                'kind': 'clarify',
                'title': 'Need operator decision',
                'summary': 'Choose rollout mode',
                'choices': ['safe', 'fast'],
                'source': 'runtime-test',
            },
        )
        item_id = create_payload['data']['item']['id']
        resolve_status, _, resolve_payload = _request(
            server,
            '/ops/approvals/resolve',
            method='POST',
            json_body={'item_id': item_id, 'decision': 'safe'},
        )
        final_status, _, final_payload = _request(server, '/ops/approvals')
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()

    assert list_status == 200
    assert list_payload['data']['count'] == 0
    assert create_status == 200
    assert create_payload['data']['item']['status'] == 'pending'
    assert create_payload['data']['item']['kind'] == 'clarify'
    assert resolve_status == 200
    assert resolve_payload['data']['item']['status'] == 'resolved'
    assert resolve_payload['data']['item']['decision'] == 'safe'
    assert final_status == 200
    assert final_payload['data']['count'] == 1
    assert final_payload['data']['items'][0]['status'] == 'resolved'
