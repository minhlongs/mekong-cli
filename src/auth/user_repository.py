# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""User Repository - Database operations for OAuth2 users."""

import uuid
from typing import Any, Dict, Optional

import bcrypt  # noqa: F401

from src.auth.user_session_repo import (
    SESSION_EXPIRY_HOURS,
    SESSION_MAX_AGE,
    UserSessionRepositoryMixin,
    create_session,
    find_or_create_user,
    find_session,
    hash_token,
    logout,
)
from src.db.database import DatabaseConnection, get_database
from src.models.user import User, UserSession  # noqa: F401


class UserRepository(UserSessionRepositoryMixin):
    """Repository for user and session database operations."""

    def __init__(self, db: Optional[DatabaseConnection] = None):
        self._db = db or get_database()

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        query = "SELECT * FROM users WHERE email = $1"
        row = await self._db.fetch_one(query, (email,))
        return User.from_dict(row) if row else None

    async def find_by_oauth(
        self,
        provider: str,
        oauth_id: str,
    ) -> Optional[User]:
        """Find user by OAuth provider and ID."""
        query = "SELECT * FROM users WHERE oauth_provider = $1 AND oauth_id = $2"
        row = await self._db.fetch_one(query, (provider, oauth_id))
        return User.from_dict(row) if row else None

    async def create_user(
        self,
        email: str,
        provider: str,
        oauth_id: str,
    ) -> User:
        """Create a new user."""
        query = """
            INSERT INTO users (email, oauth_provider, oauth_id)
            VALUES ($1, $2, $3)
            RETURNING *
        """
        row = await self._db.fetch_one(query, (email, provider, oauth_id))
        if not row:
            raise ValueError("Failed to create user")
        return User.from_dict(row)

    async def find_or_create_user(
        self,
        email: str,
        provider: str,
        oauth_id: str,
    ) -> User:
        """Find existing user or create new one."""
        user = await self.find_by_oauth(provider, oauth_id)
        if user:
            return user
        user = await self.find_by_email(email)
        if user:
            return user
        return await self.create_user(email, provider, oauth_id)

    async def update_user(self, user_id: uuid.UUID, **kwargs: Any) -> Optional[User]:
        """Update user fields."""
        if not kwargs:
            return await self.find_by_id(user_id)

        fields = ", ".join(f"{k} = ${i+1}" for i, k in enumerate(kwargs.keys()))
        values = list(kwargs.values())
        query = f"""
            UPDATE users SET {fields}, updated_at = NOW()
            WHERE id = ${len(values) + 1}
            RETURNING *
        """
        values.append(str(user_id))
        row = await self._db.fetch_one(query, tuple(values))
        return User.from_dict(row) if row else None

    async def update_user_role(self, user_id: uuid.UUID, role: str) -> Optional[User]:
        """Update user role from Stripe subscription sync."""
        query = """
            UPDATE users SET role = $1, updated_at = NOW()
            WHERE id = $2
            RETURNING *
        """
        row = await self._db.fetch_one(query, (role, str(user_id)))
        return User.from_dict(row) if row else None

    async def get_user_with_role(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get user with their current role."""
        query = """
            SELECT id, email, oauth_provider, oauth_id, role, created_at, updated_at
            FROM users
            WHERE id = $1
        """
        row = await self._db.fetch_one(query, (str(user_id),))
        if not row:
            return None

        return {
            "id": row["id"],
            "email": row["email"],
            "oauth_provider": row["oauth_provider"],
            "oauth_id": row["oauth_id"],
            "role": row.get("role", "member"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    async def find_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Find user by ID."""
        query = "SELECT * FROM users WHERE id = $1"
        row = await self._db.fetch_one(query, (str(user_id),))
        return User.from_dict(row) if row else None

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete user and associated sessions (CASCADE)."""
        query = "DELETE FROM users WHERE id = $1"
        result = await self._db.execute(query, (str(user_id),))
        return "DELETE" in result


__all__ = [
    "SESSION_EXPIRY_HOURS",
    "SESSION_MAX_AGE",
    "UserRepository",
    "create_session",
    "find_or_create_user",
    "find_session",
    "hash_token",
    "logout",
]
