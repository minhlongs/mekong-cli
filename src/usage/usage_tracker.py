import json
"""Usage Tracker — SQLite-backed CLI command usage tracking.

Tracks command invocations, agent calls, and pipeline runs per license key.
Free tier enforcement: 10 commands/day, 5 agents/day, 3 pipelines/day.

Storage: SQLite with WAL mode at ~/.mekong/raas/tenants.db

Usage:
    from src.usage.usage_tracker import UsageTracker
    tracker = UsageTracker()
    tracker.track_command("license-123", "cook")
    usage = tracker.get_daily_usage("license-123")
"""

import sqlite3
import hashlib
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Generator, List, Optional, Any

# Free tier limits
FREE_TIER_LIMITS = {
    "commands_per_day": 10,
    "agents_per_day": 5,
    "pipelines_per_day": 3,
}

# Max future timestamp tolerance (5 minutes) — guards against clock skew
MAX_FUTURE_DRIFT = timedelta(minutes=5)

# WAL checkpoint after every N operations to bound WAL file size
WAL_CHECKPOINT_INTERVAL = 100

# Retry config for SQLite lock errors
SQLITE_RETRY_MAX = 3
SQLITE_RETRY_BASE_DELAY = 0.05  # seconds


@dataclass
class DailyUsage:
    """Daily usage summary."""
    date: str  # YYYY-MM-DD
    total_commands: int = 0
    total_agents: int = 0
    total_pipelines: int = 0
    command_breakdown: Dict[str, int] = field(default_factory=dict)
    agent_breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class UsageReport:
    """Multi-day usage report."""
    license_key_hash: str
    period_days: int
    total_commands: int
    total_agents: int
    total_pipelines: int
    daily_reports: List[DailyUsage] = field(default_factory=list)


