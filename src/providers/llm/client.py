# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - LLM Client.

Universal LLM endpoint — 3 vars, any provider.
"""

from __future__ import annotations

import logging
import os

from src.core.hooks import HookContext, HookPhase, HookPipeline, create_default_pipeline
from src.core.llm_cache import LLMCache
from src.core.providers import (
    GeminiProvider,
    LLMProvider,
    LLMResponse,
    OfflineProvider,
    OpenAICompatibleProvider,
)
from src.providers.llm.client_builders import LLMClientBuildersMixin, ProviderHealth
from src.providers.llm.client_exec import LLMClientExecMixin

logger = logging.getLogger(__name__)


class LLMClient(LLMClientBuildersMixin, LLMClientExecMixin):
    """LLMClient — thin router over List[LLMProvider] with circuit-breaker failover."""

    def __init__(
        self,
        proxy_url: str | None = None,
        api_key: str | None = None,
        gemini_key: str | None = None,
        model: str | None = None,
        timeout: int = 60,
        enable_cache: bool = True,
        enable_hooks: bool = True,
        providers: list[LLMProvider] | None = None,
    ) -> None:
        self.model = model or os.getenv("LLM_MODEL", "qwen3.6-35b")
        self.timeout = timeout

        self.proxy_url = proxy_url or os.getenv("ANTIGRAVITY_PROXY_URL", "") or os.getenv("LLM_BASE_URL", "")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.gemini_key = gemini_key or os.getenv("GEMINI_API_KEY", "")

        self.hooks: HookPipeline | None = create_default_pipeline() if enable_hooks else None
        self.cache: LLMCache | None = LLMCache() if enable_cache else None
        self._pending_requests: dict[str, LLMResponse | None] = {}

        if providers is not None:
            self.providers: list[LLMProvider] = providers
        else:
            self.providers = self._build_providers_from_env()

        self._provider_health: dict[str, ProviderHealth] = {
            p.name: ProviderHealth() for p in self.providers
        }

        available_names = {p.name for p in self.providers if p.is_available()}
        if "gemini" in available_names:
            self.mode = "vertex"
        elif any(n not in ("offline",) for n in available_names):
            self.mode = "proxy"
        else:
            self.mode = "offline"

    @classmethod
    def from_config(
        cls,
        config_path: str,
        model: str | None = None,
        timeout: int = 60,
        enable_cache: bool = True,
        enable_hooks: bool = True,
    ) -> "LLMClient":
        """Create LLMClient from YAML provider config."""
        providers = cls._build_providers_from_config(config_path)
        return cls(
            model=model,
            timeout=timeout,
            enable_cache=enable_cache,
            enable_hooks=enable_hooks,
            providers=providers,
        )

    @property
    def is_available(self) -> bool:
        """True if any non-offline provider is configured."""
        return any(
            p.is_available() and p.name != "offline"
            for p in self.providers
        )


_default_client: LLMClient | None = None


def get_client() -> LLMClient:
    """Get or create default LLM client (env-var auto-detection)."""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client


__all__ = [
    "LLMClient",
    "LLMResponse",
    "ProviderHealth",
    "get_client",
    "HookContext",
    "HookPhase",
    "HookPipeline",
    "create_default_pipeline",
    "LLMCache",
    "GeminiProvider",
    "LLMProvider",
    "OfflineProvider",
    "OpenAICompatibleProvider",
]
