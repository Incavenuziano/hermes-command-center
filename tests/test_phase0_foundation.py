from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = PROJECT_ROOT / 'scripts' / 'verify_phase0_foundation.py'
SYSTEM_VERIFICATION_DOC = PROJECT_ROOT / 'docs' / 'setup' / 'system-verification.md'


def test_verify_phase0_foundation_script_reports_runtime_snapshot():
    result = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload['status'] == 'ok'
    assert payload['checks']['required_paths'] == 'ok'
    assert payload['checks']['system_verification_doc'] == 'ok'
    assert payload['runtime']['python_version']
    assert payload['runtime']['git_version'].startswith('git version ')
    assert 'Linux' in payload['runtime']['kernel']


def test_system_verification_doc_contains_recorded_runtime_snapshot():
    content = SYSTEM_VERIFICATION_DOC.read_text(encoding='utf-8')

    assert 'Status: verified' in content
    assert 'detailed verification pending' not in content
    assert '- Python:' in content
    assert '- Node:' in content
    assert '- SQLite:' in content
    assert '- Git:' in content
    assert '- Loopback port 8787:' in content
