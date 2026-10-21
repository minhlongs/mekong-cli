# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and enums for PEV ProgressTracker."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class ProgressPhase(Enum):
    """Current phase of the PEV workflow."""

    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class StepProgress:
    """Progress info for a single step."""

    step_order: int
    title: str
    status: str = "pending"
    start_time: float | None = None
    end_time: float | None = None
    error: str = ""

    @property
    def duration_ms(self) -> float:
        """Step duration in milliseconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


@dataclass
class ProgressSnapshot:
    """Immutable snapshot of current progress state."""

    phase: ProgressPhase
    total_steps: int
    completed_steps: int
    failed_steps: int
    current_step: int | None
    percentage: float
    elapsed_ms: float
    eta_ms: float | None
    steps: list[StepProgress] = field(default_factory=list)

    @property
    def remaining_steps(self) -> int:
        return self.total_steps - self.completed_steps - self.failed_steps


ProgressCallback = Callable[[ProgressSnapshot], None]
