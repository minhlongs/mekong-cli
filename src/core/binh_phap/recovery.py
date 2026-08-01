"""Binh Phap DAG recovery — retry, fallback, and operator escalation.

Provides a strategy registry where each failure mode (timeout, crash,
validation error) can be mapped to a recovery action: retry, fallback
to alternate chapter, or escalate to human.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List

logger = logging.getLogger(__name__)

RecoveryAction = str  # 'retry' | 'fallback' | 'escalate' | 'abort'


@dataclass(frozen=True)
class FailureRecord:
    """One observed failure event."""

    chapter: int
    attempt: int
    error: str
    timestamp: str


@dataclass(frozen=True)
class RecoveryStrategy:
    """Decision rule for a failure mode."""

    failure_pattern: str  # substring to match in error message
    max_attempts: int
    action: RecoveryAction
    # Chapters to branch to when action == 'fallback'
    fallback_chapters: List[int] = field(default_factory=list)
    # Whether a human sign-off is required before retry
    human_ok: bool = True


# Registry maps (chapter, failure_pattern) → RecoveryStrategy
# Indefinite size, mutable at config time — application-wide singleton.
_STRATEGIES: Dict[str, RecoveryStrategy] = {}


def register(kind: str, strategy: RecoveryStrategy) -> None:
    """Register or replace a recovery strategy by kind (unique key)."""
    _STRATEGIES[kind] = strategy
    logger.debug("Recovery strategy registered: %s → %s", kind, strategy.action)


def resolve(chapter: int, attempt: int, error: str) -> RecoveryStrategy:
    """Return the best matching strategy for a failure.

    Priority: exact chapter:attempt → chapter-specific pattern → global pattern
    → "default" (unconditional catch-all) → inline abort.
    """
    key = f"ch{chapter}:{attempt}"
    by_key = _STRATEGIES.get(key)
    if by_key and _matches(by_key.failure_pattern, error):
        return by_key

    # Try chapter-specific or chapter-agnostic patterns (skip "default" / empty)
    for kind, strategy in _STRATEGIES.items():
        if kind == "default":
            continue  # defer to catch-all below
        if not strategy.failure_pattern:
            continue
        if kind.startswith("ch"):
            ch_prefix = kind.split(":")[0]
            if ch_prefix != f"ch{chapter}":
                continue
        if _matches(strategy.failure_pattern, error):
            return strategy

    # Registered "default" is the unconditional catch-all
    default_strategy = _STRATEGIES.get("default")
    if default_strategy:
        return default_strategy

    # Hard fallback (should never reach with module-level defaults loaded)
    return RecoveryStrategy(
        failure_pattern="", max_attempts=3, action="abort", fallback_chapters=[],
    )


def _matches(pattern: str, error: str) -> bool:
    """Return True if pattern (regex or substring) appears in error."""
    if not pattern:
        return False
    import re
    try:
        return bool(re.search(pattern, error, re.IGNORECASE))
    except re.error:
        return pattern.lower() in error.lower()


# ---------------------------------------------------------------------------
# Default strategies (populate on import)
# ---------------------------------------------------------------------------

_REQUIRED_STRATEGIES: Dict[str, RecoveryStrategy] = {
    # Strategy 1: transient infra errors → retry (up to 3 attempts)
    "default": RecoveryStrategy(
        failure_pattern="",
        max_attempts=3,
        action="retry",
        human_ok=False,
    ),
    # Strategy 2: chapter 8 specific — timeout → fallback chain
    "ch8:timeout": RecoveryStrategy(
        failure_pattern="timeout",
        max_attempts=2,
        action="fallback",
        fallback_chapters=[1, 7],  # sre:incident → debug → ops:health-sweep
        human_ok=False,
    ),
    # Strategy 3: quota or auth failure → escalate to operator
    "default:auth": RecoveryStrategy(
        failure_pattern="auth|quota|forbidden",
        max_attempts=1,
        action="escalate",
        human_ok=True,
    ),
}

for _k, _v in _REQUIRED_STRATEGIES.items():
    register(_k, _v)


def should_retry(chapter: int, attempt: int, error: str) -> bool:
    strategy = resolve(chapter, attempt, error)
    return attempt < strategy.max_attempts and strategy.action == "retry"


def should_escalate(chapter: int, attempt: int, error: str) -> bool:
    return resolve(chapter, attempt, error).action == "escalate"


def fallback_targets(chapter: int, attempt: int, error: str) -> List[int]:
    strategy = resolve(chapter, attempt, error)
    return list(strategy.fallback_chapters)


@dataclass
class RecoveryDecision:
    """Outcome of a recovery check."""

    action: RecoveryAction
    reason: str
    next_attempts: int
    fallback_chapters: List[int] = field(default_factory=list)


def evaluate(chapter: int, attempt: int, error: str) -> RecoveryDecision:
    """Evaluate a failure and decide what to do next."""
    strategy = resolve(chapter, attempt, error)
    remaining = max(0, strategy.max_attempts - attempt)
    return RecoveryDecision(
        action=strategy.action,
        reason=strategy.failure_pattern or "default",
        next_attempts=remaining,
        fallback_chapters=list(strategy.fallback_chapters),
    )


# ---------------------------------------------------------------------------
# Higher-level: operator escalation logger
# ---------------------------------------------------------------------------

def escalate(chapter: int, error: str) -> None:
    """Log and flag for human review when automated recovery is impossible."""
    logger.error("[ESCALATE] Chapter %d requires human input: %s", chapter, error)
    # In a full implementation this would write to an operator queue,
    # fire a webhook, or drop a file in .mekong/bin-phap-escalation/ for
    # the human to act on when they next check.


__all__ = [
    "register",
    "resolve",
    "evaluate",
    "should_retry",
    "should_escalate",
    "fallback_targets",
    "escalate",
    "FailureRecord",
    "RecoveryStrategy",
    "RecoveryAction",
    "RecoveryDecision",
]
