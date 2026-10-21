# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""LLM Client Execution and Failover Mixin."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

import requests  # type: ignore[import-untyped]

from src.core.hooks import HookContext, HookPhase, HookPipeline
from src.core.llm_cache import LLMCache
from src.core.providers import LLMProvider, LLMResponse, OfflineProvider
from src.providers.llm.client_builders import ProviderHealth
from src.providers.llm.client_stream import LLMClientStreamMixin

logger = logging.getLogger(__name__)


class LLMClientExecMixin(LLMClientStreamMixin):
    """Mixin for chat, stream, generate, and failover logic."""

    model: str
    hooks: HookPipeline | None
    cache: LLMCache | None
    providers: list[LLMProvider]
    _provider_health: dict[str, ProviderHealth]

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        json_mode: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Send chat completion with runtime provider failover."""
        use_model = model or self.model
        hook_ctx = HookContext(
            messages=messages, model=use_model,
            temperature=temperature, max_tokens=max_tokens,
            start_time=time.time(),
        )
        if self.hooks:
            for r in self.hooks.run_phase(HookPhase.PRE_REQUEST, hook_ctx):
                if not r.passed:
                    logger.warning("[LLM] Pre-request hook failed: %s", r.error_message)
                    return self._offline_response(messages, error=f"hook: {r.error_message}")

        if self.cache and not json_mode and not tools:
            cached = self.cache.get(messages, use_model, temperature)
            if cached:
                return LLMResponse(
                    content=cached.content, model=cached.model,
                    usage=cached.usage, raw={"cache": True},
                )

        candidates = self._get_healthy_providers()
        if not candidates:
            return self._offline_response(messages, error="no providers available")

        last_error = ""
        for provider in candidates:
            if provider.name == "offline":
                break
            if provider.name not in self._provider_health:
                self._provider_health[provider.name] = ProviderHealth()
            hook_ctx.provider = provider.name
            try:
                result = provider.chat(
                    messages=messages, model=use_model,
                    temperature=temperature, max_tokens=max_tokens,
                    json_mode=json_mode, tools=tools,
                )
                self._provider_health[provider.name].record_success()
                if self.cache and not json_mode and not tools and result.content:
                    self.cache.put(messages, result.content, result.model, temperature, result.usage)
                if self.hooks:
                    hook_ctx.response_content = result.content
                    hook_ctx.response_model = result.model
                    hook_ctx.usage = result.usage or {}
                    self.hooks.run_phase(HookPhase.POST_REQUEST, hook_ctx)
                return result
            except requests.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else 0
                last_error = f"{provider.name}:{status_code}:{e}"
                logger.warning("[LLM] Provider %s HTTP %d: %s", provider.name, status_code, e)
                self._provider_health[provider.name].record_failure()
                if status_code == 400:
                    return self._offline_response(messages, error=f"bad request: {e}")
                continue
            except Exception as e:
                last_error = str(e)
                logger.warning("[LLM] Provider %s failed: %s", provider.name, e)
                self._provider_health[provider.name].record_failure()
                if self.hooks:
                    hook_ctx.error = e
                    self.hooks.run_phase(HookPhase.ON_ERROR, hook_ctx)
                continue

        return self._offline_response(messages, error=f"all providers failed: {last_error}")

    def _get_healthy_providers(self) -> list[LLMProvider]:
        """Return providers in order, skipping circuit-broken ones."""
        available = [p for p in self.providers if p.is_available()]
        if not available:
            return [OfflineProvider()]
        healthy = [
            p for p in available
            if p.name == "offline" or self._provider_health.get(p.name, ProviderHealth()).is_healthy
        ]
        return healthy if healthy else available

    def _request_hash(self, messages: list[dict[str, str]], model: str, temperature: float) -> str:
        """Generate hash for request deduplication."""
        content = json.dumps({"messages": messages, "model": model, "temperature": temperature}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _offline_response(self, messages: list[dict[str, str]], error: str = "") -> LLMResponse:
        """Generate offline placeholder response."""
        user_msg = "unknown"
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break
        return LLMResponse(
            content=f"[OFFLINE MODE] LLM unavailable{f' ({error})' if error else ''}. Request: {user_msg[:200]}",
            model="offline",
        )
