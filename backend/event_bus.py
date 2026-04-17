from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DATA_DIR, ensure_directories


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class EventBusStore:
    def __init__(self) -> None:
        ensure_directories()
        self._db_path = self._current_db_path()
        self._ensure_schema()

    def append(self, *, event_type: str, source: str, channel: str, payload: dict[str, Any]) -> dict[str, object]:
        self._ensure_current_store()
        recorded_at = _now_iso()
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO event_bus (recorded_at, event_type, source, channel, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (recorded_at, event_type, source, channel, payload_json),
            )
            conn.commit()
            event_id = cursor.lastrowid
        return {
            'event_id': event_id,
            'recorded_at': recorded_at,
            'event_type': event_type,
            'source': source,
            'channel': channel,
            'payload': json.loads(payload_json),
        }

    def replay(self, *, after_id: int | None = None, limit: int = 100) -> list[dict[str, object]]:
        self._ensure_current_store()
        bounded_limit = max(1, min(limit, 500))
        clauses = []
        params: list[object] = []
        if after_id is not None:
            clauses.append('event_id > ?')
            params.append(after_id)
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ''
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""
                SELECT event_id, recorded_at, event_type, source, channel, payload_json
                FROM event_bus
                {where_sql}
                ORDER BY event_id ASC
                LIMIT ?
                """,
                (*params, bounded_limit),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def _current_db_path(self) -> Path:
        current_root = Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR)))
        return current_root / 'event-bus.sqlite3'

    def _ensure_current_store(self) -> None:
        current_db_path = self._current_db_path()
        if current_db_path == self._db_path:
            return
        self._db_path = current_db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_bus (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> dict[str, object]:
        payload = json.loads(row['payload_json'])
        return {
            'event_id': row['event_id'],
            'recorded_at': row['recorded_at'],
            'event_type': row['event_type'],
            'source': row['source'],
            'channel': row['channel'],
            'payload': payload if isinstance(payload, dict) else {},
        }


event_bus_store = EventBusStore()
