"""5-Stage Governed StateGraph + SQLite WAL Checkpointer (Strategy C Runtime Core)."""
from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import os
import sqlite3
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Final

from src.opc.approval import ApprovalSecurityError, compute_action_digest
from src.opc.models import ActionPayload

ALLOWED_RUNTIME_ENGINES: Final[frozenset[str]] = frozenset({"langgraph", "legacy"})


class GraphStage(str, Enum):
    """Deterministic 5-stage governed workflow states plus terminal/halt outcomes."""
    INGEST_CLASSIFY = "INGEST_CLASSIFY"
    DRAFT_COMPUTE = "DRAFT_COMPUTE"
    VERIFY_REPAIR = "VERIFY_REPAIR"
    INTERRUPT_AUTHORIZE = "INTERRUPT_AUTHORIZE"
    COMMIT_RECONCILE = "COMMIT_RECONCILE"
    HANDOFF_ZALO_OA_MANAGER = "HANDOFF_ZALO_OA_MANAGER"
    COMPLETED = "COMPLETED"


STAGE_SEQUENCE: Final[tuple[GraphStage, ...]] = (
    GraphStage.INGEST_CLASSIFY, GraphStage.DRAFT_COMPUTE, GraphStage.VERIFY_REPAIR,
    GraphStage.INTERRUPT_AUTHORIZE, GraphStage.COMMIT_RECONCILE,
)


def has_langgraph_extra() -> bool:
    """Return True if optional langgraph package is installed without importing it."""
    return importlib.util.find_spec("langgraph") is not None


def resolve_runtime_engine(override: str | None = None) -> str:
    """Resolve RUNTIME_ENGINE ('langgraph' or 'legacy'), failing closed on invalid values."""
    raw = override if override is not None else os.getenv("RUNTIME_ENGINE", "langgraph")
    engine = str(raw).strip().lower()
    if engine not in ALLOWED_RUNTIME_ENGINES:
        raise ValueError(f"Unsupported RUNTIME_ENGINE '{raw}' (expected 'langgraph' or 'legacy').")
    return engine


@dataclass(frozen=True)
class GraphCheckpoint:
    """Immutable snapshot of a GovernedStateGraph thread stored in SQLite WAL."""
    thread_id: str
    current_stage: GraphStage
    state: dict[str, Any]
    interrupted: bool
    payload_sha256: str
    updated_at: int


