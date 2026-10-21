# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Retry loop hook utilities and helpers."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_pattern_warning(
    *,
    recorder: Any,
    error: str,
    provider: str | None,
    command: str | None,
) -> None:
    """Log a warning if this error matches a known recurrent pattern."""
    error_type = classify_error(error)
    similar = recorder.find_similar_failures(
        error_type=error_type,
        provider=provider,
        command=command,
        limit=3,
    )
    if len(similar) >= 2:
        logger.warning(
            "Pattern detected: '%s' error from provider='%s' has failed %d times before. Suggested action: %s",
            error_type,
            provider or "unknown",
            len(similar),
            recorder._suggest_action(error_type, provider),
        )


def classify_error(error_msg: str) -> str:
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


def copy_policy_with_attempts(policy: Any, new_attempts: int) -> Any:
    """Create a new RetryPolicy with the same settings but different max_attempts."""
    from src.core.retry_policy import RetryPolicy

    return RetryPolicy(
        max_attempts=new_attempts,
        initial_interval_seconds=policy.initial_interval_seconds,
        backoff_coefficient=policy.backoff_coefficient,
        max_interval_seconds=policy.max_interval_seconds,
        strategy=policy.strategy,
        non_retryable_errors=list(policy.non_retryable_errors),
        non_retryable_exit_codes=list(policy.non_retryable_exit_codes),
    )
