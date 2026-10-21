# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Free Tier Usage Schema and Data Models — ROIaaS Phase 6."""

from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path.home() / ".mekong" / "raas" / "free_tier_analytics.db"


@dataclass
class FreeTierUsage:
    """Free tier usage record."""
    key_id: str
    command: str
    command_cost: int = 1
    email: str = ""
    session_id: str = ""
    created_at: str = ""
    metadata: str = "{}"


_DDL = """
CREATE TABLE IF NOT EXISTS free_tier_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id          TEXT NOT NULL,
    email           TEXT,
    command         TEXT NOT NULL,
    command_cost    INTEGER DEFAULT 1,
    session_id      TEXT,
    created_at      TEXT NOT NULL,
    metadata        TEXT DEFAULT '{}',
    synced          BOOLEAN DEFAULT FALSE,
    sync_attempted  INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ftu_key_id
    ON free_tier_usage (key_id);
CREATE INDEX IF NOT EXISTS idx_ftu_created_at
    ON free_tier_usage (created_at);
CREATE INDEX IF NOT EXISTS idx_ftu_synced
    ON free_tier_usage (synced);

CREATE TABLE IF NOT EXISTS free_tier_sessions (
    session_id      TEXT PRIMARY KEY,
    key_id          TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    last_activity   TEXT,
    commands_count  INTEGER DEFAULT 0,
    total_credits   INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_fts_key_id
    ON free_tier_sessions (key_id);
"""
