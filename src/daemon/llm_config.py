"""
LLM Config — Model registry for OpenClaw daemon.

Defines model configurations, base URLs, timeouts, and fallback chain.
- Planning model : Qwen2.5-Coder-32B (local MLX)
- Worker model   : DeepSeek-R1-Distill-32B (local MLX)
- Fallback       : Bailian API (DashScope)
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
# Registry
# ---------------------------------------------------------------------------

#: Local MLX server shared by all local models
MLX_BASE_URL = "http://localhost:11435/v1"

#: Bailian / DashScope fallback
BAILIAN_BASE_URL = os.getenv(
    "BAILIAN_BASE_URL",
    "https://coding-intl.dashscope.aliyuncs.com/compatible-mode/v1",
)
BAILIAN_API_KEY = os.getenv("BAILIAN_API_KEY", "")

#: Planning / coding model (Qwen Coder — strong at structured output)
PLANNING_MODEL = ModelConfig(
    name="qwen-coder",
    model_id="mlx-community/Qwen2.5-Coder-32B-Instruct-4bit",
    base_url=MLX_BASE_URL,
    timeout=180,
    max_tokens=8192,
    temperature=0.2,
    description="Planning, coding, template generation",
)

#: Worker / reasoning model (DeepSeek R1 — strong at step-by-step reasoning)
WORKER_MODEL = ModelConfig(
    name="deepseek-r1",
    model_id="mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
    base_url=MLX_BASE_URL,
    timeout=300,
    max_tokens=4096,
    temperature=0.1,
    description="Reasoning, analysis, execution, general tasks",
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

#: Capability → ModelConfig mapping
CAPABILITY_MAP: dict[str, ModelConfig] = {
    # Qwen Coder handles structured, syntactic tasks
    "coding":    PLANNING_MODEL,
    "planning":  PLANNING_MODEL,
    "template":  PLANNING_MODEL,
    # DeepSeek R1 handles open-ended reasoning tasks
    "reasoning":  WORKER_MODEL,
    "analysis":   WORKER_MODEL,
    "execution":  WORKER_MODEL,
    "general":    WORKER_MODEL,
}


def get_model_for_capability(capability: str) -> ModelConfig:
    """
    Return the appropriate ModelConfig for a given capability string.

    Falls back to WORKER_MODEL for unknown capabilities.

    Args:
        capability: Task capability tag (e.g. "coding", "reasoning")

    Returns:
        ModelConfig instance.
    """
    return CAPABILITY_MAP.get(capability.lower(), WORKER_MODEL)


__all__ = [
    "ModelConfig",
    "PLANNING_MODEL",
    "WORKER_MODEL",
    "FALLBACK_MODEL",
    "CAPABILITY_MAP",
    "get_model_for_capability",
]
