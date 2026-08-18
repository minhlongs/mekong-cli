# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage Tracker — unified CLI usage tracking (SQLite + event bus + anomaly detection).

Tracks command invocations, agent calls, pipeline runs, API calls, model usage,
and LLM token consumption per license key. Provides free tier enforcement and
real-time anomaly detection.

Storage: SQLite with WAL mode at ~/.mekong/raas/tenants.db

Usage:
    # SQLite-backed tracker (command/agent/pipeline)
    from src.usage.usage_tracker import UsageTracker
    tracker = UsageTracker()
    tracker.track_command("license-123", "cook")
    usage = tracker.get_daily_usage("license-123")
    tracker.close()

    # Event-based tracker (API/agent/token/LLM with anomaly detection)
    from src.usage import get_metering
    metering = get_metering()
    metering.record_api_call("chat/completions")
    metering.record_token_usage("qwen3.5-plus", 1500, 500)
    summary = metering.get_usage_summary()
"""

from __future__ import annotations

import enum
import json
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Logging ────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── Free tier limits ───────────────────────────────────────────────────────

FREE_TIER_LIMITS: Dict[str, int] = {
    "commands_per_day": 10,
    "agents_per_day": 5,
    "pipelines_per_day": 3,
}

# ── WAL / SQLite operational constants ─────────────────────────────────────

MAX_FUTURE_DRIFT: timedelta = timedelta(minutes=5)
WAL_CHECKPOINT_INTERVAL: int = 100
SQLITE_RETRY_MAX: int = 3
SQLITE_RETRY_BASE_DELAY: float = 0.05  # seconds

# ── Canonical imports (do NOT reimplement — import from canonical modules) ─

from src.core.anomaly_detector import (  # noqa: E402
    AnomalyCategory,
    AnomalyType,
    UsageAnomalyDetector,
    get_detector as _get_detector,
)
from src.core.event_bus import (  # noqa: E402
    EventBus,
    EventType,
    Subscriber,
    get_event_bus,
)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 1 — Usage Event Model (metering-specific, from original
#               src.core.usage_metering)
# ═══════════════════════════════════════════════════════════════════════════


class UsageEventType(str, enum.Enum):
    """Usage-related event types emitted by the metering layer."""

    API_CALL = "usage:api_call"
    AGENT_SPAWN = "usage:agent_spawn"
    MODEL_USAGE = "usage:model_usage"
    LLM_CALL = "usage:llm_call"
    TOKEN_USAGE = "usage:token_usage"
    ANOMALY_DETECTED = "usage:anomaly_detected"


@dataclass
class UsageEvent:
    """A single usage event emitted by the event-bus metering layer."""

    event_type: UsageEventType
    category: AnomalyCategory
    metric: str
    value: float
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_type": self.event_type.value,
            "category": self.category.value,
            "metric": self.metric,
            "value": self.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 2 — SQLite-backed Usage Tracker (original UsageTracker)
# ═══════════════════════════════════════════════════════════════════════════


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

    Also exposes event-bus metering methods (record_api_call, record_llm_call,
    etc.) via ``_UsageMeteringMixin`` injected into the class at module load.
    """

    SCHEMA_VERSION: int = 1

    def __init__(
        self,
        db_path: Optional[Path] = None,
        baseline_file: Optional[str] = None,
    ) -> None:
        """Initialize usage tracker with schema versioning and WAL mode.

        Args:
            db_path: Optional database path override for testing.
            baseline_file: Optional path to the anomaly-detection baseline file.
                Passed through to the detector on first metering use.
        """
        if db_path is None:
            db_path = Path.home() / ".mekong" / "raas" / "tenants.db"
        self._db_path = Path(db_path)
        self._baseline_file = baseline_file
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self._db_path), timeout=10, check_same_thread=False
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.row_factory = sqlite3.Row
        self._op_counter: int = 0
        self._lock = threading.Lock()
        self._init_schema_version_table()
        self._run_migrations()
        self._init_tables()

    # ── Schema Versioning ─────────────────────────────────────────────────

    def _init_schema_version_table(self) -> None:
        """Create schema version tracking table if it does not exist."""
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS _schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )
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
        self._conn.executescript(
            """CREATE TABLE IF NOT EXISTS usage_events (
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
                ON usage_events(event_type);"""
        )
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
        """Execute SQL with exponential backoff retry on database lock."""
        last_error: Optional[sqlite3.OperationalError] = None
        for attempt in range(SQLITE_RETRY_MAX):
            try:
                return self._conn.execute(sql, params)
            except sqlite3.OperationalError as e:
                if "locked" not in str(e).lower():
                    raise
                last_error = e
                time.sleep(SQLITE_RETRY_BASE_DELAY * (2 ** attempt))
        raise last_error  # type: ignore[misc]

    # ── Timestamp Validation ──────────────────────────────────────────────

    def _validate_timestamp(self, timestamp: str) -> None:
        """Reject timestamps more than MAX_FUTURE_DRIFT in the future."""
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
            raise
        except Exception:
            raise ValueError(f"Invalid timestamp format: {timestamp}")

    # ── Table Init ────────────────────────────────────────────────────────

    def _init_tables(self) -> None:
        """Create usage_events table and indexes (idempotent)."""
        self._conn.executescript(
            """CREATE TABLE IF NOT EXISTS usage_events (
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
                ON usage_events(event_type);"""
        )
        self._conn.commit()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _hash_license_key(self, license_key: str) -> str:
        """Hash license key for privacy."""
        return __import__("hashlib").sha256(license_key.encode()).hexdigest()

    # ── Event Tracking (SQLite — command / agent / pipeline) ───────────────

    async def track_command(
        self,
        license_key: Optional[str] = None,
        command: Optional[str] = None,
        key_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a CLI command execution.

        Supports both calling conventions:
        - Legacy positional: ``track_command(license_key, command)``
        - Decorator keyword: ``track_command(key_id=..., command=...)``
        """
        resolved_license = key_id or license_key or (
            __import__("os").environ.get("RAAS_LICENSE_KEY") or ""
        )
        resolved_command = command or ""
        self._track_event(resolved_license, "command", resolved_command, metadata=metadata)

    def track_agent_call(
        self,
        license_key: str,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track an agent invocation."""
        self._track_event(license_key, "agent_call", agent_name, metadata=metadata)

    def track_pipeline_run(
        self,
        license_key: str,
        pipeline_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a pipeline execution."""
        self._track_event(license_key, "pipeline_run", pipeline_type, metadata=metadata)

    async def track_feature(
        self,
        feature_tag: str,
        license_key: Optional[str] = None,
        key_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a feature usage event (called by ``@track_usage`` decorator)."""
        resolved_license = license_key or key_id or (
            __import__("os").environ.get("RAAS_LICENSE_KEY") or ""
        )
        self._track_event(resolved_license, "feature", feature_tag, metadata=metadata)

    def _track_event(
        self,
        license_key: str,
        event_type: str,
        event_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert a usage event with dedup, future-timestamp check, retry, and WAL."""
        event_id = __import__("uuid").uuid4().hex
        timestamp = datetime.now(timezone.utc).isoformat()

        # Deduplication: skip if same (license, type, name) within last minute
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        existing = self._execute_with_retry(
            "SELECT id FROM usage_events "
            "WHERE license_key_hash = ? AND event_type = ? AND event_name = ? "
            "AND timestamp > ? LIMIT 1",
            (self._hash_license_key(license_key), event_type, event_name, cutoff),
        ).fetchone()
        if existing:
            return  # silent dedup

        self._validate_timestamp(timestamp)
        self._execute_with_retry(
            """INSERT INTO usage_events
            (id, license_key_hash, event_type, event_name, units, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                self._hash_license_key(license_key),
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
            """SELECT event_name, SUM(units) as count FROM usage_events
            WHERE license_key_hash = ? AND event_type = 'command'
            AND substr(timestamp, 1, 10) = ? GROUP BY event_name""",
            (license_key_hash, target_date),
        ).fetchall()

        agent_rows = self._conn.execute(
            """SELECT event_name, SUM(units) as count FROM usage_events
            WHERE license_key_hash = ? AND event_type = 'agent_call'
            AND substr(timestamp, 1, 10) = ? GROUP BY event_name""",
            (license_key_hash, target_date),
        ).fetchall()

        pipeline_row = self._conn.execute(
            """SELECT SUM(units) as count FROM usage_events
            WHERE license_key_hash = ? AND event_type = 'pipeline_run'
            AND substr(timestamp, 1, 10) = ?""",
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
        today = datetime.now(timezone.utc)
        daily_reports: List[DailyUsage] = []
        total_commands = total_agents = total_pipelines = 0
        for i in range(days):
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.get_daily_usage(license_key, date_str)
            daily_reports.append(daily)
            total_commands += daily.total_commands
            total_agents += daily.total_agents
            total_pipelines += daily.total_pipelines

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


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 3 — Event-bus Metring Mixin
#
#  Adds record_api_call, record_agent_spawn, record_model_usage,
#  record_llm_call, record_token_usage, get_usage_summary, reset_counters
#  to UsageTracker so a single tracker provides both SQLite persistence
#  and event-bus + anomaly detection.
# ═══════════════════════════════════════════════════════════════════════════


class _UsageMeteringMixin:
    """Mixin adding event-bus + anomaly detection to UsageTracker.

    Does NOT define __init__ — UsageTracker's own initializer is preserved.
    Metering state is lazily initialized via _ensure_metering on first use.
    """

    def _ensure_metering(self) -> None:
        """Lazily set up event bus + anomaly detector + counters."""
        if hasattr(self, "_metering_ready"):
            return
        self._event_bus: EventBus = get_event_bus()
        self._detector: UsageAnomalyDetector = _get_detector(
            getattr(self, "_baseline_file", None)
        )
        self._api_call_count: int = 0
        self._agent_spawn_count: int = 0
        self._llm_call_count: int = 0
        self._total_input_tokens: int = 0
        self._total_output_tokens: int = 0
        self._usage_subscribers: dict[UsageEventType, list[Subscriber]] = {}
        self._metering_ready = True

    def subscribe(self, event_type: UsageEventType, callback: Subscriber) -> None:
        """Register a callback for a usage event type.

        Delivers the originating :class:`UsageEvent` (which carries
        ``event_type``) to subscribers, independent of the underlying
        EventBus's ``Event`` shape.
        """
        self._ensure_metering()
        self._usage_subscribers.setdefault(event_type, []).append(callback)

    # -- Private helpers ---------------------------------------------------

    def _emit_usage_event(self, event: UsageEvent) -> None:
        """Emit to event bus and anomaly detector."""
        self._ensure_metering()
        self._event_bus.emit(
            EventType(event.event_type.value),
            event.to_dict(),
        )
        for callback in self._usage_subscribers.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.debug("Usage subscriber callback failed: %s", e)
        self._check_usage_anomaly(event.category, event.metric, event.value)

    def _check_usage_anomaly(
        self,
        category: AnomalyCategory,
        metric: str,
        value: float,
    ) -> Optional[AnomalyType]:
        """Run anomaly detection and emit if found.

        Returns the anomaly type if detected, or None.
        """
        anomaly = self._detector.detect_anomaly(category, metric, value)
        if anomaly:
            self._event_bus.emit(
                EventType.USAGE_ANOMALY_DETECTED,
                anomaly.to_event_data(),
            )
            logger.warning("Usage anomaly: %s", anomaly._generate_message())
            return anomaly.anomaly_type
        return None

    # -- Public recorders --------------------------------------------------

    def record_api_call(
        self,
        endpoint: str,
        method: str = "POST",
        status_code: int = 200,
    ) -> None:
        """Record an API call event."""
        self._ensure_metering()
        self._api_call_count += 1
        event = UsageEvent(
            event_type=UsageEventType.API_CALL,
            category=AnomalyCategory.API_CALLS,
            metric="requests",
            value=1.0,
            metadata={"endpoint": endpoint, "method": method, "status_code": status_code},
        )
        self._emit_usage_event(event)
        self._check_usage_anomaly(
            AnomalyCategory.API_CALLS, "requests", float(self._api_call_count)
        )

    def record_agent_spawn(
        self,
        agent_name: str,
        model: str = "",
        duration: float = 0.0,
    ) -> None:
        """Record an agent spawn event."""
        self._ensure_metering()
        self._agent_spawn_count += 1
        event = UsageEvent(
            event_type=UsageEventType.AGENT_SPAWN,
            category=AnomalyCategory.AGENT_SPAWNS,
            metric="spawns",
            value=1.0,
            metadata={"agent_name": agent_name, "model": model, "duration": duration},
        )
        self._emit_usage_event(event)
        self._check_usage_anomaly(
            AnomalyCategory.AGENT_SPAWNS, "spawns", float(self._agent_spawn_count)
        )

    def record_model_usage(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Record model usage (total token event)."""
        self._ensure_metering()
        total_tokens = input_tokens + output_tokens
        event = UsageEvent(
            event_type=UsageEventType.MODEL_USAGE,
            category=AnomalyCategory.MODEL_USAGE,
            metric=model,
            value=float(total_tokens),
            metadata={"input_tokens": input_tokens, "output_tokens": output_tokens, "cost": cost},
        )
        self._emit_usage_event(event)
        self._detector.record_metric(AnomalyCategory.MODEL_USAGE, model, float(total_tokens))
        self._check_usage_anomaly(AnomalyCategory.MODEL_USAGE, model, float(total_tokens))

    def record_llm_call(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration: float = 0.0,
    ) -> None:
        """Record an LLM call event."""
        self._ensure_metering()
        self._llm_call_count += 1
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        event = UsageEvent(
            event_type=UsageEventType.LLM_CALL,
            category=AnomalyCategory.LLM_CALLS,
            metric="calls",
            value=1.0,
            metadata={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration": duration,
            },
        )
        self._emit_usage_event(event)
        self._check_usage_anomaly(
            AnomalyCategory.LLM_CALLS, "calls", float(self._llm_call_count)
        )

    def record_token_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record token usage for a model."""
        self._ensure_metering()
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        total = input_tokens + output_tokens
        event = UsageEvent(
            event_type=UsageEventType.TOKEN_USAGE,
            category=AnomalyCategory.TOKEN_USAGE,
            metric=model,
            value=float(total),
            metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
        )
        self._emit_usage_event(event)
        self._detector.record_metric(AnomalyCategory.TOKEN_USAGE, model, float(total))
        self._check_usage_anomaly(AnomalyCategory.TOKEN_USAGE, model, float(total))

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary."""
        self._ensure_metering()
        return {
            "api_calls": self._api_call_count,
            "agent_spawns": self._agent_spawn_count,
            "llm_calls": self._llm_call_count,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "input_tokens": self._total_input_tokens,
            "output_tokens": self._total_output_tokens,
        }

    def reset_counters(self) -> None:
        """Reset aggregate counters."""
        self._ensure_metering()
        self._api_call_count = 0
        self._agent_spawn_count = 0
        self._llm_call_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def get_detector(self) -> UsageAnomalyDetector:
        """Get the underlying anomaly detector."""
        self._ensure_metering()
        return self._detector


# ── Mix in metering methods into UsageTracker ──────────────────────────────

for _name, _member in vars(_UsageMeteringMixin).items():
    if not _name.startswith("__") and callable(_member):
        setattr(UsageTracker, _name, _member)


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 4 — Module-level / Singleton Accessors
# ═══════════════════════════════════════════════════════════════════════════


# Thread-safe singleton for SQLite-backed tracker
_tracker: Optional[UsageTracker] = None
_tracker_lock = threading.Lock()



def get_tracker() -> UsageTracker:
    """Get or create the global SQLite-backed usage tracker (thread-safe)."""
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = UsageTracker()
    return _tracker


def get_rate_limiter() -> Any:
    """Get global rate limiter instance."""
    from src.auth.rate_limiter import get_rate_limiter as _get_rl  # noqa: F401

    return _get_rl()


# ── Event-bus metering singletons ─────────────────────────────────────────

_metering: Optional[UsageTracker] = None
_metering_lock = threading.Lock()


def get_metering() -> UsageTracker:
    """Get or create the global metering (UsageTracker) singleton."""
    global _metering
    if _metering is None:
        with _metering_lock:
            if _metering is None:
                _metering = UsageTracker()
    return _metering


def reset_metering() -> None:
    """Reset singleton metering (for testing)."""
    global _metering
    _metering = None


def reset_tracker() -> None:
    """Reset singleton tracker (for testing)."""
    global _tracker
    _tracker = None


# ── Backward-compat aliases ────────────────────────────────────────────────

UsageMetering = UsageTracker  # alias — UsageMetering → UsageTracker


__all__ = [
    # SQLite-backed
    "UsageTracker",
    "UsageMetering",
    "get_tracker",
    "get_rate_limiter",
    # Data classes
    "DailyUsage",
    "UsageReport",
    # Event model (metering-specific)
    "UsageEvent",
    "UsageEventType",
    # Event bus (re-exported from canonical module)
    "EventBus",
    "EventType",
    "get_event_bus",
    # Anomaly detection (re-exported from canonical module)
    "AnomalyCategory",
    "AnomalyType",
    "UsageAnomalyDetector",
    # Singletons
    "get_metering",
    "reset_metering",
    "reset_tracker",
]
