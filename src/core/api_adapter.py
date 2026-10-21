# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ALGO 6 — API Adapter."""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import AsyncIterator

import aiohttp

from src.core.model_selector import ModelConfig
from src.core.api_adapter_providers import (
    ANTHROPIC_DEFAULT_BASE_URL, anthropic_headers, anthropic_messages_url,
    detect_provider, format_for_gemini, format_for_openai, get_api_key,
)

_get_api_key = get_api_key
_anthropic_messages_url = anthropic_messages_url
_anthropic_headers = anthropic_headers

logger = logging.getLogger(__name__)
class APIAdapter:
    """Unified adapter for cloud LLM providers with connection reuse."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=20, limit_per_host=10, ttl_dns_cache=300, keepalive_timeout=30)
            self._session = aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=600, connect=10, sock_read=60), headers={"connection": "keep-alive"})
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> APIAdapter:
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def generate(self, model_config: ModelConfig, messages: list[dict], system_prompt: str | None = None) -> AsyncIterator[str]:
        provider = detect_provider(model_config.model_id)
        handlers = {"anthropic": self._generate_anthropic, "google": self._generate_google, "openai": self._generate_openai}
        if provider not in handlers:
            raise ValueError(f"Unsupported provider: {provider}")
        async for token in handlers[provider](model_config, messages, system_prompt):
            yield token

    async def _generate_anthropic(self, config: ModelConfig, messages: list[dict], system_prompt: str | None) -> AsyncIterator[str]:
        api_key = _get_api_key("anthropic")
        url = _anthropic_messages_url(os.getenv("ANTHROPIC_BASE_URL", ANTHROPIC_DEFAULT_BASE_URL))
        payload = {"model": config.model_id, "max_tokens": config.max_tokens, "temperature": config.temperature, "messages": messages, "stream": True, **({"system": system_prompt} if system_prompt else {})}
        session = await self._get_session()
        async with session.post(url, json=payload, headers=_anthropic_headers(api_key)) as resp:
            async for line in resp.content:
                text = line.decode("utf-8").strip()
                if text.startswith("data: ") and text[6:] != "[DONE]":
                    try:
                        if content := json.loads(text[6:]).get("delta", {}).get("text", ""):
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def _generate_google(self, config: ModelConfig, messages: list[dict], system_prompt: str | None) -> AsyncIterator[str]:
        api_key = _get_api_key("google")
        payload = {"contents": format_for_gemini(messages, system_prompt), "generationConfig": {"maxOutputTokens": config.max_tokens, "temperature": config.temperature}}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model_id}:streamGenerateContent?alt=sse&key={api_key}"
        session = await self._get_session()
        async with session.post(url, json=payload) as resp:
            async for line in resp.content:
                text = line.decode("utf-8").strip()
                if text.startswith("data: "):
                    try:
                        for c in json.loads(text[6:]).get("candidates", [])[:1]:
                            for part in c.get("content", {}).get("parts", []):
                                if part.get("text"):
                                    yield part["text"]
                    except json.JSONDecodeError:
                        continue

    async def _generate_openai(self, config: ModelConfig, messages: list[dict], system_prompt: str | None) -> AsyncIterator[str]:
        api_key = _get_api_key("openai")
        payload = {"model": config.model_id, "messages": format_for_openai(messages, system_prompt), "max_tokens": config.max_tokens, "temperature": config.temperature, "stream": True}
        session = await self._get_session()
        async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}) as resp:
            async for line in resp.content:
                text = line.decode("utf-8").strip()
                if text.startswith("data: ") and text[6:] != "[DONE]":
                    try:
                        if content := json.loads(text[6:])["choices"][0].get("delta", {}).get("content", ""):
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    def generate_sync(self, model_config: ModelConfig, messages: list[dict], system_prompt: str | None = None) -> str:
        provider = detect_provider(model_config.model_id)
        api_key = _get_api_key(provider)
        handlers = {"anthropic": self._sync_anthropic, "google": self._sync_google, "openai": self._sync_openai}
        return handlers[provider](model_config, messages, system_prompt, api_key) if provider in handlers else ""

    def _sync_post(self, url: str, payload: dict, headers: dict, label: str) -> dict | None:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST"), timeout=300) as resp:
                return json.loads(resp.read())
        except Exception as e:
            logger.error("%s sync failed: %s", label, e)
            return None

    def _sync_anthropic(self, config, messages, system_prompt, api_key) -> str:
        url = _anthropic_messages_url(os.getenv("ANTHROPIC_BASE_URL", ANTHROPIC_DEFAULT_BASE_URL))
        data = self._sync_post(url, {"model": config.model_id, "max_tokens": config.max_tokens, "temperature": config.temperature, "messages": messages, **({"system": system_prompt} if system_prompt else {})}, _anthropic_headers(api_key), "Anthropic")
        return "".join(b.get("text", "") for b in data.get("content", [])) if data else ""

    def _sync_google(self, config, messages, system_prompt, api_key) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.model_id}:generateContent?key={api_key}"
        data = self._sync_post(url, {"contents": format_for_gemini(messages, system_prompt), "generationConfig": {"maxOutputTokens": config.max_tokens, "temperature": config.temperature}}, {"Content-Type": "application/json"}, "Google")
        c = data.get("candidates", []) if data else []
        return "".join(p.get("text", "") for p in c[0].get("content", {}).get("parts", [])) if c else ""

    def _sync_openai(self, config, messages, system_prompt, api_key) -> str:
        data = self._sync_post("https://api.openai.com/v1/chat/completions", {"model": config.model_id, "messages": format_for_openai(messages, system_prompt), "max_tokens": config.max_tokens, "temperature": config.temperature}, _anthropic_headers(api_key), "OpenAI")
        return data["choices"][0]["message"]["content"] if data else ""


_adapter: APIAdapter | None = None


def get_adapter() -> APIAdapter:
    global _adapter
    if _adapter is None:
        _adapter = APIAdapter()
    return _adapter
