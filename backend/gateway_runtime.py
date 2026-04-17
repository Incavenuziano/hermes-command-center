from __future__ import annotations

import json
from pathlib import Path

from config import DATA_DIR


class GatewayRuntimeStore:
    def __init__(self) -> None:
        self._path = DATA_DIR / 'gateway_runtime.json'

    def get_state(self) -> dict[str, object]:
        if not self._path.exists():
            return {'status': 'online', 'action_label': 'Kill Hermes'}
        try:
            payload = json.loads(self._path.read_text(encoding='utf-8'))
        except Exception:
            return {'status': 'online', 'action_label': 'Kill Hermes'}
        if not isinstance(payload, dict):
            return {'status': 'online', 'action_label': 'Kill Hermes'}
        status = 'offline' if payload.get('status') == 'offline' else 'online'
        return {'status': status, 'action_label': 'Start Gateway' if status == 'offline' else 'Kill Hermes'}

    def set_action(self, action: str) -> dict[str, object]:
        status = 'offline' if action == 'kill' else 'online'
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({'status': status}, ensure_ascii=False, indent=2), encoding='utf-8')
        return self.get_state()


gateway_runtime_store = GatewayRuntimeStore()
