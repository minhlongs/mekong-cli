# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Credit metering models, constants, and exceptions for RaaS PEV pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

TASK_COSTS: Dict[str, int] = {
    "plan": 1,
    "execute_shell": 1,
    "execute_llm": 2,
    "execute_api": 1,
    "verify": 1,
    "cook_simple": 1,
    "cook_standard": 3,
    "cook_complex": 5,
}


class InsufficientCreditsError(Exception):
    """Raised when a tenant does not have enough credits for a task."""

    def __init__(self, tenant_id: str, required: int, available: int) -> None:
        self.tenant_id = tenant_id
        self.required = required
        self.available = available
        super().__init__(
            f"Tenant '{tenant_id}' has {available} credits but {required} required."
        )


@dataclass
class UsageEvent:
    """Single credit usage record."""

    id: str
    tenant_id: str
    mission_id: Optional[str]
    task_type: str
    credits_used: int
    timestamp: str  # ISO 8601


@dataclass
class UsageSummary:
    """Aggregated credit usage for a tenant over a period."""

    tenant_id: str
    period: str
    total_credits_used: int
    event_count: int
    breakdown: Dict[str, int]  # task_type → total credits


__all__ = [
    "TASK_COSTS",
    "InsufficientCreditsError",
    "UsageEvent",
    "UsageSummary",
]
