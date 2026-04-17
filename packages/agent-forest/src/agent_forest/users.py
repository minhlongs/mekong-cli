"""Mock user store — bcrypt-hashed passwords loaded from YAML or defaults.

Phase 3 (Land) swaps this for SQLAlchemy + Postgres.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from passlib.context import CryptContext

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def _validate_ids(user_id: str, username: str) -> None:
    if not _SAFE_ID.match(user_id):
        raise ValueError(f"invalid user_id: {user_id!r}")
    if not _SAFE_ID.match(username):
        raise ValueError(f"invalid username: {username!r}")


@dataclass(frozen=True)
class User:
    user_id: str
    username: str
    password_hash: str


def hash_password(raw: str) -> str:
    return _pwd_ctx.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd_ctx.verify(raw, hashed)


def _default_users() -> dict[str, User]:
    # Dev-only defaults; real deployments MUST override via FOREST_USERS_YAML.
    return {
        "founder1": User("usr_founder1", "founder1", hash_password("founder1-dev")),
        "founder2": User("usr_founder2", "founder2", hash_password("founder2-dev")),
    }


def load_users(yaml_path: str | None) -> dict[str, User]:
    if not yaml_path:
        return _default_users()
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"users_yaml not found: {yaml_path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    users: dict[str, User] = {}
    for entry in data.get("users", []):
        uid = entry["user_id"]
        uname = entry["username"]
        _validate_ids(uid, uname)
        raw = entry.get("password")
        hashed = entry.get("password_hash")
        if not hashed and raw:
            hashed = hash_password(raw)
        if not hashed:
            raise ValueError(f"user {uname!r} missing password/password_hash")
        users[uname] = User(uid, uname, hashed)
    return users or _default_users()


class UserStore:
    def __init__(self, users: dict[str, User]):
        self._by_username = users
        self._by_user_id = {u.user_id: u for u in users.values()}

    def get_by_username(self, username: str) -> User | None:
        return self._by_username.get(username)

    def get_by_user_id(self, user_id: str) -> User | None:
        return self._by_user_id.get(user_id)

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.get_by_username(username)
        if user and verify_password(password, user.password_hash):
            return user
        return None
