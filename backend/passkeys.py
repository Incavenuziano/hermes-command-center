from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any

from config import DATA_DIR

try:
    from webauthn import (
        generate_authentication_options,
        generate_registration_options,
        options_to_json,
        verify_authentication_response,
        verify_registration_response,
    )
    from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
    from webauthn.helpers.structs import PublicKeyCredentialDescriptor
except Exception:  # pragma: no cover - degraded mode if dependency missing
    generate_authentication_options = None
    generate_registration_options = None
    options_to_json = None
    verify_authentication_response = None
    verify_registration_response = None
    base64url_to_bytes = None
    bytes_to_base64url = None
    PublicKeyCredentialDescriptor = None


class PasskeyStore:
    def __init__(self) -> None:
        self._path = self._current_path()
        self._pending: dict[str, dict[str, Any]] = {}

    def status(self) -> dict[str, object]:
        payload = self._read()
        credentials = payload.get('credentials', []) if isinstance(payload, dict) else []
        return {
            'available': self.available,
            'required': False,
            'credential_count': len(credentials),
            'rp_id': self.rp_id,
            'rp_name': self.rp_name,
            'origin': self.origin,
        }

    @property
    def available(self) -> bool:
        return all([generate_registration_options, generate_authentication_options, options_to_json, verify_registration_response, verify_authentication_response, base64url_to_bytes, bytes_to_base64url, PublicKeyCredentialDescriptor])

    @property
    def rp_id(self) -> str:
        return os.getenv('HCC_WEBAUTHN_RP_ID', 'localhost')

    @property
    def rp_name(self) -> str:
        return os.getenv('HCC_WEBAUTHN_RP_NAME', 'Hermes Command Center')

    @property
    def origin(self) -> str:
        return os.getenv('HCC_WEBAUTHN_ORIGIN', 'http://localhost')

    def begin_registration(self, *, user_name: str) -> dict[str, object]:
        self._require_available()
        options = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_name=user_name,
            user_display_name=user_name,
        )
        public_key = json.loads(options_to_json(options))
        challenge_id = secrets.token_urlsafe(18)
        self._pending[challenge_id] = {
            'type': 'registration',
            'challenge': public_key['challenge'],
            'user_name': user_name,
        }
        return {'challenge_id': challenge_id, 'public_key': public_key}

    def finish_registration(self, *, challenge_id: str, credential: dict[str, Any]) -> dict[str, object]:
        self._require_available()
        pending = self._consume_pending(challenge_id, expected_type='registration')
        verified = verify_registration_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(pending['challenge']),
            expected_rp_id=self.rp_id,
            expected_origin=self.origin,
            require_user_verification=False,
        )
        payload = self._read()
        credentials = payload.setdefault('credentials', [])
        credentials.append(
            {
                'credential_id': bytes_to_base64url(verified.credential_id),
                'public_key': bytes_to_base64url(verified.credential_public_key),
                'sign_count': verified.sign_count,
                'user_name': pending['user_name'],
            }
        )
        self._write(payload)
        return {'registered': True, 'credential_id': bytes_to_base64url(verified.credential_id)}

    def begin_authentication(self) -> dict[str, object]:
        self._require_available()
        payload = self._read()
        credentials = payload.get('credentials', []) if isinstance(payload, dict) else []
        if not credentials:
            raise ValueError('No passkeys enrolled')
        allow = [PublicKeyCredentialDescriptor(id=base64url_to_bytes(item['credential_id'])) for item in credentials]
        options = generate_authentication_options(rp_id=self.rp_id, allow_credentials=allow)
        public_key = json.loads(options_to_json(options))
        challenge_id = secrets.token_urlsafe(18)
        self._pending[challenge_id] = {'type': 'authentication', 'challenge': public_key['challenge']}
        return {'challenge_id': challenge_id, 'public_key': public_key}

    def finish_authentication(self, *, challenge_id: str, credential: dict[str, Any]) -> dict[str, object]:
        self._require_available()
        pending = self._consume_pending(challenge_id, expected_type='authentication')
        credential_id = credential.get('id') or credential.get('rawId')
        payload = self._read()
        credentials = payload.get('credentials', []) if isinstance(payload, dict) else []
        stored = next((item for item in credentials if item.get('credential_id') == credential_id), None)
        if stored is None:
            raise KeyError('credential_not_found')
        verified = verify_authentication_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(pending['challenge']),
            expected_rp_id=self.rp_id,
            expected_origin=self.origin,
            credential_public_key=base64url_to_bytes(stored['public_key']),
            credential_current_sign_count=int(stored.get('sign_count', 0)),
            require_user_verification=False,
        )
        stored['sign_count'] = verified.new_sign_count
        self._write(payload)
        return {'verified': True, 'credential_id': stored['credential_id']}

    def _consume_pending(self, challenge_id: str, *, expected_type: str) -> dict[str, Any]:
        pending = self._pending.pop(challenge_id, None)
        if pending is None or pending.get('type') != expected_type:
            raise KeyError('challenge_not_found')
        return pending

    def _require_available(self) -> None:
        if not self.available:
            raise RuntimeError('Passkey support unavailable')

    def _current_path(self) -> Path:
        return Path(os.getenv('HCC_DATA_DIR', str(DATA_DIR))) / 'passkeys.json'

    def _read(self) -> dict[str, Any]:
        self._path = self._current_path()
        try:
            if not self._path.exists():
                return {'credentials': []}
            payload = json.loads(self._path.read_text(encoding='utf-8'))
        except Exception:
            return {'credentials': []}
        if not isinstance(payload, dict):
            return {'credentials': []}
        payload.setdefault('credentials', [])
        return payload

    def _write(self, payload: dict[str, Any]) -> None:
        self._path = self._current_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


passkey_store = PasskeyStore()
