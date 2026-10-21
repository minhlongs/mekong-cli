# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Session Manager - JWT-based session management with HTTPOnly cookies."""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

import jwt
from fastapi import Request, Response  # noqa: F401
from starlette.responses import RedirectResponse  # noqa: F401

from src.auth.session_cookies import (
    SessionCookieMixin,
    create_session,
    get_jwt_keys,
    get_token_from_request,
    is_token_revoked,
    register_jwt_key,
    revoke_session,
    revoke_token,
    validate_token,
)
from src.auth.user_repository import UserRepository
from src.models.user import User, UserSession

JWT_SECRET: Optional[str] = None
JWT_ALGORITHM = "HS256"
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "mekong-cli")
JWT_ISSUER = os.getenv("JWT_ISSUER", "mekong-auth")
JWT_KEY_ID = os.getenv("JWT_KEY_ID", "mekong-key-v1")
_active_jwt_keys: dict[str, str] = {}
_revoked_tokens: set[str] = set()


def get_jwt_secret() -> str:
    """Return JWT secret from environment variable."""
    global JWT_SECRET
    if JWT_SECRET is None:
        JWT_SECRET = os.getenv("JWT_SECRET")
        if not JWT_SECRET:
            raise RuntimeError(
                "JWT_SECRET environment variable is required. "
                "Generate one with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))' "
                "and add to your .env file."
            )
        if len(JWT_SECRET.encode()) < 32:
            raise RuntimeError(
                f"JWT_SECRET is too short: {len(JWT_SECRET.encode())} bytes. "
                "Minimum 32 bytes required for production security."
            )
    return JWT_SECRET


ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRY_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7"))

COOKIE_NAME = "__Host-session_token"
COOKIE_SECURE = os.getenv("AUTH_ENVIRONMENT", "dev") == "production"
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax" if not COOKIE_SECURE else "none"


class SessionManager(SessionCookieMixin):
    """Manager for JWT-based user sessions."""

    def __init__(self, user_repo: Optional[UserRepository] = None):
        self._user_repo = user_repo or UserRepository()

    def _create_jwt_claims(
        self, user_id: str, email: str, role: str = "member", token_type: str = "access"
    ) -> Dict[str, Any]:
        """Create JWT claims for user."""
        now = datetime.now(timezone.utc)
        expire_delta = (
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            if token_type == "access"
            else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        return {
            "aud": JWT_AUDIENCE,
            "iss": JWT_ISSUER,
            "sub": user_id,
            "email": email,
            "role": role,
            "type": token_type,
            "iat": now,
            "exp": now + expire_delta,
            "jti": secrets.token_urlsafe(16),
        }

    def create_access_token(self, user: User, role: str = "member") -> str:
        """Create JWT access token for user."""
        claims = self._create_jwt_claims(str(user.id), user.email, role, "access")
        return jwt.encode(
            claims, get_jwt_secret(), algorithm=JWT_ALGORITHM, headers={"kid": JWT_KEY_ID}
        )

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user."""
        claims = self._create_jwt_claims(str(user.id), user.email, token_type="refresh")
        return jwt.encode(
            claims, get_jwt_secret(), algorithm=JWT_ALGORITHM, headers={"kid": JWT_KEY_ID}
        )

    def decode_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                get_jwt_secret(),
                algorithms=[JWT_ALGORITHM],
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
            )
            return True, payload, None
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {e}"

    async def create_session(
        self, user: User, role: str = "member"
    ) -> Tuple[UserSession, str, str]:
        """Create new session for user."""
        access_token = self.create_access_token(user, role)
        refresh_token = self.create_refresh_token(user)
        session = await self._user_repo.create_session(
            user_id=user.id, token=access_token, expires_hours=168
        )
        return session, access_token, refresh_token

    async def validate_session(self, token: str) -> Optional[User]:
        """Validate session token and return user."""
        is_valid, payload, _error = self.decode_token(token)
        if not is_valid:
            return None
        token_jti = payload.get("jti") if isinstance(payload, dict) else None
        if token_jti and is_token_revoked(token_jti):
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        try:
            return await self._user_repo.find_by_id(UUID(user_id))
        except (ValueError, Exception):
            return None


__all__ = [
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "COOKIE_HTTPONLY",
    "COOKIE_NAME",
    "COOKIE_SAMESITE",
    "COOKIE_SECURE",
    "JWT_ALGORITHM",
    "JWT_AUDIENCE",
    "JWT_ISSUER",
    "JWT_KEY_ID",
    "JWT_SECRET",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "SessionManager",
    "create_session",
    "get_jwt_keys",
    "get_jwt_secret",
    "get_token_from_request",
    "is_token_revoked",
    "register_jwt_key",
    "revoke_session",
    "revoke_token",
    "validate_token",
]
