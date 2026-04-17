from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any


def _data_dir() -> Path:
    return Path(os.getenv('HCC_DATA_DIR', str(Path(__file__).resolve().parents[1] / '.data')))


def redact_secret_value(value: str | None) -> str:
    if not value:
        return '***'
    if len(value) <= 6:
        return '***'
    return f'{value[:2]}***{value[-2:]}'


class SecretStore:
    def __init__(self) -> None:
        self._path = _data_dir() / 'secrets.json'

    def resolve_with_metadata(self, name: str, *, env_var: str | None = None, default: str | None = None) -> tuple[str | None, dict[str, Any]]:
        env_value = os.getenv(env_var) if env_var else None
        if env_value:
            return env_value, {'backend': 'environment', 'name': name, 'env_var': env_var}

        keyring_value = self._get_from_keyring(name)
        if keyring_value:
            return keyring_value, {'backend': 'keyring', 'name': name}

        file_payload = self._read_local_store()
        if name in file_payload:
            return str(file_payload[name]), {'backend': 'plaintext-file', 'name': name, 'path': str(self._path)}

        return default, {'backend': 'default', 'name': name}

    def set_secret(self, name: str, value: str) -> dict[str, Any]:
        keyring_backend = self._get_keyring_backend()
        if keyring_backend is not None:
            keyring_backend.set_password('hermes-command-center', name, value)
            return {'backend': 'keyring', 'name': name}

        if os.getenv('HCC_ALLOW_PLAINTEXT_SECRETS', '0').strip().lower() not in {'1', 'true', 'yes', 'on'}:
            raise RuntimeError('Plaintext secret fallback is disabled; set HCC_ALLOW_PLAINTEXT_SECRETS=1 to allow it explicitly')

        payload = self._read_local_store()
        payload[name] = value
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')
        os.chmod(self._path, 0o600)
        return {'backend': 'plaintext-file', 'name': name, 'path': str(self._path)}

    def summary(self, name: str, *, env_var: str | None = None, default: str | None = None) -> dict[str, Any]:
        value, metadata = self.resolve_with_metadata(name, env_var=env_var, default=default)
        return {
            'name': name,
            'backend': metadata['backend'],
            'present': value is not None,
            'redacted': redact_secret_value(value),
        }

    def _read_local_store(self) -> dict[str, str]:
        try:
            if not self._path.exists():
                return {}
            payload = json.loads(self._path.read_text(encoding='utf-8'))
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        return {str(key): str(value) for key, value in payload.items()}

    @staticmethod
    def _get_keyring_backend():
        try:
            keyring = importlib.import_module('keyring')
        except Exception:
            return None
        return keyring

    def _get_from_keyring(self, name: str) -> str | None:
        keyring_backend = self._get_keyring_backend()
        if keyring_backend is None:
            return None
        try:
            return keyring_backend.get_password('hermes-command-center', name)
        except Exception:
            return None


secret_store = SecretStore()


def resolve_secret(name: str, *, env_var: str | None = None, default: str | None = None) -> str | None:
    value, _ = secret_store.resolve_with_metadata(name, env_var=env_var, default=default)
    return value
