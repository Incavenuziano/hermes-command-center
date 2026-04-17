from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DATA_DIR, SERVICE_NAME, ensure_directories
from event_bus import event_bus_store
from runtime_adapter import runtime_adapter


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class DerivedStateStore:
    def __init__(self) -> None:
        ensure_directories()
        self._persist_path = Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR))) / 'derived_state.json'
        self._persist_root = self._persist_path.parent
        self._overview = {
            'service': SERVICE_NAME,
            'generated_at': _now_iso(),
            'counts': {'agents': 0, 'sessions': 0, 'processes': 0, 'cron_jobs': 0},
            'agents': [],
            'sessions': [],
            'processes': [],
            'cron_jobs': [],
            'events': [],
        }
        self._events: list[dict[str, object]] = []
        self._load()
        if not self._events:
            self.ingest_event({'kind': 'system.bootstrap', 'source': 'command-center', 'data': {'status': 'ready'}})

    def overview(self) -> dict[str, object]:
        self._ensure_current_store()
        live = runtime_adapter.overview()
        merged = self._apply_events_to_overview(live)
        self._overview = {
            **merged,
            'events': deepcopy(self._events[:5]),
        }
        self._overview['counts'] = {
            'agents': len(self._overview['agents']),
            'sessions': len(self._overview['sessions']),
            'processes': len(self._overview['processes']),
            'cron_jobs': len(self._overview['cron_jobs']),
        }
        return deepcopy(self._overview)

    def event_feed(self, *, limit: int = 20) -> dict[str, object]:
        self._ensure_current_store()
        return {'items': deepcopy(self._events[:limit]), 'count': len(self._events)}

    def ingest_event(self, event: dict[str, object]) -> dict[str, object]:
        self._ensure_current_store()
        item = {
            'kind': event['kind'],
            'source': event['source'],
            'at': _now_iso(),
            'data': deepcopy(event.get('data', {})),
        }
        bus_event = event_bus_store.append(
            event_type=str(item['kind']),
            source=str(item['source']),
            channel='ops',
            payload={'at': item['at'], 'data': deepcopy(item['data'])},
        )
        item['event_id'] = bus_event['event_id']
        self._events.insert(0, item)
        self._events = self._events[:100]
        self._save()
        return deepcopy(item)

    def _load(self) -> None:
        if not self._persist_path.exists():
            return
        try:
            payload = json.loads(self._persist_path.read_text(encoding='utf-8'))
        except Exception:
            return
        events = payload.get('events', []) if isinstance(payload, dict) else []
        if isinstance(events, list):
            self._events = [item for item in events if isinstance(item, dict)][:100]

    def _ensure_current_store(self) -> None:
        current_root = Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR)))
        current_path = current_root / 'derived_state.json'
        if current_path == self._persist_path:
            return
        self._persist_root = current_root
        self._persist_path = current_path
        self._events = []
        self._load()
        if not self._events:
            bootstrap = {
                'kind': 'system.bootstrap',
                'source': 'command-center',
                'at': _now_iso(),
                'data': {'status': 'ready'},
            }
            self._events = [bootstrap]
            self._save()

    def _save(self) -> None:
        self._persist_root.mkdir(parents=True, exist_ok=True)
        payload = {'events': self._events, 'updated_at': _now_iso()}
        self._persist_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    def _apply_events_to_overview(self, overview: dict[str, object]) -> dict[str, object]:
        merged = deepcopy(overview)
        for event in reversed(self._events):
            self._apply_single_event(merged, event)
        return merged

    def _apply_single_event(self, overview: dict[str, object], event: dict[str, object]) -> None:
        data = event.get('data', {}) if isinstance(event.get('data', {}), dict) else {}
        kind = str(event.get('kind', ''))
        if kind.startswith('session.'):
            session_id = data.get('session_id')
            if isinstance(session_id, str):
                self._upsert(
                    overview['sessions'],
                    'session_id',
                    {
                        'session_id': session_id,
                        'source': data.get('source', 'runtime-event'),
                        'user_id': data.get('user_id'),
                        'model': data.get('model'),
                        'title': data.get('title', session_id),
                        'status': data.get('status', kind.split('.', 1)[1]),
                        'started_at': data.get('started_at'),
                        'updated_at': event.get('at'),
                    },
                )
        elif kind.startswith('process.'):
            process_id = data.get('process_id')
            if isinstance(process_id, str):
                self._upsert(
                    overview['processes'],
                    'process_id',
                    {
                        'process_id': process_id,
                        'pid': data.get('pid'),
                        'command': data.get('command'),
                        'cwd': data.get('cwd'),
                        'task_id': data.get('task_id'),
                        'session_key': data.get('session_key'),
                        'status': data.get('status', kind.split('.', 1)[1]),
                        'started_at': data.get('started_at'),
                        'updated_at': event.get('at'),
                    },
                )
        elif kind.startswith('cron.'):
            job_id = data.get('job_id')
            if isinstance(job_id, str):
                self._upsert(
                    overview['cron_jobs'],
                    'job_id',
                    {
                        'job_id': job_id,
                        'name': data.get('name', job_id),
                        'schedule': data.get('schedule', 'manual'),
                        'status': data.get('status', kind.split('.', 1)[1]),
                        'enabled': data.get('status') != 'paused',
                        'next_run_at': data.get('next_run_at'),
                        'last_run_at': data.get('last_run_at'),
                        'last_status': data.get('last_status'),
                    },
                )
        agent_id = data.get('agent_id')
        if isinstance(agent_id, str):
            self._upsert(
                overview['agents'],
                'agent_id',
                {
                    'agent_id': agent_id,
                    'role': data.get('role', 'worker'),
                    'status': data.get('agent_status', data.get('status', 'active')),
                    'last_seen_at': event.get('at'),
                },
            )

    @staticmethod
    def _upsert(items: list[dict[str, object]], key: str, payload: dict[str, object]) -> None:
        for index, existing in enumerate(items):
            if existing.get(key) == payload[key]:
                items[index] = {**existing, **payload}
                return
        items.insert(0, payload)


derived_state_store = DerivedStateStore()
