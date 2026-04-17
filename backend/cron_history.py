from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from config import DATA_DIR, ensure_directories


class CronHistoryStore:
    def __init__(self) -> None:
        ensure_directories()

    def list_history(self, *, job_id: str | None = None, limit: int = 20) -> dict[str, object]:
        items = self._read_items()
        if job_id is not None:
            items = [item for item in items if item.get('job_id') == job_id]
        bounded = items[:limit]
        return {'job_id': job_id, 'items': bounded, 'count': len(bounded)}

    def append(self, entry: dict[str, Any]) -> dict[str, Any]:
        items = self._read_items()
        items.insert(0, entry)
        items = items[:200]
        self._write_items(items)
        return entry

    def _path(self) -> Path:
        return Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR))) / 'cron-history.json'

    def _read_items(self) -> list[dict[str, Any]]:
        path = self._path()
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return []
        items = payload.get('items', []) if isinstance(payload, dict) else []
        return [item for item in items if isinstance(item, dict)]

    def _write_items(self, items: list[dict[str, Any]]) -> None:
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'items': items}, ensure_ascii=False, indent=2), encoding='utf-8')


cron_history_store = CronHistoryStore()
