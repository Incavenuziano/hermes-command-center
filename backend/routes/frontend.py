from __future__ import annotations

from pathlib import Path

from config import PROJECT_ROOT
from http_api import route

FRONTEND_DIR = PROJECT_ROOT / 'frontend'


def _send_file(handler, path: Path, content_type: str) -> None:
    body = path.read_bytes()
    handler.send_response(200)
    handler.send_header('Content-Type', content_type)
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.send_header('X-Contract-Version', '2026-04-15')
    handler.send_header('X-Request-ID', handler._request_id())
    handler.end_headers()
    handler.wfile.write(body)


@route('GET', '/', allow=('GET',))
def shell(handler) -> None:
    _send_file(handler, FRONTEND_DIR / 'index.html', 'text/html; charset=utf-8')


@route('GET', '/static/app.js', allow=('GET',))
def app_js(handler) -> None:
    _send_file(handler, FRONTEND_DIR / 'app.js', 'application/javascript; charset=utf-8')


@route('GET', '/static/styles.css', allow=('GET',))
def styles_css(handler) -> None:
    _send_file(handler, FRONTEND_DIR / 'styles.css', 'text/css; charset=utf-8')
