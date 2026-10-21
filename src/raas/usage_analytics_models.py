# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and default database path for RaaS per-tenant usage analytics."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

_DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"


@dataclass
class DailyUsage:
    """Credits consumed per day for a tenant."""

    date: str  # YYYY-MM-DD
    credits_used: int
    missions_count: int
    missions_completed: int
    missions_failed: int


@dataclass
class TenantUsageSummary:
    """Aggregated usage summary for a tenant."""

    tenant_id: str
    period_start: str
    period_end: str
    total_credits_used: int
    total_missions: int
    missions_completed: int
    missions_failed: int
    daily_breakdown: List[DailyUsage] = field(default_factory=list)
    complexity_breakdown: Dict[str, int] = field(default_factory=dict)
