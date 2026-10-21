# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""LLM Client Streaming and Helper Generation Mixin."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Iterator

from src.core.hooks import HookContext, HookPhase, HookPipeline
from src.core.llm_cache import LLMCache
from src.core.providers import LLMProvider, LLMResponse
from src.providers.llm.client_builders import ProviderHealth

logger = logging.getLogger(__name__)


class LLMClientStreamMixin:
    """Mixin for streaming chat completions and text/JSON generation helpers."""

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
        raise NotImplementedError

    def _get_healthy_providers(self) -> list[LLMProvider]:
        raise NotImplementedError

    def _offline_response(self, messages: list[dict[str, str]], error: str = "") -> LLMResponse:
        raise NotImplementedError

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream chat tokens with runtime provider failover."""
        use_model = model or self.model
        hook_ctx = HookContext(
            messages=messages, model=use_model,
            temperature=temperature, max_tokens=max_tokens,
            start_time=time.time(),
        )
        if self.hooks:
            for r in self.hooks.run_phase(HookPhase.PRE_REQUEST, hook_ctx):
                if not r.passed:
                    resp = self._offline_response(messages, error=f"hook: {r.error_message}")
                    if resp.content:
                        yield resp.content
                    return

        if self.cache:
            cached = self.cache.get(messages, use_model, temperature)
            if cached and cached.content:
                yield cached.content
                return

        candidates = self._get_healthy_providers()
        if not candidates:
            resp = self._offline_response(messages, error="no providers available")
            if resp.content:
                yield resp.content
            return

        last_error = ""
        for provider in candidates:
            if provider.name == "offline":
                break
            if provider.name not in self._provider_health:
                self._provider_health[provider.name] = ProviderHealth()
            hook_ctx.provider = provider.name
            try:
                yielded_any = False
                token_chunks: list[str] = []
                for chunk in provider.stream(
                    messages=messages, model=use_model,
                    temperature=temperature, max_tokens=max_tokens, **kwargs,
                ):
                    yielded_any = True
                    token_chunks.append(chunk)
                    yield chunk

                self._provider_health[provider.name].record_success()
                full_content = "".join(token_chunks)
                if self.cache and full_content:
                    self.cache.put(messages, full_content, use_model, temperature, {})
                if self.hooks:
                    hook_ctx.response_content = full_content
                    hook_ctx.response_model = use_model
                    hook_ctx.usage = {}
                    self.hooks.run_phase(HookPhase.POST_REQUEST, hook_ctx)
                return
            except Exception as e:
                last_error = str(e)
                logger.warning("[LLM] Provider %s stream failed: %s", provider.name, e)
                self._provider_health[provider.name].record_failure()
                if self.hooks:
                    hook_ctx.error = e
                    self.hooks.run_phase(HookPhase.ON_ERROR, hook_ctx)
                if yielded_any:
                    return
                continue

        resp = self._offline_response(messages, error=f"all providers failed: {last_error}")
        if resp.content:
            yield resp.content

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Simple text generation helper."""
        return self.chat([{"role": "user", "content": prompt}], **kwargs).content

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Generate and parse JSON response."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Always respond with valid JSON."},
            {"role": "user", "content": prompt},
        ]
        response = self.chat(messages, json_mode=True, **kwargs)
        try:
            parsed = json.loads(response.content)
            return parsed if isinstance(parsed, list) else dict(parsed)
        except json.JSONDecodeError:
            json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", response.content, re.DOTALL)
            if json_match:
                try:
                    parsed_match = json.loads(json_match.group(1))
                    return parsed_match if isinstance(parsed_match, list) else dict(parsed_match)
                except json.JSONDecodeError:
                    pass
            return {"raw_content": response.content}
