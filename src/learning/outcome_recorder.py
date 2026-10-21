# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Execution Outcome Recorder (C4 Learning Loop)."""

from __future__ import annotations

import logging
from typing import Any

from src.learning.outcome_analysis import OutcomeRecorderAnalysisMixin
from src.learning.outcome_models import ExecutionOutcome, OutcomeStatus

logger = logging.getLogger(__name__)


class OutcomeRecorder(OutcomeRecorderAnalysisMixin):
    """Records execution outcomes into MemoryBridge (episodic memory)."""

    _instance: OutcomeRecorder | None = None

    def __init__(self) -> None:
        self._bridge: Any | None = None
        self._outcome_index: list[ExecutionOutcome] = []
        logger.info("OutcomeRecorder initialized")

    @classmethod
    def get_instance(cls) -> OutcomeRecorder:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_bridge(self) -> Any:
        if self._bridge is None:
            from src.core.memory_bridge import get_bridge
            self._bridge = get_bridge()
        return self._bridge

    def record(self, outcome: ExecutionOutcome) -> str:
        bridge = self._get_bridge()
        from src.core.memory_bridge import MemoryKind, MemoryRecord

        record = MemoryRecord(
            content=self._build_content(outcome),
            kind=MemoryKind.EPISODIC,
            metadata=outcome.to_dict(),
        )
        record_id = bridge.record(record)
        self._outcome_index.append(outcome)
        logger.info("Recorded outcome %s: %s (retries=%d)", outcome.execution_id, outcome.status.value, outcome.retry_count)
        return record_id

    def stats(self) -> dict[str, Any]:
        total = len(self._outcome_index)
        if total == 0:
            return {"total": 0, "success_rate": 0.0, "failure_count": 0, "avg_retries": 0.0}
        successes = sum(1 for o in self._outcome_index if o.status == OutcomeStatus.SUCCESS)
        return {
            "total": total,
            "success_rate": round(successes / total * 100, 1),
            "failure_count": total - successes,
            "avg_retries": round(sum(o.retry_count for o in self._outcome_index) / total, 2),
        }

    def clear(self) -> None:
        self._outcome_index.clear()

    @staticmethod
    def _build_content(outcome: ExecutionOutcome) -> str:
        parts = [f"execution {outcome.execution_id}", outcome.status.value]
        if outcome.error_type:
            parts.append(f"error={outcome.error_type}")
        if outcome.provider:
            parts.append(f"provider={outcome.provider}")
        if outcome.command:
            parts.append(f"cmd={outcome.command[:80]}")
        if outcome.retry_count > 0:
            parts.append(f"retries={outcome.retry_count}")
        return " | ".join(parts)


def _reset_singleton() -> None:
    OutcomeRecorder._instance = None


__all__ = [
    "OutcomeStatus",
    "ExecutionOutcome",
    "OutcomeRecorder",
    "_reset_singleton",
]
