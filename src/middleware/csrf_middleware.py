# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CSRF protection middleware — double-submit cookie pattern.

On GET: sets mekong_csrf cookie if absent.
On POST/PUT/DELETE: validates X-CSRF-Token header matches cookie.
Skips webhook paths and Bearer-authenticated requests.

Activation: set CSRF_ENABLED=1 (disabled by default so existing API-token
clients and test suites work without changes).
"""
from __future__ import annotations

import asyncio
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
# Token format: <hex_token>|<version_int> — version counter prevents
# TOCTOU race where two concurrent GET requests both see token=None,
# both generate new tokens, last writer clobbers the first's token.
_TOKEN_SEP = "|"
_CURRENT_VERSION = "1"


def _is_localhost(host: str) -> bool:
    return host in ("localhost", "127.0.0.1", "::1")


# asyncio lock serializes token rotation across concurrent requests,
# preventing the TOCTOU race where two GETs both see token=None.
_csrf_lock = asyncio.Lock()


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

        raw_cookie = request.cookies.get(_COOKIE_NAME, "")
        parts = raw_cookie.split(_TOKEN_SEP, 1)
        existing_token = parts[0] if parts else ""
        existing_version = parts[1] if len(parts) > 1 else ""

        # Validate on mutating methods — check token against current version
        if method in _MUTATING_METHODS:
            header_token = request.headers.get("X-CSRF-Token", "")
            if not secrets.compare_digest(existing_token, header_token):
                # Token doesn't match current version — force re-login
                return JSONResponse(
                    {"error": "csrf_validation_failed"},
                    status_code=403,
                )

        response: Response = await call_next(request)  # type: ignore[misc]

        # Rotate token after privileged actions; otherwise issue on GET if absent.
        # Wrapped in lock so only one concurrent request can rotate at a time,
        # preventing two requests from both seeing token=None and clobbering
        # each other's freshly-issued tokens.
        is_privileged = path in _CSRF_PRIVILEGED_PATHS
        needs_token = (method == "GET" and not existing_token) or is_privileged
        if needs_token:
            async with _csrf_lock:
                # Re-read cookie after acquiring lock — another request may
                # have already issued a token while we waited.
                raw_cookie = request.cookies.get(_COOKIE_NAME, "")
                parts = raw_cookie.split(_TOKEN_SEP, 1)
                existing_token = parts[0] if parts else ""
                existing_version = parts[1] if len(parts) > 1 else ""

                # Skip if another request already issued a valid token
                if existing_token and existing_version == _CURRENT_VERSION:
                    needs_token = False

                if needs_token:
                    token = secrets.token_hex(32)
                    host = request.url.hostname or "localhost"
                    is_secure = not _is_localhost(host)
                    response.set_cookie(
                        key=_COOKIE_NAME,
                        value=f"{token}{_TOKEN_SEP}{_CURRENT_VERSION}",
                        httponly=True,
                        samesite="strict",
                        secure=is_secure,
                    )

        return response
