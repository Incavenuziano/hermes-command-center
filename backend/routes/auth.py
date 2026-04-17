from __future__ import annotations

from auth import auth_manager, build_expired_session_cookie, build_session_cookie
from config import AUTH_SESSION_TTL_SECONDS, AUTH_USER, to_jsonable
from contracts.auth import SessionState
from http_api import AuthenticationRequiredError, RequestValidationError, route


@route('POST', '/auth/login', allow=('POST',))
def login(handler) -> None:
    payload = handler.read_json_body()
    password = payload.get('password')
    if not isinstance(password, str) or not password:
        raise RequestValidationError(
            status=400,
            code='auth.invalid_request',
            message='password is required',
            details={'field': 'password'},
        )

    session_id = auth_manager.authenticate(password, existing_session_id=handler.session_id)
    if session_id is None:
        handler.send_error_envelope(
            status=401,
            code='auth.invalid_credentials',
            message='Invalid credentials',
        )
        return

    state = auth_manager.session_state(session_id)
    handler.send_data(
        to_jsonable(state),
        extra_headers={'Set-Cookie': build_session_cookie(session_id, max_age=AUTH_SESSION_TTL_SECONDS)},
    )


@route('GET', '/auth/session', allow=('GET',))
def session(handler) -> None:
    session_id = handler.require_session_id()
    state = auth_manager.session_state(session_id)
    if not state.authenticated:
        raise AuthenticationRequiredError()
    handler.send_data(to_jsonable(state))


@route('POST', '/auth/logout', allow=('POST',))
def logout(handler) -> None:
    handler.read_json_body()
    session_id = handler.require_csrf_token(auth_manager.is_valid_csrf_token)
    auth_manager.revoke(session_id)
    state = SessionState(authenticated=False, user=None, auth_mode='local-password')
    handler.send_data(to_jsonable(state), extra_headers={'Set-Cookie': build_expired_session_cookie()})
