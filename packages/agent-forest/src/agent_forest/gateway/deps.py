"""FastAPI DI helpers: settings, redis, user store, current user."""

from __future__ import annotations

from functools import lru_cache

import redis
from fastapi import Depends, Header, HTTPException, status

from agent_forest.auth import AuthError, decode_access_token
from agent_forest.config import ForestSettings
from agent_forest.users import User, UserStore, load_users
from agent_forest.users_db import SqliteUserStore


@lru_cache(maxsize=1)
def get_settings() -> ForestSettings:
    return ForestSettings.from_env()


@lru_cache(maxsize=1)
def get_user_store() -> UserStore | SqliteUserStore:
    """Pick SqliteUserStore when FOREST_DB_PATH is set, else YAML-backed UserStore."""
    settings = get_settings()
    if settings.db_path is not None:
        return SqliteUserStore(settings.db_path)
    return UserStore(load_users(settings.users_yaml))


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def reset_caches() -> None:
    """Clear DI caches — test helper."""
    get_settings.cache_clear()
    get_user_store.cache_clear()
    get_redis_client.cache_clear()


def current_user(
    authorization: str | None = Header(default=None),
    settings: ForestSettings = Depends(get_settings),
    store: UserStore | SqliteUserStore = Depends(get_user_store),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(None, 1)[1].strip()
    try:
        user_id = decode_access_token(token, settings)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = store.get_by_user_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
