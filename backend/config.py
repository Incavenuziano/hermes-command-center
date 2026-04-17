from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from secrets_store import resolve_secret, secret_store

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR
DATA_DIR = PROJECT_ROOT / '.data'
LOG_DIR = PROJECT_ROOT / 'logs'
HERMES_HOME = Path(os.getenv('HCC_HERMES_HOME', str(Path.home() / '.hermes')))
HOST = os.getenv('HCC_HOST', '127.0.0.1')
PORT = int(os.getenv('HCC_PORT', '8787'))
ENV = os.getenv('HCC_ENV', 'development')
CONTRACT_VERSION = '2026-04-15'
SERVICE_NAME = 'hermes-command-center'
MAX_REQUEST_BYTES = int(os.getenv('HCC_MAX_REQUEST_BYTES', '4096'))
AUTH_ENABLED = os.getenv('HCC_AUTH_ENABLED', '0').strip().lower() in {'1', 'true', 'yes', 'on'}
TRUST_TAILNET_ONLY = os.getenv('HCC_TRUST_TAILNET_ONLY', '0').strip().lower() in {'1', 'true', 'yes', 'on'}
AUTH_PASSWORD = resolve_secret('auth.local_password', env_var='HCC_AUTH_PASSWORD', default='dev-password') or 'dev-password'
AUTH_USER = os.getenv('HCC_AUTH_USER', 'local-operator')
AUTH_SESSION_TTL_SECONDS = int(os.getenv('HCC_AUTH_SESSION_TTL_SECONDS', '3600'))


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'service': SERVICE_NAME,
            'environment': ENV,
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    ensure_directories()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


def to_jsonable(value: Any):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def secret_backend_summary() -> dict[str, Any]:
    auth_summary = secret_store.summary('auth.local_password', env_var='HCC_AUTH_PASSWORD', default='dev-password')
    return {
        'auth_local_password': auth_summary,
    }


def security_posture_summary() -> dict[str, Any]:
    return {
        'non_loopback_requires_explicit_trusted_tailnet': True,
        'trusted_tailnet_only_enabled': TRUST_TAILNET_ONLY,
        'auth_enabled': AUTH_ENABLED,
    }
