# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage Tracker SQLite Storage and Schema Mixin."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from src.usage.usage_models import (
    MAX_FUTURE_DRIFT,
    SQLITE_RETRY_BASE_DELAY,
    SQLITE_RETRY_MAX,
    WAL_CHECKPOINT_INTERVAL,
)


class UsageSqliteMixin:
    """Mixin for SQLite schema versioning, WAL checkpoints, and event insertion."""

    SCHEMA_VERSION: int = 1
    _conn: sqlite3.Connection
    _lock: threading.Lock
    _op_counter: int

    def _init_schema_version_table(self) -> None:
        """Create schema version tracking table if it does not exist."""
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS _schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )
        self._conn.commit()

    def _get_current_version(self) -> int:
        """Return the current schema version stored in the database."""
        row = self._conn.execute("SELECT MAX(version) as v FROM _schema_version").fetchone()
        return row["v"] if row and row["v"] is not None else 0

    def _run_migrations(self) -> None:
        """Apply pending schema migrations based on current version."""
        if self._get_current_version() < self.SCHEMA_VERSION:
            self._migrate_to_v1()
            self._conn.execute("INSERT INTO _schema_version (version) VALUES (?)", (self.SCHEMA_VERSION,))
            self._conn.commit()

    def _migrate_to_v1(self) -> None:
        """Initial schema — creates usage_events table and indexes."""
        self._init_tables()

    def _init_tables(self) -> None:
        """Create usage_events table and indexes (idempotent)."""
        self._conn.executescript(
            """CREATE TABLE IF NOT EXISTS usage_events (
                id TEXT PRIMARY KEY,
                license_key_hash TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_name TEXT NOT NULL,
                units INTEGER NOT NULL DEFAULT 1,
                metadata TEXT,
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_usage_license_date
                ON usage_events(license_key_hash, substr(timestamp, 1, 10));
            CREATE INDEX IF NOT EXISTS idx_usage_type
                ON usage_events(event_type);"""
        )
        self._conn.commit()

    def _wal_checkpoint(self) -> None:
        """Run a WAL truncate checkpoint to bound WAL file size."""
        try:
            self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.OperationalError:
            pass

    def _maybe_checkpoint(self) -> None:
        """Run WAL checkpoint after every N operations."""
        with self._lock:
            self._op_counter += 1
            if self._op_counter >= WAL_CHECKPOINT_INTERVAL:
                self._op_counter = 0
                self._wal_checkpoint()

    def _execute_with_retry(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL with exponential backoff retry on database lock."""
        last_error: Optional[sqlite3.OperationalError] = None
        for attempt in range(SQLITE_RETRY_MAX):
            try:
                return self._conn.execute(sql, params)
            except sqlite3.OperationalError as e:
                if "locked" not in str(e).lower():
                    raise
                last_error = e
                time.sleep(SQLITE_RETRY_BASE_DELAY * (2 ** attempt))
        raise last_error  # type: ignore[misc]

    def _validate_timestamp(self, timestamp: str) -> None:
        """Reject timestamps more than MAX_FUTURE_DRIFT in the future."""
        try:
            event_time = datetime.fromisoformat(timestamp)
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            if event_time > datetime.now(timezone.utc) + MAX_FUTURE_DRIFT:
                raise ValueError(
                    f"Event timestamp {timestamp} is too far in the future "
                    f"(max drift: {MAX_FUTURE_DRIFT.total_seconds()}s)"
                )
        except ValueError:
            raise
        except Exception:
            raise ValueError(f"Invalid timestamp format: {timestamp}")

    def _hash_license_key(self, license_key: str) -> str:
        """Hash license key for privacy."""
        return hashlib.sha256(license_key.encode()).hexdigest()

    async def track_command(
        self, license_key: Optional[str] = None, command: Optional[str] = None,
        key_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a CLI command execution."""
        resolved_license = key_id or license_key or (os.environ.get("RAAS_LICENSE_KEY") or "")
        self._track_event(resolved_license, "command", command or "", metadata=metadata)

    def track_agent_call(
        self, license_key: str, agent_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track an agent invocation."""
        self._track_event(license_key, "agent_call", agent_name, metadata=metadata)

    def track_pipeline_run(
        self, license_key: str, pipeline_type: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track a pipeline execution."""
        self._track_event(license_key, "pipeline_run", pipeline_type, metadata=metadata)

    async def track_feature(
        self, feature_tag: str, license_key: Optional[str] = None,
        key_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a feature usage event."""
        resolved_license = license_key or key_id or (os.environ.get("RAAS_LICENSE_KEY") or "")
        self._track_event(resolved_license, "feature", feature_tag, metadata=metadata)

    def _track_event(
        self, license_key: str, event_type: str, event_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert a usage event with dedup, future-timestamp check, retry, and WAL."""
        event_id = uuid.uuid4().hex
        timestamp = datetime.now(timezone.utc).isoformat()
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        key_hash = self._hash_license_key(license_key)
        existing = self._execute_with_retry(
            "SELECT id FROM usage_events WHERE license_key_hash = ? AND event_type = ? AND event_name = ? AND timestamp > ? LIMIT 1",
            (key_hash, event_type, event_name, cutoff),
        ).fetchone()
        if existing:
            return
        self._validate_timestamp(timestamp)
        self._execute_with_retry(
            "INSERT INTO usage_events (id, license_key_hash, event_type, event_name, units, metadata, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (event_id, key_hash, event_type, event_name, 1, json.dumps(metadata or {}) if metadata else "{}", timestamp),
        )
        self._conn.commit()
        self._maybe_checkpoint()
