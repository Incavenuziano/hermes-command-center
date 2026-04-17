from __future__ import annotations

import json
import platform
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_VERIFICATION_DOC = PROJECT_ROOT / 'docs' / 'setup' / 'system-verification.md'
REQUIRED_PATHS = [
    PROJECT_ROOT / 'README.md',
    PROJECT_ROOT / '.gitignore',
    PROJECT_ROOT / 'docs' / 'product-vision.md',
    PROJECT_ROOT / 'docs' / 'security' / 'baseline.md',
    PROJECT_ROOT / 'docs' / 'architecture' / 'token-efficiency.md',
    PROJECT_ROOT / 'docs' / 'architecture' / 'adr-0001-base-strategy.md',
    PROJECT_ROOT / 'backend' / 'app.py',
    PROJECT_ROOT / 'tests' / 'test_backend_app.py',
]


def _command_output(command: list[str]) -> str:
    completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)
    return completed.stdout.strip() or completed.stderr.strip()


def _port_status(host: str, port: int) -> str:
    with socket.socket() as sock:
        sock.settimeout(0.2)
        try:
            sock.connect((host, port))
        except OSError:
            return 'closed'
    return 'open'


def main() -> int:
    missing_paths = [str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_PATHS if not path.exists()]

    doc_content = SYSTEM_VERIFICATION_DOC.read_text(encoding='utf-8') if SYSTEM_VERIFICATION_DOC.exists() else ''
    doc_ok = bool(doc_content) and 'Status: verified' in doc_content and 'detailed verification pending' not in doc_content

    payload = {
        'status': 'ok' if not missing_paths and doc_ok else 'fail',
        'checks': {
            'required_paths': 'ok' if not missing_paths else 'fail',
            'system_verification_doc': 'ok' if doc_ok else 'fail',
        },
        'missing_paths': missing_paths,
        'runtime': {
            'kernel': platform.platform(),
            'python_version': platform.python_version(),
            'node_version': _command_output(['node', '--version']),
            'npm_version': _command_output(['npm', '--version']),
            'sqlite_version': sqlite3.sqlite_version,
            'git_version': _command_output(['git', '--version']),
            'loopback_port_8787': _port_status('127.0.0.1', 8787),
            'wildcard_port_8787': _port_status('0.0.0.0', 8787),
            'is_root': hasattr(sys, 'geteuid') and sys.geteuid() == 0 if hasattr(sys, 'geteuid') else False,
        },
    }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
