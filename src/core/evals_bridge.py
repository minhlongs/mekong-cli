# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/evals_bridge.py — Continuous Learning & Offline Evals Bridge.

Provides pure-SQLite persistent telemetry for agent/PEV mission execution,
statistical evaluation queries, failure pattern clustering, and automated
improvement recommendations.

Features:
- 100% provider-neutral: standard library only (sqlite3, json, math, time).
- Default DB path: .mekong/evals.db (configurable via MEKONG_EVALS_DB_PATH).
- Thread-safe WAL mode with automatic idempotent schema creation.
- Failure pattern clustering: maps raw errors into actionable diagnostic categories.
- Evaluation metrics: success rates, p95 durations, average token & credit usage.
- Safe write-through: recording never crashes caller execution.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default database location in .mekong/evals.db
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = _PROJECT_ROOT / ".mekong" / "evals.db"

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS mission_evals (
    mission_id       TEXT    NOT NULL PRIMARY KEY,
    agent_id         TEXT    NOT NULL,
    goal             TEXT    NOT NULL,
    duration_ms      INTEGER NOT NULL DEFAULT 0,
    credits_used     REAL    NOT NULL DEFAULT 0.0,
    success          INTEGER NOT NULL DEFAULT 0,
    failure_reason   TEXT    NOT NULL DEFAULT '',
    tool_calls_count INTEGER NOT NULL DEFAULT 0,
    tokens_used      INTEGER NOT NULL DEFAULT 0,
    ts               TEXT    NOT NULL,
    metadata_json    TEXT    NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_evals_agent_ts ON mission_evals (agent_id, ts);
CREATE INDEX IF NOT EXISTS idx_evals_success ON mission_evals (success);
"""


@dataclass
class MissionEvalRecord:
    """Record of a single mission execution for evaluation."""

    mission_id: str
    agent_id: str
    goal: str
    duration_ms: int = 0
    credits_used: float = 0.0
    success: bool = True
    failure_reason: str = ""
    tool_calls_count: int = 0
    tokens_used: int = 0
    ts: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["success"] = bool(self.success)
        return d


def get_evals_db_path() -> Path:
    """Return the configured path to the evals SQLite database."""
    env_path = os.environ.get("MEKONG_EVALS_DB_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_DB


def _connect(db_path: Path) -> sqlite3.Connection:
    """Open or create the SQLite connection with WAL mode and schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    return conn


def record_mission_eval(
    mission_id: str,
    agent_id: str,
    goal: str,
    duration_ms: int = 0,
    credits_used: float = 0.0,
    success: bool = True,
    failure_reason: str = "",
    tool_calls_count: int = 0,
    tokens_used: int = 0,
    metadata: Optional[dict[str, Any]] = None,
    db_path: Optional[Path] = None,
) -> bool:
    """
    Safely record a mission evaluation event into SQLite.

    Returns True on success, False on failure. Never raises.
    """
    path = db_path or get_evals_db_path()
    try:
        conn = _connect(path)
        meta_str = json.dumps(metadata or {})
        ts_now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        conn.execute(
            """
            INSERT OR REPLACE INTO mission_evals (
                mission_id, agent_id, goal, duration_ms, credits_used,
                success, failure_reason, tool_calls_count, tokens_used,
                ts, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(mission_id),
                str(agent_id),
                str(goal),
                int(duration_ms),
                float(credits_used),
                1 if success else 0,
                str(failure_reason or ""),
                int(tool_calls_count),
                int(tokens_used),
                ts_now,
                meta_str,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        logger.warning("Failed to record mission eval in %s: %s", path, exc)
        return False


def classify_failure_reason(reason: str) -> str:
    """
    Heuristically categorize raw failure strings into diagnostic failure patterns.
    """
    if not reason:
        return "Unknown"
    norm = reason.lower()

    if any(k in norm for k in ["timeout", "timed out", "deadline", "timedout"]):
        return "Timeout"
    if any(k in norm for k in ["syntax", "typeerror", "syntaxerror", "indentationerror", "lint", "invalid syntax"]):
        return "Syntax / Type Error"
    if any(k in norm for k in ["not found", "nosuchfile", "filenotfound", "modulenotfound", "importerror", "no such file"]):
        return "Missing Dependency / File"
    if any(k in norm for k in ["permission", "forbidden", "unauthorized", "denied", "halted", "governance"]):
        return "Permission / Governance"
    if any(k in norm for k in ["context budget", "token limit", "context limit", "max tokens", "token budget", "context overflow"]):
        return "Context Budget Exceeded"
    if any(k in norm for k in ["rate limit", "quota", "429", "too many requests"]):
        return "Rate Limiting"
    if any(k in norm for k in ["tool error", "tool failure", "mcp error", "tool call failed", "tool execution"]):
        return "Tool Failure"
    if any(k in norm for k in ["assertionerror", "verification failed", "test failed", "verify error"]):
        return "Verification / Test Failure"

    return "General Execution Error"


def cluster_failures(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Cluster a list of raw failure dictionaries into categories with counts and percentages.
    """
    if not failures:
        return []

    total_failures = len(failures)
    counts: dict[str, list[str]] = {}

    for item in failures:
        reason = item.get("failure_reason", "")
        cat = classify_failure_reason(reason)
        counts.setdefault(cat, []).append(reason)

    clusters: list[dict[str, Any]] = []
    for cat, reasons in counts.items():
        cnt = len(reasons)
        sample = list(dict.fromkeys(r for r in reasons if r))[:3]
        clusters.append({
            "category": cat,
            "count": cnt,
            "percentage": round((cnt / total_failures) * 100, 1),
            "sample_reasons": sample,
        })

    # Sort clusters descending by count
    clusters.sort(key=lambda x: x["count"], reverse=True)
    return clusters


def generate_recommendations(
    metrics: dict[str, Any],
    clusters: list[dict[str, Any]],
) -> list[str]:
    """
    Generate actionable advice based on evaluation metrics and failure clusters.
    """
    recommendations: list[str] = []
    total = metrics.get("total_missions", 0)
    success_rate = metrics.get("success_rate", 1.0)

    if total == 0:
        return ["No mission telemetry recorded yet. Run goals or PEV missions to accumulate data."]

    cluster_map = {c["category"]: c["percentage"] for c in clusters}

    if cluster_map.get("Timeout", 0) >= 15.0:
        recommendations.append(
            "High timeout rate detected (>= 15%): Decompose complex goals into subagent tasks or raise step execution deadlines."
        )
    if cluster_map.get("Syntax / Type Error", 0) >= 15.0:
        recommendations.append(
            "High syntax/lint failure rate: Add a pre-flight linting and typecheck step into recipe workflows."
        )
    if cluster_map.get("Missing Dependency / File", 0) >= 15.0:
        recommendations.append(
            "Missing files/dependencies detected: Ensure project structure is verified with `mekong init` before execution."
        )
    if cluster_map.get("Context Budget Exceeded", 0) >= 10.0:
        recommendations.append(
            "Context budget limit exceeded: Enable context compression or prune unnecessary file reads in subagent prompts."
        )
    if cluster_map.get("Permission / Governance", 0) >= 10.0:
        recommendations.append(
            "Governance/permission rejections: Review `.claude/settings.json` allowlists or apply `MEKONG_CEO_OVERRIDE=1` for authorized operations."
        )
    if cluster_map.get("Tool Failure", 0) >= 15.0:
        recommendations.append(
            "Tool execution failures: Verify MCP stdio connection and parameter schemas with `scripts/mcp_server.py`."
        )
    if cluster_map.get("Verification / Test Failure", 0) >= 15.0:
        recommendations.append(
            "Verification gates failing: Tighten task specifications and run unit tests iteratively before completion."
        )

    if success_rate < 0.75:
        recommendations.append(
            f"Overall success rate is {round(success_rate * 100, 1)}% (< 75%): Run `mekong evolve` to evolve failure-prone recipes."
        )
    elif success_rate >= 0.90 and total >= 5:
        recommendations.append(
            "Mission success rate is high (>= 90%): Telemetry indicates stable execution across layer agents."
        )

    if not recommendations:
        recommendations.append("Performance within nominal bounds. No immediate interventions required.")

    return recommendations


def query_evals(
    agent_id: str = "all",
    window_days: int = 7,
    limit: int = 100,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Run statistical offline evaluation queries against SQLite.

    Args:
        agent_id: Agent identifier filter, or 'all' for all agents.
        window_days: Lookback window in days (default 7).
        limit: Max recent missions to return.
        db_path: Optional override for database path.

    Returns:
        Structured evaluation metrics dict.
    """
    path = db_path or get_evals_db_path()

    empty_result = {
        "ok": True,
        "agent_id": agent_id,
        "window_days": window_days,
        "total_missions": 0,
        "successful_missions": 0,
        "failed_missions": 0,
        "success_rate": 0.0,
        "success_rate_pct": 0.0,
        "p95_duration_ms": 0,
        "avg_duration_ms": 0.0,
        "avg_credits": 0.0,
        "total_credits": 0.0,
        "avg_tokens": 0,
        "total_tokens": 0,
        "db_path": str(path),
        "failure_clusters": [],
        "recommendations": ["No missions found for the specified lookback window."],
        "recent_missions": [],
    }

    if not path.exists():
        return empty_result

    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row

        date_expr = f"datetime(ts) >= datetime('now', '-{int(window_days)} days')"
        agent_filter = agent_id if agent_id and agent_id != "all" else None
        agent_expr = "agent_id = ?" if agent_filter else "1=1"
        params: list[Any] = [agent_filter] if agent_filter else []

        where_clause = f"WHERE {date_expr} AND {agent_expr}"

        # 1. Summary aggregations
        summary_query = f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success_cnt,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS failed_cnt,
            AVG(CAST(duration_ms AS REAL)) AS avg_dur,
            AVG(credits_used) AS avg_cred,
            SUM(credits_used) AS total_cred,
            AVG(CAST(tokens_used AS REAL)) AS avg_tok,
            SUM(tokens_used) AS total_tok
        FROM mission_evals
        {where_clause}
        """
        row = conn.execute(summary_query, params).fetchone()
        total = int(row["total"] or 0)

        if total == 0:
            conn.close()
            return empty_result

        success_cnt = int(row["success_cnt"] or 0)
        failed_cnt = int(row["failed_cnt"] or 0)
        success_rate = (success_cnt / total) if total > 0 else 0.0

        # 2. P95 calculation
        dur_query = f"""
        SELECT duration_ms
        FROM mission_evals
        {where_clause}
        ORDER BY duration_ms ASC
        """
        dur_rows = [int(r["duration_ms"]) for r in conn.execute(dur_query, params).fetchall()]
        p95_ms = 0
        if dur_rows:
            p95_idx = int(math.ceil(0.95 * len(dur_rows))) - 1
            p95_idx = max(0, min(p95_idx, len(dur_rows) - 1))
            p95_ms = dur_rows[p95_idx]

        # 3. Failures for clustering
        fail_query = f"""
        SELECT mission_id, agent_id, failure_reason
        FROM mission_evals
        {where_clause} AND success = 0
        """
        fail_rows = [dict(r) for r in conn.execute(fail_query, params).fetchall()]
        clusters = cluster_failures(fail_rows)

        # 4. Recent missions
        recent_query = f"""
        SELECT mission_id, agent_id, goal, duration_ms, credits_used,
               success, failure_reason, tool_calls_count, tokens_used, ts
        FROM mission_evals
        {where_clause}
        ORDER BY ts DESC
        LIMIT ?
        """
        recent_params = params + [int(limit)]
        recent_rows = []
        for r in conn.execute(recent_query, recent_params).fetchall():
            rd = dict(r)
            rd["success"] = bool(rd["success"])
            recent_rows.append(rd)

        conn.close()

        metrics = {
            "ok": True,
            "agent_id": agent_id,
            "window_days": window_days,
            "total_missions": total,
            "successful_missions": success_cnt,
            "failed_missions": failed_cnt,
            "success_rate": round(success_rate, 4),
            "success_rate_pct": round(success_rate * 100, 1),
            "p95_duration_ms": p95_ms,
            "avg_duration_ms": round(float(row["avg_dur"] or 0.0), 1),
            "avg_credits": round(float(row["avg_cred"] or 0.0), 2),
            "total_credits": round(float(row["total_cred"] or 0.0), 2),
            "avg_tokens": int(round(float(row["avg_tok"] or 0.0))),
            "total_tokens": int(row["total_tok"] or 0),
            "db_path": str(path),
            "failure_clusters": clusters,
            "recent_missions": recent_rows,
        }

        metrics["recommendations"] = generate_recommendations(metrics, clusters)
        return metrics

    except Exception as exc:
        logger.error("Error querying evals from %s: %s", path, exc)
        return {
            "ok": False,
            "error": str(exc),
            "db_path": str(path),
            "total_missions": 0,
        }


def clear_evals(db_path: Optional[Path] = None) -> bool:
    """Clear all mission evaluation records (primarily for testing)."""
    path = db_path or get_evals_db_path()
    if not path.exists():
        return True
    try:
        conn = sqlite3.connect(str(path))
        conn.execute("DELETE FROM mission_evals")
        conn.commit()
        conn.close()
        return True
    except Exception as exc:
        logger.warning("Failed to clear evals in %s: %s", path, exc)
        return False


__all__ = [
    "MissionEvalRecord",
    "get_evals_db_path",
    "record_mission_eval",
    "classify_failure_reason",
    "cluster_failures",
    "generate_recommendations",
    "query_evals",
    "clear_evals",
]
