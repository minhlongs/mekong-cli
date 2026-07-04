"""JWT token helpers for SessionManager."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import jwt

from src.models.user import User


class JwtSessionMixin:
    """JWT creation and decoding behavior for session managers."""

    def _create_jwt_claims(
        self,
        user_id: str,
        email: str,
        role: str = "member",
        token_type: str = "access",
    ) -> Dict[str, Any]:
        import src.auth.session_manager as config

        now = datetime.now(timezone.utc)
        expire_delta = (
            timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
            if token_type == "access"
            else timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        return {
            "aud": config.JWT_AUDIENCE,
            "iss": config.JWT_ISSUER,
            "sub": user_id,
            "email": email,
            "role": role,
            "type": token_type,
            "iat": now,
            "exp": now + expire_delta,
            "jti": secrets.token_urlsafe(16),
        }

    def create_access_token(self, user: User, role: str = "member") -> str:
        import src.auth.session_manager as config

        claims = self._create_jwt_claims(
            user_id=str(user.id),
            email=user.email,
            role=role,
            token_type="access",
        )
        return jwt.encode(
            claims,
            config.get_jwt_secret(),
            algorithm=config.JWT_ALGORITHM,
            headers={"kid": config.JWT_KEY_ID},
        )

    def create_refresh_token(self, user: User) -> str:
        import src.auth.session_manager as config

        claims = self._create_jwt_claims(
            user_id=str(user.id),
            email=user.email,
            token_type="refresh",
        )
        return jwt.encode(
            claims,
            config.get_jwt_secret(),
            algorithm=config.JWT_ALGORITHM,
            headers={"kid": config.JWT_KEY_ID},
        )

    def decode_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        import src.auth.session_manager as config

        try:
            payload = jwt.decode(
                token,
                config.get_jwt_secret(),
                algorithms=[config.JWT_ALGORITHM],
                audience=config.JWT_AUDIENCE if config._enforce_registered_claims() else None,
                issuer=config.JWT_ISSUER if config._enforce_registered_claims() else None,
                options={
                    "verify_aud": config._enforce_registered_claims(),
                    "verify_iss": config._enforce_registered_claims(),
                },
            )
            return True, payload, None
        except RuntimeError as e:
            return False, None, str(e)
        except jwt.ExpiredSignatureError:
            return False, None, "Token has expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {e}"


__all__ = ["JwtSessionMixin"]
