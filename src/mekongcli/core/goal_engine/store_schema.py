# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite schema DDL and core goal/criteria CRUD mixin for SQLiteGoalStore."""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from .models import AcceptanceCriterion, Goal, GoalStatus

_logger = logging.getLogger(__name__)

GOAL_STORE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL,
    created_at REAL NOT NULL, updated_at REAL NOT NULL, retry_limit INTEGER NOT NULL,
    stop_conditions TEXT NOT NULL, metadata TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS acceptance_criteria (
    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL, description TEXT NOT NULL,
    satisfied INTEGER NOT NULL, evidence TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL, title TEXT NOT NULL,
    description TEXT NOT NULL, role TEXT NOT NULL, status TEXT NOT NULL,
    depends_on TEXT NOT NULL, attempts INTEGER NOT NULL, max_attempts INTEGER NOT NULL,
    command TEXT, result_summary TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL, task_id TEXT,
    label TEXT NOT NULL, state TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS verification_runs (
    id TEXT PRIMARY KEY, goal_id TEXT NOT NULL, profile TEXT NOT NULL,
    passed INTEGER NOT NULL, results TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS goal_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id TEXT NOT NULL,
    event_name TEXT NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS memory_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id TEXT NOT NULL,
    kind TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL
);
"""


class GoalStoreSchemaMixin:
    """Schema setup, connection management, and goal/criteria persistence."""

    db_path: Path
    lock: threading.RLock

    @staticmethod
    def _safe_json(raw: str, fallback: Any) -> Any:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            _logger.warning("corrupted JSON in store, using fallback")
            return fallback

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except sqlite3.OperationalError:
            _logger.warning("WAL mode unavailable")
        return conn

    def _init_schema(self) -> None:
        with self.lock, self._connect() as conn:
            conn.executescript(GOAL_STORE_SCHEMA_SQL)

    def save_goal(self, goal: Goal) -> None:
        with self.lock, self._connect() as conn:
            goal.updated_at = time.time()
            conn.execute(
                """
                INSERT INTO goals
                (id, title, status, created_at, updated_at, retry_limit, stop_conditions, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title, status=excluded.status, updated_at=excluded.updated_at,
                    retry_limit=excluded.retry_limit, stop_conditions=excluded.stop_conditions,
                    metadata=excluded.metadata
                """,
                (
                    goal.id, goal.title, goal.status.value, goal.created_at,
                    goal.updated_at, goal.retry_limit,
                    json.dumps(goal.stop_conditions), json.dumps(goal.metadata),
                ),
            )

    def get_goal(self, goal_id: str) -> Goal | None:
        with self.lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
            if row is None:
                return None
            return Goal(
                id=row["id"], title=row["title"], status=GoalStatus(row["status"]),
                created_at=row["created_at"], updated_at=row["updated_at"],
                retry_limit=row["retry_limit"],
                stop_conditions=self._safe_json(row["stop_conditions"], []),
                metadata=self._safe_json(row["metadata"], {}),
            )

    def list_goals(self) -> list[Goal]:
        with self.lock, self._connect() as conn:
            rows = conn.execute("SELECT id FROM goals ORDER BY updated_at DESC").fetchall()
            return [g for row in rows if (g := self.get_goal(row["id"])) is not None]

    def save_criteria(self, goal_id: str, criteria: list[AcceptanceCriterion]) -> None:
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM acceptance_criteria WHERE goal_id = ?", (goal_id,))
            conn.executemany(
                "INSERT INTO acceptance_criteria (id, goal_id, description, satisfied, evidence) VALUES (?, ?, ?, ?, ?)",
                [(item.id, goal_id, item.description, int(item.satisfied), item.evidence) for item in criteria],
            )

    def get_criteria(self, goal_id: str) -> list[AcceptanceCriterion]:
        with self.lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM acceptance_criteria WHERE goal_id = ? ORDER BY rowid", (goal_id,)).fetchall()
            return [
                AcceptanceCriterion(
                    id=r["id"], description=r["description"], satisfied=bool(r["satisfied"]), evidence=r["evidence"]
                )
                for r in rows
            ]