class UsageTracker:
    """SQLite-backed usage tracker with schema migrations, WAL management,
    future-timestamp validation, and thread-safe singleton access.

    Attributes:
        SCHEMA_VERSION: Current schema version — bump when _init_tables schema changes.
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize usage tracker with schema versioning and WAL mode.

        Args:
            db_path: Optional database path override for testing.
        """
        if db_path is None:
            db_path = Path.home() / ".mekong" / "raas" / "tenants.db"

        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self._db_path),
            timeout=10,
            check_same_thread=False,
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.row_factory = sqlite3.Row
        self._op_counter = 0
        self._init_schema_version_table()
        self._run_migrations()
        self._init_tables()

    # ── Schema Versioning ─────────────────────────────────────────────────

    def _init_schema_version_table(self) -> None:
        """Create schema version tracking table if it does not exist."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS _schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    def _get_current_version(self) -> int:
        """Return the current schema version stored in the database."""
        row = self._conn.execute(
            "SELECT MAX(version) as v FROM _schema_version"
        ).fetchone()
        return row["v"] if row and row["v"] is not None else 0

    def _run_migrations(self) -> None:
        """Apply pending schema migrations based on current version."""
        current = self._get_current_version()
        if current < self.SCHEMA_VERSION:
            self._migrate_to_v1()
            self._conn.execute(
                "INSERT INTO _schema_version (version) VALUES (?)",
                (self.SCHEMA_VERSION,),
            )
            self._conn.commit()

    def _migrate_to_v1(self) -> None:
        """Initial schema — creates usage_events table and indexes."""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS usage_events (
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
                ON usage_events(event_type);
        """)
        self._conn.commit()

    # ── WAL Management ────────────────────────────────────────────────────

    def _wal_checkpoint(self) -> None:
        """Run a WAL truncate checkpoint to bound WAL file size."""
        try:
            self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.OperationalError:
            pass  # no-op if checkpoint cannot run right now

    def _maybe_checkpoint(self) -> None:
        """Run WAL checkpoint after every N operations."""
        with self._lock:
            self._op_counter += 1
            if self._op_counter >= WAL_CHECKPOINT_INTERVAL:
                self._op_counter = 0
                self._wal_checkpoint()

    # ── SQLite Retry ──────────────────────────────────────────────────────

    def _execute_with_retry(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL with exponential backoff retry on database lock.

        Args:
            sql: SQL statement to execute.
            params: Query parameters.

        Returns:
            sqlite3 Cursor on success.

        Raises:
            sqlite3.OperationalError: If all retries are exhausted.
        """
        last_error: Optional[sqlite3.OperationalError] = None
        for attempt in range(SQLITE_RETRY_MAX):
            try:
                return self._conn.execute(sql, params)
            except sqlite3.OperationalError as e:
                if "locked" not in str(e).lower():
                    raise
                last_error = e
                time.sleep(SQLITE_RETRY_BASE_DELAY * (2**attempt))
        raise last_error  # type: ignore[misc]

    # ── Timestamp Validation ──────────────────────────────────────────────

    def _validate_timestamp(self, timestamp: str) -> None:
        """Reject timestamps more than MAX_FUTURE_DRIFT in the future.

        Args:
            timestamp: ISO-format timestamp string to validate.

        Raises:
            ValueError: If timestamp is too far in the future.
        """
        try:
            event_time = datetime.fromisoformat(timestamp)
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if event_time > now + MAX_FUTURE_DRIFT:
                raise ValueError(
                    f"Event timestamp {timestamp} is too far in the future "
                    f"(max drift: {MAX_FUTURE_DRIFT.total_seconds()}s)"
                )
        except ValueError:
            raise  # re-raise our own validation error
        except Exception:
            raise ValueError(f"Invalid timestamp format: {timestamp}")

    # ── Table Init ────────────────────────────────────────────────────────

    def _init_tables(self) -> None:
        """Create usage_events table and indexes (idempotent, run inside migration)."""
        # Tables are created by _migrate_to_v1; this is a no-op safety net
        # for databases created before versioning was added.
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS usage_events (
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
                ON usage_events(event_type);
        """)
        self._conn.commit()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _hash_license_key(self, license_key: str) -> str:
        """Hash license key for privacy."""
        return hashlib.sha256(license_key.encode()).hexdigest()

    # ── Event Tracking ────────────────────────────────────────────────────

    def track_command(
        self,
        license_key: str,
        command: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a command execution."""
        self._track_event(license_key, "command", command, metadata=metadata)

    def track_agent_call(
        self,
        license_key: str,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track an agent call."""
        self._track_event(license_key, "agent_call", agent_name, metadata=metadata)

    def track_pipeline_run(
        self,
        license_key: str,
        pipeline_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a pipeline run."""
        self._track_event(license_key, "pipeline_run", pipeline_type, metadata=metadata)

    def _track_event(
        self,
        license_key: str,
        event_type: str,
        event_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert a usage event with dedup, future-timestamp check, retry, and WAL management."""
        import uuid

        license_key_hash = self._hash_license_key(license_key)
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Deduplication: skip if same (license, type, name) within last minute
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        existing = self._execute_with_retry(
            "SELECT id FROM usage_events "
            "WHERE license_key_hash = ? AND event_type = ? AND event_name = ? "
            "AND timestamp > ? LIMIT 1",
            (license_key_hash, event_type, event_name, cutoff),
        ).fetchone()
        if existing:
            return  # silent dedup — do not double-count rapid repeats

        # Guard against clock-skewed future timestamps
        self._validate_timestamp(timestamp)

        self._execute_with_retry(
            """
            INSERT INTO usage_events
                (id, license_key_hash, event_type, event_name, units, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                license_key_hash,
                event_type,
                event_name,
                1,
                json.dumps(metadata or {}) if metadata else "{}",
                timestamp,
            ),
        )
        self._conn.commit()
        self._maybe_checkpoint()

    # ── Query Methods ─────────────────────────────────────────────────────

    def get_daily_usage(
        self,
        license_key: str,
        date: Optional[str] = None,
    ) -> DailyUsage:
        """Get daily usage for a license key."""
        license_key_hash = self._hash_license_key(license_key)
        target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        cmd_rows = self._conn.execute(
            """
            SELECT event_name, SUM(units) as count
            FROM usage_events
            WHERE license_key_hash = ? AND event_type = 'command'
              AND substr(timestamp, 1, 10) = ?
            GROUP BY event_name
            """,
            (license_key_hash, target_date),
        ).fetchall()

        agent_rows = self._conn.execute(
            """
            SELECT event_name, SUM(units) as count
            FROM usage_events
            WHERE license_key_hash = ? AND event_type = 'agent_call'
              AND substr(timestamp, 1, 10) = ?
            GROUP BY event_name
            """,
            (license_key_hash, target_date),
        ).fetchall()

        pipeline_row = self._conn.execute(
            """
            SELECT SUM(units) as count
            FROM usage_events
            WHERE license_key_hash = ? AND event_type = 'pipeline_run'
              AND substr(timestamp, 1, 10) = ?
            """,
            (license_key_hash, target_date),
        ).fetchone()

        command_breakdown: Dict[str, int] = {}
        total_commands = 0
        for row in cmd_rows:
            command_breakdown[row["event_name"]] = row["count"] or 0
            total_commands += row["count"] or 0

        agent_breakdown: Dict[str, int] = {}
        total_agents = 0
        for row in agent_rows:
            agent_breakdown[row["event_name"]] = row["count"] or 0
            total_agents += row["count"] or 0

        return DailyUsage(
            date=target_date,
            total_commands=total_commands,
            total_agents=total_agents,
            total_pipelines=pipeline_row["count"] or 0 if pipeline_row else 0,
            command_breakdown=command_breakdown,
            agent_breakdown=agent_breakdown,
        )

    def is_free_tier_exceeded(
        self,
        license_key: str,
        date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check if free tier limit exceeded."""
        usage = self.get_daily_usage(license_key, date)

        if usage.total_commands >= FREE_TIER_LIMITS["commands_per_day"]:
            return {
                "exceeded": True,
                "reason": (
                    f"Command limit exceeded: "
                    f"{usage.total_commands}/{FREE_TIER_LIMITS['commands_per_day']}"
                ),
            }

        if usage.total_agents >= FREE_TIER_LIMITS["agents_per_day"]:
            return {
                "exceeded": True,
                "reason": (
                    f"Agent limit exceeded: "
                    f"{usage.total_agents}/{FREE_TIER_LIMITS['agents_per_day']}"
                ),
            }

        if usage.total_pipelines >= FREE_TIER_LIMITS["pipelines_per_day"]:
            return {
                "exceeded": True,
                "reason": (
                    f"Pipeline limit exceeded: "
                    f"{usage.total_pipelines}/{FREE_TIER_LIMITS['pipelines_per_day']}"
                ),
            }

        return {"exceeded": False}

    def get_free_tier_remaining(self, usage: DailyUsage) -> Dict[str, int]:
        """Get remaining free tier quota."""
        return {
            "commands_remaining": max(0, FREE_TIER_LIMITS["commands_per_day"] - usage.total_commands),
            "agents_remaining": max(0, FREE_TIER_LIMITS["agents_per_day"] - usage.total_agents),
            "pipelines_remaining": max(0, FREE_TIER_LIMITS["pipelines_per_day"] - usage.total_pipelines),
        }

    def get_usage_report(
        self,
        license_key: str,
        days: int = 7,
    ) -> UsageReport:
        """Get multi-day usage report."""
        from datetime import timedelta

        today = datetime.now(timezone.utc)
        daily_reports: List[DailyUsage] = []
        total_commands = 0
        total_agents = 0
        total_pipelines = 0

        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            daily_usage = self.get_daily_usage(license_key, date_str)
            daily_reports.append(daily_usage)
            total_commands += daily_usage.total_commands
            total_agents += daily_usage.total_agents
            total_pipelines += daily_usage.total_pipelines

        return UsageReport(
            license_key_hash=self._hash_license_key(license_key),
            period_days=days,
            total_commands=total_commands,
            total_agents=total_agents,
            total_pipelines=total_pipelines,
            daily_reports=daily_reports,
        )

    def close(self) -> None:
        """Close database connection, running a final WAL checkpoint."""
        try:
            self._wal_checkpoint()
        except Exception:
            pass
        self._conn.close()

    # ── Thread-safe Singleton ─────────────────────────────────────────────

    _tracker: Optional["UsageTracker"] = None
    _tracker_lock = threading.Lock()

    @classmethod
    def get_tracker(cls) -> "UsageTracker":
        """Return the global singleton UsageTracker instance (thread-safe)."""
        if cls._tracker is None:
            with cls._tracker_lock:
                if cls._tracker is None:
                    cls._tracker = cls()
        return cls._tracker


# ── Module-level backwards-compatible accessors ─────────────────────────────

def get_tracker() -> UsageTracker:
    """Get global usage tracker instance (thread-safe)."""
    return UsageTracker.get_tracker()


def get_rate_limiter():
    """Get global rate limiter instance."""
    from src.auth.rate_limiter import get_rate_limiter as _get_rl
    return _get_rl()
