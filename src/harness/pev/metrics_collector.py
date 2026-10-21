# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""PEV Metrics Collector — Phase 7 Telemetry."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from .metrics_models import PipelineMetrics, StepMetrics


class PEVMetricsCollector:
    """Collects and aggregates metrics for PEV pipeline executions."""

    MAX_HISTORY = 100

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._pipelines: dict[str, PipelineMetrics] = {}
        self._history: list[str] = []
        self._storage_dir = Path(storage_dir) if storage_dir else Path.home() / ".mekong" / "metrics"
        self._total_pipelines = 0
        self._total_successful = 0
        self._total_failed = 0

    def record_pipeline_start(self, pipeline_id: str) -> None:
        """Record pipeline execution start."""
        self._pipelines[pipeline_id] = PipelineMetrics(pipeline_id=pipeline_id, start_time=time.time())
        self._total_pipelines += 1

    def record_step_result(
        self, pipeline_id: str, step_order: int, success: bool,
        duration_ms: float, retry_count: int = 0, self_healed: bool = False,
    ) -> None:
        """Record step execution result within a pipeline."""
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline is None:
            return
        pipeline.steps.append(StepMetrics(
            step_order=step_order, success=success, duration_ms=duration_ms,
            retry_count=retry_count, self_healed=self_healed,
        ))
        pipeline.total_retries += retry_count
        if self_healed:
            pipeline.self_heal_count += 1

    def record_pipeline_end(self, pipeline_id: str, status: str) -> None:
        """Record pipeline completion."""
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline is None:
            return

        pipeline.end_time = time.time()
        pipeline.status = status

        if status == "completed":
            self._total_successful += 1
        elif status in ("failed", "rolled_back"):
            self._total_failed += 1

        self._history.append(pipeline_id)
        self._persist_pipeline(pipeline)
        self._trim_history()

    def get_pipeline_summary(self, pipeline_id: str) -> Optional[dict[str, Any]]:
        """Get summary for a specific pipeline."""
        pipeline = self._pipelines.get(pipeline_id)
        if pipeline is None:
            return None
        return pipeline.to_summary()

    def get_global_metrics(self) -> dict[str, Any]:
        """Get global aggregated metrics across all pipelines."""
        active = [p for p in self._pipelines.values() if p.status == "running"]
        completed = [p for p in self._pipelines.values() if p.status != "running"]

        avg_duration = 0.0
        if completed:
            avg_duration = sum(p.duration_ms for p in completed) / len(completed)

        total_retries = sum(p.total_retries for p in self._pipelines.values())
        total_self_heals = sum(p.self_heal_count for p in self._pipelines.values())

        return {
            "total_pipelines": self._total_pipelines,
            "total_successful": self._total_successful,
            "total_failed": self._total_failed,
            "overall_success_rate": (
                self._total_successful / self._total_pipelines
                if self._total_pipelines > 0
                else 0.0
            ),
            "active_pipelines": len(active),
            "avg_duration_ms": round(avg_duration, 2),
            "total_retries": total_retries,
            "total_self_heals": total_self_heals,
        }

    def get_recent_pipelines(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get summaries of most recent pipelines."""
        recent_ids = self._history[-limit:]
        results = []
        for pid in reversed(recent_ids):
            pipeline = self._pipelines.get(pid)
            if pipeline:
                results.append(pipeline.to_summary())
        return results

    def _persist_pipeline(self, pipeline: PipelineMetrics) -> None:
        """Save pipeline metrics to disk."""
        try:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
            filepath = self._storage_dir / f"{pipeline.pipeline_id}.json"
            filepath.write_text(json.dumps(pipeline.to_summary(), indent=2))
        except OSError:
            pass

    def _trim_history(self) -> None:
        """Remove oldest pipelines when exceeding MAX_HISTORY."""
        while len(self._history) > self.MAX_HISTORY:
            old_id = self._history.pop(0)
            self._pipelines.pop(old_id, None)

    def reset(self) -> None:
        """Reset all metrics (for testing)."""
        self._pipelines.clear()
        self._history.clear()
        self._total_pipelines = 0
        self._total_successful = 0
        self._total_failed = 0


_pev_metrics: Optional[PEVMetricsCollector] = None


def get_pev_metrics() -> PEVMetricsCollector:
    """Get singleton PEVMetricsCollector instance."""
    global _pev_metrics
    if _pev_metrics is None:
        _pev_metrics = PEVMetricsCollector()
    return _pev_metrics


def reset_pev_metrics() -> None:
    """Reset singleton (for testing)."""
    global _pev_metrics
    _pev_metrics = None


__all__ = [
    "PEVMetricsCollector",
    "PipelineMetrics",
    "StepMetrics",
    "get_pev_metrics",
    "reset_pev_metrics",
]
