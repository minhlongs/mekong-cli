# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Session Middleware - JWT authentication middleware for FastAPI."""

from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.auth.config import AuthConfig
from src.auth.middleware_optional import (
    AUTH_RATE_LIMITS,
    AuthMiddlewareMixin,
    OptionalAuthMiddleware,
    create_auth_middleware,
)
from src.auth.rate_limiter import (
    RateLimiter,
    RateLimitPreset,  # noqa: F401
    get_rate_limiter,
)
from src.auth.session_manager import SessionManager
from src.auth.user_repository import UserRepository
from src.models.user import User  # noqa: F401


class SessionMiddleware(AuthMiddlewareMixin, BaseHTTPMiddleware):
    """Middleware to authenticate requests via JWT session tokens."""

    def __init__(
        self,
        app: ASGIApp,
        session_manager: Optional[SessionManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        super().__init__(app)
        self._session_manager = session_manager or SessionManager()
        self._user_repo = UserRepository()
        self._rate_limiter = rate_limiter or get_rate_limiter()

    async def dispatch(self, request: Request, call_next):
        """Process request and inject user context."""
        config = AuthConfig()

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

        request.state.rate_limit_headers = rate_headers

        if config.is_dev_mode():
            request.state.authenticated = True
            request.state.user = type(
                "TestUser",
                (),
                {
                    "id": "test-user-id",
                    "email": "test@dev.local",
                    "role": "owner",
                },
            )()
            request.state.user_id = "test-user-id"
            request.state.user_email = "test@dev.local"
            request.state.user_role = "owner"
            request.state.is_dev_mode = True

            response = await call_next(request)
            for header_name, header_value in rate_headers.items():
                response.headers[header_name] = header_value
            return response

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
                request.state.is_dev_mode = False
            else:
                self._clear_auth_state(request)
        else:
            self._clear_auth_state(request)

        response = await call_next(request)
        for header_name, header_value in rate_headers.items():
            response.headers[header_name] = header_value
        return response

    @staticmethod
    def _clear_auth_state(request: Request) -> None:
        request.state.authenticated = False
        request.state.user = None
        request.state.user_id = None
        request.state.user_email = None
        request.state.user_role = None
        request.state.is_dev_mode = False


__all__ = [
    "AUTH_RATE_LIMITS",
    "OptionalAuthMiddleware",
    "SessionMiddleware",
    "create_auth_middleware",
]
