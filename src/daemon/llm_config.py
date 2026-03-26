"""
LLM Config — Model registry for OpenClaw daemon.

Dual-model architecture (MLX local only, no cloud API):
- Fast scanner : Nemotron 30B A3B (M1 Max :11436) — leads, triage, health checks (~1s)
- Deep reasoner: DeepSeek R1 Distill 32B (M1 Max :11435) — content, analysis, reasoning

Latency benchmarks (M1 Max):
  Nemotron A3B     : ~1.3s for 50 tokens  (34 tok/s — only 3B active params)
  DeepSeek R1 32B  : ~7s for 100 tokens   (~14 tok/s for 32B 4-bit)
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
# Registry — Dual-Model (Nemotron fast + DeepSeek R1 deep)
# ---------------------------------------------------------------------------

M1_MAX_HOST = os.getenv("M1_MAX_HOST", "192.168.11.111")
DEEPSEEK_BASE_URL = f"http://{M1_MAX_HOST}:11435/v1"
NEMOTRON_BASE_URL = f"http://{M1_MAX_HOST}:11436/v1"

# No cloud API — all routing is local MLX only

FAST_MODEL = ModelConfig(
    name="nemotron-fast",
    model_id="mlx-community/NVIDIA-Nemotron-3-Nano-30B-A3B-4bit",
    base_url=NEMOTRON_BASE_URL,
    timeout=30,
    max_tokens=256,
    temperature=0.3,
    description="Fast scanner: leads, triage, health checks, classification",
)

DEEP_MODEL = ModelConfig(
    name="deepseek-r1-local",
    model_id="mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
    base_url=DEEPSEEK_BASE_URL,
    timeout=180,
    max_tokens=512,
    temperature=0.1,
    description="Deep reasoner: content, analysis, sales, complex reasoning",
)

# Fallback = fast model (no cloud API)
FALLBACK_MODEL = FAST_MODEL

# Legacy aliases
CODING_MODEL = DEEP_MODEL
PLANNING_MODEL = DEEP_MODEL
WORKER_MODEL = FAST_MODEL

# Capability → ModelConfig mapping (dual-model: Nemotron fast + DeepSeek deep)
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
