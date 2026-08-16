# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI — Routing Strategy ABC.

Abstract base class for tier-aware, task-type-aware model routing.
Complements the provider-level RoutingStrategy Protocol in
provider_registry.py by adding a higher-level selection layer that
considers billing tier and task characteristics.

Public surface (Phase 2 go-live slice):
- ModelSelection — structured model pick result
- RoutingStrategy — ABC for strategy implementations
- CostOptimizedStrategy — lowest-cost model per tier
- LatencyFirstStrategy — lowest-latency model per tier
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSelection:
    """Result of a routing strategy decision.

    Attributes:
        model_id: The model identifier (e.g., 'claude-sonnet-4').
        provider: The provider name (e.g., 'anthropic', 'openai').
        tier: The billing tier that owns this selection.
        fallback: True when this selection is a degraded fallback pick.
    """

    model_id: str
    provider: str
    tier: str
    fallback: bool = False


class RoutingStrategy(ABC):
    """Abstract base for tier-and-task-aware model routing.

    Subclasses implement ``select_model`` to choose the best
    provider:model pair given a billing tier and task type.
    """

    @abstractmethod
    def select_model(self, tier: str, task_type: str) -> ModelSelection:
        """Select the optimal model for *tier* + *task_type*.

        Args:
            tier: Billing tier string (BASIC, PREMIUM, ENTERPRISE, MASTER).
            task_type: Semantic task label (e.g., 'chat', 'code', 'vision').

        Returns:
            A ``ModelSelection`` describing the chosen provider:model pair.
        """


class CostOptimizedStrategy(RoutingStrategy):
    """Route to the cheapest adequate model for each tier.

    For each tier the strategy picks the lowest-cost model that still
    satisfies common task requirements. Falls back to the tier's
    default model when no task-specific override is known.
    """

    # Tier -> task_type -> (model_id, provider)
    _TIER_MAP: dict[str, dict[str, tuple[str, str]]] = {
        "BASIC": {
            "chat": ("gpt-4o-mini", "openai"),
            "code": ("gpt-4o-mini", "openai"),
            "vision": ("gpt-4o-mini", "openai"),
        },
        "PREMIUM": {
            "chat": ("gpt-4o", "openai"),
            "code": ("claude-sonnet-4", "anthropic"),
            "vision": ("gpt-4o", "openai"),
        },
        "ENTERPRISE": {
            "chat": ("claude-sonnet-4", "anthropic"),
            "code": ("claude-sonnet-4", "anthropic"),
            "vision": ("gpt-4o", "openai"),
        },
        "MASTER": {
            "chat": ("claude-sonnet-4", "anthropic"),
            "code": ("claude-opus-4", "anthropic"),
            "vision": ("gpt-4o", "openai"),
        },
    }

    _DEFAULTS: dict[str, tuple[str, str]] = {
        "BASIC": ("gpt-4o-mini", "openai"),
        "PREMIUM": ("gpt-4o", "openai"),
        "ENTERPRISE": ("claude-sonnet-4", "anthropic"),
        "MASTER": ("claude-opus-4", "anthropic"),
    }

    def select_model(self, tier: str, task_type: str) -> ModelSelection:
        tier_upper = tier.upper()
        task_lower = task_type.lower()

        tier_tasks = self._TIER_MAP.get(tier_upper, {})
        model_id, provider = tier_tasks.get(task_lower, self._DEFAULTS.get(tier_upper, ("fable-5o-mini", "openai")))

        return ModelSelection(
            model_id=model_id,
            provider=provider,
            tier=tier_upper,
            fallback=False,
        )


class LatencyFirstStrategy(RoutingStrategy):
    """Route to the lowest-latency model for each tier.

    Prioritises speed over cost. Picks fast models that still
    respect the tier's capability floor.
    """

    _TIER_MAP: dict[str, dict[str, tuple[str, str]]] = {
        "BASIC": {
            "chat": ("gpt-4o-mini", "openai"),
            "code": ("gpt-4o-mini", "openai"),
            "vision": ("gpt-4o-mini", "openai"),
        },
        "PREMIUM": {
            "chat": ("gpt-4o-mini", "openai"),
            "code": ("gpt-4o", "openai"),
            "vision": ("gpt-4o-mini", "openai"),
        },
        "ENTERPRISE": {
            "chat": ("gpt-4o", "openai"),
            "code": ("claude-sonnet-4", "anthropic"),
            "vision": ("gpt-4o", "openai"),
        },
        "MASTER": {
            "chat": ("claude-sonnet-4", "anthropic"),
            "code": ("claude-sonnet-4", "anthropic"),
            "vision": ("gpt-4o", "openai"),
        },
    }

    _DEFAULTS: dict[str, tuple[str, str]] = {
        "BASIC": ("gpt-4o-mini", "openai"),
        "PREMIUM": ("gpt-4o-mini", "openai"),
        "ENTERPRISE": ("gpt-4o", "openai"),
        "MASTER": ("claude-sonnet-4", "anthropic"),
    }

    def select_model(self, tier: str, task_type: str) -> ModelSelection:
        tier_upper = tier.upper()
        task_lower = task_type.lower()

        tier_tasks = self._TIER_MAP.get(tier_upper, {})
        model_id, provider = tier_tasks.get(task_lower, self._DEFAULTS.get(tier_upper, ("gpt-4o-mini", "openai")))

        return ModelSelection(
            model_id=model_id,
            provider=provider,
            tier=tier_upper,
            fallback=False,
        )


__all__ = [
    "CostOptimizedStrategy",
    "LatencyFirstStrategy",
    "ModelSelection",
    "RoutingStrategy",
]
