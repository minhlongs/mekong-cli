"""Binh Phap Escalation Routing — Dual-path: ZuneF (team) vs Anthropic (dev)."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

FABLE_MODEL = "claude-fable-5"
OPUS_MODEL = "claude-opus-4-8"
ANTHROPIC_DIRECT_BASE_URL = "https://api.anthropic.com/v1"


def _first_env(*keys: str, default: str) -> str:
    """Return the first set env var, or default."""
    for k in keys:
        v = os.getenv(k)
        if v:
            return v
    return default


def _resolve(slug: str, model: str) -> dict[str, str]:
    """Build provider config for one model slot."""
    base_url = _first_env(
        f"ZUNEF_{slug}_BASE_URL",
        f"{slug}_BASE_URL",
        "ANTHROPIC_BASE_URL",
        default=ANTHROPIC_DIRECT_BASE_URL,
    )
    resolved_model = _first_env(
        f"ZUNEF_{slug}_MODEL",
        f"{slug}_MODEL",
        default=model,
    )
    provider_name = f"zunef-{slug.lower()}" if any(
        os.getenv(k) for k in (f"ZUNEF_{slug}_BASE_URL", f"ZUNEF_{slug}_MODEL")
    ) else f"anthropic-{slug.lower()}"
    return {
        "base_url": base_url,
        "model": resolved_model,
        "provider_name": provider_name,
        "api_key_env": "ZUNEF_API_KEY" if any(
            os.getenv(k) for k in (f"ZUNEF_{slug}_BASE_URL", f"ZUNEF_{slug}_MODEL")
        ) else "ANTHROPIC_API_KEY",
    }


def resolve_llm_provider(escalation_level: str) -> dict[str, str]:
    """Route escalation level to Fable (strategic) or Opus (default)."""
    is_strategic = escalation_level.lower() in ("strategic", "cloud_opus")
    slug, model = ("FABLE", FABLE_MODEL) if is_strategic else ("OPUS", OPUS_MODEL)
    return _resolve(slug, model)


def create_provider_for_level(escalation_level: str) -> Any:
    """Create LLMProvider for the given level.

    ZuneF gateway uses device-header auth (X-Device-Id), so we create
    the provider even without ZUNEF_API_KEY when base_url points to zunef.com.
    """
    try:
        from .providers import OpenAICompatibleProvider
    except ImportError:
        return None

    config = resolve_llm_provider(escalation_level)
    base_url = config["base_url"]
    api_key_env = config.get("api_key_env", "ANTHROPIC_API_KEY")
    api_key = os.getenv(api_key_env, "")
    zunef_mode = "zunef.com" in base_url.lower()

    if zunef_mode:
        # Strip /v1/ai suffix so providers don't double-append /chat/completions
        for suffix in ("/v1/ai", "/v1"):
            if base_url.lower().endswith(suffix):
                base_url = base_url[: -len(suffix)]
                break

        # ZuneF uses device-header auth, not API key
        headers = {"X-Device-Id": os.getenv("ZUNEF_DEVICE_ID", ""), "X-ZUNEF-CLIENT": "binh-phap"}
        return OpenAICompatibleProvider(
            base_url=base_url,
            api_key=api_key or "-",
            model=config["model"],
            provider_name=config["provider_name"],
            timeout=120,
            extra_headers=headers,
        )

    if not api_key:
        logger.warning(
            "Missing API key (%s); provider unavailable for %s",
            api_key_env,
            escalation_level,
        )
        return None

    return OpenAICompatibleProvider(
        base_url=base_url,
        api_key=api_key,
        model=config["model"],
        provider_name=config["provider_name"],
        timeout=120,
    )
