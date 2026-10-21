# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Storage backend abstraction for VN Pilot JSONL → SQLite migration.

Backend selection is driven by MEKONG_PILOT_STORAGE env var:
  - "jsonl"  (default): JsonlBackend — delegates to existing _append_jsonl helpers
  - "sqlite": SqliteBackend — stdlib sqlite3, WAL mode, threading.Lock

_backend() factory reads the env at call time (not module load time) so that
monkeypatch.setenv("MEKONG_PILOT_STORAGE", ...) in tests wins correctly.

The backend is cached per-process in _BACKEND_CACHE. Tests invalidate via
_reset_backend_cache() to force re-init after monkeypatching.
"""
from __future__ import annotations

import os
import threading
from typing import Protocol, runtime_checkable

from src.services.sqlite_migrations import _db_path
from src.services.storage_backend_sqlite import SqliteBackend


@runtime_checkable
class StorageBackend(Protocol):
    def append_pilot(self, record: dict) -> None: ...
    def append_conversion(self, record: dict) -> None: ...
    def append_response(self, record: dict) -> None: ...
    def append_subscription(self, record: dict) -> None: ...
    def load_pilots(self) -> list[dict]: ...
    def load_conversions(self) -> list[dict]: ...
    def load_responses(self) -> list[dict]: ...
    def get_credit_balance(self, user_id: str) -> int: ...
    def add_credits(self, user_id: str, delta: int) -> int: ...


class JsonlBackend:
    """Wraps existing _append_jsonl/_load_jsonl/_credit_balance/_add_credits.

    Imported lazily inside methods to avoid circular-import at module load time
    (vn_pilot_common imports storage_backend which would import vn_pilot_common).
    """

    def _common(self):  # type: ignore[return]
        import src.api.vn_pilot_common as _c

        return _c

    def append_pilot(self, record: dict) -> None:
        c = self._common()
        c._append_jsonl(c._pilots_path(), record)

    def append_conversion(self, record: dict) -> None:
        c = self._common()
        c._append_jsonl(c._conversions_path(), record)

    def append_response(self, record: dict) -> None:
        c = self._common()
        c._append_jsonl(c._responses_path(), record)

    def load_pilots(self) -> list[dict]:
        c = self._common()
        return c._load_jsonl(c._pilots_path())

    def load_conversions(self) -> list[dict]:
        c = self._common()
        return c._load_jsonl(c._conversions_path())

    def load_responses(self) -> list[dict]:
        c = self._common()
        return c._load_jsonl(c._responses_path())

    def append_subscription(self, record: dict) -> None:
        c = self._common()
        c._append_jsonl(c._subscriptions_path(), record)

    def get_credit_balance(self, user_id: str) -> int:
        c = self._common()
        return c._jsonl_credit_balance(user_id)

    def add_credits(self, user_id: str, delta: int) -> int:
        c = self._common()
        return c._jsonl_add_credits(user_id, delta)


_BACKEND_CACHE: dict[str, StorageBackend] = {}
_CACHE_LOCK = threading.Lock()


def _reset_backend_cache() -> None:
    """Invalidate backend cache. Call from tests after monkeypatching env."""
    with _CACHE_LOCK:
        _BACKEND_CACHE.clear()


def _backend() -> StorageBackend:
    """Return active backend, cached per process.

    Reads MEKONG_PILOT_STORAGE at call time so monkeypatch wins.
    Key includes CONFIG_DIR path so tests with different tmp_paths get
    separate SqliteBackend instances.
    """
    mode = os.getenv("MEKONG_PILOT_STORAGE", "jsonl").lower()
    cache_key = mode if mode == "jsonl" else f"{mode}:{_db_path()}"

    with _CACHE_LOCK:
        if cache_key not in _BACKEND_CACHE:
            if mode == "sqlite":
                _BACKEND_CACHE[cache_key] = SqliteBackend()
            else:
                _BACKEND_CACHE[cache_key] = JsonlBackend()
        return _BACKEND_CACHE[cache_key]


__all__ = [
    "StorageBackend",
    "JsonlBackend",
    "SqliteBackend",
    "_BACKEND_CACHE",
    "_CACHE_LOCK",
    "_reset_backend_cache",
    "_backend",
    "_db_path",
]
