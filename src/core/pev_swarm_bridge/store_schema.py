"""SQLite schema initialization and connection management for CheckpointStore."""

from __future__ import annotations

from pathlib import Path
import sqlite3

SCHEMA_DDL = """
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


class CheckpointStoreBase:
    """Base SQLite connection and schema manager for CheckpointStore."""

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
            conn.executescript(SCHEMA_DDL)
            conn.commit()
