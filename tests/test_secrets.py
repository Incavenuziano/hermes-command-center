from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from secrets_store import SecretStore, redact_secret_value  # noqa: E402


def test_secret_store_prefers_environment_over_local_store(tmp_path, monkeypatch):
    monkeypatch.setenv('HCC_DATA_DIR', str(tmp_path / 'command-center-data'))
    monkeypatch.setenv('HCC_ALLOW_PLAINTEXT_SECRETS', '1')
    monkeypatch.setenv('HCC_TEST_SECRET', 'env-secret')
    store = SecretStore()
    store.set_secret('test.secret', 'file-secret')

    value, metadata = store.resolve_with_metadata('test.secret', env_var='HCC_TEST_SECRET')

    assert value == 'env-secret'
    assert metadata['backend'] == 'environment'


def test_secret_store_uses_plaintext_fallback_with_strict_permissions(tmp_path, monkeypatch):
    data_dir = tmp_path / 'command-center-data'
    monkeypatch.setenv('HCC_DATA_DIR', str(data_dir))
    monkeypatch.setenv('HCC_ALLOW_PLAINTEXT_SECRETS', '1')
    store = SecretStore()

    metadata = store.set_secret('auth.local_password', 'stored-secret')
    value, resolved_metadata = store.resolve_with_metadata('auth.local_password')
    mode = stat.S_IMODE((data_dir / 'secrets.json').stat().st_mode)

    assert metadata['backend'] == 'plaintext-file'
    assert value == 'stored-secret'
    assert resolved_metadata['backend'] == 'plaintext-file'
    assert mode == 0o600


def test_redact_secret_value_masks_long_values():
    assert redact_secret_value('super-secret-token') == 'su***en'
    assert redact_secret_value('abcd') == '***'
