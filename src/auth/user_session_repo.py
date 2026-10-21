# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""User Session Repository Mixin & Convenience Helpers."""

import sys
import uuid
from datetime import datetime, timedelta
from typing import Any, List, Optional

import bcrypt

from src.models.user import User, UserSession

SESSION_EXPIRY_HOURS = 24
SESSION_MAX_AGE = SESSION_EXPIRY_HOURS * 60 * 60


def _facade():
    return sys.modules["src.auth.user_repository"]


def hash_token(token: str) -> str:
    """Hash session token for secure storage using bcrypt."""
    return bcrypt.hashpw(token.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


class UserSessionRepositoryMixin:
    """Session database operations mixin for UserRepository."""

    _db: Any

    async def create_session(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_hours: int = SESSION_EXPIRY_HOURS,
    ) -> UserSession:
        """Create a new user session."""
        f = _facade()
        hasher = getattr(f, "hash_token", hash_token)
        token_hash = hasher(token)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

        query = """
            INSERT INTO user_sessions (user_id, token_hash, expires_at)
            VALUES ($1, $2, $3)
            RETURNING *
        """
        row = await self._db.fetch_one(
            query,
            (str(user_id), token_hash, expires_at),
        )
        if not row:
            raise ValueError("Failed to create session")
        return UserSession.from_dict(row)

    async def find_session_by_token(self, token: str) -> Optional[UserSession]:
        """Find session by token (hashes token and looks up)."""
        f = _facade()
        hasher = getattr(f, "hash_token", hash_token)
        token_hash = hasher(token)
        query = """
            SELECT s.*, u.email, u.oauth_provider
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token_hash = $1 AND s.expires_at > NOW()
        """
        row = await self._db.fetch_one(query, (token_hash,))
        return UserSession.from_dict(row) if row else None

    async def find_session_by_id(self, session_id: uuid.UUID) -> Optional[UserSession]:
        """Find session by ID."""
        query = """
            SELECT s.*, u.email, u.oauth_provider
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = $1 AND s.expires_at > NOW()
        """
        row = await self._db.fetch_one(query, (str(session_id),))
        return UserSession.from_dict(row) if row else None

    async def find_user_sessions(self, user_id: uuid.UUID) -> List[UserSession]:
        """Find all valid sessions for a user."""
        query = """
            SELECT * FROM user_sessions
            WHERE user_id = $1 AND expires_at > NOW()
            ORDER BY created_at DESC
        """
        rows = await self._db.fetch_all(query, (str(user_id),))
        return [UserSession.from_dict(row) for row in rows]

    async def delete_session(self, session_id: uuid.UUID) -> bool:
        """Delete a session (logout)."""
        query = "DELETE FROM user_sessions WHERE id = $1"
        result = await self._db.execute(query, (str(session_id),))
        return "DELETE" in result

    async def delete_user_sessions(self, user_id: uuid.UUID) -> int:
        """Delete all sessions for a user (logout everywhere)."""
        query = "DELETE FROM user_sessions WHERE user_id = $1"
        result = await self._db.execute(query, (str(user_id),))
        parts = result.split()
        return int(parts[1]) if len(parts) > 1 else 0

    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions from database."""
        query = "SELECT cleanup_expired_sessions()"
        result = await self._db.fetchval(query)
        return result or 0


async def find_or_create_user(
    email: str,
    provider: str,
    oauth_id: str,
) -> User:
    """Find or create user from OAuth2 login."""
    repo = _facade().UserRepository()
    return await repo.find_or_create_user(email, provider, oauth_id)


async def create_session(user_id: uuid.UUID, token: str) -> UserSession:
    """Create user session."""
    repo = _facade().UserRepository()
    return await repo.create_session(user_id, token)


async def find_session(token: str) -> Optional[UserSession]:
    """Find session by token."""
    repo = _facade().UserRepository()
    return await repo.find_session_by_token(token)


async def logout(session_id: uuid.UUID) -> bool:
    """Delete session (logout)."""
    repo = _facade().UserRepository()
    return await repo.delete_session(session_id)
