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

import json
import os
import sqlite3
import stat
import threading
from pathlib import Path
from typing import Protocol, runtime_checkable

import src.api.vn_pilot_state as _state
from src.services.sqlite_migrations import _db_path, ensure_schema

# ---------- Protocol (narrow — only what vn_pilot_common.py uses) ----------


@runtime_checkable
class StorageBackend(Protocol):
    def append_pilot(self, record: dict) -> None: ...
    def append_conversion(self, record: dict) -> None: ...
    def append_response(self, record: dict) -> None: ...
    def load_pilots(self) -> list[dict]: ...
    def load_conversions(self) -> list[dict]: ...
    def load_responses(self) -> list[dict]: ...
    def get_credit_balance(self, user_id: str) -> int: ...
    def add_credits(self, user_id: str, delta: int) -> int: ...


# ---------- JSONL Backend (delegates to existing helpers — DRY) ----------


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

    def get_credit_balance(self, user_id: str) -> int:
        c = self._common()
        return c._jsonl_credit_balance(user_id)

    def add_credits(self, user_id: str, delta: int) -> int:
        c = self._common()
        return c._jsonl_add_credits(user_id, delta)


# ---------- SQLite Backend ----------


class SqliteBackend:
    """sqlite3-based backend with WAL mode + threading.Lock.

    Raises RuntimeError at __init__ if pilot.db does not exist — fail-fast
    prevents accidental empty-DB writes in a misconfigured deployment.
    Run scripts/migrate-jsonl-to-sqlite.py first to create the DB.

    Single connection per process, shared via threading.Lock (safe because
    sqlite3 with check_same_thread=False serializes through the lock).
    """

    def __init__(self) -> None:
        db = _db_path()
        if not db.exists():
            raise RuntimeError(
                f"SQLite DB missing at {db}; run scripts/migrate-jsonl-to-sqlite.py first"
            )
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            # Apply WAL + NORMAL even if DB was created externally
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.commit()

    # -- pilots --

    def append_pilot(self, record: dict) -> None:
        raw = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO pilots
                  (user_id, org_id, name, zalo, business_type, city,
                   industry, source, onboarded_at, pilot_end_at, status, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("user_id", ""),
                    record.get("org_id", "default"),
                    record.get("name", ""),
                    record.get("zalo", ""),
                    record.get("business_type"),
                    record.get("city"),
                    record.get("industry"),
                    record.get("source"),
                    record.get("onboarded_at", ""),
                    record.get("pilot_end_at", ""),
                    record.get("status", "active"),
                    raw,
                ),
            )
            self._conn.commit()

    def load_pilots(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT raw_payload FROM pilots"
            ).fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]

    # -- conversions --

    def append_conversion(self, record: dict) -> None:
        raw = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO conversions
                  (user_id, org_id, tier, monthly_vnd, started_at,
                   recorded_at, bank_tx_ref, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("user_id", ""),
                    record.get("org_id", "default"),
                    record.get("tier", ""),
                    record.get("monthly_vnd", 0),
                    record.get("started_at", ""),
                    record.get("recorded_at", ""),
                    record.get("bank_tx_ref"),
                    raw,
                ),
            )
            self._conn.commit()

    def load_conversions(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT raw_payload FROM conversions"
            ).fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]

    # -- poll_responses --

    def append_response(self, record: dict) -> None:
        raw = json.dumps(record, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO poll_responses
                  (user_id, score, comment, iso_week, recorded_at, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("user_id", ""),
                    record.get("score", 0),
                    record.get("comment"),
                    record.get("iso_week", ""),
                    record.get("recorded_at", ""),
                    raw,
                ),
            )
            self._conn.commit()

    def load_responses(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT raw_payload FROM poll_responses"
            ).fetchall()
        return [json.loads(r["raw_payload"]) for r in rows]

    # -- credits --

    def get_credit_balance(self, user_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT balance FROM pilot_credits WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return int(row["balance"]) if row else 0

    def add_credits(self, user_id: str, delta: int) -> int:
        with self._lock:
            # Upsert: insert (floored at 0) or update existing balance + delta (floored at 0)
            # "excluded.balance" in the UPDATE branch refers to the inserted value (delta),
            # but we want MAX(0, current + delta). Use a subquery-free approach:
            # First ensure row exists, then do atomic update.
            self._conn.execute(
                "INSERT OR IGNORE INTO pilot_credits (user_id, balance) VALUES (?, 0)",
                (user_id,),
            )
            self._conn.execute(
                "UPDATE pilot_credits SET balance = MAX(0, balance + ?) WHERE user_id = ?",
                (delta, user_id),
            )
            self._conn.commit()
            row = self._conn.execute(
                "SELECT balance FROM pilot_credits WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return int(row["balance"]) if row else 0


# ---------- Factory + cache ----------

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
    # For sqlite, include db path in cache key so tests get fresh instances
    cache_key = mode if mode == "jsonl" else f"{mode}:{_db_path()}"

    with _CACHE_LOCK:
        if cache_key not in _BACKEND_CACHE:
            if mode == "sqlite":
                _BACKEND_CACHE[cache_key] = SqliteBackend()
            else:
                _BACKEND_CACHE[cache_key] = JsonlBackend()
        return _BACKEND_CACHE[cache_key]
