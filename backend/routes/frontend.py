from __future__ import annotations

from pathlib import Path

from config import PROJECT_ROOT
from http_api import SECURITY_HEADERS, route

FRONTEND_DIR = PROJECT_ROOT / 'frontend'


def _send_file(handler, path: Path, content_type: str) -> None:
    body = path.read_bytes()
    handler.send_response(200)
    handler.send_header('Content-Type', content_type)
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.send_header('X-Contract-Version', '2026-04-15')
    handler.send_header('X-Request-ID', handler._request_id())
    for header_name, header_value in SECURITY_HEADERS.items():
        handler.send_header(header_name, header_value)
    handler.end_headers()
    handler.wfile.write(body)


def _send_shell(handler) -> None:
    _send_file(handler, FRONTEND_DIR / 'index.html', 'text/html; charset=utf-8')


@route('GET', '/', allow=('GET',))
def shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/agents', allow=('GET',))
def agents_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/cron', allow=('GET',))
def cron_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/activity', allow=('GET',))
def activity_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/processes', allow=('GET',))
def processes_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/terminal', allow=('GET',))
def terminal_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/memory', allow=('GET',))
def memory_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/skills', allow=('GET',))
def skills_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/files', allow=('GET',))
def files_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/profiles', allow=('GET',))
def profiles_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/channels', allow=('GET',))
def channels_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/usage', allow=('GET',))
def usage_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/chat', allow=('GET',))
def chat_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/sessions', allow=('GET',))
def sessions_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/tasks', allow=('GET',))
def tasks_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/calendar', allow=('GET',))
def calendar_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/integrations', allow=('GET',))
def integrations_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/skill', allow=('GET',))
def skill_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/documents', allow=('GET',))
def documents_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/database', allow=('GET',))
def database_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/apis', allow=('GET',))
def apis_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/hooks', allow=('GET',))
def hooks_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/preferences', allow=('GET',))
def preferences_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/doctor', allow=('GET',))
def doctor_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/logs', allow=('GET',))
def logs_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/tailscale', allow=('GET',))
def tailscale_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/config', allow=('GET',))
def config_shell(handler) -> None:
    _send_shell(handler)


@route('GET', '/static/app.js', allow=('GET',))
def app_js(handler) -> None:
    _send_file(handler, FRONTEND_DIR / 'app.js', 'application/javascript; charset=utf-8')


@route('GET', '/static/styles.css', allow=('GET',))
def styles_css(handler) -> None:
    _send_file(handler, FRONTEND_DIR / 'styles.css', 'text/css; charset=utf-8')
