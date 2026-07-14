"""Mekong CLI - Retry Loop Hooks (C4 Learning Loop).

Hooks the StageRetryExecutor / RetryPolicy retry loop to:
  - query MemoryBridge for similar past failures before retrying
  - surface pattern warnings to the user
  - auto-tune retry thresholds from historical data

Usage::

    from src.learning.retry_hooks import attach_learning_hooks

    executor = StageRetryExecutor(policy=RetryPolicy(max_attempts=3))
    attach_learning_hooks(executor, provider="openai")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from src.core.stage_retry import StageRetryExecutor

if TYPE_CHECKING:
    pass

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
    """Attach C4 learning hooks to a StageRetryExecutor.

    Wraps the executor's on_retry callback to inject outcome recording
    and pattern-based warnings.

    Args:
        executor: The StageRetryExecutor to augment.
        provider: Provider name for outcome records (e.g. "openai").
        command: Command string for similarity matching.
        warn_on_pattern: If True, emit warnings when similar past failures
            are found via MemoryBridge.
        auto_tune: If True, adjust the executor's max_attempts based on
            historical retry data before executing.
        max_threshold: Hard ceiling for auto-tuned retry count.
    """

    from src.learning.outcome_recorder import (
        OutcomeRecorder,
        OutcomeStatus,
        _reset_singleton,
    )

    recorder = OutcomeRecorder.get_instance()
    original_policy = executor.policy
    original_on_retry = executor.on_retry

    # --- Auto-tune threshold before first use ---
    if auto_tune:
        suggested = recorder.suggest_retry_threshold(
            error_type=None,
            provider=provider,
            current_threshold=original_policy.max_attempts,
            max_threshold=max_threshold,
        )
        if suggested != original_policy.max_attempts:
            logger.info(
                "Auto-tuning retry threshold: %d -> %d (provider=%s)",
                original_policy.max_attempts,
                suggested,
                provider,
            )
            executor.policy = _copy_policy_with_attempts(
                original_policy, suggested
            )

    def learning_on_retry(
        stage_index: int, attempt: int, delay: float, error: str
    ) -> None:
        """Wrapped retry callback: record outcome + check patterns."""
        # Forward to original callback
        if original_on_retry:
            original_on_retry(stage_index, attempt, delay, error)

        if warn_on_pattern:
            _check_pattern_warning(
                recorder=recorder,
                error=error,
                provider=provider,
                command=command,
            )

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
    """Convenience function to record an execution outcome.

    This is the D1 entry point — call it from executor.py after any
    step or stage finishes.

    Args:
        execution_id: Unique execution/workflow identifier.
        status: One of "success", "failure", "retry", "partial".
        retry_count: Number of retries performed.
        error_message: Raw error text.
        error_type: Categorized error (e.g. "timeout", "auth").
        provider: LLM or service provider name.
        command: Command string that was executed.
        recipe: Recipe name if applicable.
        duration_ms: Wall-clock duration.
        metadata: Extra key-value data.

    Returns:
        MemoryBridge record ID.
    """
    from src.learning.outcome_recorder import (
        ExecutionOutcome,
        OutcomeRecorder,
        OutcomeStatus,
    )

    recorder = OutcomeRecorder.get_instance()
    outcome = ExecutionOutcome(
        execution_id=execution_id,
        status=OutcomeStatus(status),
        retry_count=retry_count,
        error_message=error_message,
        error_type=error_type,
        provider=provider,
        command=command,
        recipe=recipe,
        duration_ms=duration_ms,
        metadata=metadata or {},
    )
    return recorder.record(outcome)


def check_before_retry(
    *,
    error_type: str | None = None,
    provider: str | None = None,
    command: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Query MemoryBridge for similar failures before retrying (D2).

    Call this at the top of a retry handler to get context on past
    failures with similar characteristics.

    Args:
        error_type: Error category filter.
        provider: Provider name filter.
        command: Command string filter.
        limit: Max results.

    Returns:
        List of dict summaries of similar past failures.
    """
    from src.learning.outcome_recorder import (
        OutcomeRecorder,
        OutcomeStatus,
    )

    recorder = OutcomeRecorder.get_instance()
    similar = recorder.find_similar_failures(
        error_type=error_type,
        provider=provider,
        command=command,
        limit=limit,
    )
    return [
        {
            "execution_id": o.execution_id,
            "error_type": o.error_type,
            "error_message": o.error_message,
            "provider": o.provider,
            "retry_count": o.retry_count,
            "finished_at": o.finished_at,
            "was_failure": o.status == OutcomeStatus.FAILURE,
        }
        for o in similar
    ]


def get_pattern_warnings(min_occurrences: int = 3) -> list[dict[str, Any]]:
    """Surface recurring failure patterns as warnings (D3).

    Args:
        min_occurrences: Minimum times a pattern must appear.

    Returns:
        List of pattern warning dicts.
    """
    from src.learning.outcome_recorder import (
        OutcomeRecorder,
    )

    recorder = OutcomeRecorder.get_instance()
    return recorder.get_failure_patterns(min_occurrences=min_occurrences)


# --- private helpers ---


def _check_pattern_warning(
    *,
    recorder: Any,
    error: str,
    provider: str | None,
    command: str | None,
) -> None:
    """Log a warning if this error matches a known recurrent pattern."""
    # Extract coarse error type from message
    error_type = _classify_error(error)
    similar = recorder.find_similar_failures(
        error_type=error_type,
        provider=provider,
        command=command,
        limit=3,
    )
    if len(similar) >= 2:
        logger.warning(
            "Pattern detected: '%s' error from provider='%s' "
            "has failed %d times before. "
            "Suggested action: %s",
            error_type,
            provider or "unknown",
            len(similar),
            recorder._suggest_action(error_type, provider),
        )


def _classify_error(error_msg: str) -> str:
    """Coarse classification of error messages into categories."""
    lower = error_msg.lower()
    if "timeout" in lower or "timed out" in lower:
        return "timeout"
    if "auth" in lower or "api key" in lower or "unauthorized" in lower:
        return "auth"
    if "rate" in lower or "429" in lower:
        return "rate_limit"
    if "connection" in lower or "connect" in lower or "network" in lower:
        return "connection"
    if "forbidden" in lower or "permission" in lower:
        return "forbidden"
    if "context" in lower or "too long" in lower or "token" in lower:
        return "context_length"
    return "unknown"


def _copy_policy_with_attempts(policy: Any, new_attempts: int) -> Any:
    """Create a new RetryPolicy with the same settings but different max_attempts."""
    from src.core.retry_policy import BackoffStrategy, RetryPolicy

    return RetryPolicy(
        max_attempts=new_attempts,
        initial_interval_seconds=policy.initial_interval_seconds,
        backoff_coefficient=policy.backoff_coefficient,
        max_interval_seconds=policy.max_interval_seconds,
        strategy=policy.strategy,
        non_retryable_errors=list(policy.non_retryable_errors),
        non_retryable_exit_codes=list(policy.non_retryable_exit_codes),
    )


__all__ = [
    "attach_learning_hooks",
    "get_pattern_warnings",
    "record_outcome",
    "check_before_retry",
]
