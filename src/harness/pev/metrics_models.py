# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models for PEV Metrics Collector."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class StepMetrics:
    """Metrics for a single step execution."""

    step_order: int
    success: bool
    duration_ms: float
    retry_count: int = 0
    self_healed: bool = False
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class PipelineMetrics:
    """Aggregated metrics for a pipeline execution."""

    pipeline_id: str
    start_time: float = 0.0
    end_time: float = 0.0
    status: str = "running"
    steps: list[StepMetrics] = field(default_factory=list)
    total_retries: int = 0
    self_heal_count: int = 0

    @property
    def duration_ms(self) -> float:
        """Total pipeline duration in milliseconds."""
        if self.end_time <= 0:
            return (
                (time.time() - self.start_time) * 1000
                if self.start_time > 0
                else 0.0
            )
        return (self.end_time - self.start_time) * 1000

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def successful_steps(self) -> int:
        return sum(1 for s in self.steps if s.success)

    @property
    def failed_steps(self) -> int:
        return sum(1 for s in self.steps if not s.success)

    @property
    def success_rate(self) -> float:
        """Success rate as 0.0-1.0."""
        if self.total_steps == 0:
            return 0.0
        return self.successful_steps / self.total_steps

    def to_summary(self) -> dict[str, Any]:
        """Generate summary dict for dashboard/reporting."""
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status,
            "duration_ms": round(self.duration_ms, 2),
            "total_steps": self.total_steps,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "success_rate": round(self.success_rate, 4),
            "total_retries": self.total_retries,
            "self_heal_count": self.self_heal_count,
            "start_time": datetime.fromtimestamp(
                self.start_time, tz=timezone.utc
            ).isoformat()
            if self.start_time > 0
            else None,
            "end_time": datetime.fromtimestamp(
                self.end_time, tz=timezone.utc
            ).isoformat()
            if self.end_time > 0
            else None,
        }
