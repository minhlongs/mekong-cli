# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Phap DAG recovery — retry, fallback, and operator escalation."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List

logger = logging.getLogger(__name__)
RecoveryAction = str  # 'retry' | 'fallback' | 'escalate' | 'abort'


@dataclass(frozen=True)
class FailureRecord:
    chapter: int
    attempt: int
    error: str
    timestamp: str


@dataclass(frozen=True)
class RecoveryStrategy:
    failure_pattern: str
    max_attempts: int
    action: RecoveryAction
    fallback_chapters: List[int] = field(default_factory=list)
    human_ok: bool = True


_STRATEGIES: Dict[str, RecoveryStrategy] = {}


def register(kind: str, strategy: RecoveryStrategy) -> None:
    """Register or replace a recovery strategy by kind (unique key)."""
    _STRATEGIES[kind] = strategy
    logger.debug("Recovery strategy registered: %s → %s", kind, strategy.action)


def resolve(chapter: int, attempt: int, error: str) -> RecoveryStrategy:
    """Return the best matching strategy for a failure."""
    by_key = _STRATEGIES.get(f"ch{chapter}:{attempt}")
    if by_key and _matches(by_key.failure_pattern, error):
        return by_key

    for kind, strategy in _STRATEGIES.items():
        if kind == "default" or not strategy.failure_pattern:
            continue
        if kind.startswith("ch") and kind.split(":")[0] != f"ch{chapter}":
            continue
        if _matches(strategy.failure_pattern, error):
            return strategy

    return _STRATEGIES.get("default") or RecoveryStrategy(failure_pattern="", max_attempts=3, action="abort", fallback_chapters=[])


def _matches(pattern: str, error: str) -> bool:
    if not pattern:
        return False
    try:
        return bool(re.search(pattern, error, re.IGNORECASE))
    except re.error:
        return pattern.lower() in error.lower()


_REQUIRED_STRATEGIES: Dict[str, RecoveryStrategy] = {
    "default": RecoveryStrategy(failure_pattern="", max_attempts=3, action="retry", human_ok=False),
    "ch8:timeout": RecoveryStrategy(failure_pattern="timeout", max_attempts=2, action="fallback", fallback_chapters=[1, 7], human_ok=False),
    "default:auth": RecoveryStrategy(failure_pattern="auth|quota|forbidden", max_attempts=1, action="escalate", human_ok=True),
}

for _k, _v in _REQUIRED_STRATEGIES.items():
    register(_k, _v)


def should_retry(chapter: int, attempt: int, error: str) -> bool:
    strategy = resolve(chapter, attempt, error)
    return attempt < strategy.max_attempts and strategy.action == "retry"


def should_escalate(chapter: int, attempt: int, error: str) -> bool:
    return resolve(chapter, attempt, error).action == "escalate"


def fallback_targets(chapter: int, attempt: int, error: str) -> List[int]:
    return list(resolve(chapter, attempt, error).fallback_chapters)


@dataclass
class RecoveryDecision:
    action: RecoveryAction
    reason: str
    next_attempts: int
    fallback_chapters: List[int] = field(default_factory=list)


def evaluate(chapter: int, attempt: int, error: str) -> RecoveryDecision:
    strategy = resolve(chapter, attempt, error)
    return RecoveryDecision(
        action=strategy.action, reason=strategy.failure_pattern or "default",
        next_attempts=max(0, strategy.max_attempts - attempt),
        fallback_chapters=list(strategy.fallback_chapters),
    )


def escalate(chapter: int, error: str) -> None:
    logger.error("[ESCALATE] Chapter %d requires human input: %s", chapter, error)


__all__ = [
    "register", "resolve", "evaluate", "should_retry", "should_escalate",
    "fallback_targets", "escalate", "FailureRecord", "RecoveryStrategy",
    "RecoveryAction", "RecoveryDecision",
]
