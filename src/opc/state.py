"""SQLite WAL persistent state store for OPC workflow runs, approvals, and actions."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.opc.models import ActionPayload, ApprovalDecision, ApprovalToken, WorkflowStatus


class StateStore:
    """ACID-compliant SQLite store with WAL mode for idempotent execution and recovery."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS opc_runs (run_id TEXT PRIMARY KEY, pack_id TEXT NOT NULL, status TEXT NOT NULL, business_profile_json TEXT NOT NULL, proposal_input_json TEXT NOT NULL, proposal_draft_json TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS opc_approvals (token_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES opc_runs(run_id), action_digest TEXT NOT NULL, principal TEXT NOT NULL, decision TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL, consumed INTEGER NOT NULL DEFAULT 0, revoked INTEGER NOT NULL DEFAULT 0, revision_notes TEXT DEFAULT '');
                CREATE TABLE IF NOT EXISTS opc_actions (idempotency_key TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES opc_runs(run_id), capability TEXT NOT NULL, connector TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL, response_json TEXT, error_message TEXT, created_at INTEGER NOT NULL, completed_at INTEGER);
                """
            )

    def save_run(
        self, run_id: str, pack_id: str, status: WorkflowStatus,
        profile_data: dict[str, Any], input_data: dict[str, Any],
        now: int, draft_data: dict[str, Any] | None = None,
    ) -> None:
        """Create or update an OPC workflow run."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO opc_runs (run_id, pack_id, status, business_profile_json, proposal_input_json, proposal_draft_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    status=excluded.status, proposal_draft_json=excluded.proposal_draft_json, updated_at=excluded.updated_at
                """,
                (
                    run_id, pack_id, status.value,
                    json.dumps(profile_data, sort_keys=True),
                    json.dumps(input_data, sort_keys=True),
                    json.dumps(draft_data, sort_keys=True) if draft_data else None,
                    now, now,
                ),
            )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Retrieve run row by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM opc_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "run_id": row["run_id"],
                "pack_id": row["pack_id"],
                "status": WorkflowStatus(row["status"]),
                "business_profile": json.loads(row["business_profile_json"]),
                "proposal_input": json.loads(row["proposal_input_json"]),
                "proposal_draft": json.loads(row["proposal_draft_json"]) if row["proposal_draft_json"] else None,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def save_approval(self, token: ApprovalToken) -> None:
        """Persist or update an approval token."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO opc_approvals (token_id, run_id, action_digest, principal, decision, created_at, expires_at, consumed, revoked, revision_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(token_id) DO UPDATE SET
                    consumed=excluded.consumed, revoked=excluded.revoked, decision=excluded.decision, revision_notes=excluded.revision_notes
                """,
                (
                    token.token_id, token.run_id, token.action_digest, token.principal,
                    token.decision.value, token.created_at, token.expires_at,
                    1 if token.consumed else 0, 1 if token.revoked else 0, token.revision_notes,
                ),
            )

    def get_approval(self, token_id: str) -> ApprovalToken | None:
        """Fetch approval token by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM opc_approvals WHERE token_id = ?", (token_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ApprovalToken(
                token_id=row["token_id"],
                run_id=row["run_id"],
                action_digest=row["action_digest"],
                principal=row["principal"],
                decision=ApprovalDecision(row["decision"]),
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                consumed=bool(row["consumed"]),
                revoked=bool(row["revoked"]),
                revision_notes=row["revision_notes"] or "",
            )

    def record_action_attempt(
        self, idempotency_key: str, run_id: str, capability: str,
        connector: str, payload: ActionPayload, now: int,
    ) -> bool:
        """Record initial action attempt. Returns False if already dispatched/recorded."""
        with self._get_connection() as conn:
            try:
                payload_str = json.dumps(
                    {"recipient": payload.recipient, "content": payload.content, "parameters": payload.parameters, "budget": payload.budget_amount},
                    sort_keys=True,
                )
                conn.execute(
                    "INSERT INTO opc_actions (idempotency_key, run_id, capability, connector, status, payload_json, created_at) VALUES (?, ?, ?, ?, 'in_flight', ?, ?)",
                    (idempotency_key, run_id, capability, connector, payload_str, now),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def mark_action_result(
        self, idempotency_key: str, status: str,
        response_data: dict[str, Any] | None, error_message: str | None, now: int,
    ) -> None:
        """Update action with final or intermediate execution outcome."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE opc_actions SET status = ?, response_json = ?, error_message = ?, completed_at = ? WHERE idempotency_key = ?",
                (status, json.dumps(response_data) if response_data else None, error_message, now, idempotency_key),
            )
