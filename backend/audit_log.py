from __future__ import annotations

import json
import os
import sqlite3
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DATA_DIR, ensure_directories
from event_bus import event_bus_store


AUDIT_LOG_SCHEMA_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class AuditLogStore:
    def __init__(self) -> None:
        ensure_directories()
        self._db_path = self._current_db_path()
        self._ensure_schema()

    def list_entries(self, *, limit: int = 20) -> dict[str, object]:
        self._ensure_current_store()
        bounded_limit = max(1, min(limit, 100))
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT entry_id, recorded_at, actor_session_id, actor_user, auth_mode,
                       action_type, target_type, target_id, result, details_json
                FROM operator_audit_log
                ORDER BY entry_id DESC
                LIMIT ?
                """,
                (bounded_limit,),
            ).fetchall()
            total_count = conn.execute('SELECT COUNT(*) FROM operator_audit_log').fetchone()[0]
        items = [self._row_to_entry(row) for row in rows]
        return {'items': items, 'count': total_count}

    def append_entry(
        self,
        *,
        actor_session_id: str,
        actor_user: str,
        auth_mode: str,
        action_type: str,
        target_type: str,
        target_id: str,
        result: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, object]:
        self._ensure_current_store()
        entry = {
            'recorded_at': _now_iso(),
            'actor_session_id': actor_session_id,
            'actor_user': actor_user,
            'auth_mode': auth_mode,
            'action_type': action_type,
            'target_type': target_type,
            'target_id': target_id,
            'result': result,
            'details_json': json.dumps(deepcopy(details or {}), ensure_ascii=False, sort_keys=True),
        }
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO operator_audit_log (
                    recorded_at,
                    actor_session_id,
                    actor_user,
                    auth_mode,
                    action_type,
                    target_type,
                    target_id,
                    result,
                    details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry['recorded_at'],
                    entry['actor_session_id'],
                    entry['actor_user'],
                    entry['auth_mode'],
                    entry['action_type'],
                    entry['target_type'],
                    entry['target_id'],
                    entry['result'],
                    entry['details_json'],
                ),
            )
            conn.commit()
            entry_id = cursor.lastrowid
        record = self.get_entry(entry_id)
        event_bus_store.append(
            event_type='audit.entry',
            source='command-center',
            channel='audit',
            payload=deepcopy(record),
        )
        return record

    def get_entry(self, entry_id: int) -> dict[str, object]:
        self._ensure_current_store()
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT entry_id, recorded_at, actor_session_id, actor_user, auth_mode,
                       action_type, target_type, target_id, result, details_json
                FROM operator_audit_log
                WHERE entry_id = ?
                """,
                (entry_id,),
            ).fetchone()
        if row is None:
            raise KeyError(entry_id)
        return self._row_to_entry(row)

    def _current_db_path(self) -> Path:
        current_root = Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR)))
        return current_root / 'audit-log.sqlite3'

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
                CREATE TABLE IF NOT EXISTS operator_audit_log (
                    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    actor_session_id TEXT NOT NULL,
                    actor_user TEXT NOT NULL,
                    auth_mode TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    result TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO audit_log_metadata(key, value)
                VALUES ('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(AUDIT_LOG_SCHEMA_VERSION),),
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS operator_audit_log_no_update
                BEFORE UPDATE ON operator_audit_log
                BEGIN
                    SELECT RAISE(ABORT, 'operator_audit_log is append-only');
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS operator_audit_log_no_delete
                BEFORE DELETE ON operator_audit_log
                BEGIN
                    SELECT RAISE(ABORT, 'operator_audit_log is append-only');
                END;
                """
            )
            conn.commit()

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> dict[str, object]:
        details = json.loads(row['details_json'])
        return {
            'entry_id': row['entry_id'],
            'recorded_at': row['recorded_at'],
            'actor': {
                'session_id': row['actor_session_id'],
                'user': row['actor_user'],
                'auth_mode': row['auth_mode'],
            },
            'action': {
                'type': row['action_type'],
                'target_type': row['target_type'],
                'target_id': row['target_id'],
                'result': row['result'],
            },
            'details': details if isinstance(details, dict) else {},
        }


audit_log_store = AuditLogStore()
