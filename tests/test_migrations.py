from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / 'backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from migrations import MigrationManager  # noqa: E402


def test_migration_manager_initializes_command_center_stores(tmp_path):
    data_dir = tmp_path / 'command-center-data'
    manager = MigrationManager(data_dir=data_dir)

    report = manager.apply_all()

    assert report['applied']
    assert (data_dir / 'audit-log.sqlite3').exists()
    assert (data_dir / 'event-bus.sqlite3').exists()

    with sqlite3.connect(data_dir / 'audit-log.sqlite3') as conn:
        version = conn.execute("SELECT value FROM audit_log_metadata WHERE key = 'schema_version'").fetchone()[0]
    with sqlite3.connect(data_dir / 'event-bus.sqlite3') as conn:
        version_row = conn.execute("SELECT version FROM schema_migrations WHERE target = 'event_bus'").fetchone()

    assert version == '1'
    assert version_row[0] == '1'


def test_migration_manager_is_idempotent_on_repeat_runs(tmp_path):
    data_dir = tmp_path / 'command-center-data'
    manager = MigrationManager(data_dir=data_dir)

    first = manager.apply_all()
    second = manager.apply_all()

    assert first['applied']
    assert second['applied'] == []
    assert second['current_versions'] == first['current_versions']
