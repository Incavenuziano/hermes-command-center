from __future__ import annotations

from config import to_jsonable
from http_api import AuthenticationRequiredError, route
from auth import auth_manager


@route('GET', '/operators/me', allow=('GET',))
def current_operator(handler) -> None:
    session_id = handler.require_session_id()
    state = auth_manager.session_state(session_id)
    if not state.authenticated:
        raise AuthenticationRequiredError()
    handler.send_data(
        to_jsonable(
            {
                'user': state.user,
                'auth_mode': state.auth_mode,
                'session': state,
            }
        )
    )
