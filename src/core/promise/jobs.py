# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Durable job/run store for the promise execution spine.

Guarantees required by the founder directive and tested in
``tests/test_promise_run_lifecycle.py``:

* Every submission is a persisted row **before** any handler runs, so a
  refresh or process restart reads back the true state.
* ``workspace_id`` is part of every primary lookup — cross-workspace reads
  return ``None`` instead of leaking another tenant's run.
* ``(workspace_id, idempotency_key)`` is unique, so a duplicate submission
  returns the original job rather than executing twice.
* Jobs interrupted by a crash while an *uncertain* external effect was in
  flight are recovered as ``NEEDS_RECONCILIATION`` — never as ``COMPLETED``
  and never silently dropped.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import sqlite3
import typing
import uuid

# Canonical lifecycle states.
STATUS_QUEUED = "QUEUED"
STATUS_RUNNING = "RUNNING"
STATUS_AWAITING_APPROVAL = "AWAITING_APPROVAL"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"
STATUS_CANCELLED = "CANCELLED"
STATUS_NEEDS_RECONCILIATION = "NEEDS_RECONCILIATION"
STATUS_NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
STATUS_REJECTED = "REJECTED"

TERMINAL_STATUSES: frozenset[str] = frozenset({
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_CANCELLED,
    STATUS_NOT_IMPLEMENTED,
    STATUS_REJECTED,
})

ACTIVE_STATUSES: frozenset[str] = frozenset({
    STATUS_QUEUED,
    STATUS_RUNNING,
    STATUS_AWAITING_APPROVAL,
    STATUS_NEEDS_RECONCILIATION,
})

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    STATUS_QUEUED: frozenset({STATUS_RUNNING, STATUS_AWAITING_APPROVAL, STATUS_CANCELLED,
                              STATUS_FAILED, STATUS_NOT_IMPLEMENTED, STATUS_REJECTED}),
    # AWAITING_APPROVAL -> QUEUED is the resume-after-approval path: an approver
    # grants the token and the run goes back into the execution queue.
    STATUS_AWAITING_APPROVAL: frozenset({STATUS_QUEUED, STATUS_RUNNING, STATUS_CANCELLED,
                                         STATUS_FAILED, STATUS_REJECTED}),
    STATUS_RUNNING: frozenset({STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED,
                               STATUS_NEEDS_RECONCILIATION}),
    STATUS_NEEDS_RECONCILIATION: frozenset({STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED}),
    STATUS_COMPLETED: frozenset(),
    STATUS_FAILED: frozenset(),
    STATUS_CANCELLED: frozenset(),
    STATUS_NOT_IMPLEMENTED: frozenset(),
    STATUS_REJECTED: frozenset(),
}


class JobStoreError(RuntimeError):
    """Raised on illegal lifecycle operations."""


def _utcnow() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def new_run_id(prefix: str = "RUN") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"


