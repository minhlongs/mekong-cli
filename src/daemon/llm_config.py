"""
LLM Config — Model registry for OpenClaw daemon.

Tri-model architecture for Solo Company Operations:
- Fast scanner : Nemotron 30B (M1 Max :11436) — leads, triage, health checks
- Deep reasoner: DeepSeek R1 32B (M1 Max :11435) — content, analysis, sales
- Coding/API   : Qwen 3.5 Plus (DashScope API) — code gen, validation
- Fallback     : Bailian API (when local MLX unhealthy)
"""

import os
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Model Configurations
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    """Configuration for a single LLM endpoint."""

    name: str
    model_id: str
    base_url: str
    api_key: str = "local"          # "local" = no auth needed
    timeout: int = 120              # seconds
    max_tokens: int = 4096
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
# Registry — Tri-Model Architecture
# ---------------------------------------------------------------------------

#: M1 Max MLX endpoints (each model on separate port)
M1_MAX_HOST = os.getenv("M1_MAX_HOST", "192.168.11.111")
DEEPSEEK_BASE_URL = f"http://{M1_MAX_HOST}:11435/v1"
NEMOTRON_BASE_URL = f"http://{M1_MAX_HOST}:11436/v1"

#: DashScope Coding Plan API (sk-sp-* keys, /v1 NOT /compatible-mode/v1)
DASHSCOPE_BASE_URL = os.getenv(
    "CODING_PLAN_URL",
    "https://coding-intl.dashscope.aliyuncs.com/v1",
)
DASHSCOPE_API_KEY = os.getenv("BAILIAN_CODING_PLAN_API_KEY",
    os.getenv("DASHSCOPE_API_KEY", ""))

#: Bailian / DashScope fallback (legacy compat)
BAILIAN_BASE_URL = os.getenv(
    "BAILIAN_BASE_URL",
    "https://coding-intl.dashscope.aliyuncs.com/compatible-mode/v1",
)
BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY", "")

#: Fast scanner — Nemotron 30B (quick checks, lead scanning, triage)
FAST_MODEL = ModelConfig(
    name="nemotron-fast",
    model_id="mlx-community/NVIDIA-Nemotron-3-Nano-30B-A3B-4bit",
    base_url=NEMOTRON_BASE_URL,
    timeout=60,
    max_tokens=2048,
    temperature=0.3,
    description="Fast scanner: leads, triage, health checks, classification",
)

#: Deep coder — Qwen2.5-Coder-32B (coding, content writing, analysis)
#: Note: port 11435 was originally DeepSeek R1, model hot-swapped to Qwen Coder
DEEP_MODEL = ModelConfig(
    name="qwen-coder-local",
    model_id="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
    base_url=DEEPSEEK_BASE_URL,
    timeout=300,
    max_tokens=4096,
    temperature=0.1,
    description="Deep coder: content, analysis, sales, coding, complex reasoning",
)

#: Coding model — Qwen 3.5 Plus via DashScope API
CODING_MODEL = ModelConfig(
    name="qwen-coder",
    model_id="qwen3.5-plus",
    base_url=DASHSCOPE_BASE_URL,
    api_key=DASHSCOPE_API_KEY,
    timeout=120,
    max_tokens=8192,
    temperature=0.2,
    description="Coding, validation, code review via DashScope API",
)

#: Bailian fallback model (used when local MLX is unhealthy)
FALLBACK_MODEL = ModelConfig(
    name="bailian-fallback",
    model_id="qwen-plus",
    base_url=BAILIAN_BASE_URL,
    api_key=BAILIAN_API_KEY,
    timeout=60,
    max_tokens=4096,
    temperature=0.3,
    description="Bailian API fallback when local MLX unavailable",
)

# Legacy aliases for backward compatibility
PLANNING_MODEL = CODING_MODEL
WORKER_MODEL = DEEP_MODEL

#: Capability → ModelConfig mapping (tri-model routing)
CAPABILITY_MAP: dict[str, ModelConfig] = {
    # Nemotron fast — quick, lightweight tasks
    "lead_scan":     FAST_MODEL,
    "triage":        FAST_MODEL,
    "classification": FAST_MODEL,
    "health_check":  FAST_MODEL,
    "quick_check":   FAST_MODEL,
    "monitoring":    FAST_MODEL,
    # DeepSeek R1 deep — reasoning-heavy tasks
    "content_write": DEEP_MODEL,
    "reasoning":     DEEP_MODEL,
    "analysis":      DEEP_MODEL,
    "sales":         DEEP_MODEL,
    "general":       DEEP_MODEL,
    "execution":     DEEP_MODEL,
    # Qwen API — coding and validation tasks
    "coding":        CODING_MODEL,
    "code_review":   CODING_MODEL,
    "validation":    CODING_MODEL,
    "planning":      CODING_MODEL,
    "template":      CODING_MODEL,
}


def get_model_for_capability(capability: str) -> ModelConfig:
    """
    Return the appropriate ModelConfig for a given capability string.

    Routing hierarchy: FAST_MODEL for scans → DEEP_MODEL for reasoning
    → CODING_MODEL for code → FALLBACK for unknown.

    Args:
        capability: Task capability tag (e.g. "lead_scan", "content_write")

    Returns:
        ModelConfig instance.
    """
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
