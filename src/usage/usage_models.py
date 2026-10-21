# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage Tracker Models and Constants."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Dict, List

from src.core.anomaly_detector import AnomalyCategory

FREE_TIER_LIMITS: Dict[str, int] = {
    "commands_per_day": 10,
    "agents_per_day": 5,
    "pipelines_per_day": 3,
}

MAX_FUTURE_DRIFT: timedelta = timedelta(minutes=5)
WAL_CHECKPOINT_INTERVAL: int = 100
SQLITE_RETRY_MAX: int = 3
SQLITE_RETRY_BASE_DELAY: float = 0.05


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


@dataclass
class DailyUsage:
    """Daily usage summary."""

    date: str
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
