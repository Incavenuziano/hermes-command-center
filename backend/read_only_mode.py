from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from config import DATA_DIR, ensure_directories


class ReadOnlyModeStore:
    def __init__(self) -> None:
        ensure_directories()

    def get_state(self) -> dict[str, Any]:
        path = self._path()
        if not path.exists():
            return {'enabled': False, 'reason': None}
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return {'enabled': False, 'reason': None}
        if not isinstance(payload, dict):
            return {'enabled': False, 'reason': None}
        return {
            'enabled': bool(payload.get('enabled', False)),
            'reason': payload.get('reason'),
        }

    def set_state(self, *, enabled: bool, reason: str | None) -> dict[str, Any]:
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {'enabled': enabled, 'reason': reason}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return payload

    def _path(self) -> Path:
        return Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR))) / 'read-only-mode.json'


read_only_mode_store = ReadOnlyModeStore()
