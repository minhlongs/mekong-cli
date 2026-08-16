# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Session persistence and refresh lifecycle helpers."""

from __future__ import annotations

from typing import Optional, Tuple
from uuid import UUID

from src.models.user import User, UserSession


class SessionLifecycleMixin:
    """Database-backed session lifecycle behavior."""

    async def create_session(
        self,
        user: User,
        role: str = "member",
    ) -> Tuple[UserSession, str, str]:
        access_token = self.create_access_token(user, role)
        refresh_token = self.create_refresh_token(user)
        session = await self._user_repo.create_session(
            user_id=user.id,
            token=access_token,
            expires_hours=168,
        )
        return session, access_token, refresh_token

    async def validate_session(self, token: str) -> Optional[User]:
        import src.auth.session_manager as config

        is_valid, payload, error = self.decode_token(token)
        if not is_valid:
            return None

        token_jti = payload.get("jti") if isinstance(payload, dict) else None
        if token_jti and config.is_token_revoked(token_jti):
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            return await self._user_repo.find_by_id(UUID(user_id))
        except (ValueError, Exception):
            return None

    async def revoke_session(self, session_id: UUID) -> bool:
        return await self._user_repo.delete_session(session_id)

    async def revoke_all_user_sessions(self, user_id: UUID) -> int:
        return await self._user_repo.delete_user_sessions(user_id)

    async def refresh_session(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        import src.auth.session_manager as config

        is_valid, payload, error = self.decode_token(refresh_token)
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
                config.revoke_token(old_jti)
            return new_access, new_refresh
        except (ValueError, Exception):
            return None


__all__ = ["SessionLifecycleMixin"]
