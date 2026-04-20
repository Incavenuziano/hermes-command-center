from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler
from typing import Callable
from urllib.parse import parse_qs, urlparse

from auth import TRUSTED_LOCAL_SESSION_ID, parse_session_cookie
from config import AUTH_ENABLED, CONTRACT_VERSION, MAX_REQUEST_BYTES, to_jsonable
from contracts.errors import ErrorEnvelope

logger = logging.getLogger(__name__)
SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Content-Security-Policy': (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    ),
}

RouteHandler = Callable[['ApiHandler'], None]


@dataclass(slots=True)
class RouteDefinition:
    method: str
    path: str
    handler: RouteHandler
    allow: tuple[str, ...]


class RequestValidationError(Exception):
    def __init__(self, *, status: int, code: str, message: str, details: dict[str, object] | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


class AuthenticationRequiredError(Exception):
    pass


class CsrfValidationError(Exception):
    pass


class ApiHandler(BaseHTTPRequestHandler):
    server_version = 'HermesCommandCenter/0.4'
    protocol_version = 'HTTP/1.1'
    routes: dict[tuple[str, str], RouteDefinition] = {}
    allowed_methods_by_path: dict[str, tuple[str, ...]] = {}

    def log_message(self, fmt, *args):
        return

    def _request_id(self) -> str:
        return getattr(self, '_hermes_request_id', '') or str(uuid.uuid4())

    @property
    def parsed_url(self):
        return urlparse(self.path)

    @property
    def path_only(self) -> str:
        return self.parsed_url.path

    @property
    def query_params(self) -> dict[str, list[str]]:
        return parse_qs(self.parsed_url.query, keep_blank_values=True)

    @property
    def session_id(self) -> str | None:
        return parse_session_cookie(self.headers.get('Cookie'))

    def require_session_id(self) -> str:
        session_id = self.session_id
        if not session_id:
            if not AUTH_ENABLED:
                return TRUSTED_LOCAL_SESSION_ID
            raise AuthenticationRequiredError()
        return session_id

    def require_csrf_token(self, validator) -> str:
        session_id = self.require_session_id()
        if not AUTH_ENABLED and session_id == TRUSTED_LOCAL_SESSION_ID:
            return session_id
        csrf_token = self.headers.get('X-CSRF-Token')
        if not validator(session_id, csrf_token):
            raise CsrfValidationError()
        return session_id

    def _content_length(self) -> int:
        header_value = self.headers.get('Content-Length', '0')
        try:
            return int(header_value)
        except ValueError as exc:
            raise RequestValidationError(
                status=400,
                code='request.invalid_content_length',
                message='Invalid Content-Length header',
                details={'content_length': header_value},
            ) from exc

    def _content_type(self) -> str:
        raw_content_type = self.headers.get('Content-Type', '')
        return raw_content_type.split(';', 1)[0].strip().lower()

    def read_json_body(self, *, max_bytes: int = MAX_REQUEST_BYTES) -> dict:
        content_type = self._content_type()
        if content_type != 'application/json':
            raise RequestValidationError(
                status=415,
                code='request.unsupported_media_type',
                message='Unsupported media type',
                details={'expected': 'application/json', 'received': content_type or None},
            )

        content_length = self._content_length()
        if content_length > max_bytes:
            raise RequestValidationError(
                status=413,
                code='request.payload_too_large',
                message='Request payload too large',
                details={'max_bytes': max_bytes, 'content_length': content_length},
            )

        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode('utf-8') or '{}')
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RequestValidationError(
                status=400,
                code='request.invalid_json',
                message='Invalid JSON request body',
                details={'content_type': content_type},
            ) from exc

        if not isinstance(payload, dict):
            raise RequestValidationError(
                status=400,
                code='request.invalid_json_shape',
                message='JSON request body must be an object',
                details={'received_type': type(payload).__name__},
            )

        return payload

    def _meta(self) -> dict[str, str]:
        return {'request_id': self._request_id(), 'contract_version': CONTRACT_VERSION}

    def _base_headers(self, body_length: int) -> None:
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(body_length))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Contract-Version', CONTRACT_VERSION)
        self.send_header('X-Request-ID', self._request_id())
        for header_name, header_value in SECURITY_HEADERS.items():
            self.send_header(header_name, header_value)

    def _json(self, payload: dict, status: int = 200, extra_headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self._base_headers(len(body))
        for header_name, header_value in (extra_headers or {}).items():
            self.send_header(header_name, header_value)
        self.end_headers()
        self.wfile.write(body)

    def send_data(self, data: dict, status: int = 200, extra_headers: dict[str, str] | None = None) -> None:
        self._json({'data': data, 'meta': self._meta()}, status=status, extra_headers=extra_headers)

    def send_panel_data(self, data: dict, *, panel: dict | None = None, status: int = 200, extra_headers: dict[str, str] | None = None) -> None:
        flat = panel if panel is not None else data
        self._json({**flat, 'data': data, 'meta': self._meta()}, status=status, extra_headers=extra_headers)

    def send_error_envelope(
        self,
        *,
        status: int,
        code: str,
        message: str,
        details: dict[str, object] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        envelope = ErrorEnvelope(code=code, message=message, details=details or {}, request_id=self._request_id())
        self._json({'error': to_jsonable(envelope), 'meta': self._meta()}, status=status, extra_headers=extra_headers)

    def _dispatch(self, method: str) -> None:
        self._hermes_request_id = str(uuid.uuid4())
        logger.info(
            json.dumps(
                {
                    'event': 'request.received',
                    'method': method,
                    'path': self.path_only,
                    'query': self.query_params,
                    'request_id': self._request_id(),
                },
                ensure_ascii=False,
            )
        )

        route = self.routes.get((method, self.path_only))
        if route is not None:
            try:
                route.handler(self)
            except RequestValidationError as exc:
                self.send_error_envelope(status=exc.status, code=exc.code, message=exc.message, details=exc.details)
            except AuthenticationRequiredError:
                self.send_error_envelope(
                    status=401,
                    code='auth.authentication_required',
                    message='Authentication required',
                )
            except CsrfValidationError:
                self.send_error_envelope(
                    status=403,
                    code='auth.csrf_token_required',
                    message='A valid CSRF token is required',
                )
            return

        allowed_methods = self.allowed_methods_by_path.get(self.path_only)
        if allowed_methods:
            self.send_error_envelope(
                status=405,
                code='route.method_not_allowed',
                message='Method not allowed',
                details={'path': self.path_only, 'method': method, 'allowed_methods': list(allowed_methods)},
                extra_headers={'Allow': ', '.join(allowed_methods)},
            )
            return

        self.send_error_envelope(
            status=404,
            code='route.not_found',
            message='Route not found',
            details={'path': self.path_only, 'method': method},
        )

    def do_GET(self) -> None:
        self._dispatch('GET')

    def do_POST(self) -> None:
        self._dispatch('POST')


def route(method: str, path: str, allow: tuple[str, ...] | None = None):
    def decorator(func: RouteHandler) -> RouteHandler:
        normalized_allow = tuple(allow or (method,))
        ApiHandler.routes[(method, path)] = RouteDefinition(method=method, path=path, handler=func, allow=normalized_allow)
        existing = set(ApiHandler.allowed_methods_by_path.get(path, ()))
        existing.update(normalized_allow)
        ApiHandler.allowed_methods_by_path[path] = tuple(sorted(existing))
        return func

    return decorator
