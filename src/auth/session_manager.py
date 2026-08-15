"""
Session Manager - JWT-based session management with HTTPOnly cookies

Handles JWT token generation, validation, refresh, and cookie management.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

import jwt
from fastapi import Request, Response
from starlette.responses import RedirectResponse

from src.models.user import User, UserSession
from src.auth.user_repository import UserRepository
from src.auth.env_validator import _is_test_or_ci

# JWT Configuration
JWT_SECRET: Optional[str] = None
JWT_ALGORITHM = "HS256"
JWT_KEY_ID = os.getenv("JWT_KEY_ID", "mekong-key-1")
# Key rotation: map of kid -> secret. Always include at least the active key.
_active_jwt_keys: dict[str, str] = {}


def register_jwt_key(kid: str, secret: str) -> None:
    """Register a JWT signing key for rotation support."""
    _active_jwt_keys[kid] = secret


def get_jwt_keys() -> dict[str, str]:
    """Return all active JWT keys for verification (rotation: old keys stay valid)."""
    if not _active_jwt_keys:
        # Auto-register the default secret on first access
        _active_jwt_keys[JWT_KEY_ID] = get_jwt_secret()
    return dict(_active_jwt_keys)


JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "mekong-cli")
JWT_ISSUER = os.getenv("JWT_ISSUER", "mekong-auth")
JWT_KEY_ID = os.getenv("JWT_KEY_ID", "mekong-key-v1")
_revoked_tokens: set[str] = set()


def get_jwt_secret() -> str:
    """Return JWT secret from environment variable.

    If JWT_SECRET is not set, auto-generates a secure random secret.
    This allows tests to run without manual environment configuration.

    Returns:
        JWT secret string (minimum 32 bytes)

    Raises:
        RuntimeError: If the generated or configured secret is too short
    """
    global JWT_SECRET
    if JWT_SECRET is None:
        JWT_SECRET = os.getenv("JWT_SECRET")
        if not JWT_SECRET:
            # Only auto-generate for test/CI environments
            if _is_test_or_ci():
                # Deterministic fallback for CI tests
                JWT_SECRET = "test-jwt-secret-fallback-" + "x" * 24
            else:
                raise RuntimeError(
                    "JWT_SECRET environment variable is required in production. "
                    "Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
    if len(JWT_SECRET.encode()) < 32:
        raise RuntimeError(
            f"JWT_SECRET is too short: {len(JWT_SECRET.encode())} bytes. "
            "Minimum 32 bytes required for security. "
            "Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    return JWT_SECRET


ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRY_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7"))

# Cookie configuration
COOKIE_NAME = "__Host-session_token"
COOKIE_HTTPONLY = True


def _cookie_secure() -> bool:
    """Check if cookies should have the Secure flag (runtime, not import-time)."""
    return os.getenv("AUTH_ENVIRONMENT", "dev") == "production"


def _cookie_samesite() -> str:
    """Return appropriate SameSite value based on environment."""
    return "none" if _cookie_secure() else "lax"


# Module-level attributes for backward compatibility (tests and other code read these)
# These are evaluated at import time for simplicity; the _cookie_secure() function
# is the primary source of truth for runtime checks.
COOKIE_SECURE: bool = _cookie_secure()
COOKIE_SAMESITE: str = _cookie_samesite()


def revoke_token(jti: str) -> None:
    """Add a token JTI to the revocation blacklist."""
    _revoked_tokens.add(jti)


def is_token_revoked(jti: str) -> bool:
    """Check if a token JTI is in the revocation blacklist."""
    return jti in _revoked_tokens


class SessionManager:
    """Manager for JWT-based user sessions."""

    def __init__(self, user_repo: Optional[UserRepository] = None):
        self._user_repo = user_repo or UserRepository()

    def _create_jwt_claims(
        self,
        user_id: str,
        email: str,
        role: str = "member",
        token_type: str = "access",
    ) -> Dict[str, Any]:
        """Create JWT claims for user.

        Args:
            user_id: User UUID as string
            email: User email address
            role: User role for RBAC
            token_type: 'access' or 'refresh'

        Returns:
            JWT claims dictionary
        """
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
        """Create JWT access token for user.

        Args:
            user: User object
            role: User role for RBAC (default: member)

        Returns:
            Encoded JWT access token string
        """
        claims = self._create_jwt_claims(
            user_id=str(user.id),
            email=user.email,
            role=role,
            token_type="access",
        )
        return jwt.encode(
            claims,
            get_jwt_secret(),
            algorithm=JWT_ALGORITHM,
            headers={"kid": JWT_KEY_ID},
        )

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token for user.

        Args:
            user: User object

        Returns:
            Encoded JWT refresh token string
        """
        claims = self._create_jwt_claims(
            user_id=str(user.id),
            email=user.email,
            token_type="refresh",
        )
        return jwt.encode(
            claims,
            get_jwt_secret(),
            algorithm=JWT_ALGORITHM,
            headers={"kid": JWT_KEY_ID},
        )

    def decode_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Tuple of (is_valid, payload_dict, error_message)
        """
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
        self,
        user: User,
        role: str = "member",
    ) -> Tuple[UserSession, str, str]:
        """Create new session for user.

        Generates access and refresh tokens, stores session in database.

        Args:
            user: User object
            role: User role for RBAC

        Returns:
            Tuple of (session, access_token, refresh_token)
        """
        access_token = self.create_access_token(user, role)
        refresh_token = self.create_refresh_token(user)

        session = await self._user_repo.create_session(
            user_id=user.id,
            token=access_token,
            expires_hours=168,
        )

        return session, access_token, refresh_token

    async def validate_session(self, token: str) -> Optional[User]:
        """Validate session token and return user.

        Checks JWT signature, expiry, and revocation blacklist.

        Args:
            token: JWT access token

        Returns:
            User object if valid, None otherwise
        """
        is_valid, payload, error = self.decode_token(token)
        if not is_valid:
            return None

        # Reject revoked tokens
        token_jti = payload.get("jti") if isinstance(payload, dict) else None
        if token_jti and is_token_revoked(token_jti):
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user = await self._user_repo.find_by_id(UUID(user_id))
            return user
        except (ValueError, Exception):
            return None

    async def revoke_session(self, session_id: UUID) -> bool:
        """Revoke/invalidate a session (logout).

        Args:
            session_id: Session UUID to revoke

        Returns:
            True if session was revoked, False otherwise
        """
        return await self._user_repo.delete_session(session_id)

    async def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoke all sessions for a user (logout everywhere).

        Args:
            user_id: User UUID

        Returns:
            Number of sessions revoked
        """
        return await self._user_repo.delete_user_sessions(user_id)

    async def refresh_session(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh session using refresh token.

        Validates the refresh token type claim, generates new tokens,
        and revokes the old refresh token to prevent reuse.

        Args:
            refresh_token: JWT refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token) if successful,
            None if refresh token is invalid or expired
        """
        is_valid, payload, error = self.decode_token(refresh_token)
        if not is_valid:
            return None

        # Enforce token type — reject access tokens presented as refresh
        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            return None

        # Fetch user to ensure still exists
        try:
            user = await self._user_repo.find_by_id(UUID(user_id))
            if not user:
                return None

            # Generate new tokens
            new_access = self.create_access_token(user)
            new_refresh = self.create_refresh_token(user)

            # Revoke old refresh token to prevent reuse
            old_jti = payload.get("jti")
            if old_jti:
                revoke_token(old_jti)

            return new_access, new_refresh
        except (ValueError, Exception):
            return None

    # === HTTPOnly Cookie Helpers ===

    def create_session_cookie(
        self,
        token: str,
        expires_in_days: int = 7,
    ) -> Dict[str, Any]:
        """Create HTTPOnly cookie parameters for session token.

        Args:
            token: JWT session token
            expires_in_days: Cookie expiration in days

        Returns:
            Dictionary of cookie parameters for Response.set_cookie()
        """
        return {
            "key": COOKIE_NAME,
            "value": token,
            "httponly": COOKIE_HTTPONLY,
            "secure": _cookie_secure(),
            "samesite": _cookie_samesite(),
            "max_age": expires_in_days * 24 * 60 * 60,
            "path": "/",
        }

    def set_session_cookie(
        self,
        response: Response,
        token: str,
        expires_in_days: int = 7,
    ) -> Response:
        """Set session cookie on response.

        Args:
            response: FastAPI Response object
            token: JWT session token
            expires_in_days: Cookie expiration in days

        Returns:
            Response with cookie set
        """
        cookie_params = self.create_session_cookie(token, expires_in_days)
        response.set_cookie(**cookie_params)
        return response

    def get_session_cookie(self, request: Request) -> Optional[str]:
        """Extract session token from request cookie.

        Supports both the secure __Host- prefixed cookie name and the legacy
        plain name for backward compatibility.

        Args:
            request: FastAPI Request object

        Returns:
            Session token if present, None otherwise
        """
        # Try __Host- prefixed name first (preferred)
        token = request.cookies.get(COOKIE_NAME)
        if token:
            return token
        # Fallback to legacy name for backward compatibility
        return request.cookies.get("session_token")

    def delete_session_cookie(self, response: Response) -> Response:
        """Delete session cookie from response.

        Args:
            response: FastAPI Response object

        Returns:
            Response with cookie deleted
        """
        response.delete_cookie(
            key=COOKIE_NAME,
            path="/",
            domain=None,
        )
        return response

    def create_logout_redirect(
        self,
        response: Response,
        redirect_to: str = "/",
    ) -> RedirectResponse:
        """Create redirect response that clears session cookie.

        Args:
            response: Response object (for cookie clearing)
            redirect_to: URL to redirect to after logout

        Returns:
            RedirectResponse with cleared session cookie
        """
        redirect = RedirectResponse(url=redirect_to, status_code=303)
        self.delete_session_cookie(redirect)
        return redirect


# Convenience functions for simple usage
async def create_session(user: User, role: str = "member") -> Tuple[UserSession, str, str]:
    """Create new session for user."""
    manager = SessionManager()
    return await manager.create_session(user, role)


async def validate_token(token: str) -> Optional[User]:
    """Validate token and return user."""
    manager = SessionManager()
    return await manager.validate_session(token)


async def revoke_session(session_id: UUID) -> bool:
    """Revoke session."""
    manager = SessionManager()
    return await manager.revoke_session(session_id)


def get_token_from_request(request: Request) -> Optional[str]:
    """Get session token from request cookie."""
    manager = SessionManager()
    return manager.get_session_cookie(request)
