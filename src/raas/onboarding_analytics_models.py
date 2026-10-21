# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models for RaaS onboarding funnel analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

_DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"


@dataclass
class ConversionRate:
    """Conversion rate between two funnel steps."""

    from_step: str
    to_step: str
    from_count: int
    to_count: int
    conversion_rate: float  # Percentage (0-100)
    drop_off_count: int
    drop_off_rate: float  # Percentage (0-100)


@dataclass
class DropOffPoint:
    """A point where users drop off from the funnel."""

    step_name: str
    step_order: int
    users_reached: int
    users_dropped: int
    drop_off_rate: float  # Percentage of users who dropped at this step
    drop_off_severity: str  # "critical" | "high" | "medium" | "low"


@dataclass
class TimeToComplete:
    """Time metrics for completing funnel steps."""

    step_name: str
    avg_hours: float
    median_hours: float
    min_hours: float
    max_hours: float
    sample_count: int


@dataclass
class CohortData:
    """Cohort analysis data."""

    period: str
    period_type: str  # "daily" | "weekly" | "monthly"
    users_started: int
    users_completed: int
    conversion_rate: float
    avg_time_to_complete_hours: float
    users_by_step: Dict[str, int] = field(default_factory=dict)
