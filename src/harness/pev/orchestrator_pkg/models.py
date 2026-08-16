# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Orchestrator data models — OrchestrationStatus, StepResult, OrchestrationResult.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from ..verifier import VerificationReport, ExecutionResult
from ..parser import RecipeStep, Recipe


class OrchestrationStatus(Enum):
    """Status of orchestration workflow"""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    ROLLED_BACK = "rolled_back"


@dataclass
class StepResult:
    """Result of executing and verifying a single step"""

    step: RecipeStep
    execution: ExecutionResult
    verification: VerificationReport
    retry_count: int = 0
    self_healed: bool = False


@dataclass
class OrchestrationResult:
    """Complete result of Plan → Execute → Verify workflow"""

    status: OrchestrationStatus
    recipe: Recipe
    step_results: List[StepResult] = field(default_factory=list)
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100


__all__ = [
    "OrchestrationStatus",
    "StepResult",
    "OrchestrationResult",
]
