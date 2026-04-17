from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from config import HERMES_HOME
from http_api import RequestValidationError


def _truncate(value: str, limit: int = 240) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + '…'


def _redact(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 4:
        return '*' * len(value)
    return '***' + value[-4:]


class KnowledgeSurfacesAdapter:
    @property
    def hermes_home(self) -> Path:
        return Path(os.getenv('HCC_HERMES_HOME', str(HERMES_HOME)))

    @property
    def memory_path(self) -> Path:
        return self.hermes_home / 'memory.json'

    @property
    def skills_dir(self) -> Path:
        return self.hermes_home / 'skills'

    @property
    def workspace_dir(self) -> Path:
        return self.hermes_home / 'workspace'

    @property
    def profiles_path(self) -> Path:
        return self.hermes_home / 'profiles.json'

    @property
    def gateway_path(self) -> Path:
        return self.hermes_home / 'gateway.json'

    def memory_summary(self) -> dict[str, object]:
        payload = self._read_json(self.memory_path, {})
        memory_items = payload.get('memory', []) if isinstance(payload, dict) else []
        user_items = payload.get('user', []) if isinstance(payload, dict) else []
        items: list[dict[str, object]] = []
        for scope, collection in (('memory', memory_items), ('user', user_items)):
            if not isinstance(collection, list):
                continue
            for item in collection:
                if not isinstance(item, dict):
                    continue
                text = str(item.get('text') or '')
                items.append({
                    'id': item.get('id') or f'{scope}-{len(items) + 1}',
                    'scope': scope,
                    'text': text,
                    'preview': _truncate(text, 96),
                    'updated_at': item.get('updated_at'),
                })
        return {
            'counts': {'memory': len(memory_items) if isinstance(memory_items, list) else 0, 'user': len(user_items) if isinstance(user_items, list) else 0},
            'items': items,
        }

    def skills_summary(self) -> dict[str, object]:
        items: list[dict[str, object]] = []
        if self.skills_dir.exists():
            for skill_dir in sorted(self.skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / 'SKILL.md'
                if not skill_md.exists():
                    continue
                text = skill_md.read_text(encoding='utf-8')
                first_line = next((line.strip('# ').strip() for line in text.splitlines() if line.strip()), skill_dir.name)
                items.append({
                    'skill_id': skill_dir.name,
                    'title': first_line or skill_dir.name,
                    'path': str(skill_md.relative_to(self.hermes_home)),
                    'preview': _truncate(text.replace('\n', ' '), 120),
                })
        return {'count': len(items), 'items': items}

    def files_summary(self) -> dict[str, object]:
        items: list[dict[str, object]] = []
        if self.workspace_dir.exists():
            for path in sorted(self.workspace_dir.rglob('*')):
                if not path.is_file():
                    continue
                rel = path.relative_to(self.workspace_dir)
                preview = _truncate(path.read_text(encoding='utf-8', errors='ignore').replace('\n', ' '), 120)
                items.append({'path': str(rel), 'size_bytes': path.stat().st_size, 'preview': preview})
        return {'root': str(self.workspace_dir), 'count': len(items), 'items': items}

    def profiles_summary(self) -> dict[str, object]:
        payload = self._read_json(self.profiles_path, {'profiles': [], 'active_profile_id': None})
        profiles = payload.get('profiles', []) if isinstance(payload, dict) else []
        items = []
        for item in profiles if isinstance(profiles, list) else []:
            if not isinstance(item, dict):
                continue
            items.append({
                'id': item.get('id'),
                'label': item.get('label') or item.get('id'),
                'sensitivity': item.get('sensitivity') or 'standard',
                'requires_reauth': bool(item.get('requires_reauth', False)),
            })
        return {'active_profile_id': payload.get('active_profile_id') if isinstance(payload, dict) else None, 'items': items, 'count': len(items)}

    def gateway_summary(self) -> dict[str, object]:
        payload = self._read_json(self.gateway_path, {'gateway': {}, 'channels': []})
        gateway = payload.get('gateway', {}) if isinstance(payload, dict) else {}
        channels = payload.get('channels', []) if isinstance(payload, dict) else []
        redacted_channels = []
        for item in channels if isinstance(channels, list) else []:
            if not isinstance(item, dict):
                continue
            redacted_channels.append({
                'id': item.get('id'),
                'label': item.get('label') or item.get('id'),
                'platform': item.get('platform'),
                'delivery_state': item.get('delivery_state') or 'unknown',
                'secret_redacted': _redact(str(item.get('secret')) if item.get('secret') is not None else None),
            })
        return {
            'gateway': {
                'status': gateway.get('status') if isinstance(gateway, dict) else None,
                'transport': gateway.get('transport') if isinstance(gateway, dict) else None,
                'bot_token_redacted': _redact(str(gateway.get('bot_token')) if isinstance(gateway, dict) and gateway.get('bot_token') is not None else None),
            },
            'channels': redacted_channels,
            'count': len(redacted_channels),
        }

    @staticmethod
    def _read_json(path: Path, fallback: Any) -> Any:
        try:
            if not path.exists():
                return fallback
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return fallback


knowledge_surfaces = KnowledgeSurfacesAdapter()
