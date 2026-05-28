"""SQLite-backed durable goal store."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import (
    AcceptanceCriterion,
    AgentRole,
    Checkpoint,
    Goal,
    GoalStatus,
    GoalTask,
    TaskStatus,
    VerificationRun,
)


class SQLiteGoalStore:
    """Durable local-first store for goals, tasks, checkpoints, events, and gates."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else Path(".mekong/goals.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    retry_limit INTEGER NOT NULL,
                    stop_conditions TEXT NOT NULL,
                    metadata TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS acceptance_criteria (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    satisfied INTEGER NOT NULL,
                    evidence TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    command TEXT,
                    result_summary TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    task_id TEXT,
                    label TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS verification_runs (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    profile TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    results TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS goal_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )

    def save_goal(self, goal: Goal) -> None:
        goal.updated_at = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO goals
                    (id, title, status, created_at, updated_at, retry_limit, stop_conditions, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    status=excluded.status,
                    updated_at=excluded.updated_at,
                    retry_limit=excluded.retry_limit,
                    stop_conditions=excluded.stop_conditions,
                    metadata=excluded.metadata
                """,
                (
                    goal.id,
                    goal.title,
                    goal.status.value,
                    goal.created_at,
                    goal.updated_at,
                    goal.retry_limit,
                    json.dumps(goal.stop_conditions),
                    json.dumps(goal.metadata),
                ),
            )

    def get_goal(self, goal_id: str) -> Goal | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if row is None:
            return None
        return Goal(
            id=row["id"],
            title=row["title"],
            status=GoalStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            retry_limit=row["retry_limit"],
            stop_conditions=json.loads(row["stop_conditions"]),
            metadata=json.loads(row["metadata"]),
        )

    def list_goals(self) -> list[Goal]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM goals ORDER BY updated_at DESC").fetchall()
        goals: list[Goal] = []
        for row in rows:
            goal = self.get_goal(row["id"])
            if goal is not None:
                goals.append(goal)
        return goals

    def save_criteria(self, goal_id: str, criteria: list[AcceptanceCriterion]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM acceptance_criteria WHERE goal_id = ?", (goal_id,))
            conn.executemany(
                """
                INSERT INTO acceptance_criteria
                    (id, goal_id, description, satisfied, evidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.id,
                        goal_id,
                        item.description,
                        int(item.satisfied),
                        item.evidence,
                    )
                    for item in criteria
                ],
            )

    def get_criteria(self, goal_id: str) -> list[AcceptanceCriterion]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM acceptance_criteria WHERE goal_id = ? ORDER BY rowid",
                (goal_id,),
            ).fetchall()
        return [
            AcceptanceCriterion(
                id=row["id"],
                description=row["description"],
                satisfied=bool(row["satisfied"]),
                evidence=row["evidence"],
            )
            for row in rows
        ]

    def save_tasks(self, tasks: list[GoalTask]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO tasks
                    (id, goal_id, title, description, role, status, depends_on,
                     attempts, max_attempts, command, result_summary, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    attempts=excluded.attempts,
                    command=excluded.command,
                    result_summary=excluded.result_summary,
                    updated_at=excluded.updated_at
                """,
                [
                    (
                        task.id,
                        task.goal_id,
                        task.title,
                        task.description,
                        task.role.value,
                        task.status.value,
                        json.dumps(task.depends_on),
                        task.attempts,
                        task.max_attempts,
                        task.command,
                        task.result_summary,
                        task.created_at,
                        task.updated_at,
                    )
                    for task in tasks
                ],
            )

    def get_tasks(self, goal_id: str) -> list[GoalTask]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE goal_id = ? ORDER BY created_at, rowid",
                (goal_id,),
            ).fetchall()
        return [
            GoalTask(
                id=row["id"],
                goal_id=row["goal_id"],
                title=row["title"],
                description=row["description"],
                role=AgentRole(row["role"]),
                status=TaskStatus(row["status"]),
                depends_on=json.loads(row["depends_on"]),
                attempts=row["attempts"],
                max_attempts=row["max_attempts"],
                command=row["command"],
                result_summary=row["result_summary"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (id, goal_id, task_id, label, state, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.id,
                    checkpoint.goal_id,
                    checkpoint.task_id,
                    checkpoint.label,
                    json.dumps(checkpoint.state),
                    checkpoint.created_at,
                ),
            )

    def get_checkpoints(self, goal_id: str) -> list[Checkpoint]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM checkpoints WHERE goal_id = ? ORDER BY created_at",
                (goal_id,),
            ).fetchall()
        return [
            Checkpoint(
                id=row["id"],
                goal_id=row["goal_id"],
                task_id=row["task_id"],
                label=row["label"],
                state=json.loads(row["state"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_verification_run(self, run: VerificationRun) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO verification_runs (id, goal_id, profile, passed, results, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.goal_id,
                    run.profile,
                    int(run.passed),
                    json.dumps(run.results),
                    run.created_at,
                ),
            )

    def get_latest_verification(self, goal_id: str) -> VerificationRun | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM verification_runs
                WHERE goal_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (goal_id,),
            ).fetchone()
        if row is None:
            return None
        return VerificationRun(
            id=row["id"],
            goal_id=row["goal_id"],
            profile=row["profile"],
            passed=bool(row["passed"]),
            results=json.loads(row["results"]),
            created_at=row["created_at"],
        )

    def add_event(self, goal_id: str, event_name: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO goal_events (goal_id, event_name, payload, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (goal_id, event_name, json.dumps(payload), time.time()),
            )

    def get_events(self, goal_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM goal_events WHERE goal_id = ? ORDER BY id",
                (goal_id,),
            ).fetchall()
        return [
            {
                "event_name": row["event_name"],
                "payload": json.loads(row["payload"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def add_memory(self, goal_id: str, kind: str, content: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_records (goal_id, kind, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (goal_id, kind, content, time.time()),
            )

    def get_memory(self, goal_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_records WHERE goal_id = ? ORDER BY id",
                (goal_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def snapshot(self, goal_id: str) -> dict[str, Any]:
        goal = self.get_goal(goal_id)
        if goal is None:
            raise KeyError(goal_id)
        return {
            "goal": asdict(goal) | {"status": goal.status.value},
            "criteria": [asdict(item) for item in self.get_criteria(goal_id)],
            "tasks": [
                asdict(task) | {"role": task.role.value, "status": task.status.value}
                for task in self.get_tasks(goal_id)
            ],
            "checkpoints": [asdict(item) for item in self.get_checkpoints(goal_id)],
            "verification": (
                asdict(self.get_latest_verification(goal_id))
                if self.get_latest_verification(goal_id)
                else None
            ),
            "events": self.get_events(goal_id),
            "memory": self.get_memory(goal_id),
        }
