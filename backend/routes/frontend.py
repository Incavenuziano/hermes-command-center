from __future__ import annotations

import mimetypes
from pathlib import Path

from config import PROJECT_ROOT
from http_api import SECURITY_HEADERS, ApiHandler, route

FRONTEND_DIR = PROJECT_ROOT / 'frontend'

MIME_MAP = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.jsx': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
}


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


def _resolve_static(handler) -> None:
    raw_path = handler.path_only
    if not raw_path.startswith('/static/'):
        handler.send_error_envelope(
            status=404, code='route.not_found',
            message='Route not found', details={'path': raw_path, 'method': 'GET'},
        )
        return
    relative = raw_path[len('/static/'):]
    file_path = (FRONTEND_DIR / relative).resolve()
    if not str(file_path).startswith(str(FRONTEND_DIR.resolve())):
        handler.send_error_envelope(
            status=403, code='static.forbidden',
            message='Forbidden', details={'path': raw_path},
        )
        return
    if not file_path.is_file():
        handler.send_error_envelope(
            status=404, code='static.not_found',
            message='Static file not found', details={'path': raw_path},
        )
        return
    suffix = file_path.suffix.lower()
    content_type = MIME_MAP.get(suffix, mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream')
    _send_file(handler, file_path, content_type)


# --- SPA shell routes (all pages serve index.html) ---

_SPA_PAGES = [
    '/', '/agents', '/cron', '/activity', '/processes', '/terminal',
    '/memory', '/skills', '/files', '/profiles', '/channels', '/usage',
    '/chat', '/sessions', '/tasks', '/calendar', '/integrations', '/skill',
    '/documents', '/database', '/apis', '/hooks', '/preferences', '/doctor',
    '/logs', '/tailscale', '/config', '/dashboard',
]

for _page in _SPA_PAGES:
    def _make_handler(page_path):
        @route('GET', page_path, allow=('GET',))
        def _shell_handler(handler, _p=page_path) -> None:
            _send_shell(handler)
        _shell_handler.__name__ = f'shell_{page_path.strip("/") or "root"}'
        return _shell_handler
    _make_handler(_page)


# --- Static asset catch-all ---
# Register known static paths so the router can resolve them.
# The generic handler serves any file under frontend/.

_STATIC_PATHS = [
    '/static/styles.css',
    '/static/app.js',
    '/static/vendor/react.production.min.js',
    '/static/vendor/react-dom.production.min.js',
    '/static/vendor/babel.min.js',
    '/static/hermes/data.js',
    '/static/hermes/icons.jsx',
    '/static/hermes/primitives.jsx',
    '/static/hermes/layout.jsx',
    '/static/hermes/pages_a.jsx',
    '/static/hermes/pages_b.jsx',
    '/static/hermes/pages_c.jsx',
    '/static/hermes/app.jsx',
]

for _static in _STATIC_PATHS:
    def _make_static_handler(static_path):
        @route('GET', static_path, allow=('GET',))
        def _static_handler(handler, _s=static_path) -> None:
            _resolve_static(handler)
        _static_handler.__name__ = f'static_{static_path.strip("/").replace("/", "_").replace(".", "_")}'
        return _static_handler
    _make_static_handler(_static)