class SqliteGraphCheckpointer:
    """SQLite WAL checkpointer and side-effect idempotency journal for GovernedStateGraph."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                "CREATE TABLE IF NOT EXISTS opc_graph_checkpoints (thread_id TEXT PRIMARY KEY, current_stage TEXT NOT NULL, state_json TEXT NOT NULL, interrupted INTEGER NOT NULL DEFAULT 0, payload_sha256 TEXT NOT NULL DEFAULT '', updated_at INTEGER NOT NULL);"
                "CREATE TABLE IF NOT EXISTS opc_side_effect_journal (idempotency_key TEXT PRIMARY KEY, thread_id TEXT NOT NULL, approval_token_id TEXT NOT NULL, payload_sha256 TEXT NOT NULL, result_json TEXT NOT NULL, created_at INTEGER NOT NULL);"
            )

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        try:
            yield conn
        finally:
            conn.close()

    def put(self, thread_id: str, stage: GraphStage, state: dict[str, Any], *, interrupted: bool = False, payload_sha256: str = "", now: int | None = None) -> GraphCheckpoint:
        ts = int(time.time()) if now is None else int(now)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO opc_graph_checkpoints (thread_id, current_stage, state_json, interrupted, payload_sha256, updated_at) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(thread_id) DO UPDATE SET current_stage=excluded.current_stage, state_json=excluded.state_json, interrupted=excluded.interrupted, payload_sha256=excluded.payload_sha256, updated_at=excluded.updated_at",
                (thread_id, stage.value, json.dumps(state, sort_keys=True, ensure_ascii=False), 1 if interrupted else 0, payload_sha256, ts),
            )
        return GraphCheckpoint(thread_id, stage, dict(state), interrupted, payload_sha256, ts)

    def get(self, thread_id: str) -> GraphCheckpoint | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM opc_graph_checkpoints WHERE thread_id = ?", (thread_id,)).fetchone()
            return GraphCheckpoint(row["thread_id"], GraphStage(row["current_stage"]), json.loads(row["state_json"]), bool(row["interrupted"]), row["payload_sha256"] or "", int(row["updated_at"])) if row else None

    def execute_side_effect_once(self, thread_id: str, approval_token_id: str, payload_sha256: str, commit_fn: Callable[[dict[str, Any]], dict[str, Any]], state: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        idem_key = f"act_{hashlib.sha256(f'{thread_id}:{payload_sha256}'.encode('utf-8')).hexdigest()}"
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if (row := conn.execute("SELECT result_json FROM opc_side_effect_journal WHERE idempotency_key = ?", (idem_key,)).fetchone()) is not None:
                conn.execute("COMMIT")
                cached = json.loads(row["result_json"])
                return (cached if cached.get("status") != "in_flight" else {"status": "deduplicated"}), True
            conn.execute("INSERT INTO opc_side_effect_journal (idempotency_key, thread_id, approval_token_id, payload_sha256, result_json, created_at) VALUES (?, ?, ?, ?, ?, ?)", (idem_key, thread_id, approval_token_id, payload_sha256, '{"status":"in_flight"}', int(time.time())))
            conn.execute("COMMIT")
        try:
            out = commit_fn(state)
        except Exception:
            with self._connect() as conn:
                conn.execute("DELETE FROM opc_side_effect_journal WHERE idempotency_key = ? AND result_json = '{\"status\":\"in_flight\"}'", (idem_key,))
            raise
        with self._connect() as conn:
            conn.execute("UPDATE opc_side_effect_journal SET result_json = ? WHERE idempotency_key = ?", (json.dumps(out, sort_keys=True, ensure_ascii=False), idem_key))
        return out, False


class GovernedStateGraph:
    """5-Stage Governed StateGraph pausing at INTERRUPT_AUTHORIZE with idempotent resume."""

    def __init__(self, checkpointer: SqliteGraphCheckpointer, nodes: dict[GraphStage, Callable[[dict[str, Any]], dict[str, Any]]] | None = None) -> None:
        self.checkpointer, self.nodes = checkpointer, dict(nodes or {})

    def run_until_interrupt(self, run_id: str, initial_state: dict[str, Any]) -> GraphCheckpoint:
        state = dict(initial_state)
        for stage in STAGE_SEQUENCE[:4]:
            if stage in self.nodes:
                state = dict(self.nodes[stage](state))
            if state.get("handoff_status") == GraphStage.HANDOFF_ZALO_OA_MANAGER.value:
                return self.checkpointer.put(run_id, GraphStage.HANDOFF_ZALO_OA_MANAGER, state, interrupted=False, payload_sha256=str(state.get("payload_sha256", "")))
            is_pause = stage == GraphStage.INTERRUPT_AUTHORIZE
            cp = self.checkpointer.put(run_id, stage, state, interrupted=is_pause, payload_sha256=str(state.get("payload_sha256", "")))
            if is_pause:
                return cp
        raise RuntimeError("Unreachable StateGraph termination before INTERRUPT_AUTHORIZE.")

    def resume(self, run_id: str, approval_token_id: str, payload_sha256: str, commit_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> GraphCheckpoint:
        if (cp := self.checkpointer.get(run_id)) is None:
            raise KeyError(f"No StateGraph checkpoint found for '{run_id}'.")
        if cp.current_stage not in (GraphStage.INTERRUPT_AUTHORIZE, GraphStage.COMMIT_RECONCILE, GraphStage.COMPLETED):
            raise ApprovalSecurityError(f"Cannot resume '{run_id}' from stage '{cp.current_stage.value}'.")
        if not cp.payload_sha256 or not payload_sha256 or not hmac.compare_digest(cp.payload_sha256, payload_sha256):
            raise ApprovalSecurityError(f"Checkpoint payload_sha256 mismatch for '{run_id}' (fail-closed).")
        if (eff_commit := (commit_fn or self.nodes.get(GraphStage.COMMIT_RECONCILE))) is None:
            raise ValueError("Missing commit_fn for COMMIT_RECONCILE resume.")
        commit_out, deduplicated = self.checkpointer.execute_side_effect_once(run_id, approval_token_id, payload_sha256, eff_commit, dict(cp.state))
        merged = {**cp.state, "approval_token_id": approval_token_id, "commit_result": commit_out, "side_effect_deduplicated": deduplicated}
        self.checkpointer.put(run_id, GraphStage.COMMIT_RECONCILE, merged, interrupted=False, payload_sha256=payload_sha256)
        if str(commit_out.get("status", "completed")) in ("completed", "deduplicated"):
            return self.checkpointer.put(run_id, GraphStage.COMPLETED, merged, interrupted=False, payload_sha256=payload_sha256)
        return self.checkpointer.put(run_id, GraphStage.COMMIT_RECONCILE, merged, interrupted=False, payload_sha256=payload_sha256)


def record_pilot_checkpoint(checkpointer: SqliteGraphCheckpointer | None, run_id: str, payload: ActionPayload, extra: dict[str, Any]) -> str:
    """Persist INTERRUPT_AUTHORIZE checkpoint bound to ActionPayload SHA-256 when checkpointer is active."""
    digest = compute_action_digest(payload)
    if checkpointer is not None:
        checkpointer.put(run_id, GraphStage.INTERRUPT_AUTHORIZE, {**extra, "payload_sha256": digest}, interrupted=True, payload_sha256=digest)
    return digest


def build_handoff_outcome(checkpointer: SqliteGraphCheckpointer | None, event_id: str, sender_id: str, reason_code: str, detail: str, citations: tuple[dict[str, Any], ...], runtime_engine: str) -> dict[str, Any]:
    """Record and return structured HANDOFF_ZALO_OA_MANAGER payload on low confidence or math halt."""
    tid, st = f"handoff_{event_id}", GraphStage.HANDOFF_ZALO_OA_MANAGER.value
    out: dict[str, Any] = {"status": st, "handoff_status": st, "thread_id": tid, "event_id": event_id, "sender_id": sender_id, "reason_code": reason_code, "detail": detail, "citations": citations, "runtime_engine": runtime_engine}
    if checkpointer is not None:
        checkpointer.put(tid, GraphStage.HANDOFF_ZALO_OA_MANAGER, {**out, "citations": list(citations)}, interrupted=False)
    return out
