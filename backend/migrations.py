from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Callable


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            target TEXT PRIMARY KEY,
            version TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class MigrationManager:
    def __init__(self, *, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or Path(os.getenv('HCC_DATA_DIR', str(Path(__file__).resolve().parents[1] / '.data')))
        self.targets: dict[str, tuple[str, Path, Callable[[sqlite3.Connection], None]]] = {
            'audit_log': ('1', self.data_dir / 'audit-log.sqlite3', self._migrate_audit_log_v1),
            'event_bus': ('1', self.data_dir / 'event-bus.sqlite3', self._migrate_event_bus_v1),
        }

    def apply_all(self) -> dict[str, object]:
        applied: list[dict[str, str]] = []
        current_versions: dict[str, str] = {}
        for target, (desired_version, db_path, migration) in self.targets.items():
            with _connect(db_path) as conn:
                existing = conn.execute('SELECT version FROM schema_migrations WHERE target = ?', (target,)).fetchone()
                current_version = existing[0] if existing else None
                if current_version != desired_version:
                    migration(conn)
                    conn.execute(
                        """
                        INSERT INTO schema_migrations(target, version, updated_at)
                        VALUES (?, ?, ?)
                        ON CONFLICT(target) DO UPDATE SET version = excluded.version, updated_at = excluded.updated_at
                        """,
                        (target, desired_version, _now_iso()),
                    )
                    conn.commit()
                    applied.append({'target': target, 'version': desired_version})
                current_versions[target] = desired_version
        return {'applied': applied, 'current_versions': current_versions}

    @staticmethod
    def _migrate_audit_log_v1(conn: sqlite3.Connection) -> None:
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
            VALUES ('schema_version', '1')
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """
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

    @staticmethod
    def _migrate_event_bus_v1(conn: sqlite3.Connection) -> None:
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


migration_manager = MigrationManager()
