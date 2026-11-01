# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite-backed durable goal store."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from .models import (
    AcceptanceCriterion,
    AgentRole,
    Checkpoint,
    ExecutionTruthStatus,
    Goal,
    GoalStatus,
    GoalTask,
    ImmutableMandate,
    OutboxEntry,
    TaskStatus,
    VerificationRun,
    WorkerLease,
)

_logger = logging.getLogger(__name__)

MAX_AUTONOMOUS_WORKERS = 2
OPERATOR_CONTROL_RESERVED = 1


class MandateIntegrityError(RuntimeError):
    """Raised when a ticket mandate is mutated or tampered with after admission."""


class LeaseCapacityError(RuntimeError):
    """Raised when a worker lease request exceeds bounded lane capacity."""


class SQLiteGoalStore:
    """Durable local-first store for goals, tasks, checkpoints, events, and gates."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else Path(".mekong/goals.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._init_schema()

    @staticmethod
    def _safe_json(raw: str, fallback: Any) -> Any:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            _logger.warning("corrupted JSON in store, using fallback")
            return fallback

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
        except sqlite3.OperationalError:
            _logger.warning("WAL mode unavailable")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def _ensure_column(
        conn: sqlite3.Connection,
        table: str,
        column: str,
        col_ddl: str,
    ) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {row["name"] for row in rows}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_ddl}")

    def _init_schema(self) -> None:
        with self.lock:
            with self._connect() as conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS goals (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL,
                        truth_status TEXT NOT NULL DEFAULT 'PLANNED',
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
                        truth_status TEXT NOT NULL DEFAULT 'PLANNED',
                        depends_on TEXT NOT NULL,
                        attempts INTEGER NOT NULL,
                        max_attempts INTEGER NOT NULL,
                        command TEXT,
                        result_summary TEXT NOT NULL,
                        exit_code INTEGER,
                        stdout TEXT NOT NULL DEFAULT '',
                        stderr TEXT NOT NULL DEFAULT '',
                        blocked_reason TEXT,
                        is_idempotent INTEGER NOT NULL DEFAULT 0,
                        side_effect_uncertain INTEGER NOT NULL DEFAULT 0,
                        mutates_workspace INTEGER NOT NULL DEFAULT 0,
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
                    CREATE TABLE IF NOT EXISTS tickets (
                        ticket_id TEXT PRIMARY KEY,
                        goal_id TEXT NOT NULL,
                        source_id TEXT NOT NULL,
                        event_id TEXT NOT NULL,
                        requester TEXT NOT NULL,
                        authorized_scope TEXT NOT NULL,
                        workspace_id TEXT NOT NULL,
                        mandate_version INTEGER NOT NULL,
                        policy_version TEXT NOT NULL,
                        accepted_at TEXT NOT NULL,
                        permitted_capabilities_json TEXT NOT NULL,
                        resource_boundaries_json TEXT NOT NULL,
                        risk_classification TEXT NOT NULL,
                        cost_budget REAL NOT NULL,
                        retry_budget INTEGER NOT NULL,
                        verification_requirements TEXT NOT NULL,
                        mandate_hash TEXT NOT NULL,
                        truth_status TEXT NOT NULL DEFAULT 'PLANNED',
                        thread_id TEXT,
                        measured_tokens INTEGER,
                        estimated_tokens INTEGER,
                        actual_cost REAL,
                        estimated_cost REAL,
                        cost_status TEXT NOT NULL DEFAULT 'UNKNOWN',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        UNIQUE(source_id, event_id)
                    );
                    CREATE TRIGGER IF NOT EXISTS trg_tickets_immutable_mandate
                    BEFORE UPDATE ON tickets
                    WHEN (
                        NEW.authorized_scope != OLD.authorized_scope
                        OR NEW.permitted_capabilities_json != OLD.permitted_capabilities_json
                        OR NEW.resource_boundaries_json != OLD.resource_boundaries_json
                        OR NEW.risk_classification != OLD.risk_classification
                        OR NEW.cost_budget != OLD.cost_budget
                        OR NEW.retry_budget != OLD.retry_budget
                        OR NEW.verification_requirements != OLD.verification_requirements
                        OR NEW.mandate_hash != OLD.mandate_hash
                    ) AND NEW.mandate_version <= OLD.mandate_version
                    BEGIN
                        SELECT RAISE(ABORT, 'ImmutableMandate violation: worker cannot mutate mandate fields without version bump');
                    END;
                    CREATE TABLE IF NOT EXISTS worker_leases (
                        worker_id TEXT PRIMARY KEY,
                        lane_kind TEXT NOT NULL,
                        ticket_id TEXT NOT NULL,
                        task_id TEXT NOT NULL,
                        lease_expires_at REAL NOT NULL,
                        heartbeat_at REAL NOT NULL,
                        attempt_no INTEGER NOT NULL DEFAULT 1,
                        is_idempotent INTEGER NOT NULL DEFAULT 0,
                        side_effect_uncertain INTEGER NOT NULL DEFAULT 0,
                        worktree_path TEXT
                    );
                    CREATE TABLE IF NOT EXISTS report_outbox (
                        outbox_id TEXT PRIMARY KEY,
                        ticket_id TEXT NOT NULL,
                        source_id TEXT NOT NULL,
                        thread_id TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL UNIQUE,
                        callback_url TEXT,
                        payload_json TEXT NOT NULL,
                        delivery_status TEXT NOT NULL DEFAULT 'PENDING',
                        attempts INTEGER NOT NULL DEFAULT 0,
                        max_attempts INTEGER NOT NULL DEFAULT 3,
                        next_retry_at REAL NOT NULL DEFAULT 0.0,
                        last_error TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    );
                    """
                )
                # Idempotent column migrations for existing databases
                self._ensure_column(conn, "goals", "truth_status", "TEXT NOT NULL DEFAULT 'PLANNED'")
                self._ensure_column(conn, "tasks", "truth_status", "TEXT NOT NULL DEFAULT 'PLANNED'")
                self._ensure_column(conn, "tasks", "exit_code", "INTEGER")
                self._ensure_column(conn, "tasks", "stdout", "TEXT NOT NULL DEFAULT ''")
                self._ensure_column(conn, "tasks", "stderr", "TEXT NOT NULL DEFAULT ''")
                self._ensure_column(conn, "tasks", "blocked_reason", "TEXT")
                self._ensure_column(conn, "tasks", "is_idempotent", "INTEGER NOT NULL DEFAULT 0")
                self._ensure_column(conn, "tasks", "side_effect_uncertain", "INTEGER NOT NULL DEFAULT 0")
                self._ensure_column(conn, "tasks", "mutates_workspace", "INTEGER NOT NULL DEFAULT 0")

    def save_goal(self, goal: Goal) -> None:
        with self.lock:
            goal.updated_at = time.time()
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO goals
                    (id, title, status, truth_status, created_at, updated_at, retry_limit, stop_conditions, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title=excluded.title,
                        status=excluded.status,
                        truth_status=excluded.truth_status,
                        updated_at=excluded.updated_at,
                        retry_limit=excluded.retry_limit,
                        stop_conditions=excluded.stop_conditions,
                        metadata=excluded.metadata
                    """,
                    (
                        goal.id,
                        goal.title,
                        goal.status.value,
                        goal.truth_status.value,
                        goal.created_at,
                        goal.updated_at,
                        goal.retry_limit,
                        json.dumps(goal.stop_conditions),
                        json.dumps(goal.metadata),
                    ),
                )

    def get_goal(self, goal_id: str) -> Goal | None:
        with self.lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM goals WHERE id = ?", (goal_id,)
                ).fetchone()
                if row is None:
                    return None
                row_keys = set(row.keys())
                truth_raw = row["truth_status"] if "truth_status" in row_keys and row["truth_status"] else "PLANNED"
                return Goal(
                    id=row["id"],
                    title=row["title"],
                    status=GoalStatus(row["status"]),
                    truth_status=ExecutionTruthStatus(truth_raw),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    retry_limit=row["retry_limit"],
                    stop_conditions=self._safe_json(row["stop_conditions"], []),
                    metadata=self._safe_json(row["metadata"], {}),
                )

    def list_goals(self) -> list[Goal]:
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM goals ORDER BY updated_at DESC"
                ).fetchall()
                goals: list[Goal] = []
                for row in rows:
                    goal = self.get_goal(row["id"])
                    if goal is not None:
                        goals.append(goal)
                return goals

    def save_criteria(
        self, goal_id: str, criteria: list[AcceptanceCriterion]
    ) -> None:
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM acceptance_criteria WHERE goal_id = ?",
                    (goal_id,),
                )
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
        with self.lock:
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
        with self.lock:
            with self._connect() as conn:
                conn.executemany(
                    """
                    INSERT INTO tasks
                    (id, goal_id, title, description, role, status, truth_status, depends_on,
                     attempts, max_attempts, command, result_summary, exit_code, stdout, stderr,
                     blocked_reason, is_idempotent, side_effect_uncertain, mutates_workspace,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status=excluded.status,
                        truth_status=excluded.truth_status,
                        attempts=excluded.attempts,
                        max_attempts=excluded.max_attempts,
                        command=excluded.command,
                        result_summary=excluded.result_summary,
                        exit_code=excluded.exit_code,
                        stdout=excluded.stdout,
                        stderr=excluded.stderr,
                        blocked_reason=excluded.blocked_reason,
                        is_idempotent=excluded.is_idempotent,
                        side_effect_uncertain=excluded.side_effect_uncertain,
                        mutates_workspace=excluded.mutates_workspace,
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
                            task.truth_status.value,
                            json.dumps(task.depends_on),
                            task.attempts,
                            task.max_attempts,
                            task.command,
                            task.result_summary,
                            task.exit_code,
                            task.stdout,
                            task.stderr,
                            task.blocked_reason,
                            int(task.is_idempotent),
                            int(task.side_effect_uncertain),
                            int(task.mutates_workspace),
                            task.created_at,
                            task.updated_at,
                        )
                        for task in tasks
                    ],
                )

    def get_tasks(self, goal_id: str) -> list[GoalTask]:
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE goal_id = ? ORDER BY created_at, rowid",
                    (goal_id,),
                ).fetchall()
                result: list[GoalTask] = []
                for row in rows:
                    rkeys = set(row.keys())
                    truth_raw = row["truth_status"] if "truth_status" in rkeys and row["truth_status"] else "PLANNED"
                    result.append(
                        GoalTask(
                            id=row["id"],
                            goal_id=row["goal_id"],
                            title=row["title"],
                            description=row["description"],
                            role=AgentRole(row["role"]),
                            status=TaskStatus(row["status"]),
                            truth_status=ExecutionTruthStatus(truth_raw),
                            depends_on=self._safe_json(row["depends_on"], []),
                            attempts=row["attempts"],
                            max_attempts=row["max_attempts"],
                            command=row["command"],
                            result_summary=row["result_summary"],
                            exit_code=row["exit_code"] if "exit_code" in rkeys else None,
                            stdout=row["stdout"] if "stdout" in rkeys and row["stdout"] else "",
                            stderr=row["stderr"] if "stderr" in rkeys and row["stderr"] else "",
                            blocked_reason=row["blocked_reason"] if "blocked_reason" in rkeys else None,
                            is_idempotent=bool(row["is_idempotent"]) if "is_idempotent" in rkeys else False,
                            side_effect_uncertain=bool(row["side_effect_uncertain"]) if "side_effect_uncertain" in rkeys else False,
                            mutates_workspace=bool(row["mutates_workspace"]) if "mutates_workspace" in rkeys else False,
                            created_at=row["created_at"],
                            updated_at=row["updated_at"],
                        )
                    )
                return result

    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        with self.lock:
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
        with self.lock:
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
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO verification_runs
                    (id, goal_id, profile, passed, results, created_at)
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

    def get_latest_verification(
        self, goal_id: str
    ) -> VerificationRun | None:
        with self.lock:
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

    def add_event(
        self,
        goal_id: str,
        event_name: str,
        payload: dict[str, Any],
    ) -> None:
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO goal_events (goal_id, event_name, payload, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (goal_id, event_name, json.dumps(payload), time.time()),
                )

    def get_events(self, goal_id: str) -> list[dict[str, Any]]:
        with self.lock:
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
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO memory_records (goal_id, kind, content, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (goal_id, kind, content, time.time()),
                )

    def get_memory(self, goal_id: str) -> list[dict[str, Any]]:
        with self.lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM memory_records WHERE goal_id = ? ORDER BY id",
                    (goal_id,),
                ).fetchall()
                return [dict(row) for row in rows]

    def snapshot(self, goal_id: str) -> dict[str, Any]:
        with self.lock:
            goal = self.get_goal(goal_id)
            if goal is None:
                raise KeyError(goal_id)
            latest_verif = self.get_latest_verification(goal_id)
            return {
                "goal": asdict(goal) | {
                    "status": goal.status.value,
                    "truth_status": goal.truth_status.value,
                },
                "criteria": [
                    asdict(item) for item in self.get_criteria(goal_id)
                ],
                "tasks": [
                    asdict(task) | {
                        "role": task.role.value,
                        "status": task.status.value,
                        "truth_status": task.truth_status.value,
                    }
                    for task in self.get_tasks(goal_id)
                ],
                "checkpoints": [
                    asdict(item) for item in self.get_checkpoints(goal_id)
                ],
                "verification": (
                    asdict(latest_verif) if latest_verif is not None else None
                ),
                "events": self.get_events(goal_id),
                "memory": self.get_memory(goal_id),
            }

    # --- Durable Tickets & Immutable Mandates (G2) ---

    def admit_ticket(
        self,
        goal_id: str,
        mandate: ImmutableMandate,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Admit a durable ticket idempotently on ``(source_id, event_id)``."""
        if not mandate.verify_hash():
            raise MandateIntegrityError("Mandate HMAC verification failed on ticket admission")

        with self.lock:
            with self._connect() as conn:
                existing = conn.execute(
                    "SELECT * FROM tickets WHERE source_id = ? AND event_id = ?",
                    (mandate.source_id, mandate.event_id),
                ).fetchone()
                if existing is not None:
                    return dict(existing) | {"deduplicated": True}

                now_str = str(time.time())
                conn.execute(
                    """
                    INSERT INTO tickets (
                        ticket_id, goal_id, source_id, event_id, requester,
                        authorized_scope, workspace_id, mandate_version, policy_version,
                        accepted_at, permitted_capabilities_json, resource_boundaries_json,
                        risk_classification, cost_budget, retry_budget,
                        verification_requirements, mandate_hash, truth_status,
                        thread_id, cost_status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'UNKNOWN', ?, ?)
                    """,
                    (
                        mandate.ticket_id,
                        goal_id,
                        mandate.source_id,
                        mandate.event_id,
                        mandate.requester,
                        mandate.authorized_scope,
                        mandate.workspace_id,
                        mandate.mandate_version,
                        mandate.policy_version,
                        mandate.accepted_at,
                        json.dumps(list(mandate.permitted_capabilities)),
                        json.dumps(list(mandate.resource_boundaries)),
                        mandate.risk_classification,
                        mandate.cost_budget,
                        mandate.retry_budget,
                        mandate.verification_requirements,
                        mandate.mandate_hash,
                        ExecutionTruthStatus.PLANNED.value,
                        thread_id,
                        now_str,
                        now_str,
                    ),
                )
                row = conn.execute(
                    "SELECT * FROM tickets WHERE ticket_id = ?",
                    (mandate.ticket_id,),
                ).fetchone()
                return dict(row) | {"deduplicated": False}

    def get_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        with self.lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM tickets WHERE ticket_id = ?",
                    (ticket_id,),
                ).fetchone()
                return dict(row) if row is not None else None

    def verify_mandate_integrity(self, ticket_id: str) -> ImmutableMandate:
        """Load ticket mandate and verify its cryptographic HMAC-SHA256 digest."""
        row = self.get_ticket(ticket_id)
        if row is None:
            raise KeyError(ticket_id)
        mandate = ImmutableMandate(
            ticket_id=row["ticket_id"],
            source_id=row["source_id"],
            event_id=row["event_id"],
            requester=row["requester"],
            authorized_scope=row["authorized_scope"],
            workspace_id=row["workspace_id"],
            mandate_version=int(row["mandate_version"]),
            policy_version=row["policy_version"],
            accepted_at=row["accepted_at"],
            permitted_capabilities=tuple(self._safe_json(row["permitted_capabilities_json"], [])),
            resource_boundaries=tuple(self._safe_json(row["resource_boundaries_json"], [])),
            risk_classification=row["risk_classification"],
            cost_budget=float(row["cost_budget"]),
            retry_budget=int(row["retry_budget"]),
            verification_requirements=row["verification_requirements"],
            mandate_hash=row["mandate_hash"],
        )
        if not mandate.verify_hash():
            raise MandateIntegrityError(f"Mandate hash mismatch for ticket {ticket_id}")
        return mandate

    def attempt_worker_mandate_mutation(
        self,
        ticket_id: str,
        **illegal_updates: Any,
    ) -> None:
        """Attempt to mutate mandate fields as a worker (must be rejected by trigger & guard)."""
        forbidden_fields = {
            "authorized_scope",
            "permitted_capabilities_json",
            "permitted_capabilities",
            "resource_boundaries_json",
            "resource_boundaries",
            "risk_classification",
            "cost_budget",
            "retry_budget",
            "verification_requirements",
            "mandate_hash",
        }
        attempted = forbidden_fields.intersection(illegal_updates.keys())
        if attempted:
            with self.lock:
                with self._connect() as conn:
                    col = next(iter(attempted))
                    sql_col = (
                        f"{col}_json"
                        if col in ("permitted_capabilities", "resource_boundaries")
                        else col
                    )
                    val = illegal_updates[col]
                    if isinstance(val, (list, tuple)):
                        val = json.dumps(list(val))
                    try:
                        conn.execute(
                            f"UPDATE tickets SET {sql_col} = ? WHERE ticket_id = ?",
                            (val, ticket_id),
                        )
                    except sqlite3.DatabaseError as exc:
                        raise MandateIntegrityError(str(exc)) from exc
            raise MandateIntegrityError(
                f"Worker mutation of mandate fields {sorted(attempted)} is forbidden"
            )

    def record_ticket_cost(
        self,
        ticket_id: str,
        *,
        measured_tokens: int | None = None,
        estimated_tokens: int | None = None,
        actual_cost: float | None = None,
        estimated_cost: float | None = None,
    ) -> dict[str, Any]:
        """Record honest token/cost accounting without fabricating 0.0 for unknown cost."""
        if actual_cost is not None:
            cost_status = "MEASURED"
        elif estimated_cost is not None:
            cost_status = "ESTIMATED"
        else:
            cost_status = "UNKNOWN"

        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE tickets
                    SET measured_tokens = ?,
                        estimated_tokens = ?,
                        actual_cost = ?,
                        estimated_cost = ?,
                        cost_status = ?,
                        updated_at = ?
                    WHERE ticket_id = ?
                    """,
                    (
                        measured_tokens,
                        estimated_tokens,
                        actual_cost,
                        estimated_cost,
                        cost_status,
                        str(time.time()),
                        ticket_id,
                    ),
                )
        updated = self.get_ticket(ticket_id)
        if updated is None:
            raise KeyError(ticket_id)
        return updated

    # --- Worker Leases & Crash Reconciliation (G4 & G5) ---

    def acquire_worker_lease(
        self,
        lease: WorkerLease,
        now: float | None = None,
    ) -> bool:
        """Acquire a bounded worker lease (2 AUTONOMOUS + 1 OPERATOR_CONTROL)."""
        current = time.time() if now is None else now
        with self.lock:
            with self._connect() as conn:
                active_rows = conn.execute(
                    "SELECT * FROM worker_leases WHERE lane_kind = ? AND lease_expires_at > ?",
                    (lease.lane_kind, current),
                ).fetchall()
                cap = (
                    MAX_AUTONOMOUS_WORKERS
                    if lease.lane_kind == "AUTONOMOUS"
                    else OPERATOR_CONTROL_RESERVED
                )
                active_ids = {r["worker_id"] for r in active_rows}
                if lease.worker_id not in active_ids and len(active_rows) >= cap:
                    return False

                conn.execute(
                    """
                    INSERT INTO worker_leases (
                        worker_id, lane_kind, ticket_id, task_id,
                        lease_expires_at, heartbeat_at, attempt_no,
                        is_idempotent, side_effect_uncertain, worktree_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(worker_id) DO UPDATE SET
                        lane_kind=excluded.lane_kind,
                        ticket_id=excluded.ticket_id,
                        task_id=excluded.task_id,
                        lease_expires_at=excluded.lease_expires_at,
                        heartbeat_at=excluded.heartbeat_at,
                        attempt_no=excluded.attempt_no,
                        is_idempotent=excluded.is_idempotent,
                        side_effect_uncertain=excluded.side_effect_uncertain,
                        worktree_path=excluded.worktree_path
                    """,
                    (
                        lease.worker_id,
                        lease.lane_kind,
                        lease.ticket_id,
                        lease.task_id,
                        lease.lease_expires_at,
                        lease.heartbeat_at,
                        lease.attempt_no,
                        int(lease.is_idempotent),
                        int(lease.side_effect_uncertain),
                        lease.worktree_path,
                    ),
                )
                return True

    def release_worker_lease(self, worker_id: str) -> None:
        with self.lock:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM worker_leases WHERE worker_id = ?",
                    (worker_id,),
                )

    def list_active_leases(
        self,
        lane_kind: str | None = None,
        now: float | None = None,
    ) -> list[dict[str, Any]]:
        current = time.time() if now is None else now
        with self.lock:
            with self._connect() as conn:
                if lane_kind:
                    rows = conn.execute(
                        "SELECT * FROM worker_leases WHERE lane_kind = ? AND lease_expires_at > ?",
                        (lane_kind, current),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM worker_leases WHERE lease_expires_at > ?",
                        (current,),
                    ).fetchall()
                return [dict(r) for r in rows]

    def reconcile_orphaned_running_tasks(
        self,
        goal_id: str,
        now: float | None = None,
    ) -> list[GoalTask]:
        """Reconcile orphaned RUNNING tasks whose worker lease has expired or is missing."""
        current = time.time() if now is None else now
        with self.lock:
            tasks = self.get_tasks(goal_id)
            goal = self.get_goal(goal_id)
            retry_limit = goal.retry_limit if goal else 3

            with self._connect() as conn:
                lease_rows = conn.execute(
                    "SELECT * FROM worker_leases ORDER BY lease_expires_at ASC"
                ).fetchall()
                leases_by_task = {r["task_id"]: dict(r) for r in lease_rows}
                tkt_row = conn.execute(
                    "SELECT MIN(retry_budget) AS min_rb FROM tickets WHERE goal_id = ?",
                    (goal_id,),
                ).fetchone()
                ticket_rb = (
                    int(tkt_row["min_rb"])
                    if tkt_row and tkt_row["min_rb"] is not None
                    else retry_limit
                )

            reconciled: list[GoalTask] = []
            for task in tasks:
                if task.status != TaskStatus.RUNNING:
                    continue
                lease = leases_by_task.get(task.id)
                if lease is not None and float(lease["lease_expires_at"]) > current:
                    continue

                is_idemp = task.is_idempotent or (
                    bool(lease["is_idempotent"]) if lease is not None else False
                )
                uncertain = task.side_effect_uncertain or (
                    bool(lease["side_effect_uncertain"]) if lease is not None else False
                )
                budget = min(task.max_attempts, retry_limit, ticket_rb)

                if is_idemp and not uncertain and task.attempts < budget:
                    task.status = TaskStatus.PENDING
                    task.truth_status = ExecutionTruthStatus.RETRY_WAIT
                    task.blocked_reason = None
                    task.result_summary = "Recovered orphaned idempotent task for retry"
                else:
                    task.status = TaskStatus.BLOCKED
                    task.truth_status = ExecutionTruthStatus.WAITING_APPROVAL
                    reason = (
                        "orphaned_uncertain_side_effect"
                        if uncertain or not is_idemp
                        else "orphaned_retry_budget_exhausted"
                    )
                    task.blocked_reason = reason
                    task.result_summary = f"Blocked after orphaned RUNNING state: {reason}"

                task.updated_at = current
                reconciled.append(task)
                if lease is not None:
                    self.release_worker_lease(lease["worker_id"])

            if reconciled:
                self.save_tasks(reconciled)
            return reconciled

    # --- Transactional Report Outbox (G4) ---

    def enqueue_outbox(
        self,
        entry: OutboxEntry,
        callback_url: str | None = None,
    ) -> dict[str, Any]:
        """Persist outbound report transactionally and deduplicate by ``idempotency_key``."""
        with self.lock:
            with self._connect() as conn:
                existing = conn.execute(
                    "SELECT * FROM report_outbox WHERE idempotency_key = ?",
                    (entry.idempotency_key,),
                ).fetchone()
                if existing is not None:
                    return dict(existing) | {"deduplicated": True}

                conn.execute(
                    """
                    INSERT INTO report_outbox (
                        outbox_id, ticket_id, source_id, thread_id,
                        idempotency_key, callback_url, payload_json,
                        delivery_status, attempts, max_attempts,
                        next_retry_at, last_error, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.outbox_id,
                        entry.ticket_id,
                        entry.source_id,
                        entry.thread_id,
                        entry.idempotency_key,
                        callback_url,
                        entry.payload_json,
                        entry.delivery_status,
                        entry.attempts,
                        entry.max_attempts,
                        entry.next_retry_at,
                        entry.last_error,
                        entry.created_at,
                        entry.updated_at,
                    ),
                )
                row = conn.execute(
                    "SELECT * FROM report_outbox WHERE outbox_id = ?",
                    (entry.outbox_id,),
                ).fetchone()
                return dict(row) | {"deduplicated": False}

    def process_outbox_delivery(
        self,
        outbox_id: str,
        transport: Any,
        now: float | None = None,
    ) -> dict[str, Any]:
        """Attempt delivery of an outbox entry and transition state to SENT, FAILED_RETRYABLE, or DEAD_LETTER."""
        current = time.time() if now is None else now
        with self.lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM report_outbox WHERE outbox_id = ?",
                    (outbox_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(outbox_id)
                if row["delivery_status"] == "SENT":
                    return dict(row)

                attempts = int(row["attempts"]) + 1
                max_attempts = int(row["max_attempts"])
                callback_url = row["callback_url"]
                payload = self._safe_json(row["payload_json"], {})

                code = 0
                last_error: str | None = None
                if not callback_url:
                    status = "SENT"
                else:
                    try:
                        code = int(transport(callback_url, payload))
                        if 200 <= code < 300:
                            status = "SENT"
                        else:
                            last_error = f"HTTP {code}"
                            status = "DEAD_LETTER" if attempts >= max_attempts else "FAILED_RETRYABLE"
                    except Exception as exc:
                        last_error = str(exc)
                        status = "DEAD_LETTER" if attempts >= max_attempts else "FAILED_RETRYABLE"

                next_retry = current + (2 ** attempts) if status == "FAILED_RETRYABLE" else 0.0
                conn.execute(
                    """
                    UPDATE report_outbox
                    SET delivery_status = ?,
                        attempts = ?,
                        next_retry_at = ?,
                        last_error = ?,
                        updated_at = ?
                    WHERE outbox_id = ?
                    """,
                    (status, attempts, next_retry, last_error, current, outbox_id),
                )
                updated = conn.execute(
                    "SELECT * FROM report_outbox WHERE outbox_id = ?",
                    (outbox_id,),
                ).fetchone()
                return dict(updated)

