from __future__ import annotations

import os
import sys
from http.server import ThreadingHTTPServer

from config import AUTH_ENABLED, HOST, PORT, TRUST_TAILNET_ONLY, configure_logging
from http_api import ApiHandler
from migrations import migration_manager
from routes import system  # noqa: F401  Ensures route registration.


def apply_runtime_posture() -> None:
    os.umask(0o077)


def run_startup_checks() -> list[str]:
    errors: list[str] = []
    if hasattr(os, 'geteuid') and os.geteuid() == 0 and os.getenv('HCC_ALLOW_ROOT') != '1':
        errors.append('Refusing to run as root without HCC_ALLOW_ROOT=1')

    non_loopback_bind = HOST not in {'127.0.0.1', 'localhost'}
    if non_loopback_bind and os.getenv('HCC_ALLOW_NON_LOOPBACK') != '1':
        errors.append('Refusing non-loopback bind without HCC_ALLOW_NON_LOOPBACK=1')
    if non_loopback_bind and not AUTH_ENABLED and not TRUST_TAILNET_ONLY:
        errors.append('Refusing trusted-local non-loopback bind without HCC_TRUST_TAILNET_ONLY=1')

    if not (1 <= PORT <= 65535):
        errors.append('HCC_PORT must be between 1 and 65535')

    return errors


def build_app(host: str = HOST, port: int = PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), ApiHandler)


def main() -> None:
    startup_errors = run_startup_checks()
    if startup_errors:
        raise SystemExit('\n'.join(startup_errors))

    configure_logging()
    apply_runtime_posture()
    migration_manager.apply_all()
    server = build_app()
    print(f'Hermes Command Center listening on http://{HOST}:{PORT}', file=sys.stderr)
    server.serve_forever()
