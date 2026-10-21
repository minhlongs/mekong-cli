# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Session Cookies & Convenience Helpers."""

import os
import sys
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from fastapi import Request, Response
from starlette.responses import RedirectResponse

from src.models.user import User, UserSession


def _facade():
    return sys.modules["src.auth.session_manager"]


def register_jwt_key(kid: str, secret: str) -> None:
    """Register a JWT signing key for rotation support."""
    _facade()._active_jwt_keys[kid] = secret


def get_jwt_keys() -> dict[str, str]:
    """Return all active JWT keys for verification."""
    f = _facade()
    if not f._active_jwt_keys:
        f._active_jwt_keys[f.JWT_KEY_ID] = f.get_jwt_secret()
    return dict(f._active_jwt_keys)


def revoke_token(jti: str) -> None:
    """Add a token JTI to the revocation blacklist."""
    _facade()._revoked_tokens.add(jti)


def is_token_revoked(jti: str) -> bool:
    """Check if a token JTI is in the revocation blacklist."""
    return jti in _facade()._revoked_tokens


class SessionCookieMixin:
    """Mixin providing HTTPOnly cookie and session lifecycle helpers."""

    def create_session_cookie(
        self,
        token: str,
        expires_in_days: int = 7,
    ) -> Dict[str, Any]:
        """Create HTTPOnly cookie parameters for session token."""
        f = _facade()
        os_mod = getattr(f, "os", os)
        secure = os_mod.getenv("AUTH_ENVIRONMENT", "dev") == "production"
        return {
            "key": f.COOKIE_NAME,
            "value": token,
            "httponly": f.COOKIE_HTTPONLY,
            "secure": secure,
            "samesite": "none" if secure else f.COOKIE_SAMESITE,
            "max_age": expires_in_days * 24 * 60 * 60,
            "path": "/",
        }

    def set_session_cookie(
        self,
        response: Response,
        token: str,
        expires_in_days: int = 7,
    ) -> Response:
        """Set session cookie on response."""
        cookie_params = self.create_session_cookie(token, expires_in_days)
        response.set_cookie(**cookie_params)
        return response

    def get_session_cookie(self, request: Request) -> Optional[str]:
        """Extract session token from request cookie."""
        return request.cookies.get(_facade().COOKIE_NAME)

    def delete_session_cookie(self, response: Response) -> Response:
        """Delete session cookie from response."""
        response.delete_cookie(key=_facade().COOKIE_NAME, path="/", domain=None)
        return response

    def create_logout_redirect(
        self,
        response: Response,
        redirect_to: str = "/",
    ) -> RedirectResponse:
        """Create redirect response that clears session cookie."""
        redirect = RedirectResponse(url=redirect_to, status_code=303)
        self.delete_session_cookie(redirect)
        return redirect

    async def revoke_session(self, session_id: UUID) -> bool:
        """Revoke/invalidate a session (logout)."""
        return await self._user_repo.delete_session(session_id)

    async def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoke all sessions for a user (logout everywhere)."""
        return await self._user_repo.delete_user_sessions(user_id)

    async def refresh_session(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh session using refresh token."""
        is_valid, payload, _error = self.decode_token(refresh_token)
        if not is_valid or payload.get("type") != "refresh":
            return None
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or not email:
            return None
        try:
            user = await self._user_repo.find_by_id(UUID(user_id))
            if not user:
                return None
            new_access = self.create_access_token(user)
            new_refresh = self.create_refresh_token(user)
            old_jti = payload.get("jti")
            if old_jti:
                revoke_token(old_jti)
            return new_access, new_refresh
        except (ValueError, Exception):
            return None


async def create_session(user: User, role: str = "member") -> Tuple[UserSession, str, str]:
    """Create new session for user."""
    return await _facade().SessionManager().create_session(user, role)


async def validate_token(token: str) -> Optional[User]:
    """Validate token and return user."""
    return await _facade().SessionManager().validate_session(token)


async def revoke_session(session_id: UUID) -> bool:
    """Revoke session."""
    return await _facade().SessionManager().revoke_session(session_id)


def get_token_from_request(request: Request) -> Optional[str]:
    """Get session token from request cookie."""
    return _facade().SessionManager().get_session_cookie(request)
