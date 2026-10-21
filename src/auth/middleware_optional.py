# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Optional Auth Middleware & Auth Middleware Mixin."""

import sys
from typing import Optional
from uuid import UUID

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.auth.rate_limiter import RateLimiter, RateLimitPreset
from src.auth.session_manager import SessionManager
from src.models.user import User

AUTH_RATE_LIMITS = {
    "/auth/login": RateLimitPreset.AUTH_LOGIN,
    "/auth/callback": RateLimitPreset.AUTH_CALLBACK,
    "/auth/refresh": RateLimitPreset.AUTH_REFRESH,
    "/auth/dev-login": RateLimitPreset.AUTH_DEV_LOGIN,
}


def _facade():
    return sys.modules["src.auth.middleware"]


class AuthMiddlewareMixin:
    """Shared authentication and rate limiting methods for auth middlewares."""

    _session_manager: SessionManager
    _user_repo: object
    _rate_limiter: RateLimiter

    async def _authenticate_user(
        self,
        token: str,
    ) -> Optional[tuple[User, dict]]:
        """Authenticate user from JWT token."""
        is_valid, payload, _error = self._session_manager.decode_token(token)
        if not is_valid:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user = await self._user_repo.find_by_id(UUID(user_id))
            if not user:
                return None
            return user, payload
        except (ValueError, Exception):
            return None

    async def _check_rate_limit(
        self,
        request: Request,
    ) -> tuple[bool, dict[str, str]]:
        """Check rate limit for auth endpoints."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif request.headers.get("X-Real-IP"):
            client_ip = request.headers.get("X-Real-IP").strip()
        else:
            client_ip = request.client.host if request.client else "127.0.0.1"

        path = request.url.path
        preset = None
        f = _facade()
        limits = getattr(f, "AUTH_RATE_LIMITS", AUTH_RATE_LIMITS)

        for endpoint, endpoint_preset in limits.items():
            if path.startswith(endpoint):
                preset = endpoint_preset
                break

        if preset is None:
            return True, {}

        key = f"{client_ip}:{path}"
        return await self._rate_limiter.check_limit(key, preset=preset)


class OptionalAuthMiddleware(AuthMiddlewareMixin, BaseHTTPMiddleware):
    """Middleware that makes authentication optional."""

    def __init__(
        self,
        app: ASGIApp,
        session_manager: Optional[SessionManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        super().__init__(app)
        f = _facade()
        self._session_manager = session_manager or f.SessionManager()
        self._user_repo = f.UserRepository()
        self._rate_limiter = rate_limiter or f.get_rate_limiter()

    async def dispatch(self, request: Request, call_next):
        """Process request and attach user context if authenticated."""
        allowed, rate_headers = await self._check_rate_limit(request)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": int(rate_headers.get("Retry-After", 60)),
                },
                headers=rate_headers,
            )

        token = self._session_manager.get_session_cookie(request)
        if token:
            result = await self._authenticate_user(token)
            if result:
                user, payload = result
                request.state.authenticated = True
                request.state.user = user
                request.state.user_id = payload.get("sub")
                request.state.user_email = payload.get("email")
                request.state.user_role = payload.get("role", "member")
            else:
                request.state.authenticated = False
                request.state.user = None
                request.state.user_role = None
        else:
            request.state.authenticated = False
            request.state.user = None
            request.state.user_role = None

        response = await call_next(request)
        for header_name, header_value in rate_headers.items():
            response.headers[header_name] = header_value
        return response


def create_auth_middleware(dev_mode: bool = False):
    """Factory function to create appropriate auth middleware."""
    if dev_mode:
        class DevBypassMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                request.state.authenticated = True
                request.state.user = type(
                    "DevUser",
                    (),
                    {"id": "dev-user", "email": "dev@local", "role": "owner"},
                )()
                request.state.user_role = "owner"
                return await call_next(request)

        return DevBypassMiddleware
    return _facade().SessionMiddleware
