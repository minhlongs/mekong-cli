"""SQLite-backed UserStore — Giai đoạn 3.1.A of Solo-Platform PDF.

Opens the path to Postgres: swap the connection string when SQLAlchemy lands.
For now stdlib sqlite3 keeps zero-new-deps and mirrors the pattern used by
``agent_core.memory.SeedMemory`` (SQLite + WAL, 0600 chmod, file-based).

Public surface is compatible with the in-memory ``UserStore`` from ``users.py``
(``get_by_username`` / ``get_by_user_id`` / ``authenticate``) PLUS a
``register_user(username, password, user_id=None)`` method for runtime signup.
Gateway route wiring lands in 3.1.B.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from agent_forest.users import User, _validate_ids, hash_password, verify_password

log = logging.getLogger(__name__)

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
"""


class SqliteUserStore:
    """SQLite-backed user store with passlib bcrypt hashing."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA_SQL)
            conn.commit()
        self._chmod_0600(self.db_path)

    @staticmethod
    def _chmod_0600(p: Path) -> None:
        try:
            os.chmod(str(p), stat.S_IRUSR | stat.S_IWUSR)
        except OSError as exc:
            log.debug("chmod 0600 failed on %s: %s", p, exc)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        try:
            yield conn
        finally:
            conn.close()

    def register_user(
        self, username: str, password: str, user_id: str | None = None
    ) -> User:
        """Create a new user; raises ValueError on duplicate or invalid id."""
        uid = user_id or f"usr_{uuid.uuid4().hex[:12]}"
        _validate_ids(uid, username)
        hashed = hash_password(password)
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO users (user_id, username, password_hash) VALUES (?, ?, ?)",
                    (uid, username, hashed),
                )
                conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"username or user_id already exists: {exc}") from exc
        return User(uid, username, hashed)

    def get_by_username(self, username: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        return User(*row) if row else None

    def get_by_user_id(self, user_id: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id, username, password_hash FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return User(*row) if row else None

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.get_by_username(username)
        if user and verify_password(password, user.password_hash):
            return user
        return None

    def count(self) -> int:
        """Return total user count — useful for dashboards / status CLIs."""
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return int(row[0]) if row else 0
