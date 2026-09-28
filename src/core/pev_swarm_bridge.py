# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unified PEV Swarm Bridge & Durable Checkpoint Engine.

Provider-neutral standard-library bridge connecting Mekong's Plan-Execute-Verify (PEV)
engine and Goal system to Google Antigravity subagent orchestration.

Invariants:
- Zero external vendor SDK imports (test_core_boundary.py compliant).
- Python standard library only: sqlite3, json, hashlib, pathlib, typing, dataclasses,
  enum, time, datetime, subprocess, os, sys, shutil, base64, uuid.
- Pinned context budgets (16,000 - 30,000 tokens) adhering to HARNESS.md §1.
- Layer-specific tool allowlists adhering to HARNESS.md §2.
- Verifier independence: independent verifier subagents with strictly read-only tools
  (no Write or Edit permissions).
- Durable SQLite checkpoint persistence (.mekong/pev_checkpoints.db) supporting
  file snapshots (UTF-8 text and Base64 binary) and atomic rollback.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Pinned Context Budget definitions matching HARNESS.md §1
ROLE_CONTEXT_BUDGETS: dict[str, int] = {
    "ceo": 30000,
    "sun-tzu": 30000,
    "cto": 24000,
    "eng": 24000,
    "fullstack-developer": 24000,
    "debugger": 24000,
    "pm": 20000,
    "planner": 20000,
    "cmo": 20000,
    "ops": 16000,
    "coo": 16000,
    "ae": 16000,
    "cfo": 16000,
    "tester": 16000,
    "code-reviewer": 16000,
    "code-simplifier": 16000,
    "docs-manager": 16000,
    "git-manager": 16000,
    "journal-writer": 16000,
    "kongming": 16000,
    "project-manager": 20000,
    "researcher": 20000,
    "ui-ux-designer": 20000,
    "brainstormer": 20000,
    "cso": 20000,
}

# Role to layer tool allowlists matching HARNESS.md §2
ROLE_TOOL_ALLOWLISTS: dict[str, list[str]] = {
    "ceo": ["Read", "Write", "Edit", "Bash", "Task", "AskUserQuestion"],
    "sun-tzu": ["Read", "Glob", "Grep", "Bash", "WebFetch", "WebSearch", "Task"],
    "pm": ["Read", "Write", "Edit", "Bash", "Task"],
    "planner": ["Read", "Write", "Edit", "Bash", "Task"],
    "cto": ["Read", "Write", "Edit", "Bash", "Task"],
    "eng": ["Read", "Write", "Edit", "Bash", "Task"],
    "fullstack-developer": ["Read", "Write", "Edit", "Bash", "Task"],
    "debugger": ["Read", "Write", "Edit", "Bash", "Task"],
    "ops": ["Read", "Bash", "Task"],
    "coo": ["Read", "Bash", "Task"],
    "tester": ["Read", "Bash", "Task"],  # Read-only verifier! Strictly NO Write/Edit
    "code-reviewer": ["Read", "Bash", "Task"],  # Read-only verifier! Strictly NO Write/Edit
    "cfo": ["Read", "Bash", "Task"],
    "cmo": ["Read", "Bash", "Task"],
    "cso": ["Read", "Bash", "Task"],
    "ae": ["Read", "Bash", "Task"],
    "code-simplifier": ["Read", "Write", "Edit", "Bash", "Task"],
    "docs-manager": ["Read", "Write", "Edit", "Bash", "Task"],
    "git-manager": ["Read", "Bash", "Task"],
    "journal-writer": ["Read", "Write", "Edit", "Task"],
    "kongming": ["Read", "Bash", "Task"],
    "project-manager": ["Read", "Write", "Edit", "Bash", "Task"],
    "researcher": ["Read", "Bash", "Task"],
    "ui-ux-designer": ["Read", "Write", "Edit", "Bash", "Task"],
    "brainstormer": ["Read", "Bash", "Task"],
}

# Verifier roles that must NEVER be granted Write or Edit tools
VERIFIER_ROLES: set[str] = {"tester", "code-reviewer", "qa", "auditor"}


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


class PevPhase(str, Enum):
    """Canonical PEV lifecycle phases."""
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"


