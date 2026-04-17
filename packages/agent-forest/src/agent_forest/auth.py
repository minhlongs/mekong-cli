"""JWT token creation + decoding. HS256, pluggable secret via ForestSettings."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from agent_forest.config import ForestSettings


class AuthError(Exception):
    """Raised for invalid/expired tokens."""


def create_access_token(user_id: str, settings: ForestSettings) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: ForestSettings) -> str:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise AuthError(f"Invalid or expired token: {exc}") from exc
    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Token payload missing 'sub' claim")
    return str(user_id)
