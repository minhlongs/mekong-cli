# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
LLM Config — Model registry for OpenClaw daemon.

Dual-model architecture (Rapid-MLX local only, no cloud API):
- Primary model  : Qwen 3.6-35B (M1 Max :8001) — all tasks (~95 tok/s)
- Fallback       : Qwen 3.5-9B (M1 Max :8001) — VRAM pressure fallback

Latency benchmarks (M1 Max):
  Qwen 3.6-35B    : ~0.4s for 50 tokens  (95 tok/s — 256 MoE experts)
  Qwen 3.5-9B     : ~0.5s for 50 tokens  (108 tok/s — lightweight)
"""

import os
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for a single LLM endpoint."""

    name: str
    model_id: str
    base_url: str
    api_key: str = "local"
    timeout: int = 120
    max_tokens: int = 512
    temperature: float = 0.3
    description: str = ""

    @property
    def chat_url(self) -> str:
        """OpenAI-compatible chat completions URL."""
        return f"{self.base_url.rstrip('/')}/chat/completions"

    @property
    def models_url(self) -> str:
        """URL to list available models (health check)."""
        return f"{self.base_url.rstrip('/')}/models"


# ---------------------------------------------------------------------------
# Registry — Qwen 3.6-35B primary (Rapid-MLX)
# ---------------------------------------------------------------------------

RAPID_MLX_HOST = os.getenv("RAPID_MLX_HOST", "127.0.0.1")
RAPID_MLX_BASE_URL = f"http://{RAPID_MLX_HOST}:8001/v1"

# No cloud API — all routing is local Rapid-MLX only

FAST_MODEL = ModelConfig(
    name="qwen3.6-35b",
    model_id="qwen3.6-35b",
    base_url=RAPID_MLX_BASE_URL,
    timeout=30,
    max_tokens=256,
    temperature=0.3,
    description="Primary model: Qwen 3.6-35B, 256 MoE experts, 262K context",
)

DEEP_MODEL = ModelConfig(
    name="qwen3.6-35b",
    model_id="qwen3.6-35b",
    base_url=RAPID_MLX_BASE_URL,
    timeout=180,
    max_tokens=512,
    temperature=0.1,
    description="Deep reasoning: Qwen 3.6-35B, 262K context window",
)

# Fallback = Qwen 3.5-9B (lighter)
FALLBACK_MODEL = ModelConfig(
    name="qwen3.5-9b",
    model_id="qwen3.5-9b",
    base_url=RAPID_MLX_BASE_URL,
    timeout=60,
    max_tokens=256,
    temperature=0.3,
    description="Fallback model: Qwen 3.5-9B, lightweight",
)

# Legacy aliases
CODING_MODEL = FAST_MODEL
PLANNING_MODEL = FAST_MODEL
WORKER_MODEL = FAST_MODEL

# Capability → ModelConfig mapping (Qwen 3.6-35B handles all)
CAPABILITY_MAP: dict[str, ModelConfig] = {
    "lead_scan":     FAST_MODEL,
    "triage":        FAST_MODEL,
    "classification": FAST_MODEL,
    "health_check":  FAST_MODEL,
    "quick_check":   FAST_MODEL,
    "monitoring":    FAST_MODEL,
    "content_write": DEEP_MODEL,
    "reasoning":     DEEP_MODEL,
    "analysis":      DEEP_MODEL,
    "sales":         DEEP_MODEL,
    "general":       DEEP_MODEL,
    "execution":     DEEP_MODEL,
    "coding":        DEEP_MODEL,
    "code_review":   DEEP_MODEL,
    "validation":    DEEP_MODEL,
    "planning":      DEEP_MODEL,
    "template":      DEEP_MODEL,
}


def get_model_for_capability(capability: str) -> ModelConfig:
    """Return the appropriate ModelConfig for a given capability string."""
    return CAPABILITY_MAP.get(capability.lower(), DEEP_MODEL)


__all__ = [
    "ModelConfig",
    "FAST_MODEL",
    "DEEP_MODEL",
    "CODING_MODEL",
    "PLANNING_MODEL",
    "WORKER_MODEL",
    "FALLBACK_MODEL",
    "CAPABILITY_MAP",
    "get_model_for_capability",
]
