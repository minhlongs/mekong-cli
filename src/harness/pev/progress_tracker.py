# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Progress tracking for PEV orchestration workflows.

Provides real-time progress reporting with callbacks,
percentage tracking, ETA estimation, and step-level detail.
"""

from __future__ import annotations

import time

from .progress_models import (
    ProgressCallback,
    ProgressPhase,
    ProgressSnapshot,
    StepProgress,
)


class ProgressTracker:
    """Tracks and reports progress of PEV workflow execution."""

    def __init__(self) -> None:
        self._phase = ProgressPhase.PLANNING
        self._total_steps = 0
        self._completed = 0
        self._failed = 0
        self._current_step: int | None = None
        self._start_time: float | None = None
        self._steps: dict[int, StepProgress] = {}
        self._callbacks: list[ProgressCallback] = []

    def register_callback(self, callback: ProgressCallback) -> None:
        """Register a progress listener."""
        self._callbacks.append(callback)

    def start_workflow(self, total_steps: int) -> None:
        """Initialize tracking for a new workflow."""
        self._total_steps = total_steps
        self._completed = 0
        self._failed = 0
        self._current_step = None
        self._start_time = time.time()
        self._steps = {}
        self._phase = ProgressPhase.PLANNING
        self._notify()

    def set_phase(self, phase: ProgressPhase) -> None:
        """Transition to a new workflow phase."""
        self._phase = phase
        self._notify()

    def step_started(self, order: int, title: str) -> None:
        """Mark a step as started."""
        self._current_step = order
        self._steps[order] = StepProgress(
            step_order=order,
            title=title,
            status="running",
            start_time=time.time(),
        )
        self._phase = ProgressPhase.EXECUTING
        self._notify()

    def step_completed(self, order: int) -> None:
        """Mark a step as completed successfully."""
        if order in self._steps:
            self._steps[order].status = "passed"
            self._steps[order].end_time = time.time()
        self._completed += 1
        self._current_step = None
        self._notify()

    def step_failed(self, order: int, error: str = "") -> None:
        """Mark a step as failed."""
        if order in self._steps:
            self._steps[order].status = "failed"
            self._steps[order].end_time = time.time()
            self._steps[order].error = error
        self._failed += 1
        self._current_step = None
        self._notify()

    def step_skipped(self, order: int, title: str = "") -> None:
        """Mark a step as skipped."""
        self._steps[order] = StepProgress(
            step_order=order,
            title=title,
            status="skipped",
        )
        self._notify()

    def finish(self, success: bool = True) -> None:
        """Mark the workflow as complete."""
        self._phase = ProgressPhase.COMPLETE if success else ProgressPhase.FAILED
        self._current_step = None
        self._notify()

    def snapshot(self) -> ProgressSnapshot:
        """Create an immutable snapshot of current progress."""
        elapsed = self._elapsed_ms()
        return ProgressSnapshot(
            phase=self._phase,
            total_steps=self._total_steps,
            completed_steps=self._completed,
            failed_steps=self._failed,
            current_step=self._current_step,
            percentage=self._percentage(),
            elapsed_ms=elapsed,
            eta_ms=self._estimate_eta(elapsed),
            steps=list(self._steps.values()),
        )

    def _percentage(self) -> float:
        """Calculate completion percentage."""
        if self._total_steps == 0:
            return 0.0
        done = self._completed + self._failed
        return (done / self._total_steps) * 100

    def _elapsed_ms(self) -> float:
        """Total elapsed time in milliseconds."""
        if self._start_time is None:
            return 0.0
        return (time.time() - self._start_time) * 1000

    def _estimate_eta(self, elapsed_ms: float) -> float | None:
        """Estimate remaining time based on average step duration."""
        done = self._completed + self._failed
        if done == 0 or self._total_steps == 0:
            return None
        remaining = self._total_steps - done
        avg_per_step = elapsed_ms / done
        return avg_per_step * remaining

    def _notify(self) -> None:
        """Notify all registered callbacks with current snapshot."""
        snap = self.snapshot()
        for cb in self._callbacks:
            try:
                cb(snap)
            except Exception:
                pass


__all__ = [
    "ProgressCallback",
    "ProgressPhase",
    "ProgressSnapshot",
    "ProgressTracker",
    "StepProgress",
]
