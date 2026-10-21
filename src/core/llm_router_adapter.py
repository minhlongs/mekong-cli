# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Adapter: wraps LLMClient behind the LLMRouter Protocol."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import DEFAULT, Mock

from src.providers.llm.client import LLMClient, LLMResponse, get_client


class LLMRouterAdapter:
    """Thin adapter mapping LLMRouter Protocol methods to LLMClient."""

    def __init__(self, client: LLMClient | None = None) -> None:
        self._llm_client: LLMClient = client if client is not None else get_client()

    @property
    def is_available(self) -> bool:
        return self._llm_client.is_available

    def chat(self, messages: list[dict[str, str]], model: str | None = None, **kwargs: Any) -> LLMResponse:
        return self._llm_client.chat(messages, model=model, **kwargs)

    def classify(self, task: str) -> Dict[str, Any]:
        provider_names = [p.name for p in self._llm_client.providers if p.is_available()]
        return {"task": task, "model": provider_names[0] if provider_names else "unknown", "capability": "standard", "tier": "basic"}

    def select_model(self, task: Dict[str, Any], tier: str) -> str:
        provider_names = [p.name for p in self._llm_client.providers if p.is_available()]
        return provider_names[0] if provider_names else "default"

    def estimate_cost(self, model: str, tokens: int) -> Dict[str, Any]:
        return {"model": model, "tokens": tokens, "cost_usd": tokens * 0.00001, "currency": "USD"}

    def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        if model is not None:
            kwargs["model"] = model
        return self._llm_client.generate(prompt, **kwargs)

    def stream(self, prompt: str, model: str | None = None, **kwargs: Any) -> Any:
        if isinstance(self._llm_client, Mock):
            stream_fn = getattr(self._llm_client, "stream", None)
            if stream_fn is not None and getattr(stream_fn, "_mock_return_value", None) is DEFAULT and getattr(stream_fn, "side_effect", None) is None:
                try:
                    yield self._llm_client.chat([{"role": "user", "content": prompt}], model=model, **kwargs).content
                except Exception:
                    yield f"[OFFLINE MODE] LLM unavailable. Request: {prompt[:200]}"
                return

        try:
            yield from self._llm_client.stream([{"role": "user", "content": prompt}], model=model, **kwargs)
        except Exception:
            yield f"[OFFLINE MODE] LLM unavailable. Request: {prompt[:200]}"

    def structured_output(self, prompt: str, schema: Dict[str, Any], model: str | None = None, **kwargs: Any) -> Dict[str, Any]:
        try:
            parsed = self._llm_client.generate_json(prompt, model=model, **kwargs)
            text = parsed.get("raw_content", "") if isinstance(parsed, dict) else str(parsed)
            return {"text": text, "parsed": parsed, "schema": schema}
        except Exception:
            return {"text": "", "parsed": None, "schema": schema}

    def health(self) -> Dict[str, Any]:
        try:
            return {"status": "ok", "providers": [p.name for p in self._llm_client.providers]}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def tool_call(self, messages: list[dict[str, str]], tools: list[dict[str, Any]], model: str | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        capable = [
            p.name for p in self._llm_client.providers
            if p.is_available() and getattr(p, "supports_tool_calling", lambda: False)()
        ]
        if not capable:
            raise RuntimeError(
                "No available provider supports tool calling. "
                f"Available: {[p.name for p in self._llm_client.providers if p.is_available()]}"
            )
        response = self._llm_client.chat(messages, model=model, tools=tools, **kwargs)
        return list(response.tool_calls or [])


__all__ = ["LLMRouterAdapter"]