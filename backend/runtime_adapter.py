from __future__ import annotations

import json
import os
import signal
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import HERMES_HOME, SERVICE_NAME
from http_api import RequestValidationError


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class HermesRuntimeAdapter:
    def __init__(self, hermes_home: Path | None = None) -> None:
        self._hermes_home = hermes_home

    @property
    def hermes_home(self) -> Path:
        if self._hermes_home is not None:
            return self._hermes_home
        return Path(os.getenv('HCC_HERMES_HOME', str(HERMES_HOME)))

    @property
    def sessions_index_path(self) -> Path:
        return self.hermes_home / 'sessions' / 'sessions.json'

    @property
    def processes_path(self) -> Path:
        return self.hermes_home / 'processes.json'

    @property
    def cron_jobs_path(self) -> Path:
        return self.hermes_home / 'cron' / 'jobs.json'

    @property
    def state_db_path(self) -> Path:
        return self.hermes_home / 'state.db'

    def overview(self) -> dict[str, Any]:
        sessions = self.list_sessions()
        processes = self.list_processes()
        cron_jobs = self.list_cron_jobs()
        agents = self._derive_agents(sessions)
        return {
            'service': SERVICE_NAME,
            'generated_at': _now_iso(),
            'counts': {
                'agents': len(agents),
                'sessions': len(sessions),
                'processes': len(processes),
                'cron_jobs': len(cron_jobs),
            },
            'agents': agents,
            'sessions': sessions,
            'processes': processes,
            'cron_jobs': cron_jobs,
        }

    def list_sessions(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if self.state_db_path.exists():
            conn = sqlite3.connect(self.state_db_path)
            conn.row_factory = sqlite3.Row
            try:
                data = conn.execute(
                    "SELECT id, source, user_id, model, started_at, ended_at, title, input_tokens, output_tokens, reasoning_tokens, estimated_cost_usd, actual_cost_usd FROM sessions ORDER BY started_at DESC LIMIT 50"
                ).fetchall()
            finally:
                conn.close()
            for row in data:
                rows.append(
                    {
                        'session_id': row['id'],
                        'source': row['source'],
                        'user_id': row['user_id'],
                        'model': row['model'],
                        'title': row['title'] or row['id'],
                        'status': 'active' if row['ended_at'] is None else 'ended',
                        'started_at': self._from_ts(row['started_at']),
                        'updated_at': self._from_ts(row['ended_at'] or row['started_at']),
                        'agent_id': 'agent-main',
                        'input_tokens': row['input_tokens'] or 0,
                        'output_tokens': row['output_tokens'] or 0,
                        'reasoning_tokens': row['reasoning_tokens'] or 0,
                        'estimated_cost_usd': row['estimated_cost_usd'] or 0.0,
                        'actual_cost_usd': row['actual_cost_usd'] or 0.0,
                    }
                )
        index = self._read_json(self.sessions_index_path, {})
        if isinstance(index, dict):
            index_map = {item.get('session_id'): item for item in index.values() if isinstance(item, dict)}
            for item in rows:
                meta = index_map.get(item['session_id']) or {}
                item['display_name'] = meta.get('display_name')
                item['platform'] = meta.get('platform')
                item['chat_type'] = meta.get('chat_type')
                item['session_key'] = meta.get('session_key')
                item['updated_at'] = meta.get('updated_at', item['updated_at'])
        return rows

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        for item in self.list_sessions():
            if item['session_id'] == session_id:
                return item
        return None

    def list_processes(self) -> list[dict[str, Any]]:
        items = self._read_json(self.processes_path, [])
        if not isinstance(items, list):
            return []
        result = []
        for item in items:
            if not isinstance(item, dict):
                continue
            pid = item.get('pid')
            alive = isinstance(pid, int) and self._pid_alive(pid)
            result.append(
                {
                    'process_id': item.get('session_id'),
                    'pid': pid,
                    'command': item.get('command'),
                    'cwd': item.get('cwd'),
                    'task_id': item.get('task_id'),
                    'session_key': item.get('session_key'),
                    'status': 'running' if alive else 'exited',
                    'started_at': self._from_ts(item.get('started_at')),
                    'updated_at': _now_iso(),
                }
            )
        return result

    def get_process(self, process_id: str) -> dict[str, Any] | None:
        for item in self.list_processes():
            if item['process_id'] == process_id:
                return item
        return None

    def list_cron_jobs(self) -> list[dict[str, Any]]:
        payload = self._read_json(self.cron_jobs_path, {'jobs': []})
        jobs = payload.get('jobs', []) if isinstance(payload, dict) else []
        result = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            result.append(
                {
                    'job_id': job.get('id'),
                    'name': job.get('name') or job.get('id'),
                    'schedule': job.get('schedule_display') or 'manual',
                    'status': job.get('state') or ('scheduled' if job.get('enabled') else 'paused'),
                    'enabled': bool(job.get('enabled', False)),
                    'next_run_at': job.get('next_run_at'),
                    'last_run_at': job.get('last_run_at'),
                    'last_status': job.get('last_status'),
                }
            )
        return result

    def control_cron_job(self, job_id: str, action: str) -> dict[str, Any]:
        payload = self._read_json(self.cron_jobs_path, {'jobs': []})
        jobs = payload.get('jobs', []) if isinstance(payload, dict) else []
        for job in jobs:
            if isinstance(job, dict) and job.get('id') == job_id:
                if action == 'pause':
                    job['enabled'] = False
                    job['state'] = 'paused'
                elif action == 'resume':
                    job['enabled'] = True
                    job['state'] = 'scheduled'
                elif action == 'run':
                    job['last_run_at'] = _now_iso()
                    job['last_status'] = 'requested'
                    job['state'] = 'run_requested'
                else:
                    raise RequestValidationError(status=400, code='ops.invalid_action', message='Unsupported cron action', details={'action': action})
                payload['updated_at'] = _now_iso()
                self.cron_jobs_path.parent.mkdir(parents=True, exist_ok=True)
                self.cron_jobs_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
                return {
                    'job_id': job.get('id'),
                    'name': job.get('name') or job.get('id'),
                    'schedule': job.get('schedule_display') or 'manual',
                    'status': job.get('state'),
                    'enabled': bool(job.get('enabled', False)),
                    'next_run_at': job.get('next_run_at'),
                    'last_run_at': job.get('last_run_at'),
                    'last_status': job.get('last_status'),
                }
        raise RequestValidationError(status=404, code='ops.job_not_found', message='Cron job not found', details={'job_id': job_id})

    def get_cron_job(self, job_id: str) -> dict[str, Any]:
        for job in self.list_cron_jobs():
            if job.get('job_id') == job_id:
                return job
        raise RequestValidationError(status=404, code='ops.job_not_found', message='Cron job not found', details={'job_id': job_id})

    def kill_process(self, process_id: str) -> dict[str, Any]:
        process = self.get_process(process_id)
        if process is None:
            raise RequestValidationError(status=404, code='ops.process_not_found', message='Process not found', details={'process_id': process_id})
        pid = process.get('pid')
        if not isinstance(pid, int):
            raise RequestValidationError(status=400, code='ops.invalid_process', message='Process has no valid pid', details={'process_id': process_id})
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            process['status'] = 'exited'
            return process
        process['status'] = 'termination_requested'
        process['updated_at'] = _now_iso()
        return process

    def _derive_agents(self, sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not sessions:
            return []
        return [
            {
                'agent_id': 'agent-main',
                'role': 'main',
                'status': 'active' if any(item.get('status') == 'active' for item in sessions) else 'idle',
                'last_seen_at': sessions[0].get('updated_at'),
            }
        ]

    @staticmethod
    def _read_json(path: Path, fallback: Any) -> Any:
        try:
            if not path.exists():
                return fallback
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return fallback

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    @staticmethod
    def _from_ts(value: Any) -> str | None:
        if value in (None, ''):
            return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        return str(value)


runtime_adapter = HermesRuntimeAdapter()
