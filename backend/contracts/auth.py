from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SessionState:
    authenticated: bool
    user: str | None
    auth_mode: str
    issued_at: int | None = None
    expires_at: int | None = None
    csrf_token: str | None = None
