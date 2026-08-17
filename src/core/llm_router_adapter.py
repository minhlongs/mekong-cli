# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps LLMRouter to satisfy LLMRouter Protocol."""

from __future__ import annotations

from typing import Any, Dict


class LLMRouterAdapter:
    """Thin adapter mapping LLMRouter Protocol methods to LLMRouter.route().

    Protocol → Implementation:
    - classify(task)          → route(task) then extract classification info
    - select_model(task, tier) → route(task) then check tier compatibility
    - estimate_cost(model, tokens) → lookup from route result metadata
    - generate(prompt, model) → placeholder completion (LLM call stubbed)
    - health() → status dict from router
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
        try:
            result = router.route(task)
            return {
                "task": task,
                "model": result.name,
                "capability": "standard",
                "tier": result.tier if hasattr(result, "tier") else "basic",
            }
        except Exception:
            return {"task": task, "model": "unknown", "capability": "standard", "tier": "basic"}

    def select_model(self, task: Dict[str, Any], tier: str) -> str:
        """Select model for task + tier, return model name."""
        router = self._get_router()
        try:
            result = router.route(task)
            if tier and hasattr(result, "tier") and result.tier != tier:
                return "fallback"
            return result.name
        except Exception:
            return "default"

    def estimate_cost(self, model: str, tokens: int) -> Dict[str, Any]:
        """Estimate cost for model + token count."""
        return {
            "model": model,
            "tokens": tokens,
            "cost_usd": tokens * 0.00001,
            "currency": "USD",
        }

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        """Generate text completion for a prompt.

        Protocol method — adapts to underlying router capability.
        """
        if model:
            return f"[stub] {prompt[:50]}... via {model}"
        try:
            router = self._get_router()
            result = router.route(prompt)
            return f"[stub] {prompt[:50]}... via {result.name}"
        except Exception:
            return f"[stub] {prompt[:50]}... via default"

    def stream(self, prompt: str, model: str | None = None, **kwargs: Any) -> Any:
        """Stream LLM response token by token."""
        try:
            router = self._get_router()
            if hasattr(router, "stream"):
                yield from router.stream(prompt, model=model, **kwargs)
                return
            # Fallback: yield the full response as a single chunk
            result = self.generate(prompt, model=model, **kwargs)
            yield result
        except Exception:
            yield f"[stub] {prompt[:50]}... (stream fallback)"

    def structured_output(self, prompt: str, schema: Dict[str, Any], model: str | None = None, **kwargs: Any) -> Dict[str, Any]:
        """Generate structured output conforming to schema."""
        try:
            router = self._get_router()
            if hasattr(router, "structured_output"):
                return router.structured_output(prompt, schema=schema, model=model, **kwargs)
            # Fallback: return prompt as text in a dict
            result = self.generate(prompt, model=model, **kwargs)
            return {"text": result, "schema": schema}
        except Exception:
            return {"text": f"[stub] {prompt[:50]}... (structured fallback)", "schema": schema}

    def health(self) -> Dict[str, Any]:
        """Check router health status."""
        try:
            router = self._get_router()
            return {"status": "ok", "router": type(router).__name__}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}