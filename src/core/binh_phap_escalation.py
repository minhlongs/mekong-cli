"""Binh Phap Escalation Routing — M1 Max LLM Provider Resolution.

Maps topology engine's abstract escalation levels to concrete LLM configs:
  Level 0-1: local_mlx ($0/query) → M1 Max MLX Server or Ollama
  Level 2: cloud_sonnet → Anthropic Claude Sonnet (via API key)
  Level 3: cloud_opus → Anthropic Claude Opus (via API key)
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Abstract escalation level → concrete provider config
ESCALATION_PROVIDERS: dict[str, dict[str, str]] = {
    "local_mlx": {
        "base_url": "http://192.168.11.111:11435/v1",
        "model": "qwen2.5-coder:32b",
        "provider_name": "m1max-mlx",
        "fallback_url": "http://192.168.11.111:11434/v1",
        "fallback_model": "qwen2.5-coder:32b",
        "fallback_name": "m1max-ollama",
    },
    "cloud_sonnet": {
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-sonnet-4-6",
        "provider_name": "anthropic-sonnet",
    },
    "cloud_opus": {
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-opus-4-6",
        "provider_name": "anthropic-opus",
    },
}


def resolve_llm_provider(escalation_level: str) -> dict[str, str]:
    """Resolve abstract escalation level to concrete LLM provider config.

    Returns dict with: base_url, model, provider_name.
    Uses env vars to override defaults (for flexible deployment).
    """
    config = ESCALATION_PROVIDERS.get(escalation_level, ESCALATION_PROVIDERS["local_mlx"])

    if escalation_level == "local_mlx":
        return {
            "base_url": os.getenv("MLX_BASE_URL", config["base_url"]),
            "model": os.getenv("MLX_MODEL", config["model"]),
            "provider_name": config["provider_name"],
            "fallback_url": os.getenv("OLLAMA_BASE_URL", config["fallback_url"]),
            "fallback_model": os.getenv("OLLAMA_MODEL", config["fallback_model"]),
            "fallback_name": config["fallback_name"],
        }
    elif escalation_level in ("cloud_sonnet", "cloud_opus"):
        return {
            "base_url": os.getenv("ANTHROPIC_BASE_URL", config["base_url"]),
            "model": config["model"],
            "provider_name": config["provider_name"],
            "api_key_env": "ANTHROPIC_API_KEY",
        }

    return dict(config)


def create_provider_for_level(escalation_level: str) -> Any:
    """Create an LLMProvider instance for the given escalation level.

    Returns OpenAICompatibleProvider configured for the right endpoint.
    Returns None if provider can't be created.
    """
    try:
        from .providers import OpenAICompatibleProvider
    except ImportError:
        return None

    config = resolve_llm_provider(escalation_level)

    if escalation_level == "local_mlx":
        return OpenAICompatibleProvider(
            base_url=config["base_url"],
            api_key="local",
            model=config["model"],
            provider_name=config["provider_name"],
            timeout=120,
        )
    else:
        api_key = os.getenv(config.get("api_key_env", "ANTHROPIC_API_KEY"), "")
        if not api_key:
            logger.warning("No API key for %s escalation", escalation_level)
            return None
        return OpenAICompatibleProvider(
            base_url=config["base_url"],
            api_key=api_key,
            model=config["model"],
            provider_name=config["provider_name"],
            timeout=120,
        )