class JobStore:
    """SQLite (WAL) store for promise jobs and their audit event log."""

    def __init__(self, db_path: str | pathlib.Path) -> None:
        self.db_path = pathlib.Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS promise_jobs (
                    run_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    command_id TEXT NOT NULL,
                    op_id TEXT,
                    subcommand TEXT,
                    params_json TEXT NOT NULL,
                    params_digest TEXT NOT NULL,
                    idempotency_key TEXT,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    external_effect TEXT NOT NULL DEFAULT 'NONE',
                    approval_token_id TEXT,
                    receipt_id TEXT,
                    result_json TEXT,
                    verification_json TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    code_version TEXT,
                    duration_ms INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS ux_promise_jobs_idem
                    ON promise_jobs(workspace_id, idempotency_key);
                CREATE INDEX IF NOT EXISTS ix_promise_jobs_ws
                    ON promise_jobs(workspace_id, created_at DESC);
                CREATE TABLE IF NOT EXISTS promise_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    from_status TEXT,
                    to_status TEXT,
                    detail_json TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_promise_events_run
                    ON promise_events(run_id, seq);
                """
            )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------
    def create_job(
        self,
        *,
        workspace_id: str,
        principal_id: str,
        command_id: str,
        params: dict[str, typing.Any],
        params_digest: str,
        op_id: str | None = None,
        subcommand: str | None = None,
        idempotency_key: str | None = None,
        status: str = STATUS_QUEUED,
        external_effect: str = "NONE",
        code_version: str = "",
        run_id: str | None = None,
    ) -> dict[str, typing.Any]:
        active_run_id = run_id or new_run_id()
        now = _utcnow()
        with self._connect() as conn:
            if idempotency_key:
                existing = conn.execute(
                    "SELECT run_id FROM promise_jobs WHERE workspace_id = ? AND idempotency_key = ?",
                    (workspace_id, idempotency_key),
                ).fetchone()
                if existing:
                    raise DuplicateSubmissionError(existing["run_id"])
            try:
                conn.execute(
                    """
                    INSERT INTO promise_jobs (
                        run_id, workspace_id, principal_id, command_id, op_id, subcommand,
                        params_json, params_digest, idempotency_key, status, attempts,
                        external_effect, code_version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    """,
                    (
                        active_run_id, workspace_id, principal_id, command_id, op_id, subcommand,
                        json.dumps(params, sort_keys=True, ensure_ascii=False, default=str),
                        params_digest, idempotency_key, status, external_effect, code_version,
                        now, now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise DuplicateSubmissionError(None) from exc
        self.append_event(active_run_id, workspace_id, "JOB_CREATED", None, status,
                          {"command_id": command_id, "op_id": op_id})
        return self.get_job(active_run_id, workspace_id) or {}

    def transition(
        self,
        run_id: str,
        workspace_id: str,
        to_status: str,
        *,
        event_type: str = "STATUS_CHANGED",
        detail: dict[str, typing.Any] | None = None,
        **fields: typing.Any,
    ) -> dict[str, typing.Any]:
        job = self.get_job(run_id, workspace_id)
        if not job:
            raise JobStoreError(f"run '{run_id}' not found in workspace '{workspace_id}'")
        from_status = job["status"]
        if to_status not in ALLOWED_TRANSITIONS.get(from_status, frozenset()):
            raise JobStoreError(f"illegal transition {from_status} -> {to_status} for run {run_id}")
        sets = ["status = ?", "updated_at = ?"]
        values: list[typing.Any] = [to_status, _utcnow()]
        if to_status == STATUS_RUNNING and not job.get("started_at"):
            sets.append("started_at = ?")
            values.append(_utcnow())
        if to_status in TERMINAL_STATUSES or to_status == STATUS_NEEDS_RECONCILIATION:
            sets.append("finished_at = ?")
            values.append(_utcnow())
        for key, value in fields.items():
            column = key if key.endswith("_json") or key in {
                "attempts", "error_code", "error_message", "receipt_id", "approval_token_id",
                "duration_ms", "op_id", "result_json", "verification_json",
            } else None
            if column is None:
                raise JobStoreError(f"unsupported job field '{key}'")
            sets.append(f"{column} = ?")
            values.append(value)
        values.extend([run_id, workspace_id])
        with self._connect() as conn:
            conn.execute(f"UPDATE promise_jobs SET {', '.join(sets)} WHERE run_id = ? AND workspace_id = ?", values)
        self.append_event(run_id, workspace_id, event_type, from_status, to_status, detail or {})
        return self.get_job(run_id, workspace_id) or {}

    def append_event(
        self,
        run_id: str,
        workspace_id: str,
        event_type: str,
        from_status: str | None,
        to_status: str | None,
        detail: dict[str, typing.Any] | None = None,
    ) -> None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM promise_events WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO promise_events (run_id, workspace_id, seq, event_type, from_status,
                                            to_status, detail_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, workspace_id, int(row["next_seq"]), event_type, from_status, to_status,
                    json.dumps(detail or {}, sort_keys=True, ensure_ascii=False, default=str),
                    _utcnow(),
                ),
            )

    def request_cancellation(self, run_id: str, workspace_id: str) -> dict[str, typing.Any]:
        job = self.get_job(run_id, workspace_id)
        if not job:
            raise JobStoreError(f"run '{run_id}' not found in workspace '{workspace_id}'")
        if job["status"] in TERMINAL_STATUSES:
            raise JobStoreError(f"run '{run_id}' already finished with status {job['status']}")
        if job["status"] in (STATUS_QUEUED, STATUS_AWAITING_APPROVAL):
            return self.transition(run_id, workspace_id, STATUS_CANCELLED,
                                   event_type="CANCELLED_BEFORE_START",
                                   detail={"reason": "cancelled before execution began"})
        self.append_event(run_id, workspace_id, "CANCELLATION_REQUESTED", job["status"], job["status"],
                          {"reason": "cooperative cancellation signalled"})
        with self._connect() as conn:
            conn.execute(
                "UPDATE promise_jobs SET updated_at = ?, error_code = 'CANCEL_REQUESTED' WHERE run_id = ?",
                (_utcnow(), run_id),
            )
        return self.get_job(run_id, workspace_id) or {}

    # ------------------------------------------------------------------
    # Reads (always workspace scoped)
    # ------------------------------------------------------------------
    def get_job(self, run_id: str, workspace_id: str) -> dict[str, typing.Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM promise_jobs WHERE run_id = ? AND workspace_id = ?",
                (run_id, workspace_id),
            ).fetchone()
        return self._hydrate(row) if row else None

    def find_by_idempotency_key(self, workspace_id: str, key: str) -> dict[str, typing.Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM promise_jobs WHERE workspace_id = ? AND idempotency_key = ?",
                (workspace_id, key),
            ).fetchone()
        return self._hydrate(row) if row else None

    def list_jobs(
        self,
        workspace_id: str,
        *,
        status: str | None = None,
        command_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, typing.Any]]:
        clauses = ["workspace_id = ?"]
        values: list[typing.Any] = [workspace_id]
        if status:
            clauses.append("status = ?")
            values.append(status)
        if command_id:
            clauses.append("command_id = ?")
            values.append(command_id)
        values.append(int(limit))
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM promise_jobs WHERE {' AND '.join(clauses)} "
                "ORDER BY created_at DESC LIMIT ?",
                values,
            ).fetchall()
        return [self._hydrate(r) for r in rows]

    def events(self, run_id: str, workspace_id: str) -> list[dict[str, typing.Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM promise_events WHERE run_id = ? AND workspace_id = ? ORDER BY seq ASC",
                (run_id, workspace_id),
            ).fetchall()
        return [
            {**dict(r), "detail": json.loads(r["detail_json"] or "{}")}
            for r in rows
        ]

    def count_by_status(self, workspace_id: str) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS cnt FROM promise_jobs WHERE workspace_id = ? GROUP BY status",
                (workspace_id,),
            ).fetchall()
        return {r["status"]: int(r["cnt"]) for r in rows}

    def recover_interrupted(self, *, uncertain_effects: frozenset[str], code_version: str) -> list[dict[str, str]]:
        """Reclassify jobs left mid-flight by a crash or restart.

        Jobs whose external effect may already have happened become
        ``NEEDS_RECONCILIATION``; everything else is failed honestly with
        ``INTERRUPTED_BY_RESTART`` so nobody mistakes a lost run for success.
        """
        recovered: list[dict[str, str]] = []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM promise_jobs WHERE status IN (?, ?)",
                (STATUS_RUNNING, STATUS_QUEUED),
            ).fetchall()
        for row in rows:
            job = self._hydrate(row)
            effect = job.get("external_effect", "NONE")
            target = STATUS_NEEDS_RECONCILIATION if effect in uncertain_effects else STATUS_FAILED
            detail = {
                "reason": "process restarted while the job was in flight",
                "recovered_by_code_version": code_version,
                "external_effect": effect,
            }
            with self._connect() as conn:
                conn.execute(
                    "UPDATE promise_jobs SET status = ?, error_code = ?, error_message = ?, "
                    "updated_at = ?, finished_at = ? WHERE run_id = ?",
                    (
                        target,
                        "AWAITING_RECONCILIATION" if target == STATUS_NEEDS_RECONCILIATION
                        else "INTERRUPTED_BY_RESTART",
                        json.dumps(detail, sort_keys=True),
                        _utcnow(), _utcnow(), job["run_id"],
                    ),
                )
            self.append_event(job["run_id"], job["workspace_id"], "RESTART_RECOVERY",
                              job["status"], target, detail)
            recovered.append({"run_id": job["run_id"], "status": target,
                              "workspace_id": job["workspace_id"]})
        return recovered

    @staticmethod
    def _hydrate(row: sqlite3.Row) -> dict[str, typing.Any]:
        data = dict(row)
        data["params"] = json.loads(data.pop("params_json") or "{}")
        data["result"] = json.loads(data["result_json"]) if data.get("result_json") else None
        data["verification"] = (
            json.loads(data["verification_json"]) if data.get("verification_json") else None
        )
        return data


class DuplicateSubmissionError(JobStoreError):
    """Raised when an idempotency key is reused inside one workspace."""

    def __init__(self, existing_run_id: str | None) -> None:
        self.existing_run_id = existing_run_id
        super().__init__(
            f"duplicate submission (existing run: {existing_run_id or 'race with parallel insert'})"
        )


__all__ = [
    "ACTIVE_STATUSES",
    "ALLOWED_TRANSITIONS",
    "STATUS_AWAITING_APPROVAL",
    "STATUS_CANCELLED",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "STATUS_NEEDS_RECONCILIATION",
    "STATUS_NOT_IMPLEMENTED",
    "STATUS_QUEUED",
    "STATUS_REJECTED",
    "STATUS_RUNNING",
    "TERMINAL_STATUSES",
    "DuplicateSubmissionError",
    "JobStore",
    "JobStoreError",
    "new_run_id",
]
