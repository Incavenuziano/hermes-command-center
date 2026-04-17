from __future__ import annotations

import json
import os
import secrets
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DATA_DIR


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class ApprovalsStore:
    def __init__(self) -> None:
        self._path = self._current_path()

    def list_items(self) -> dict[str, object]:
        payload = self._read()
        items = sorted(payload.get('items', []), key=lambda item: item.get('created_at', ''), reverse=True)
        return {'items': items, 'count': len(items)}

    def enqueue(self, *, kind: str, title: str, summary: str, source: str, choices: list[str] | None = None) -> dict[str, object]:
        payload = self._read()
        item = {
            'id': secrets.token_urlsafe(10),
            'kind': kind,
            'title': title,
            'summary': summary,
            'source': source,
            'choices': list(choices or []),
            'status': 'pending',
            'decision': None,
            'created_at': _now_iso(),
            'resolved_at': None,
        }
        payload['items'].append(item)
        self._write(payload)
        return deepcopy(item)

    def resolve(self, *, item_id: str, decision: str) -> dict[str, object]:
        payload = self._read()
        for item in payload.get('items', []):
            if item.get('id') == item_id:
                item['status'] = 'resolved'
                item['decision'] = decision
                item['resolved_at'] = _now_iso()
                self._write(payload)
                return deepcopy(item)
        raise KeyError(item_id)

    def _current_path(self) -> Path:
        return Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR))) / 'approvals.json'

    def _read(self) -> dict[str, Any]:
        self._path = self._current_path()
        try:
            if not self._path.exists():
                return {'items': []}
            payload = json.loads(self._path.read_text(encoding='utf-8'))
        except Exception:
            return {'items': []}
        if not isinstance(payload, dict):
            return {'items': []}
        payload.setdefault('items', [])
        return payload

    def _write(self, payload: dict[str, Any]) -> None:
        self._path = self._current_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


approvals_store = ApprovalsStore()
