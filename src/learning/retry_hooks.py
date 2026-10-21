# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Retry Loop Hooks (C4 Learning Loop)."""

from __future__ import annotations

import logging
from typing import Any

from src.core.stage_retry import StageRetryExecutor
from src.learning.retry_helpers import (
    check_pattern_warning,
    classify_error,
    copy_policy_with_attempts,
)

logger = logging.getLogger(__name__)


def attach_learning_hooks(
    executor: StageRetryExecutor,
    *,
    provider: str | None = None,
    command: str | None = None,
    warn_on_pattern: bool = True,
    auto_tune: bool = False,
    max_threshold: int = 5,
) -> None:
    """Attach C4 learning hooks to a StageRetryExecutor."""
    from src.learning.outcome_recorder import OutcomeRecorder

    recorder = OutcomeRecorder.get_instance()
    original_policy = executor.policy
    original_on_retry = executor.on_retry

    if auto_tune:
        suggested = recorder.suggest_retry_threshold(
            error_type=None, provider=provider,
            current_threshold=original_policy.max_attempts, max_threshold=max_threshold,
        )
        if suggested != original_policy.max_attempts:
            logger.info("Auto-tuning retry threshold: %d -> %d (provider=%s)", original_policy.max_attempts, suggested, provider)
            executor.policy = copy_policy_with_attempts(original_policy, suggested)

    def learning_on_retry(stage_index: int, attempt: int, delay: float, error: str) -> None:
        if original_on_retry:
            original_on_retry(stage_index, attempt, delay, error)
        if warn_on_pattern:
            check_pattern_warning(recorder=recorder, error=error, provider=provider, command=command)

    executor.on_retry = learning_on_retry


def record_outcome(
    execution_id: str,
    status: str,
    *,
    retry_count: int = 0,
    error_message: str | None = None,
    error_type: str | None = None,
    provider: str | None = None,
    command: str | None = None,
    recipe: str | None = None,
    duration_ms: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Convenience function to record an execution outcome."""
    from src.learning.outcome_recorder import ExecutionOutcome, OutcomeRecorder, OutcomeStatus

    recorder = OutcomeRecorder.get_instance()
    outcome = ExecutionOutcome(
        execution_id=execution_id, status=OutcomeStatus(status), retry_count=retry_count,
        error_message=error_message, error_type=error_type, provider=provider,
        command=command, recipe=recipe, duration_ms=duration_ms, metadata=metadata or {},
    )
    return recorder.record(outcome)


def check_before_retry(
    *,
    error_type: str | None = None,
    provider: str | None = None,
    command: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Query MemoryBridge for similar failures before retrying (D2)."""
    from src.learning.outcome_recorder import OutcomeRecorder, OutcomeStatus

    recorder = OutcomeRecorder.get_instance()
    similar = recorder.find_similar_failures(error_type=error_type, provider=provider, command=command, limit=limit)
    return [
        {
            "execution_id": o.execution_id, "error_type": o.error_type,
            "error_message": o.error_message, "provider": o.provider,
            "retry_count": o.retry_count, "finished_at": o.finished_at,
            "was_failure": o.status == OutcomeStatus.FAILURE,
        }
        for o in similar
    ]


def get_pattern_warnings(min_occurrences: int = 3) -> list[dict[str, Any]]:
    """Surface recurring failure patterns as warnings (D3)."""
    from src.learning.outcome_recorder import OutcomeRecorder

    return OutcomeRecorder.get_instance().get_failure_patterns(min_occurrences=min_occurrences)


_classify_error = classify_error

__all__ = [
    "attach_learning_hooks",
    "get_pattern_warnings",
    "record_outcome",
    "check_before_retry",
    "classify_error",
    "_classify_error",
    "check_pattern_warning",
    "copy_policy_with_attempts",
]
