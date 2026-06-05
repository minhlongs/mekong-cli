"""CSRF protection middleware — double-submit cookie pattern.

On GET: sets mekong_csrf cookie if absent.
On POST/PUT/DELETE: validates X-CSRF-Token header matches cookie.
Skips webhook paths and Bearer-authenticated requests.

Activation: set CSRF_ENABLED=1 (disabled by default so existing API-token
clients and test suites work without changes).
"""
from __future__ import annotations

import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

# Only active when explicitly enabled — avoids breaking API-token clients / tests
_CSRF_ACTIVE = os.getenv("CSRF_ENABLED", "0") == "1"

# Actions that require token rotation — each privileged action gets a fresh token
_CSRF_PRIVILEGED_PATHS = {"/v1/auth/login", "/v1/auth/password-change"}
_CSRF_SKIP_PREFIXES = (
    "/v1/webhook/",
    "/v1/polar/",
    "/v1/payments/",
)
_CSRF_SKIP_EXACT = {"/health", "/healthz", "/metrics"}

_MUTATING_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
_COOKIE_NAME = "mekong_csrf"


def _is_localhost(host: str) -> bool:
    return host in ("localhost", "127.0.0.1", "::1")


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF middleware for Starlette/FastAPI."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: object) -> Response:  # type: ignore[override]
        if not _CSRF_ACTIVE:
            return await call_next(request)  # type: ignore[misc]

        path = request.url.path
        method = request.method.upper()

        # Skip CSRF for exempt paths
        if path in _CSRF_SKIP_EXACT:
            return await call_next(request)  # type: ignore[misc]
        for prefix in _CSRF_SKIP_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)  # type: ignore[misc]

        # Skip CSRF for Bearer-authenticated requests (API token auth)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)  # type: ignore[misc]

        existing_token = request.cookies.get(_COOKIE_NAME)

        # Validate on mutating methods
        if method in _MUTATING_METHODS:
            header_token = request.headers.get("X-CSRF-Token", "")
            if not existing_token or not header_token or not secrets.compare_digest(existing_token, header_token):
                return JSONResponse(
                    {"error": "csrf_validation_failed"},
                    status_code=403,
                )

        response: Response = await call_next(request)  # type: ignore[misc]

        # Rotate token after privileged actions; otherwise issue on GET if absent
        is_privileged = path in _CSRF_PRIVILEGED_PATHS
        if (method == "GET" and not existing_token) or is_privileged:
            token = secrets.token_hex(32)
            host = request.url.hostname or "localhost"
            is_secure = not _is_localhost(host)
            response.set_cookie(
                key=_COOKIE_NAME,
                value=token,
                httponly=True,
                samesite="strict",
                secure=is_secure,
            )

        return response
