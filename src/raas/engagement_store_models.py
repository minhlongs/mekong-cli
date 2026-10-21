# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Engagement event data models, DDL, and date helper for retention tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

_DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"

_DDL = """
CREATE TABLE IF NOT EXISTS engagement_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    event_count  INTEGER DEFAULT 1,
    event_date   TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    UNIQUE(user_id, event_type, event_date)
);
CREATE INDEX IF NOT EXISTS idx_engagement_user_date ON engagement_events(user_id, event_date);
CREATE INDEX IF NOT EXISTS idx_engagement_workspace ON engagement_events(workspace_id);

CREATE TABLE IF NOT EXISTS user_streaks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          TEXT NOT NULL UNIQUE,
    current_streak   INTEGER DEFAULT 0,
    longest_streak   INTEGER DEFAULT 0,
    last_active_date TEXT,
    streak_started   TEXT,
    grace_used       INTEGER DEFAULT 0,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_health_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id  TEXT NOT NULL,
    score         INTEGER NOT NULL,
    grade         TEXT NOT NULL,
    components    TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    UNIQUE(workspace_id, snapshot_date)
);
CREATE INDEX IF NOT EXISTS idx_health_ws_date ON workspace_health_snapshots(workspace_id, snapshot_date);

CREATE TABLE IF NOT EXISTS nudge_dismissals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL,
    nudge_id     TEXT NOT NULL,
    dismissed_at TEXT NOT NULL,
    reason       TEXT DEFAULT 'manual',
    UNIQUE(user_id, nudge_id)
);
CREATE INDEX IF NOT EXISTS idx_nudge_user ON nudge_dismissals(user_id);
"""


@dataclass
class EngagementEvent:
    user_id: str
    workspace_id: str
    event_type: str
    event_count: int
    event_date: str
    created_at: str


@dataclass
class DailyActivity:
    event_date: str
    total_events: int
    event_types: List[str] = field(default_factory=list)


@dataclass
class StreakData:
    user_id: str
    current_streak: int
    longest_streak: int
    last_active_date: Optional[str]
    streak_started: Optional[str]
    grace_used: int


@dataclass
class HealthSnapshot:
    workspace_id: str
    score: int
    grade: str
    components: Dict[str, float]
    snapshot_date: str


def _cutoff_date(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
