# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous engine data models — telemetry shapes for one AGI cycle."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from .governance import GovernanceDecision


@dataclass
class ConsciousnessReport:
    score: int = 0; memory_health: float = 0.0; nlu_health: float = 0.0; router_health: float = 0.0  # noqa: E702
    executor_health: float = 0.0; learner_health: float = 0.0; evolution_health: float = 0.0  # noqa: E702
    governance_health: float = 0.0; reflection_health: float = 0.0; world_model_health: float = 0.0  # noqa: E702


@dataclass
class DecisionTrace:
    goal: str; timestamp: float = field(default_factory=time.time); intent_classified: str = ""  # noqa: E702
    confidence: float = 0.0; governance_decision: str = ""; strategy_used: str = ""  # noqa: E702
    world_state_summary: str = ""; reflection_summary: str = ""; result: str = ""  # noqa: E702


@dataclass
class CycleResult:
    goal: str = ""; governance_decision: Optional[GovernanceDecision] = None; executed: bool = False  # noqa: E702
    result_status: str = ""; recipe_generated: bool = False; patterns_detected: int = 0  # noqa: E702
    reflection_summary: str = ""; world_diff_summary: str = ""; decision_trace: Optional[DecisionTrace] = None  # noqa: E702
