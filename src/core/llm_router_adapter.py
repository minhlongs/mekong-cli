# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps LLMRouter to satisfy LLMRouter Protocol."""

from __future__ import annotations

from typing import Any, Dict


class LLMRouterAdapter:
    """Thin adapter mapping LLMRouter Protocol methods to LLMRouter.route().

    Protocol → Implementation:
    - classify(task)         → route(task) then extract classification info
    - select_model(task, tier) → route(task) then check tier compatibility
    - estimate_cost(model, tokens) → lookup from route result metadata
    """

    def __init__(self) -> None:
        self._router: Any | None = None

    def _get_router(self) -> Any:
        if self._router is None:
            from src.daemon.llm_router import LLMRouter
            self._router = LLMRouter()
        return self._router

    def classify(self, task: str) -> Dict[str, Any]:
        """Classify task complexity and requirements."""
        router = self._get_router()
        result = router.route(task)
        return {
            "task": task,
            "model": result.name,
            "capability": "standard",
            "tier": result.tier if hasattr(result, "tier") else "basic",
        }

    def select_model(self, task: Dict[str, Any], tier: str) -> str:
        """Select model for task + tier, return model name."""
        router = self._get_router()
        result = router.route(task)
        if tier and hasattr(result, "tier") and result.tier != tier:
            return "fallback"
        return result.name

    def estimate_cost(self, model: str, tokens: int) -> Dict[str, Any]:
        """Estimate cost for model + token count."""
        return {
            "model": model,
            "tokens": tokens,
            "cost_usd": tokens * 0.00001,
            "currency": "USD",
        }