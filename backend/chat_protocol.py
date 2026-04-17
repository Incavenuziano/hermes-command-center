from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from config import HERMES_HOME
from http_api import RequestValidationError


class ChatTranscriptStore:
    @property
    def hermes_home(self) -> Path:
        return Path(os.getenv('HCC_HERMES_HOME', str(HERMES_HOME)))

    @property
    def sessions_dir(self) -> Path:
        return self.hermes_home / 'sessions'

    def transcript(self, session_id: str) -> dict[str, Any]:
        if not isinstance(session_id, str) or not session_id:
            raise RequestValidationError(status=400, code='ops.invalid_request', message='session_id is required', details={'field': 'session_id'})

        payload = self._read_session_payload(session_id)
        messages = payload.get('messages', [])
        if not isinstance(messages, list):
            messages = []

        items = [self._normalize_message(index + 1, item) for index, item in enumerate(messages) if isinstance(item, dict)]
        session = {
            'session_id': payload.get('session_id', session_id),
            'model': payload.get('model'),
            'platform': payload.get('platform'),
            'started_at': payload.get('session_start'),
            'updated_at': payload.get('last_updated'),
            'message_count': len(items),
        }
        return {
            'session': session,
            'items': items,
            'count': len(items),
            'last_message_id': items[-1]['message_id'] if items else 0,
        }

    def _read_session_payload(self, session_id: str) -> dict[str, Any]:
        path = self.sessions_dir / f'session_{session_id}.json'
        if not path.exists():
            raise RequestValidationError(status=404, code='ops.session_not_found', message='Session transcript not found', details={'session_id': session_id})
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception as exc:
            raise RequestValidationError(status=500, code='ops.session_transcript_invalid', message='Session transcript is unreadable', details={'session_id': session_id}) from exc
        if not isinstance(payload, dict):
            raise RequestValidationError(status=500, code='ops.session_transcript_invalid', message='Session transcript must be an object', details={'session_id': session_id})
        return payload

    def _normalize_message(self, message_id: int, item: dict[str, Any]) -> dict[str, Any]:
        tool_calls = []
        raw_tool_calls = item.get('tool_calls', [])
        if isinstance(raw_tool_calls, list):
            for call in raw_tool_calls:
                if not isinstance(call, dict):
                    continue
                function_payload = call.get('function', {}) if isinstance(call.get('function'), dict) else {}
                tool_calls.append({
                    'id': call.get('id'),
                    'type': call.get('type'),
                    'name': function_payload.get('name'),
                    'arguments': function_payload.get('arguments'),
                })

        return {
            'message_id': message_id,
            'role': item.get('role'),
            'content': item.get('content', ''),
            'tool_call_id': item.get('tool_call_id'),
            'tool_calls': tool_calls,
            'finish_reason': item.get('finish_reason'),
        }


chat_transcript_store = ChatTranscriptStore()
