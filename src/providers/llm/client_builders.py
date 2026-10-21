# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""LLM Client Provider Health and Discovery Mixin."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

import requests  # type: ignore[import-untyped]

from src.core.providers import (
    GeminiProvider, LLMProvider, OfflineProvider, OpenAICompatibleProvider,
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderHealth:
    """Tracks consecutive failures per provider for circuit breaker."""

    failures: int = 0
    last_failure: float = 0.0
    cooldown_secs: float = 15.0

    @property
    def is_healthy(self) -> bool:
        """True if fewer than 3 failures, or cooldown has elapsed."""
        return self.failures < 3 or (time.time() - self.last_failure) > self.cooldown_secs

    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure = time.time()

    def record_success(self) -> None:
        self.failures = 0


_AUTO_PROVIDERS = [
    ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", "anthropic/claude-sonnet-4", "openrouter"),
    ("AGENTROUTER_API_KEY", "https://agentrouter.org/v1", "claude-sonnet-4-6-20250514", "agentrouter"),
    ("DASHSCOPE_API_KEY", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen3-coder-plus", "qwen"),
    ("DEEPSEEK_API_KEY", "https://api.deepseek.com", "deepseek-chat", "deepseek"),
]


class LLMClientBuildersMixin:
    """Mixin for building LLM providers from env vars and YAML configs."""

    model: str
    timeout: int
    proxy_url: str
    api_key: str
    gemini_key: str
    _vn_provider: OpenAICompatibleProvider
    _local_llm_cache: bool | None = None

    def _build_providers_from_env(self) -> list[LLMProvider]:
        """Universal LLM provider detection — 3 env vars, any provider."""
        built: list[LLMProvider] = []
        if os.getenv("LLM_MODE", "byok").lower() == "legacy":
            if self.proxy_url:
                built.append(OpenAICompatibleProvider(
                    base_url=self.proxy_url, api_key=self.api_key or "",
                    model=self.model, provider_name="proxy", timeout=self.timeout,
                ))
            built.append(OfflineProvider())
            return built

        base_url, api_key = os.getenv("LLM_BASE_URL", ""), os.getenv("LLM_API_KEY", "")
        if base_url and api_key:
            built.append(OpenAICompatibleProvider(
                base_url=base_url, api_key=api_key, model=os.getenv("LLM_MODEL", "") or self.model,
                provider_name="primary", timeout=self.timeout,
            ))

        for env_key, url, default_model, name in _AUTO_PROVIDERS:
            if key := os.getenv(env_key, ""):
                built.append(OpenAICompatibleProvider(
                    base_url=url, api_key=key, model=default_model, provider_name=name, timeout=self.timeout,
                ))

        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        anthropic_base = os.getenv("ANTHROPIC_BASE_URL", "")
        if anthropic_key and "localhost" not in anthropic_base and "127.0.0.1" not in anthropic_base:
            built.append(OpenAICompatibleProvider(
                base_url="https://api.anthropic.com/v1", api_key=anthropic_key,
                model="claude-sonnet-4-6-20250514", provider_name="anthropic-direct",
                timeout=self.timeout,
            ))

        if self.api_key:
            built.append(OpenAICompatibleProvider(
                base_url="https://api.openai.com/v1", api_key=self.api_key,
                model=self.model, provider_name="openai-direct", timeout=self.timeout,
            ))

        google_key = os.getenv("GOOGLE_API_KEY", "") or self.gemini_key
        if google_key:
            built.append(GeminiProvider(api_key=google_key, model=self.model))

        local_url = os.getenv("LOCAL_LLM_URL", "")
        ollama_url = os.getenv("OLLAMA_BASE_URL", "")
        local_model = os.getenv("LOCAL_LLM_MODEL", "") or os.getenv("OLLAMA_MODEL", "qwen3.6-35b")
        if local_url:
            built.append(OpenAICompatibleProvider(
                base_url=local_url, api_key=os.getenv("LLM_API_KEY", "mlx"),
                model=local_model, provider_name="local-llm", timeout=self.timeout,
            ))
        elif ollama_url or self._check_local_llm_running():
            built.append(OpenAICompatibleProvider(
                base_url=ollama_url or "http://localhost:8001/v1", api_key="mlx",
                model=local_model, provider_name="local-llm", timeout=self.timeout,
            ))

        self._vn_provider = OpenAICompatibleProvider(
            base_url=os.getenv("VN_LLM_BASE_URL", "http://localhost:11434/v1"),
            api_key="mlx", model=os.getenv("VN_LLM_MODEL", "qwen3-8b"),
            provider_name="vn-local-mlx", timeout=self.timeout,
        )
        built.append(OfflineProvider())
        return built

    def get_vn_provider(self) -> OpenAICompatibleProvider:
        """Return the Vietnamese LLM provider (Qwen3-8B local MLX)."""
        return self._vn_provider

    def _check_local_llm_running(self) -> bool:
        """Probe local LLM health endpoint (cached after first check)."""
        cls = type(self)
        if cls._local_llm_cache is not None:
            return cls._local_llm_cache
        for port in (8001, 11434, 11435):
            try:
                if requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=1).status_code == 200:
                    cls._local_llm_cache = True
                    return True
            except Exception:
                continue
        cls._local_llm_cache = False
        return False

    @staticmethod
    def _build_providers_from_config(config_path: str) -> list[LLMProvider]:
        """Load providers from YAML config file."""
        try:
            import yaml  # type: ignore
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.exception("[LLMClient] Cannot load config %s: %s", config_path, e)
            return [OfflineProvider()]

        built: list[LLMProvider] = []
        for entry in config.get("providers", []):
            ptype = entry.get("type", "")
            if ptype == "gemini":
                api_key = os.getenv(entry.get("api_key_env", "GEMINI_API_KEY"), "")
                if api_key:
                    built.append(GeminiProvider(api_key=api_key, model=entry.get("model", "gemini-2.5-pro")))
            elif ptype == "openai_compatible":
                base_url = entry.get("base_url", "")
                if base_url:
                    built.append(OpenAICompatibleProvider(
                        base_url=base_url,
                        api_key=os.getenv(entry.get("api_key_env", "OPENAI_API_KEY"), ""),
                        model=entry.get("model", ""),
                        provider_name=entry.get("name", "openai_compatible"),
                        timeout=entry.get("timeout", 60),
                    ))
            else:
                logger.warning("[LLMClient] Unknown provider type in config: %s", ptype)

        built.append(OfflineProvider())
        return built
