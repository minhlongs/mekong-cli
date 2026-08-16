# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Execution Outcome Recorder (C4 Learning Loop).

Records execution outcomes (success/failure/retry_count) per execution,
stored in MemoryBridge for pattern analysis and retry threshold tuning.

Deliverables: C4 Phase — Learning Loop
  - D1: execution-outcome recorder (this module)
  - D2: similar-past-failures query before retry
  - D3: pattern warnings surfaced to user
  - D4: threshold auto-tuning from MemoryBridge
  - D5: CLI `mekong learn <execution_id>`
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OutcomeStatus(str, Enum):
    """Execution outcome status."""

    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    PARTIAL = "partial"


@dataclass(frozen=True)
class ExecutionOutcome:
    """Single execution outcome record.

    Attributes:
        execution_id: Unique execution identifier (e.g. workflow ID).
        status: Final outcome status.
        retry_count: Number of retries performed.
        started_at: Unix timestamp of execution start.
        finished_at: Unix timestamp of execution end.
        duration_ms: Total wall-clock duration in milliseconds.
        error_type: Category of error (if failed), e.g. "timeout", "auth".
        error_message: Raw error text from last attempt.
        provider: LLM or service provider that was called.
        command: The command that was executed.
        recipe: Recipe name if applicable.
        metadata: Extra fields (model, tokens, circuit_breaker_tripped, etc.).
    """

    execution_id: str
    status: OutcomeStatus
    retry_count: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    error_type: str | None = None
    error_message: str | None = None
    provider: str | None = None
    command: str | None = None
    recipe: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for MemoryBridge storage."""
        return {
            "execution_id": self.execution_id,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "provider": self.provider,
            "command": self.command,
            "recipe": self.recipe,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ExecutionOutcome:
        """Deserialize from dict."""
        return ExecutionOutcome(
            execution_id=data["execution_id"],
            status=OutcomeStatus(data["status"]),
            retry_count=data.get("retry_count", 0),
            started_at=data.get("started_at", time.time()),
            finished_at=data.get("finished_at", time.time()),
            duration_ms=data.get("duration_ms", 0.0),
            error_type=data.get("error_type"),
            error_message=data.get("error_message"),
            provider=data.get("provider"),
            command=data.get("command"),
            recipe=data.get("recipe"),
            metadata=data.get("metadata", {}),
        )


class OutcomeRecorder:
    """Records execution outcomes into MemoryBridge (episodic memory).

    Uses the MemoryBridge protocol so the implementation is backend-agnostic.
    Outcomes are stored as EPISODIC memory entries with rich metadata for
    later pattern analysis.

    Usage::

        recorder = OutcomeRecorder.get_instance()
        outcome = ExecutionOutcome(
            execution_id="wf-001",
            status=OutcomeStatus.FAILURE,
            retry_count=2,
            error_message="Connection timeout",
        )
        recorder.record(outcome)

    Class patterns:
        similar = recorder.find_similar_failures(
            error_type="timeout",
            provider="openai",
            limit=5,
        )
    """

    _instance: OutcomeRecorder | None = None

    def __init__(self) -> None:
        self._bridge: Any | None = None
        self._outcome_index: list[ExecutionOutcome] = []
        logger.info("OutcomeRecorder initialized")

    @classmethod
    def get_instance(cls) -> OutcomeRecorder:
        """Return singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_bridge(self) -> Any:
        """Lazy-load MemoryBridge (avoid circular imports at module load time)."""
        if self._bridge is None:
            from src.core.memory_bridge import get_bridge

            self._bridge = get_bridge()
        return self._bridge

    def record(self, outcome: ExecutionOutcome) -> str:
        """Persist an execution outcome to MemoryBridge.

        Args:
            outcome: ExecutionOutcome to record.

        Returns:
            MemoryBridge record ID.
        """
        bridge = self._get_bridge()
        from src.core.memory_bridge import MemoryRecord, MemoryKind

        record = MemoryRecord(
            content=self._build_content(outcome),
            kind=MemoryKind.EPISODIC,
            metadata=outcome.to_dict(),
        )
        record_id = bridge.record(record)
        self._outcome_index.append(outcome)
        logger.info(
            "Recorded outcome %s: %s (retries=%d)",
            outcome.execution_id,
            outcome.status.value,
            outcome.retry_count,
        )
        return record_id

    def find_similar_failures(
        self,
        *,
        error_type: str | None = None,
        provider: str | None = None,
        command: str | None = None,
        limit: int = 10,
    ) -> list[ExecutionOutcome]:
        """Query MemoryBridge for past failures with similar characteristics.

        Called BEFORE retry to surface known-bad configurations or providers.

        Args:
            error_type: Filter by error category (e.g. "timeout", "auth").
            provider: Filter by provider name.
            command: Filter by command string (substring match).
            limit: Maximum results.

        Returns:
            List of matching ExecutionOutcome records, newest first.
        """
        from src.core.memory_bridge import MemoryKind

        outcomes: list[ExecutionOutcome] = []

        # Primary: semantic search via MemoryBridge
        try:
            bridge = self._bridge or self._get_bridge()
            query_parts: list[str] = []
            if error_type:
                query_parts.append(error_type)
            if provider:
                query_parts.append(provider)
            if command:
                token = command.split()[0] if command else ""
                if token:
                    query_parts.append(token)

            query = " ".join(query_parts) if query_parts else "failure error"

            results = bridge.search(
                query=query,
                limit=limit,
                kind=MemoryKind.EPISODIC,
            )
            for rec in results:
                meta = rec.metadata or {}
                if meta.get("status") != OutcomeStatus.FAILURE.value:
                    continue
                if error_type and meta.get("error_type") != error_type:
                    continue
                if provider and meta.get("provider") != provider:
                    continue
                if command and command not in (meta.get("command") or ""):
                    continue
                try:
                    outcomes.append(ExecutionOutcome.from_dict(meta))
                except (KeyError, ValueError):
                    continue
        except Exception:
            # MemoryBridge may be unavailable (e.g. MagicMock in tests,
            # missing backend). Fall through to in-memory index below.
            pass

        # Fallback: filter the in-memory index directly
        if not outcomes:
            for o in self._outcome_index:
                if o.status != OutcomeStatus.FAILURE:
                    continue
                if error_type and o.error_type != error_type:
                    continue
                if provider and o.provider != provider:
                    continue
                if command and command not in (o.command or ""):
                    continue
                outcomes.append(o)

        # Newest first, capped to limit
        outcomes.sort(key=lambda o: o.finished_at, reverse=True)
        return outcomes[:limit]

    def get_failure_patterns(self, min_occurrences: int = 3) -> list[dict[str, Any]]:
        """Detect recurring failure patterns from the in-memory index.

        Groups failures by (error_type, provider) and returns patterns that
        exceed the occurrence threshold.  Used by D3 (pattern warnings).

        Args:
            min_occurrences: Minimum times a pattern must appear.

        Returns:
            List of pattern dicts with keys: error_type, provider,
            occurrences, sample_commands, last_seen, suggested_action.
        """

        groups: dict[tuple[str | None, str | None], list[ExecutionOutcome]] = {}
        for o in self._outcome_index:
            if o.status != OutcomeStatus.FAILURE:
                continue
            key = (o.error_type, o.provider)
            groups.setdefault(key, []).append(o)

        patterns: list[dict[str, Any]] = []
        for (error_type, provider), items in groups.items():
            if len(items) < min_occurrences:
                continue
            items.sort(key=lambda o: o.finished_at, reverse=True)
            commands = list(
                {o.command for o in items if o.command}
            )[:5]
            patterns.append(
                {
                    "error_type": error_type or "unknown",
                    "provider": provider or "unknown",
                    "occurrences": len(items),
                    "sample_commands": commands,
                    "last_seen": items[0].finished_at,
                    "suggested_action": self._suggest_action(error_type, provider),
                }
            )
        patterns.sort(key=lambda p: p["occurrences"], reverse=True)
        return patterns

    @staticmethod
    def _suggest_action(error_type: str | None, provider: str | None) -> str:
        """Return a human-readable remediation suggestion."""
        suggestions = {
            "timeout": "Increase timeout or switch provider",
            "auth": "Check API key / credentials",
            "rate_limit": "Add delay between retries",
            "connection": "Check network / try fallback provider",
            "invalid_api_key": "Rotate API key",
            "forbidden": "Check permissions / quota",
            "context_length": "Reduce prompt size or use longer-context model",
        }
        key = (error_type or "").lower().split(":")[0]
        return suggestions.get(key, "Review error and consider alternative provider")

    def suggest_retry_threshold(
        self,
        *,
        error_type: str | None = None,
        provider: str | None = None,
        current_threshold: int = 3,
        max_threshold: int = 5,
    ) -> int:
        """Auto-tune retry threshold based on historical outcomes (D4).

        If past failures for (error_type, provider) have a high average
        retry_count, suggest increasing the threshold.  If success rate
        is already high at the current threshold, suggest decreasing.

        Args:
            error_type: Error category to analyze.
            provider: Provider to analyze.
            current_threshold: Current retry max_attempts.
            max_threshold: Hard ceiling for suggested threshold.

        Returns:
            Suggested retry threshold (1 .. max_threshold).
        """
        similar = self.find_similar_failures(
            error_type=error_type,
            provider=provider,
            limit=50,
        )
        if not similar:
            return current_threshold

        avg_retries = sum(o.retry_count for o in similar) / len(similar)
        if avg_retries >= current_threshold:
            # Failures often hit the ceiling — raise it (up to max).
            return min(current_threshold + 1, max_threshold)
        if avg_retries < current_threshold * 0.4:
            # Most succeed on first try — lower it to save time.
            return max(current_threshold - 1, 1)
        return current_threshold

    def stats(self) -> dict[str, Any]:
        """Aggregate statistics from the in-memory index."""
        total = len(self._outcome_index)
        if total == 0:
            return {"total": 0, "success_rate": 0.0, "failure_count": 0, "avg_retries": 0.0}
        successes = sum(
            1 for o in self._outcome_index if o.status == OutcomeStatus.SUCCESS
        )
        failures = total - successes
        avg_retries = (
            sum(o.retry_count for o in self._outcome_index) / total
        )
        return {
            "total": total,
            "success_rate": round(successes / total * 100, 1),
            "failure_count": failures,
            "avg_retries": round(avg_retries, 2),
        }

    def clear(self) -> None:
        """Clear in-memory index (for testing)."""
        self._outcome_index.clear()

    # --- private helpers ---

    @staticmethod
    def _build_content(outcome: ExecutionOutcome) -> str:
        """Build a human-readable summary for MemoryBridge content field."""
        parts = [
            f"execution {outcome.execution_id}",
            outcome.status.value,
        ]
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
    """Reset singleton (for testing)."""
    OutcomeRecorder._instance = None


__all__ = [
    "OutcomeStatus",
    "ExecutionOutcome",
    "OutcomeRecorder",
    "_reset_singleton",
]
