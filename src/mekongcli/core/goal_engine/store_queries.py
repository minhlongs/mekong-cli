# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Task, checkpoint, verification, event, memory, and snapshot queries for SQLiteGoalStore."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import asdict
from typing import Any

from .models import (
    AcceptanceCriterion,
    AgentRole,
    Checkpoint,
    Goal,
    GoalTask,
    TaskStatus,
    VerificationRun,
)


class GoalStoreQueriesMixin:
    """Query and persistence methods for tasks, checkpoints, verifications, events, and memory."""

    lock: threading.RLock

    # Declarations only: the concrete SQLiteGoalStore owns the implementation.
    def _connect(self) -> sqlite3.Connection:
        raise NotImplementedError

    @staticmethod
    def _safe_json(raw: str, fallback: Any) -> Any:
        raise NotImplementedError

    def get_goal(self, goal_id: str) -> Goal | None:
        raise NotImplementedError

    def get_criteria(self, goal_id: str) -> list[AcceptanceCriterion]:
        raise NotImplementedError

    def save_tasks(self, tasks: list[GoalTask]) -> None:
        with self.lock, self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO tasks
                (id, goal_id, title, description, role, status, depends_on,
                 attempts, max_attempts, command, result_summary, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status, attempts=excluded.attempts,
                    command=excluded.command, result_summary=excluded.result_summary,
                    updated_at=excluded.updated_at
                """,
                [
                    (
                        t.id, t.goal_id, t.title, t.description, t.role.value, t.status.value,
                        json.dumps(t.depends_on), t.attempts, t.max_attempts,
                        t.command, t.result_summary, t.created_at, t.updated_at,
                    )
                    for t in tasks
                ],
            )

    def get_tasks(self, goal_id: str) -> list[GoalTask]:
        with self.lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE goal_id = ? ORDER BY created_at, rowid", (goal_id,)
            ).fetchall()
            return [
                GoalTask(
                    id=r["id"], goal_id=r["goal_id"], title=r["title"], description=r["description"],
                    role=AgentRole(r["role"]), status=TaskStatus(r["status"]),
                    depends_on=self._safe_json(r["depends_on"], []), attempts=r["attempts"],
                    max_attempts=r["max_attempts"], command=r["command"],
                    result_summary=r["result_summary"], created_at=r["created_at"], updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO checkpoints (id, goal_id, task_id, label, state, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    checkpoint.id, checkpoint.goal_id, checkpoint.task_id,
                    checkpoint.label, json.dumps(checkpoint.state), checkpoint.created_at,
                ),
            )

    def get_checkpoints(self, goal_id: str) -> list[Checkpoint]:
        with self.lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM checkpoints WHERE goal_id = ? ORDER BY created_at", (goal_id,)).fetchall()
            return [
                Checkpoint(
                    id=r["id"], goal_id=r["goal_id"], task_id=r["task_id"],
                    label=r["label"], state=json.loads(r["state"]), created_at=r["created_at"],
                )
                for r in rows
            ]

    def save_verification_run(self, run: VerificationRun) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO verification_runs (id, goal_id, profile, passed, results, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (run.id, run.goal_id, run.profile, int(run.passed), json.dumps(run.results), run.created_at),
            )

    def get_latest_verification(self, goal_id: str) -> VerificationRun | None:
        with self.lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM verification_runs WHERE goal_id = ? ORDER BY created_at DESC LIMIT 1", (goal_id,)
            ).fetchone()
            if row is None:
                return None
            return VerificationRun(
                id=row["id"], goal_id=row["goal_id"], profile=row["profile"],
                passed=bool(row["passed"]), results=json.loads(row["results"]), created_at=row["created_at"],
            )

    def add_event(self, goal_id: str, event_name: str, payload: dict[str, Any]) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO goal_events (goal_id, event_name, payload, created_at) VALUES (?, ?, ?, ?)",
                (goal_id, event_name, json.dumps(payload), time.time()),
            )

    def get_events(self, goal_id: str) -> list[dict[str, Any]]:
        with self.lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM goal_events WHERE goal_id = ? ORDER BY id", (goal_id,)).fetchall()
            return [
                {"event_name": r["event_name"], "payload": json.loads(r["payload"]), "created_at": r["created_at"]}
                for r in rows
            ]

    def add_memory(self, goal_id: str, kind: str, content: str) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO memory_records (goal_id, kind, content, created_at) VALUES (?, ?, ?, ?)",
                (goal_id, kind, content, time.time()),
            )

    def get_memory(self, goal_id: str) -> list[dict[str, Any]]:
        with self.lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM memory_records WHERE goal_id = ? ORDER BY id", (goal_id,)).fetchall()
            return [dict(row) for row in rows]

    def snapshot(self, goal_id: str) -> dict[str, Any]:
        with self.lock:
            goal = self.get_goal(goal_id)
            if goal is None:
                raise KeyError(goal_id)
            latest_ver = self.get_latest_verification(goal_id)
            return {
                "goal": asdict(goal) | {"status": goal.status.value},
                "criteria": [asdict(item) for item in self.get_criteria(goal_id)],
                "tasks": [
                    asdict(task) | {"role": task.role.value, "status": task.status.value}
                    for task in self.get_tasks(goal_id)
                ],
                "checkpoints": [asdict(item) for item in self.get_checkpoints(goal_id)],
                "verification": asdict(latest_ver) if latest_ver else None,
                "events": self.get_events(goal_id),
                "memory": self.get_memory(goal_id),
            }
