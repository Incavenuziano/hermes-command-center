from __future__ import annotations

from auth import auth_manager
from http_api import AuthenticationRequiredError, RequestValidationError, route
from passkeys import passkey_store


def _require_password_authenticated(handler) -> str:
    session_id = handler.require_csrf_token(auth_manager.is_valid_csrf_token)
    state = auth_manager.session_state(session_id)
    if not state.authenticated or state.auth_mode != 'local-password':
        raise AuthenticationRequiredError()
    return session_id


def _require_authenticated(handler) -> str:
    session_id = handler.require_session_id()
    state = auth_manager.session_state(session_id)
    if not state.authenticated:
        raise AuthenticationRequiredError()
    return session_id


@route('GET', '/auth/passkeys/status', allow=('GET',))
def passkey_status(handler) -> None:
    handler.send_data(passkey_store.status())


@route('POST', '/auth/passkeys/register/options', allow=('POST',))
def passkey_register_options(handler) -> None:
    session_id = _require_password_authenticated(handler)
    state = auth_manager.session_state(session_id)
    payload = handler.read_json_body()
    user_name = payload.get('user_name') if isinstance(payload.get('user_name'), str) and payload.get('user_name') else state.user
    try:
        result = passkey_store.begin_registration(user_name=str(user_name))
    except RuntimeError as exc:
        raise RequestValidationError(status=503, code='passkey.unavailable', message=str(exc)) from exc
    handler.send_data(result)


@route('POST', '/auth/passkeys/register/verify', allow=('POST',))
def passkey_register_verify(handler) -> None:
    _require_password_authenticated(handler)
    payload = handler.read_json_body()
    challenge_id = payload.get('challenge_id')
    credential = payload.get('credential')
    if not isinstance(challenge_id, str) or not challenge_id:
        raise RequestValidationError(status=400, code='passkey.invalid_request', message='challenge_id is required', details={'field': 'challenge_id'})
    if not isinstance(credential, dict):
        raise RequestValidationError(status=400, code='passkey.invalid_request', message='credential is required', details={'field': 'credential'})
    try:
        result = passkey_store.finish_registration(challenge_id=challenge_id, credential=credential)
    except KeyError as exc:
        raise RequestValidationError(status=404, code='passkey.challenge_not_found', message='Passkey challenge not found') from exc
    except RuntimeError as exc:
        raise RequestValidationError(status=503, code='passkey.unavailable', message=str(exc)) from exc
    except Exception as exc:
        raise RequestValidationError(status=400, code='passkey.registration_failed', message='Passkey registration failed', details={'reason': str(exc)}) from exc
    handler.send_data(result)


@route('POST', '/auth/passkeys/authenticate/options', allow=('POST',))
def passkey_authenticate_options(handler) -> None:
    _require_authenticated(handler)
    payload = handler.read_json_body()
    try:
        result = passkey_store.begin_authentication()
    except ValueError as exc:
        raise RequestValidationError(status=400, code='passkey.not_enrolled', message=str(exc)) from exc
    except RuntimeError as exc:
        raise RequestValidationError(status=503, code='passkey.unavailable', message=str(exc)) from exc
    handler.send_data(result)


@route('POST', '/auth/passkeys/authenticate/verify', allow=('POST',))
def passkey_authenticate_verify(handler) -> None:
    _require_authenticated(handler)
    payload = handler.read_json_body()
    challenge_id = payload.get('challenge_id')
    credential = payload.get('credential')
    if not isinstance(challenge_id, str) or not challenge_id:
        raise RequestValidationError(status=400, code='passkey.invalid_request', message='challenge_id is required', details={'field': 'challenge_id'})
    if not isinstance(credential, dict):
        raise RequestValidationError(status=400, code='passkey.invalid_request', message='credential is required', details={'field': 'credential'})
    try:
        result = passkey_store.finish_authentication(challenge_id=challenge_id, credential=credential)
    except KeyError as exc:
        raise RequestValidationError(status=404, code='passkey.challenge_not_found', message='Passkey challenge not found') from exc
    except RuntimeError as exc:
        raise RequestValidationError(status=503, code='passkey.unavailable', message=str(exc)) from exc
    except Exception as exc:
        raise RequestValidationError(status=400, code='passkey.authentication_failed', message='Passkey authentication failed', details={'reason': str(exc)}) from exc
    handler.send_data(result)
