# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Seed config package — LLM settings + tier configs."""

import os

# LLM / model settings (previously in flat config.py)
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3")
EMBED_MODEL: str = os.getenv("EMBED_MODEL", "llama3")
LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))

CHROMA_PATH: str = os.getenv("CHROMA_PATH", "/tmp/seed_chroma")
SQLITE_PATH: str = os.getenv("SQLITE_PATH", "/tmp/seed_memory.db")
OUTPUTS_DIR: str = os.getenv("OUTPUTS_DIR", "/tmp/seed_outputs")

# Tier configs — imports from sub-module
from .tiers import (  # noqa: E402
    TierKey,
    TierConfig,
    get_tier,
    tier_credits,
    tier_features,
    mcu_cost,
    tier_credits_dict,
    mcu_costs_dict,
    TierQuotas,
    tier_quotas,
    vn_tier_for_pricing_file,
    trial_config,
)

__all__ = [
    "OLLAMA_BASE_URL",
    "LLM_MODEL",
    "EMBED_MODEL",
    "LLM_TIMEOUT",
    "CHROMA_PATH",
    "SQLITE_PATH",
    "OUTPUTS_DIR",
    "TierKey",
    "TierConfig",
    "get_tier",
    "tier_credits",
    "tier_features",
    "mcu_cost",
    "tier_credits_dict",
    "mcu_costs_dict",
    "TierQuotas",
    "tier_quotas",
    "vn_tier_for_pricing_file",
    "trial_config",
]