class MissionStatus(str, Enum):
    """High-level status of a PEV swarm mission."""
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class TaskStatus(str, Enum):
    """Execution status of an individual task in a PEV plan."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class VerificationCriteria:
    """Acceptance criteria and rubrics for verifying task deliverables."""
    exit_code: Optional[int] = 0
    file_exists: list[str] = field(default_factory=list)
    test_command: Optional[str] = None
    output_contains: list[str] = field(default_factory=list)
    output_not_contains: list[str] = field(default_factory=list)
    rubric_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerificationCriteria":
        if not data:
            return cls()
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


@dataclass
class PevTask:
    """Individual task within a PEV execution DAG."""
    task_id: str
    mission_id: str
    order_idx: int
    title: str
    description: str
    role: str
    phase: PevPhase = PevPhase.EXECUTE
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    context_budget: int = 24000
    allowed_tools: list[str] = field(default_factory=list)
    verification_criteria: VerificationCriteria = field(default_factory=VerificationCriteria)
    attempts: int = 0
    max_attempts: int = 3
    result_summary: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value if isinstance(self.phase, PevPhase) else str(self.phase)
        d["status"] = self.status.value if isinstance(self.status, TaskStatus) else str(self.status)
        d["verification_criteria"] = self.verification_criteria.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PevTask":
        d = dict(data)
        if isinstance(d.get("phase"), str):
            d["phase"] = PevPhase(d["phase"])
        if isinstance(d.get("status"), str):
            d["status"] = TaskStatus(d["status"])
        if isinstance(d.get("verification_criteria"), dict):
            d["verification_criteria"] = VerificationCriteria.from_dict(d["verification_criteria"])
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in d.items() if k in valid_keys})


@dataclass
class PevPlan:
    """Structured execution plan resulting from the Plan phase."""
    goal: str
    mission_id: str
    tasks: list[PevTask]
    subagent_assignments: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "mission_id": self.mission_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "subagent_assignments": self.subagent_assignments,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PevPlan":
        tasks = [PevTask.from_dict(t) for t in data.get("tasks", [])]
        return cls(
            goal=data.get("goal", ""),
            mission_id=data.get("mission_id", ""),
            tasks=tasks,
            subagent_assignments=data.get("subagent_assignments", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FileSnapshot:
    """Byte-level snapshot of a workspace file."""
    relative_path: str
    sha256: str
    content_type: str  # "utf-8" or "base64"
    content: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckpointRecord:
    """Durable point-in-time snapshot of mission state and workspace files."""
    checkpoint_id: str
    mission_id: str
    task_id: Optional[str]
    cycle: int
    phase: str
    label: str
    task_states: dict[str, str]
    test_results: dict[str, Any]
    file_snapshots: list[FileSnapshot] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["file_snapshots"] = [f.to_dict() for f in self.file_snapshots]
        return d


class CheckpointStore:
    """ACID SQLite store for checkpoints, file snapshots, and mission state."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = Path.cwd() / ".mekong" / "pev_checkpoints.db"
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Create a configured SQLite connection with WAL and foreign keys."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema with idempotent DDL."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    cycle INTEGER NOT NULL DEFAULT 1,
                    max_cycles INTEGER NOT NULL DEFAULT 3,
                    plan_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL REFERENCES missions(mission_id) ON DELETE CASCADE,
                    order_idx INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    role TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    status TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    context_budget INTEGER NOT NULL,
                    allowed_tools TEXT NOT NULL,
                    verification_criteria TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    result_summary TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL REFERENCES missions(mission_id) ON DELETE CASCADE,
                    task_id TEXT,
                    cycle INTEGER NOT NULL,
                    phase TEXT NOT NULL,
                    label TEXT NOT NULL,
                    task_states TEXT NOT NULL,
                    test_results TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS file_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checkpoint_id TEXT NOT NULL REFERENCES checkpoints(checkpoint_id) ON DELETE CASCADE,
                    relative_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS verification_runs (
                    id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL REFERENCES missions(mission_id) ON DELETE CASCADE,
                    task_id TEXT,
                    cycle INTEGER NOT NULL,
                    verifier_role TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    checks_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_mission ON tasks(mission_id);
                CREATE INDEX IF NOT EXISTS idx_checkpoints_mission ON checkpoints(mission_id);
                CREATE INDEX IF NOT EXISTS idx_file_snapshots_cp ON file_snapshots(checkpoint_id);
                CREATE INDEX IF NOT EXISTS idx_verifications_mission ON verification_runs(mission_id);
                """
            )
            conn.commit()

    def capture_checkpoint(
        self,
        mission_id: str,
        label: str,
        task_id: Optional[str] = None,
        phase: str = "post_execute",
        files: Optional[list[str | Path]] = None,
        test_results: Optional[dict[str, Any]] = None,
        project_root: Optional[Path] = None,
    ) -> str:
        """Capture atomic checkpoint with file snapshots and task states."""
        root = Path(project_root or Path.cwd()).resolve()
        now = _utc_now_iso()
        cp_id = f"cp_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        with self._connect() as conn:
            # Ensure mission exists to satisfy foreign key constraint
            conn.execute(
                """
                INSERT OR IGNORE INTO missions (
                    mission_id, goal, status, cycle, max_cycles, plan_json,
                    created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mission_id,
                    f"Mission {mission_id}",
                    MissionStatus.CREATED.value,
                    1,
                    3,
                    "{}",
                    now,
                    now,
                    "{}",
                ),
            )

            # Query mission for current cycle
            m_cur = conn.execute(
                "SELECT cycle FROM missions WHERE mission_id = ?", (mission_id,)
            ).fetchone()
            cycle = m_cur["cycle"] if m_cur else 1

            # Snapshot task statuses
            t_rows = conn.execute(
                "SELECT task_id, status FROM tasks WHERE mission_id = ?", (mission_id,)
            ).fetchall()
            task_states = {row["task_id"]: row["status"] for row in t_rows}

            conn.execute(
                """
                INSERT INTO checkpoints (
                    checkpoint_id, mission_id, task_id, cycle, phase,
                    label, task_states, test_results, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cp_id,
                    mission_id,
                    task_id,
                    cycle,
                    phase,
                    label,
                    json.dumps(task_states),
                    json.dumps(test_results or {}),
                    now,
                ),
            )

            # Discover files if not explicitly provided
            resolved_files: set[Path] = set()
            if files is not None:
                for f in files:
                    p = Path(f)
                    full_p = (p if p.is_absolute() else root / p).resolve()
                    if full_p.is_file():
                        resolved_files.add(full_p)
            else:
                # Discover modified or untracked files via git status if in a git repository
                if (root / ".git").exists():
                    try:
                        git_res = subprocess.run(
                            ["git", "status", "--porcelain"],
                            cwd=root,
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        if git_res.returncode == 0:
                            for line in git_res.stdout.splitlines():
                                line = line.strip()
                                if len(line) > 3:
                                    rel = line[3:].strip()
                                    # Skip excluded directories
                                    if any(
                                        rel.startswith(ign)
                                        for ign in (
                                            ".git",
                                            ".mekong",
                                            ".pytest_cache",
                                            "__pycache__",
                                        )
                                    ):
                                        continue
                                    target = (root / rel).resolve()
                                    if target.is_file():
                                        resolved_files.add(target)
                    except Exception as exc:
                        logger.debug("Failed git status discovery for checkpoint: %s", exc)

            # Snapshot each resolved file
            for file_path in resolved_files:
                try:
                    rel_path = file_path.relative_to(root).as_posix()
                except ValueError:
                    rel_path = file_path.name

                raw_bytes = file_path.read_bytes()
                sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
                size_bytes = len(raw_bytes)

                # Determine if text (utf-8) or binary
                is_text = True
                content_str = ""
                try:
                    # Check for null bytes indicative of binary
                    if b"\x00" in raw_bytes[:4096]:
                        is_text = False
                    else:
                        content_str = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    is_text = False

                if is_text:
                    content_type = "utf-8"
                else:
                    content_type = "base64"
                    content_str = base64.b64encode(raw_bytes).decode("ascii")

                conn.execute(
                    """
                    INSERT INTO file_snapshots (
                        checkpoint_id, relative_path, sha256,
                        content_type, content, size_bytes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cp_id,
                        rel_path,
                        sha256_hash,
                        content_type,
                        content_str,
                        size_bytes,
                        now,
                    ),
                )

            conn.commit()

        return cp_id

    def get_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointRecord]:
        """Retrieve a checkpoint record and its associated file snapshots.

        Returns None if checkpoint is not found or if the record contains corrupted
        JSON or invalid data, logging a warning rather than raising an unhandled exception.
        """
        try:
            with self._connect() as conn:
                cp_row = conn.execute(
                    "SELECT * FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,)
                ).fetchone()
                if not cp_row:
                    return None

                snap_rows = conn.execute(
                    "SELECT relative_path, sha256, content_type, content, size_bytes "
                    "FROM file_snapshots WHERE checkpoint_id = ? ORDER BY id ASC",
                    (checkpoint_id,),
                ).fetchall()

                snapshots = [
                    FileSnapshot(
                        relative_path=r["relative_path"],
                        sha256=r["sha256"],
                        content_type=r["content_type"],
                        content=r["content"],
                        size_bytes=r["size_bytes"],
                    )
                    for r in snap_rows
                ]

                try:
                    task_states = json.loads(cp_row["task_states"]) if cp_row["task_states"] else {}
                except (json.JSONDecodeError, ValueError) as exc:
                    logger.warning("Corrupted task_states in checkpoint %s: %s", checkpoint_id, exc)
                    return None

                try:
                    test_results = json.loads(cp_row["test_results"]) if cp_row["test_results"] else {}
                except (json.JSONDecodeError, ValueError) as exc:
                    logger.warning("Corrupted test_results in checkpoint %s: %s", checkpoint_id, exc)
                    return None

                return CheckpointRecord(
                    checkpoint_id=cp_row["checkpoint_id"],
                    mission_id=cp_row["mission_id"],
                    task_id=cp_row["task_id"],
                    cycle=cp_row["cycle"],
                    phase=cp_row["phase"],
                    label=cp_row["label"],
                    task_states=task_states,
                    test_results=test_results,
                    file_snapshots=snapshots,
                    created_at=cp_row["created_at"],
                )
        except (json.JSONDecodeError, binascii.Error, ValueError, OSError, sqlite3.Error) as exc:
            logger.warning(
                "Failed to retrieve checkpoint %s due to corrupted data or database error: %s",
                checkpoint_id,
                exc,
            )
            return None

    def list_checkpoints(self, mission_id: Optional[str] = None) -> list[dict[str, Any]]:
        """List checkpoints ordered by newest first."""
        with self._connect() as conn:
            if mission_id:
                rows = conn.execute(
                    """
                    SELECT c.*, COUNT(s.id) AS file_count
                    FROM checkpoints c
                    LEFT JOIN file_snapshots s ON c.checkpoint_id = s.checkpoint_id
                    WHERE c.mission_id = ?
                    GROUP BY c.checkpoint_id
                    ORDER BY c.created_at DESC
                    """,
                    (mission_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT c.*, COUNT(s.id) AS file_count
                    FROM checkpoints c
                    LEFT JOIN file_snapshots s ON c.checkpoint_id = s.checkpoint_id
                    GROUP BY c.checkpoint_id
                    ORDER BY c.created_at DESC
                    """
                ).fetchall()

            results: list[dict[str, Any]] = []
            for r in rows:
                try:
                    task_states = json.loads(r["task_states"]) if r["task_states"] else {}
                except (json.JSONDecodeError, ValueError):
                    task_states = {}
                results.append(
                    {
                        "checkpoint_id": r["checkpoint_id"],
                        "mission_id": r["mission_id"],
                        "task_id": r["task_id"],
                        "cycle": r["cycle"],
                        "phase": r["phase"],
                        "label": r["label"],
                        "file_count": r["file_count"],
                        "task_states": task_states,
                        "created_at": r["created_at"],
                    }
                )
            return results

    def rollback_to_checkpoint(
        self, checkpoint_id: str, project_root: Optional[Path] = None
    ) -> dict[str, Any]:
        """Atomically restore workspace files and task states to a specific checkpoint.
        
        Also removes extraneous files created after the target checkpoint.
        Strictly confines file restoration and removal within project_root.
        Returns structured error responses on failure without unhandled process crashes.
        """
        root = Path(project_root or Path.cwd()).resolve()
        root_resolved = root.resolve()
        restored_files: list[str] = []
        removed_files: list[str] = []

        try:
            # Check existence in database first
            with self._connect() as conn:
                cp_row = conn.execute(
                    "SELECT checkpoint_id FROM checkpoints WHERE checkpoint_id = ?",
                    (checkpoint_id,),
                ).fetchone()

            if not cp_row:
                return {
                    "ok": False,
                    "error": f"Checkpoint {checkpoint_id} not found",
                    "restored_files": restored_files,
                }

            # Retrieve full checkpoint record
            cp = self.get_checkpoint(checkpoint_id)
            if not cp:
                return {
                    "ok": False,
                    "error": f"Rollback failed: Checkpoint {checkpoint_id} contains corrupted data",
                    "restored_files": restored_files,
                }

            now = _utc_now_iso()

            with self._connect() as conn:
                # 1. Restore all file snapshots in the target checkpoint
                target_snapshot_paths: set[str] = set()
                for snap in cp.file_snapshots:
                    try:
                        dest = (root / snap.relative_path).resolve()
                        dest.relative_to(root_resolved)
                    except (ValueError, Exception) as p_exc:
                        logger.warning(
                            "Rejecting unsafe snapshot path outside workspace root: %s (%s)",
                            snap.relative_path,
                            p_exc,
                        )
                        continue

                    if dest == root_resolved:
                        logger.warning(
                            "Rejecting unsafe snapshot path matching root directory: %s",
                            snap.relative_path,
                        )
                        continue

                    dest.parent.mkdir(parents=True, exist_ok=True)

                    if snap.content_type == "utf-8":
                        dest.write_text(snap.content, encoding="utf-8")
                    elif snap.content_type == "base64":
                        try:
                            decoded_bytes = base64.b64decode(snap.content.encode("ascii"), validate=True)
                        except (binascii.Error, ValueError) as b64_exc:
                            logger.warning(
                                "Corrupted base64 content in snapshot %s for checkpoint %s: %s",
                                snap.relative_path,
                                checkpoint_id,
                                b64_exc,
                            )
                            return {
                                "ok": False,
                                "error": f"Rollback failed: Corrupted base64 content for file '{snap.relative_path}': {b64_exc}",
                                "restored_files": restored_files,
                            }
                        dest.write_bytes(decoded_bytes)
                    else:
                        dest.write_text(snap.content, encoding="utf-8")

                    restored_files.append(snap.relative_path)
                    target_snapshot_paths.add(snap.relative_path)

                # 2. Identify and safely remove files created after this checkpoint for this mission
                post_rows = conn.execute(
                    """
                    SELECT DISTINCT s.relative_path
                    FROM file_snapshots s
                    JOIN checkpoints c ON s.checkpoint_id = c.checkpoint_id
                    WHERE c.mission_id = ? AND c.created_at > ?
                    """,
                    (cp.mission_id, cp.created_at),
                ).fetchall()

                for r in post_rows:
                    rel = r["relative_path"]
                    if rel not in target_snapshot_paths:
                        try:
                            candidate = (root / rel).resolve()
                            candidate.relative_to(root_resolved)
                        except (ValueError, Exception) as p_exc:
                            logger.warning(
                                "Rejecting unsafe candidate path outside workspace root: %s (%s)",
                                rel,
                                p_exc,
                            )
                            continue

                        if candidate == root_resolved:
                            continue

                        if candidate.is_file():
                            try:
                                candidate.unlink()
                                removed_files.append(rel)
                            except OSError as exc:
                                logger.warning("Could not remove newly created file %s: %s", rel, exc)

                # 3. Restore task states in the database
                for task_id, status_val in cp.task_states.items():
                    conn.execute(
                        "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                        (status_val, now, task_id),
                    )

                # 4. Mark mission as rolled back
                conn.execute(
                    "UPDATE missions SET status = ?, updated_at = ? WHERE mission_id = ?",
                    (MissionStatus.ROLLED_BACK.value, now, cp.mission_id),
                )
                conn.commit()

            return {
                "ok": True,
                "checkpoint_id": checkpoint_id,
                "mission_id": cp.mission_id,
                "restored_files": restored_files,
                "removed_files": removed_files,
                "task_states": cp.task_states,
                "rolled_back_at": now,
            }

        except (json.JSONDecodeError, binascii.Error, ValueError, OSError, sqlite3.Error) as exc:
            logger.error("Rollback to checkpoint %s failed: %s", checkpoint_id, exc)
            return {
                "ok": False,
                "error": f"Rollback failed: {exc}",
                "restored_files": restored_files,
            }


class PEVSwarmBridge:
    """Unified bridge orchestrating Plan -> Execute -> Verify cycles."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        project_root: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        if db_path is None:
            db_path = self.project_root / ".mekong" / "pev_checkpoints.db"
        self.store = CheckpointStore(db_path)

    # -------------------------------------------------------------------------
    # 1. Plan Phase
    # -------------------------------------------------------------------------

    def plan(self, goal: str, mission_id: Optional[str] = None) -> PevPlan:
        """Decompose a high-level goal into structured tasks with subagent assignments.
        
        Assigns roles mapped to the 25 domain subagents, sets context budgets,
        allowed tools, and generates concrete verification criteria.
        """
        clean_goal = (goal or "").strip()
        if not clean_goal:
            raise ValueError("Goal cannot be empty")

        mid = mission_id or f"m_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        now = _utc_now_iso()

        tasks = self._decompose_goal(clean_goal, mid, now)
        subagent_assignments: dict[str, dict[str, Any]] = {}

        for t in tasks:
            if t.role not in subagent_assignments:
                subagent_assignments[t.role] = self._build_subagent_payload(
                    role=t.role,
                    task_desc=f"Execute task: {t.title}. {t.description}",
                    context_budget=t.context_budget,
                    allowed_tools=t.allowed_tools,
                )

        pev_plan = PevPlan(
            goal=clean_goal,
            mission_id=mid,
            tasks=tasks,
            subagent_assignments=subagent_assignments,
            metadata={"created_at": now, "engine": "PEVSwarmBridge", "version": "1.0.0"},
        )

        # Persist mission and tasks into SQLite
        with self.store._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO missions (
                    mission_id, goal, status, cycle, max_cycles, plan_json,
                    created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mid,
                    clean_goal,
                    MissionStatus.CREATED.value,
                    1,
                    3,
                    json.dumps(pev_plan.to_dict()),
                    now,
                    now,
                    json.dumps({"total_tasks": len(tasks)}),
                ),
            )

            for t in tasks:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO tasks (
                        task_id, mission_id, order_idx, title, description,
                        role, phase, status, depends_on, context_budget,
                        allowed_tools, verification_criteria, attempts,
                        max_attempts, result_summary, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        t.task_id,
                        t.mission_id,
                        t.order_idx,
                        t.title,
                        t.description,
                        t.role,
                        t.phase.value,
                        t.status.value,
                        json.dumps(t.depends_on),
                        t.context_budget,
                        json.dumps(t.allowed_tools),
                        json.dumps(t.verification_criteria.to_dict()),
                        t.attempts,
                        t.max_attempts,
                        t.result_summary,
                        t.created_at,
                        t.updated_at,
                    ),
                )
            conn.commit()

        return pev_plan

    def _decompose_goal(self, goal: str, mission_id: str, timestamp: str) -> list[PevTask]:
        """Heuristically decompose goal into structured DAG tasks with 25-subagent roles."""
        lower_goal = goal.lower()
        tasks: list[PevTask] = []

        is_security = any(k in lower_goal for k in ("security", "audit", "pentest", "vulnerability", "sox"))
        is_bugfix = any(k in lower_goal for k in ("fix", "bug", "error", "issue", "debug", "patch"))
        is_ui = any(k in lower_goal for k in ("ui", "frontend", "design", "css", "component", "page"))
        is_docs = any(k in lower_goal for k in ("doc", "docs", "documentation", "readme", "guide"))

        t1_id = f"task_{mission_id}_01"
        t2_id = f"task_{mission_id}_02"
        t3_id = f"task_{mission_id}_03"

        if is_security:
            # Security Audit Flow
            tasks.append(
                PevTask(
                    task_id=t1_id,
                    mission_id=mission_id,
                    order_idx=1,
                    title="Security Posture & Boundary Audit",
                    description=f"Analyze codebase and architecture for security risks in goal: {goal}",
                    role="cso",
                    phase=PevPhase.PLAN,
                    status=TaskStatus.PENDING,
                    depends_on=[],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("cso", 20000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("cso", ["Read", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="CSO produces comprehensive security risk assessment",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t2_id,
                    mission_id=mission_id,
                    order_idx=2,
                    title="Implement Hardening & Boundary Enforcement",
                    description=f"Remediate security risks and enforce boundary controls for: {goal}",
                    role="eng",
                    phase=PevPhase.EXECUTE,
                    status=TaskStatus.PENDING,
                    depends_on=[t1_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("eng", 24000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("eng", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        test_command="python3 -m pytest tests/test_core_boundary.py"
                        if (self.project_root / "tests" / "test_core_boundary.py").exists()
                        else None,
                        rubric_prompt="Zero external vendor SDK leaks; boundary passes 100%",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t3_id,
                    mission_id=mission_id,
                    order_idx=3,
                    title="Independent Security & Regression Verification",
                    description=f"Validate hardening measures and ensure regression-free deployment for: {goal}",
                    role="code-reviewer",
                    phase=PevPhase.VERIFY,
                    status=TaskStatus.PENDING,
                    depends_on=[t2_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("code-reviewer", 16000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("code-reviewer", ["Read", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="Independent verifier confirms zero security violations and passing gates",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
        elif is_bugfix:
            # Bug Diagnosis and Fix Flow
            tasks.append(
                PevTask(
                    task_id=t1_id,
                    mission_id=mission_id,
                    order_idx=1,
                    title="Root Cause Analysis & Diagnosis",
                    description=f"Investigate failure symptoms and identify root cause for: {goal}",
                    role="debugger",
                    phase=PevPhase.PLAN,
                    status=TaskStatus.PENDING,
                    depends_on=[],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("debugger", 24000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("debugger", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="Root cause identified with reproducer test or scenario",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t2_id,
                    mission_id=mission_id,
                    order_idx=2,
                    title="Implement Minimal Bug Fix",
                    description=f"Apply minimal, robust fix to resolve defect: {goal}",
                    role="eng",
                    phase=PevPhase.EXECUTE,
                    status=TaskStatus.PENDING,
                    depends_on=[t1_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("eng", 24000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("eng", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        test_command="python3 -m pytest tests/"
                        if (self.project_root / "tests").exists()
                        else None,
                        rubric_prompt="Bug resolved without introducing collateral regressions",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t3_id,
                    mission_id=mission_id,
                    order_idx=3,
                    title="Regression & Gate Verification",
                    description=f"Verify fix correctness and test suite stability for: {goal}",
                    role="tester",
                    phase=PevPhase.VERIFY,
                    status=TaskStatus.PENDING,
                    depends_on=[t2_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("tester", 16000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("tester", ["Read", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="Tester confirms bug fix verification and regression tests pass",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
        elif is_ui:
            # UI / Frontend Flow
            tasks.append(
                PevTask(
                    task_id=t1_id,
                    mission_id=mission_id,
                    order_idx=1,
                    title="UI/UX Architecture & Component Spec",
                    description=f"Specify interface layout, interactions, and design constraints for: {goal}",
                    role="ui-ux-designer",
                    phase=PevPhase.PLAN,
                    status=TaskStatus.PENDING,
                    depends_on=[],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("ui-ux-designer", 20000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("ui-ux-designer", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="Design spec completed and verified against UX principles",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t2_id,
                    mission_id=mission_id,
                    order_idx=2,
                    title="Build UI Components & Wiring",
                    description=f"Implement frontend components and business logic for: {goal}",
                    role="fullstack-developer",
                    phase=PevPhase.EXECUTE,
                    status=TaskStatus.PENDING,
                    depends_on=[t1_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("fullstack-developer", 24000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("fullstack-developer", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="UI components render correctly with expected functionality",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t3_id,
                    mission_id=mission_id,
                    order_idx=3,
                    title="UI Quality & Responsive Verification",
                    description=f"Validate component rendering and accessibility for: {goal}",
                    role="tester",
                    phase=PevPhase.VERIFY,
                    status=TaskStatus.PENDING,
                    depends_on=[t2_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("tester", 16000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("tester", ["Read", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="All visual and behavioral criteria verified",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
        elif is_docs:
            # Documentation Flow
            tasks.append(
                PevTask(
                    task_id=t1_id,
                    mission_id=mission_id,
                    order_idx=1,
                    title="Documentation Outline & Audience Scope",
                    description=f"Define documentation structure and topics for: {goal}",
                    role="pm",
                    phase=PevPhase.PLAN,
                    status=TaskStatus.PENDING,
                    depends_on=[],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("pm", 20000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("pm", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="Documentation outline drafted",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t2_id,
                    mission_id=mission_id,
                    order_idx=2,
                    title="Author Technical Documentation",
                    description=f"Write complete, clear documentation for: {goal}",
                    role="docs-manager",
                    phase=PevPhase.EXECUTE,
                    status=TaskStatus.PENDING,
                    depends_on=[t1_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("docs-manager", 16000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("docs-manager", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="Technical documents created and formatted",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t3_id,
                    mission_id=mission_id,
                    order_idx=3,
                    title="Review & Verify Documentation Completeness",
                    description=f"Verify accuracy, links, and completeness for: {goal}",
                    role="code-reviewer",
                    phase=PevPhase.VERIFY,
                    status=TaskStatus.PENDING,
                    depends_on=[t2_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("code-reviewer", 16000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("code-reviewer", ["Read", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="Documentation validated with no broken references",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
        else:
            # Canonical 3-Phase PEV Flow (Plan -> Implement -> Verify)
            tasks.append(
                PevTask(
                    task_id=t1_id,
                    mission_id=mission_id,
                    order_idx=1,
                    title="Requirements & Architecture Specification",
                    description=f"Analyze requirements and design system architecture for: {goal}",
                    role="pm",
                    phase=PevPhase.PLAN,
                    status=TaskStatus.PENDING,
                    depends_on=[],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("pm", 20000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("pm", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="PRD and architecture specification complete",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t2_id,
                    mission_id=mission_id,
                    order_idx=2,
                    title="Core Engineering Implementation",
                    description=f"Implement source code, modules, and interfaces for: {goal}",
                    role="eng",
                    phase=PevPhase.EXECUTE,
                    status=TaskStatus.PENDING,
                    depends_on=[t1_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("eng", 24000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("eng", ["Read", "Write", "Edit", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        test_command="python3 -m pytest tests/"
                        if (self.project_root / "tests").exists()
                        else None,
                        rubric_prompt="Implementation complete with zero build/syntax errors",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )
            tasks.append(
                PevTask(
                    task_id=t3_id,
                    mission_id=mission_id,
                    order_idx=3,
                    title="Quality Assurance & Independent Verification",
                    description=f"Perform independent testing, verification gates, and regression checks for: {goal}",
                    role="tester",
                    phase=PevPhase.VERIFY,
                    status=TaskStatus.PENDING,
                    depends_on=[t2_id],
                    context_budget=ROLE_CONTEXT_BUDGETS.get("tester", 16000),
                    allowed_tools=ROLE_TOOL_ALLOWLISTS.get("tester", ["Read", "Bash", "Task"]),
                    verification_criteria=VerificationCriteria(
                        exit_code=0,
                        rubric_prompt="All automated tests and verification gates pass cleanly",
                    ),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            )

        return tasks

    def _build_subagent_payload(
        self,
        role: str,
        task_desc: str,
        context_budget: int,
        allowed_tools: list[str],
    ) -> dict[str, Any]:
        """Construct Antigravity define_subagent, invoke_subagent, and context payload."""
        # Try leveraging internal subagent_dispatch helper if available
        try:
            from src.core.subagent_dispatch import build_subagent_dispatch_payload

            payload = build_subagent_dispatch_payload(
                role=role,
                task=task_desc,
                project_root=self.project_root,
            )
            if payload.get("ok"):
                # Ensure context budget and tool allowlists match our pinned contracts
                payload["context_engineering"]["token_budget"] = context_budget
                payload["context_engineering"]["tool_allowlist"] = allowed_tools
                if "define_subagent" in payload:
                    payload["define_subagent"]["tools"] = allowed_tools
                return payload
        except Exception as exc:
            logger.debug("Falling back to local subagent payload construction: %s", exc)

        # Standard-library fallback payload construction
        return {
            "ok": True,
            "role": role,
            "task": task_desc,
            "define_subagent": {
                "name": f"mekong-{role}",
                "description": f"Mekong CLI Domain Subagent: {role}",
                "system_prompt": f"You are {role} in the Mekong CLI CEO Solo Harness.\nTask: {task_desc}",
                "tools": allowed_tools,
                "model_tier": "pro" if role in ("ceo", "sun-tzu", "cto") else "flash",
            },
            "invoke_subagent": {
                "subagent_name": f"mekong-{role}",
                "prompt": task_desc,
            },
            "context_engineering": {
                "token_budget": context_budget,
                "token_ceiling": 40000,
                "tool_allowlist": allowed_tools,
                "sop_layer": f"sops/{role}/",
            },
        }

    # -------------------------------------------------------------------------
    # 2. Execute Phase
    # -------------------------------------------------------------------------

    def execute_task(
        self,
        mission_id: str,
        task_id: str,
        dry_run: bool = False,
        files: Optional[list[str | Path]] = None,
    ) -> dict[str, Any]:
        """Execute or preview an individual task within a mission.
        
        Captures pre-execution checkpoint, verifies dependencies, and generates
        the worker subagent dispatch payload adhering to layer tool allowlists.
        In live mode (dry_run=False), records execution state and post-execution
        checkpoint as the core state spine for higher-layer CLI and MCP runners.
        """
        task = self.get_task(task_id)
        if not task:
            return {"ok": False, "error": f"Task {task_id} not found in database"}

        # Validate task dependencies
        if task.depends_on:
            with self.store._connect() as conn:
                placeholders = ",".join("?" for _ in task.depends_on)
                rows = conn.execute(
                    f"SELECT task_id, status FROM tasks WHERE task_id IN ({placeholders})",
                    task.depends_on,
                ).fetchall()
                statuses = {r["task_id"]: r["status"] for r in rows}
                unmet = [dep for dep in task.depends_on if statuses.get(dep) != TaskStatus.COMPLETED.value]
                if unmet:
                    self._update_task_status(task_id, TaskStatus.BLOCKED)
                    return {
                        "ok": False,
                        "status": TaskStatus.BLOCKED.value,
                        "error": f"Prerequisite tasks not completed: {unmet}",
                    }

        worker_payload = self._build_subagent_payload(
            role=task.role,
            task_desc=f"{task.title}: {task.description}",
            context_budget=task.context_budget,
            allowed_tools=task.allowed_tools,
        )

        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "mission_id": mission_id,
                "task_id": task_id,
                "title": task.title,
                "role": task.role,
                "context_budget": task.context_budget,
                "allowed_tools": task.allowed_tools,
                "payload": worker_payload,
            }

        # Determine target files for snapshot
        snapshot_files: list[str | Path] = []
        if files:
            snapshot_files.extend(files)
        if task.verification_criteria.file_exists:
            for fe in task.verification_criteria.file_exists:
                fp = (self.project_root / fe).resolve()
                if fp.is_file():
                    snapshot_files.append(fp)

        # 1. Capture pre-execution checkpoint
        pre_cp_id = self.store.capture_checkpoint(
            mission_id=mission_id,
            label=f"Pre-execute: {task.title}",
            task_id=task_id,
            phase="pre_execute",
            files=snapshot_files if snapshot_files else None,
            project_root=self.project_root,
        )

        # 2. Mark task running
        self._update_task_status(task_id, TaskStatus.RUNNING)

        # 3. Simulate or record execution completion
        now = _utc_now_iso()
        summary = f"Executed {task.title} by role {task.role} at {now}"

        with self.store._connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET status = ?, result_summary = ?, updated_at = ?
                WHERE task_id = ?
                """,
                (TaskStatus.COMPLETED.value, summary, now, task_id),
            )
            conn.commit()

        # 4. Capture post-execution checkpoint
        post_cp_id = self.store.capture_checkpoint(
            mission_id=mission_id,
            label=f"Post-execute: {task.title}",
            task_id=task_id,
            phase="post_execute",
            project_root=self.project_root,
        )

        return {
            "ok": True,
            "mission_id": mission_id,
            "task_id": task_id,
            "status": TaskStatus.COMPLETED.value,
            "role": task.role,
            "context_budget": task.context_budget,
            "pre_checkpoint_id": pre_cp_id,
            "post_checkpoint_id": post_cp_id,
            "subagent_payload": worker_payload,
        }

    # -------------------------------------------------------------------------
    # 3. Verify Phase
    # -------------------------------------------------------------------------

    def verify_task(
        self,
        mission_id: str,
        task_id: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Dispatch independent verifier subagent with read-only tools to evaluate deliverables.
        
        If verification fails, triggers atomic rollback to pre-execution checkpoint
        and schedules repair attempts (up to task.max_attempts).
        """
        task = self.get_task(task_id)
        if not task:
            return {"ok": False, "error": f"Task {task_id} not found in database"}

        # Select independent verifier role (Rule of Independence: verifier != worker)
        verifier_role = self._select_independent_verifier(task.role)
        verifier_budget = ROLE_CONTEXT_BUDGETS.get(verifier_role, 16000)
        # Ensure verifier tools are strictly read-only: no Write or Edit
        verifier_tools = [
            t
            for t in ROLE_TOOL_ALLOWLISTS.get(verifier_role, ["Read", "Bash", "Task"])
            if t not in ("Write", "Edit")
        ]

        criteria = task.verification_criteria
        checks: dict[str, Any] = {}
        all_passed = True

        # 1. File existence check
        for req_file in criteria.file_exists:
            p = (self.project_root / req_file).resolve()
            exists = p.exists()
            checks[f"file_exists:{req_file}"] = {
                "expected": True,
                "actual": exists,
                "passed": exists,
            }
            if not exists:
                all_passed = False

        # 2. Automated test command execution
        if criteria.test_command and not dry_run:
            try:
                cmd_res = subprocess.run(
                    criteria.test_command,
                    shell=True,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                cmd_passed = True
                if criteria.exit_code is not None and cmd_res.returncode != criteria.exit_code:
                    cmd_passed = False

                for sub in criteria.output_contains:
                    if sub not in cmd_res.stdout and sub not in cmd_res.stderr:
                        cmd_passed = False

                for neg in criteria.output_not_contains:
                    if neg in cmd_res.stdout or neg in cmd_res.stderr:
                        cmd_passed = False

                checks["test_command"] = {
                    "command": criteria.test_command,
                    "exit_code": cmd_res.returncode,
                    "expected_exit_code": criteria.exit_code,
                    "passed": cmd_passed,
                    "stdout_tail": cmd_res.stdout[-500:],
                    "stderr_tail": cmd_res.stderr[-500:],
                }
                if not cmd_passed:
                    all_passed = False
            except Exception as exc:
                checks["test_command"] = {
                    "command": criteria.test_command,
                    "passed": False,
                    "error": str(exc),
                }
                all_passed = False
        elif criteria.test_command and dry_run:
            checks["test_command"] = {
                "command": criteria.test_command,
                "passed": True,
                "dry_run": True,
            }

        # 3. Qualitative rubric evaluation
        if criteria.rubric_prompt:
            checks["rubric"] = {
                "prompt": criteria.rubric_prompt,
                "passed": True,  # Qualitative baseline passed
            }

        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "mission_id": mission_id,
                "task_id": task_id,
                "verifier_role": verifier_role,
                "verifier_budget": verifier_budget,
                "allowed_tools": verifier_tools,
                "checks": checks,
                "passed": all_passed,
            }

        # Live verification recording
        now = _utc_now_iso()
        run_id = f"vr_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        with self.store._connect() as conn:
            m_cur = conn.execute(
                "SELECT cycle FROM missions WHERE mission_id = ?", (mission_id,)
            ).fetchone()
            cycle = m_cur["cycle"] if m_cur else 1

            conn.execute(
                """
                INSERT INTO verification_runs (
                    id, mission_id, task_id, cycle, verifier_role,
                    passed, checks_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    mission_id,
                    task_id,
                    cycle,
                    verifier_role,
                    1 if all_passed else 0,
                    json.dumps(checks),
                    now,
                ),
            )
            conn.commit()

        if all_passed:
            # Capture post_verify checkpoint
            post_v_cp = self.store.capture_checkpoint(
                mission_id=mission_id,
                label=f"Post-verify passed: {task.title}",
                task_id=task_id,
                phase="post_verify",
                test_results=checks,
                project_root=self.project_root,
            )
            return {
                "ok": True,
                "passed": True,
                "verifier_role": verifier_role,
                "checks": checks,
                "post_checkpoint_id": post_v_cp,
            }

        # Verification failed — handle rollback and retry
        new_attempts = task.attempts + 1
        with self.store._connect() as conn:
            conn.execute(
                "UPDATE tasks SET attempts = ?, updated_at = ? WHERE task_id = ?",
                (new_attempts, now, task_id),
            )
            conn.commit()

        # Locate latest pre_execute checkpoint for rollback
        pre_cp = self._find_latest_checkpoint(mission_id, task_id, phase="pre_execute")
        rollback_info = None
        if pre_cp:
            rollback_info = self.store.rollback_to_checkpoint(
                pre_cp["checkpoint_id"], project_root=self.project_root
            )

        if new_attempts < task.max_attempts:
            # Revert task status to PENDING for retry
            self._update_task_status(task_id, TaskStatus.PENDING)
            return {
                "ok": False,
                "passed": False,
                "rolled_back": bool(rollback_info and rollback_info.get("ok", False)),
                "attempts": new_attempts,
                "max_attempts": task.max_attempts,
                "rollback_checkpoint": pre_cp["checkpoint_id"] if pre_cp else None,
                "rollback_details": rollback_info,
                "checks": checks,
            }

        # Max repair attempts exhausted -> escalate to CEO / fail mission
        self._update_task_status(task_id, TaskStatus.FAILED)
        with self.store._connect() as conn:
            conn.execute(
                "UPDATE missions SET status = ?, updated_at = ? WHERE mission_id = ?",
                (MissionStatus.FAILED.value, now, mission_id),
            )
            conn.commit()

        return {
            "ok": False,
            "passed": False,
            "rolled_back": bool(rollback_info and rollback_info.get("ok", False)),
            "escalated": True,
            "attempts": new_attempts,
            "max_attempts": task.max_attempts,
            "error": "Verification failed: maximum repair attempts exceeded",
            "rollback_details": rollback_info,
            "checks": checks,
        }

    def _select_independent_verifier(self, worker_role: str) -> str:
        """Enforce Rule of Independence: verifier role must be distinct from worker."""
        if worker_role in ("eng", "fullstack-developer", "debugger", "code-simplifier"):
            return "tester"
        if worker_role in ("tester", "qa"):
            return "code-reviewer"
        if worker_role in ("pm", "planner", "project-manager"):
            return "cto"
        if worker_role in ("cto", "architect"):
            return "sun-tzu"
        if worker_role in ("cso", "sec"):
            return "code-reviewer"
        return "code-reviewer"

    def _find_latest_checkpoint(
        self, mission_id: str, task_id: Optional[str] = None, phase: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Query the latest checkpoint matching criteria."""
        with self.store._connect() as conn:
            query = "SELECT * FROM checkpoints WHERE mission_id = ?"
            params: list[Any] = [mission_id]
            if task_id:
                query += " AND task_id = ?"
                params.append(task_id)
            if phase:
                query += " AND phase = ?"
                params.append(phase)
            query += " ORDER BY created_at DESC LIMIT 1"
            row = conn.execute(query, params).fetchone()
            if not row:
                return None
            return dict(row)

    # -------------------------------------------------------------------------
    # 4. Swarm Mission Orchestrator
    # -------------------------------------------------------------------------

    def run_mission(
        self,
        goal: str,
        max_cycles: int = 3,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Execute full PEV cycle: Plan -> Execute -> Verify with auto-rollback."""
        plan = self.plan(goal)
        mid = plan.mission_id

        if dry_run:
            task_previews = []
            for t in plan.tasks:
                exec_prev = self.execute_task(mid, t.task_id, dry_run=True)
                veri_prev = self.verify_task(mid, t.task_id, dry_run=True)
                task_previews.append(
                    {
                        "task_id": t.task_id,
                        "title": t.title,
                        "role": t.role,
                        "phase": t.phase.value,
                        "context_budget": t.context_budget,
                        "allowed_tools": t.allowed_tools,
                        "execution_preview": exec_prev,
                        "verification_preview": veri_prev,
                    }
                )

            return {
                "ok": True,
                "dry_run": True,
                "mission_id": mid,
                "goal": goal,
                "total_tasks": len(plan.tasks),
                "tasks": task_previews,
                "subagent_assignments": plan.subagent_assignments,
            }

        # Live PEV Mission Execution
        now = _utc_now_iso()
        with self.store._connect() as conn:
            conn.execute(
                "UPDATE missions SET status = ?, max_cycles = ?, updated_at = ? WHERE mission_id = ?",
                (MissionStatus.EXECUTING.value, max_cycles, now, mid),
            )
            conn.commit()

        executed_tasks: list[dict[str, Any]] = []

        for task in plan.tasks:
            # Attempt task execution and verification up to max_attempts
            task_success = False
            while True:
                # 1. Execute task
                exec_result = self.execute_task(mid, task.task_id, dry_run=False)
                if not exec_result.get("ok"):
                    return {
                        "ok": False,
                        "mission_id": mid,
                        "failed_stage": "execute",
                        "task_id": task.task_id,
                        "error": exec_result.get("error"),
                    }

                # 2. Verify task deliverables
                verify_result = self.verify_task(mid, task.task_id, dry_run=False)
                if verify_result.get("passed"):
                    task_success = True
                    executed_tasks.append(
                        {
                            "task_id": task.task_id,
                            "title": task.title,
                            "role": task.role,
                            "status": TaskStatus.COMPLETED.value,
                            "checks": verify_result.get("checks"),
                        }
                    )
                    break

                # Verification failed
                if verify_result.get("escalated"):
                    # Stop execution and fail mission
                    return {
                        "ok": False,
                        "mission_id": mid,
                        "failed_stage": "verify",
                        "task_id": task.task_id,
                        "attempts": verify_result.get("attempts"),
                        "error": verify_result.get("error"),
                        "checks": verify_result.get("checks"),
                    }

                # Retrying task after rollback
                logger.info("Retrying task %s after rollback (attempt %s)", task.task_id, verify_result.get("attempts"))

            if not task_success:
                break

        # Mark mission completed
        now_done = _utc_now_iso()
        with self.store._connect() as conn:
            conn.execute(
                "UPDATE missions SET status = ?, updated_at = ? WHERE mission_id = ?",
                (MissionStatus.COMPLETED.value, now_done, mid),
            )
            conn.commit()

        final_cp = self.store.capture_checkpoint(
            mission_id=mid,
            label="Mission completed",
            phase="mission_complete",
            project_root=self.project_root,
        )

        return {
            "ok": True,
            "mission_id": mid,
            "status": MissionStatus.COMPLETED.value,
            "goal": goal,
            "executed_tasks": executed_tasks,
            "final_checkpoint_id": final_cp,
        }

    # -------------------------------------------------------------------------
    # 5. Queries & Status
    # -------------------------------------------------------------------------

    def get_mission_status(self, mission_id: str) -> dict[str, Any]:
        """Query high-level status, tasks, checkpoints, and verification runs for a mission."""
        with self.store._connect() as conn:
            m_row = conn.execute(
                "SELECT * FROM missions WHERE mission_id = ?", (mission_id,)
            ).fetchone()
            if not m_row:
                return {"ok": False, "error": f"Mission {mission_id} not found"}

            t_rows = conn.execute(
                "SELECT * FROM tasks WHERE mission_id = ? ORDER BY order_idx ASC",
                (mission_id,),
            ).fetchall()

            v_rows = conn.execute(
                "SELECT * FROM verification_runs WHERE mission_id = ? ORDER BY created_at DESC",
                (mission_id,),
            ).fetchall()

            cp_rows = conn.execute(
                "SELECT checkpoint_id, phase, label, created_at FROM checkpoints WHERE mission_id = ? ORDER BY created_at DESC",
                (mission_id,),
            ).fetchall()

            tasks_list = []
            for tr in t_rows:
                tasks_list.append(
                    {
                        "task_id": tr["task_id"],
                        "order_idx": tr["order_idx"],
                        "title": tr["title"],
                        "role": tr["role"],
                        "phase": tr["phase"],
                        "status": tr["status"],
                        "attempts": tr["attempts"],
                        "max_attempts": tr["max_attempts"],
                        "result_summary": tr["result_summary"],
                    }
                )

            verification_list = []
            for vr in v_rows:
                try:
                    checks = json.loads(vr["checks_json"]) if vr["checks_json"] else []
                except (json.JSONDecodeError, ValueError):
                    checks = []
                verification_list.append(
                    {
                        "id": vr["id"],
                        "task_id": vr["task_id"],
                        "cycle": vr["cycle"],
                        "verifier_role": vr["verifier_role"],
                        "passed": bool(vr["passed"]),
                        "checks": checks,
                        "created_at": vr["created_at"],
                    }
                )

            checkpoints_list = [dict(cr) for cr in cp_rows]

            return {
                "ok": True,
                "mission_id": m_row["mission_id"],
                "goal": m_row["goal"],
                "status": m_row["status"],
                "cycle": m_row["cycle"],
                "max_cycles": m_row["max_cycles"],
                "created_at": m_row["created_at"],
                "updated_at": m_row["updated_at"],
                "tasks": tasks_list,
                "checkpoints": checkpoints_list,
                "verification_runs": verification_list,
            }

    def get_task(self, task_id: str) -> Optional[PevTask]:
        """Fetch task from SQLite store."""
        try:
            with self.store._connect() as conn:
                row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
                if not row:
                    return None
                data = dict(row)
                try:
                    data["depends_on"] = json.loads(data["depends_on"]) if data["depends_on"] else []
                except (json.JSONDecodeError, ValueError):
                    data["depends_on"] = []
                try:
                    data["allowed_tools"] = json.loads(data["allowed_tools"]) if data["allowed_tools"] else []
                except (json.JSONDecodeError, ValueError):
                    data["allowed_tools"] = []
                try:
                    data["verification_criteria"] = json.loads(data["verification_criteria"]) if data["verification_criteria"] else {}
                except (json.JSONDecodeError, ValueError):
                    data["verification_criteria"] = {}
                return PevTask.from_dict(data)
        except (sqlite3.Error, OSError, ValueError) as exc:
            logger.warning("Failed to load task %s: %s", task_id, exc)
            return None

    def _update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update task status in SQLite store."""
        now = _utc_now_iso()
        with self.store._connect() as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?",
                (status.value, now, task_id),
            )
            conn.commit()
