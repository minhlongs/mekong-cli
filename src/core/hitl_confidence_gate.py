"""HITL Confidence Gate — route agent decisions by confidence score.

>85%  → AUTONOMOUS (no human needed)
60-85% → ESCALATE_REVIEW (human reviews but agent may proceed)
<60%   → ESCALATE_BLOCK (blocked until human approves)

Target escalation rate in mature deployments: 10-15%.
"""
from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque

log = logging.getLogger(__name__)

HISTORY_LIMIT = 1000


class GateDecision(Enum):
    AUTONOMOUS = "autonomous"
    ESCALATE_REVIEW = "escalate_review"
    ESCALATE_BLOCK = "escalate_block"


@dataclass
class GateThresholds:
    autonomous_min: float = 0.85
    review_min: float = 0.60

    def __post_init__(self) -> None:
        if not (0.0 <= self.review_min <= self.autonomous_min <= 1.0):
            raise ValueError(
                "Thresholds must satisfy 0 <= review_min <= autonomous_min <= 1"
            )


@dataclass
class EscalationRequest:
    task_id: str
    agent_id: str
    action_description: str
    confidence: float
    decision: GateDecision
    reasoning: str
    timestamp: float


@dataclass
class _Stats:
    total: int = 0
    autonomous: int = 0
    review: int = 0
    block: int = 0


class HITLConfidenceGate:
    """Evaluate agent confidence and route to autonomous or human review."""

    def __init__(self, thresholds: GateThresholds | None = None) -> None:
        self._thresholds = thresholds or GateThresholds()
        self._history: Deque[EscalationRequest] = deque(maxlen=HISTORY_LIMIT)
        self._stats = _Stats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        confidence: float,
        task_id: str,
        agent_id: str,
        action: str,
        reasoning: str = "",
    ) -> EscalationRequest:
        """Evaluate confidence and return an EscalationRequest."""
        decision = self._classify(confidence)
        req = EscalationRequest(
            task_id=task_id,
            agent_id=agent_id,
            action_description=action,
            confidence=confidence,
            decision=decision,
            reasoning=reasoning,
            timestamp=time.time(),
        )
        self._record(req)
        log.debug(
            "HITL gate: task=%s agent=%s confidence=%.3f decision=%s",
            task_id,
            agent_id,
            confidence,
            decision.value,
        )
        return req

    def should_proceed(self, confidence: float) -> bool:
        """Return True only when confidence meets the autonomous threshold."""
        return confidence >= self._thresholds.autonomous_min

    def get_stats(self) -> dict:
        t = self._stats.total
        return {
            "total_evaluations": t,
            "autonomous_count": self._stats.autonomous,
            "review_count": self._stats.review,
            "block_count": self._stats.block,
            "escalation_rate": (
                (self._stats.review + self._stats.block) / t if t > 0 else 0.0
            ),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _classify(self, confidence: float) -> GateDecision:
        if confidence >= self._thresholds.autonomous_min:
            return GateDecision.AUTONOMOUS
        if confidence >= self._thresholds.review_min:
            return GateDecision.ESCALATE_REVIEW
        return GateDecision.ESCALATE_BLOCK

    def _record(self, req: EscalationRequest) -> None:
        self._history.append(req)
        self._stats.total += 1
        if req.decision is GateDecision.AUTONOMOUS:
            self._stats.autonomous += 1
        elif req.decision is GateDecision.ESCALATE_REVIEW:
            self._stats.review += 1
        else:
            self._stats.block += 1


# ------------------------------------------------------------------
# Formatting helper
# ------------------------------------------------------------------

def format_escalation_message(request: EscalationRequest) -> str:
    """Return a human-readable escalation message."""
    label = {
        GateDecision.AUTONOMOUS: "proceeding autonomously",
        GateDecision.ESCALATE_REVIEW: "requesting human review",
        GateDecision.ESCALATE_BLOCK: "BLOCKED — awaiting human approval",
    }[request.decision]

    lines = [
        f"[HITL Gate] {label.upper()}",
        f"  Task     : {request.task_id}",
        f"  Agent    : {request.agent_id}",
        f"  Action   : {request.action_description}",
        f"  Confidence: {request.confidence:.1%}",
    ]
    if request.reasoning:
        lines.append(f"  Reasoning: {request.reasoning}")
    return "\n".join(lines)
