# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Onboarding funnel data models and SQLite schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

_DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"

_DDL = """
-- Onboarding funnel events table
CREATE TABLE IF NOT EXISTS onboarding_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT NOT NULL,
    workspace_id    TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    event_data      TEXT DEFAULT '{}',
    created_at      TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_onboarding_user ON onboarding_events(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_workspace ON onboarding_events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_type ON onboarding_events(event_type);
CREATE INDEX IF NOT EXISTS idx_onboarding_created_at ON onboarding_events(created_at);
"""

FUNNEL_STEPS = [
    "signup_started",
    "workspace_created",
    "llm_configured",
    "polar_connected",
    "first_mission_started",
    "first_mission_completed",
]


@dataclass
class FunnelStep:
    """A single step in the onboarding funnel."""

    step_name: str
    step_order: int
    count: int
    unique_users: int
    conversion_rate: float = 0.0


@dataclass
class FunnelData:
    """Complete funnel data with all steps and metrics."""

    period_start: str
    period_end: str
    total_days: int
    steps: List[FunnelStep] = field(default_factory=list)
    overall_conversion_rate: float = 0.0
