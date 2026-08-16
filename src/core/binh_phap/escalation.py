# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""BINH_PHAP_ESCALATION_ORIG"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

FABLE_MODEL = "claude-fable-5"
OPUS_MODEL = "claude-opus-4-8"
ANTHROPIC_DIRECT_BASE_URL = "https://api.anthropic.com/v1"


def _first_env(*keys: str, default: str) -> str:
    for k in keys:
        v = os.getenv(k)
        if v:
            return v
    return default


def _resolve(slug: str, model: str) -> dict[str, str]:
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
    is_strategic = escalation_level.lower() in ("strategic", "cloud_opus")
    slug, model = ("FABLE", FABLE_MODEL) if is_strategic else ("OPUS", OPUS_MODEL)
    return _resolve(slug, model)


def create_provider_for_level(escalation_level: str) -> Any:
    return None


def resolve_llm_call(provider_config: dict[str, str]) -> dict[str, str]:
    base_url = (provider_config.get("base_url") or "").rstrip("/")
    api_key = provider_config.get("api_key") or ""
    model = provider_config.get("model") or ""
    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "provider_name": provider_config.get("provider_name") or "unknown",
    }
