from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from http import cookies

from config import AUTH_ENABLED, AUTH_PASSWORD, AUTH_SESSION_TTL_SECONDS, AUTH_USER, ENV
from contracts.auth import SessionState

SESSION_COOKIE_NAME = 'session_id'
TRUSTED_LOCAL_SESSION_ID = '__trusted_local__'


@dataclass(slots=True)
class AuthSession:
    user: str
    issued_at: int
    expires_at: int
    csrf_token: str

    @property
    def authenticated(self) -> bool:
        return True


class AuthManager:
    def __init__(self) -> None:
        self._sessions: dict[str, AuthSession] = {}

    def authenticate(self, password: str, *, existing_session_id: str | None = None) -> str | None:
        if password != AUTH_PASSWORD:
            return None
        self.revoke(existing_session_id)
        session_id = secrets.token_urlsafe(24)
        issued_at = self._now()
        self._sessions[session_id] = AuthSession(
            user=AUTH_USER,
            issued_at=issued_at,
            expires_at=issued_at + AUTH_SESSION_TTL_SECONDS,
            csrf_token=secrets.token_urlsafe(24),
        )
        return session_id

    def _now(self) -> int:
        return int(time.time())

    def get_session(self, session_id: str | None) -> AuthSession | None:
        if not session_id:
            return None
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.expires_at <= self._now():
            self._sessions.pop(session_id, None)
            return None
        return session

    def get_user_for_session(self, session_id: str | None) -> str | None:
        session = self.get_session(session_id)
        if session is None:
            return None
        return session.user

    def revoke(self, session_id: str | None) -> None:
        if session_id:
            self._sessions.pop(session_id, None)

    def is_valid_csrf_token(self, session_id: str | None, csrf_token: str | None) -> bool:
        session = self.get_session(session_id)
        if session is None or not csrf_token:
            return False
        return secrets.compare_digest(session.csrf_token, csrf_token)

    def session_state(self, session_id: str | None) -> SessionState:
        session = self.get_session(session_id)
        if session is None:
            if not AUTH_ENABLED:
                return SessionState(authenticated=True, user=AUTH_USER, auth_mode='local-trusted')
            return SessionState(authenticated=False, user=None, auth_mode='local-password')
        return SessionState(
            authenticated=True,
            user=session.user,
            auth_mode='local-password',
            issued_at=session.issued_at,
            expires_at=session.expires_at,
            csrf_token=session.csrf_token,
        )


def parse_session_cookie(raw_cookie_header: str | None) -> str | None:
    if not raw_cookie_header:
        return None
    cookie_jar = cookies.SimpleCookie()
    cookie_jar.load(raw_cookie_header)
    morsel = cookie_jar.get(SESSION_COOKIE_NAME)
    if morsel is None:
        return None
    return morsel.value


def build_session_cookie(session_id: str, *, max_age: int | None = None) -> str:
    cookie = cookies.SimpleCookie()
    cookie[SESSION_COOKIE_NAME] = session_id
    cookie[SESSION_COOKIE_NAME]['path'] = '/'
    cookie[SESSION_COOKIE_NAME]['httponly'] = True
    cookie[SESSION_COOKIE_NAME]['samesite'] = 'Strict'
    if ENV != 'development':
        cookie[SESSION_COOKIE_NAME]['secure'] = True
    if max_age is not None:
        cookie[SESSION_COOKIE_NAME]['max-age'] = max_age
    return cookie.output(header='').strip()


def build_expired_session_cookie() -> str:
    secure_suffix = '; Secure' if ENV != 'development' else ''
    return f'{SESSION_COOKIE_NAME}=; HttpOnly; Max-Age=0; Path=/; SameSite=Strict{secure_suffix}'


auth_manager = AuthManager()
