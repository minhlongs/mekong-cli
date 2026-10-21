# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and event mixins for PEV Structured Logger."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class PEVLogEntry:
    """Structured log entry for PEV operations."""

    timestamp: str
    level: str
    component: str
    operation: str
    message: str
    duration_ms: Optional[float] = None
    step_order: Optional[int] = None
    pipeline_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to JSON, omitting None fields."""
        data = {k: v for k, v in asdict(self).items() if v is not None}
        return json.dumps(data, default=str)


class PEVLifecycleEventsMixin:
    """Verification, orchestration, and pipeline log methods for PEVStructuredLogger."""

    COMPONENT_VERIFIER = "verifier"
    COMPONENT_ORCHESTRATOR = "orchestrator"
    COMPONENT_PIPELINE = "pipeline"

    def set_pipeline_id(self, pipeline_id: str) -> None: ...  # pragma: no cover
    def clear_pipeline_id(self) -> None: ...  # pragma: no cover
    def _log(self, level: int, component: str, operation: str, message: str, **kwargs: Any) -> PEVLogEntry: ...  # pragma: no cover

    def verify_started(self, step_order: int, **kwargs: Any) -> PEVLogEntry:
        """Log verification start."""
        return self._log(
            logging.INFO,
            self.COMPONENT_VERIFIER,
            "verify_started",
            f"Verifying step {step_order}",
            step_order=step_order,
            **kwargs,
        )

    def verify_passed(self, step_order: int, **kwargs: Any) -> PEVLogEntry:
        """Log verification passed."""
        return self._log(
            logging.INFO,
            self.COMPONENT_VERIFIER,
            "verify_passed",
            f"Step {step_order} verification passed",
            step_order=step_order,
            **kwargs,
        )

    def verify_failed(
        self, step_order: int, reason: str, **kwargs: Any
    ) -> PEVLogEntry:
        """Log verification failure."""
        return self._log(
            logging.WARNING,
            self.COMPONENT_VERIFIER,
            "verify_failed",
            f"Step {step_order} verification failed: {reason}",
            step_order=step_order,
            reason=reason,
            **kwargs,
        )

    def orchestration_started(self, goal: str, **kwargs: Any) -> PEVLogEntry:
        """Log orchestration workflow start."""
        return self._log(
            logging.INFO,
            self.COMPONENT_ORCHESTRATOR,
            "orchestration_started",
            f"Orchestration started: {goal}",
            goal=goal,
            **kwargs,
        )

    def orchestration_completed(
        self, status: str, duration_ms: float, **kwargs: Any
    ) -> PEVLogEntry:
        """Log orchestration completion."""
        level = logging.INFO if status == "success" else logging.WARNING
        return self._log(
            level,
            self.COMPONENT_ORCHESTRATOR,
            "orchestration_completed",
            f"Orchestration {status}",
            duration_ms=duration_ms,
            status=status,
            **kwargs,
        )

    def rollback_triggered(self, reason: str, **kwargs: Any) -> PEVLogEntry:
        """Log rollback trigger."""
        return self._log(
            logging.WARNING,
            self.COMPONENT_ORCHESTRATOR,
            "rollback_triggered",
            f"Rollback triggered: {reason}",
            reason=reason,
            **kwargs,
        )

    def pipeline_started(
        self, pipeline_id: str, stage_count: int, **kwargs: Any
    ) -> PEVLogEntry:
        """Log pipeline start."""
        self.set_pipeline_id(pipeline_id)
        return self._log(
            logging.INFO,
            self.COMPONENT_PIPELINE,
            "pipeline_started",
            f"Pipeline {pipeline_id} started with {stage_count} stages",
            stage_count=stage_count,
            **kwargs,
        )

    def pipeline_completed(
        self,
        pipeline_id: str,
        status: str,
        duration_ms: float,
        **kwargs: Any,
    ) -> PEVLogEntry:
        """Log pipeline completion."""
        level = logging.INFO if status == "completed" else logging.WARNING
        entry = self._log(
            level,
            self.COMPONENT_PIPELINE,
            "pipeline_completed",
            f"Pipeline {pipeline_id} {status}",
            duration_ms=duration_ms,
            status=status,
            **kwargs,
        )
        self.clear_pipeline_id()
        return entry
