"""ALGO 2 — Model Selector.

Selects the optimal LLM model based on TaskProfile and system state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.core.task_classifier import TaskProfile


@dataclass
class SystemState:
    """Current system state for model selection."""

    local_available: bool = False
    local_models: list[str] = field(default_factory=list)
    api_keys: dict[str, bool] = field(default_factory=dict)
    local_load: float = 0.0
    tenant_tier: str = "starter"


@dataclass
class ModelConfig:
    """Selected model configuration."""

    model_id: str
    provider: Literal["mlx", "ollama", "anthropic", "google", "openai"]
    max_tokens: int
    temperature: float
    context_window: int = 0
    cost_per_mtok_input: float = 0.0
    cost_per_mtok_output: float = 0.0


# (agent_role, complexity, requires_reasoning, data_sensitivity) → model_id
# "*" means wildcard match
MODEL_ROUTING_MATRIX: dict[tuple[str, str, bool | str, str], str] = {
    # CTO: CODE
    ("cto", "simple", False, "public"): "gemini-2.0-flash",
    ("cto", "simple", False, "internal"): "gemini-2.0-flash",
    ("cto", "simple", False, "sensitive"): "mlx:deepseek-coder-v2:16b",
    ("cto", "standard", True, "public"): "claude-sonnet-4-6",
    ("cto", "standard", True, "internal"): "claude-sonnet-4-6",
    ("cto", "standard", True, "sensitive"): "mlx:deepseek-coder-v2:33b",
    ("cto", "complex", True, "public"): "claude-opus-4-6",
    ("cto", "complex", True, "internal"): "claude-opus-4-6",
    ("cto", "complex", True, "sensitive"): "mlx:deepseek-coder-v2:33b",
    # CMO/EDITOR: CREATIVE
    ("cmo", "simple", False, "*"): "gemini-2.0-flash",
    ("cmo", "standard", True, "*"): "gemini-2.0-flash",
    ("cmo", "complex", True, "*"): "gemini-2.0-pro",
    ("editor", "simple", False, "*"): "gemini-2.0-flash",
    ("editor", "standard", False, "*"): "gemini-2.0-flash",
    ("editor", "complex", False, "*"): "gemini-2.0-flash",
    # COO: OPS (prefer local)
    ("coo", "simple", False, "*"): "mlx:llama3.2:3b",
    ("coo", "standard", False, "*"): "mlx:llama3.2:3b",
    ("coo", "complex", False, "*"): "mlx:llama3.2:3b",
    # CFO/DATA: ANALYSIS
    ("cfo", "simple", False, "sensitive"): "mlx:qwen3.6:35b",
    ("cfo", "simple", False, "public"): "gemini-2.0-flash-lite",
    ("cfo", "standard", False, "sensitive"): "mlx:qwen3.6:35b",
    ("cfo", "standard", False, "public"): "gemini-2.0-flash-lite",
    ("cfo", "complex", False, "sensitive"): "mlx:qwen3.6:35b",
    ("cfo", "complex", False, "public"): "gemini-2.0-flash-lite",
    ("data", "simple", False, "sensitive"): "mlx:qwen3.6:35b",
    ("data", "simple", False, "public"): "gemini-2.0-flash-lite",
    ("data", "standard", False, "sensitive"): "mlx:qwen3.6:35b",
    ("data", "standard", False, "public"): "gemini-2.0-flash-lite",
    ("data", "complex", False, "sensitive"): "mlx:qwen3.6:35b",
    ("data", "complex", False, "public"): "gemini-2.0-flash-lite",
    # CS: SUPPORT
    ("cs", "simple", False, "*"): "mlx:mistral:7b",
    ("cs", "standard", False, "*"): "claude-haiku-4-5",
    ("cs", "complex", True, "*"): "claude-haiku-4-5",
    # SALES
    ("sales", "simple", False, "*"): "claude-haiku-4-5",
    ("sales", "standard", True, "*"): "claude-sonnet-4-6",
    ("sales", "complex", True, "*"): "claude-sonnet-4-6",
}

CONTEXT_WINDOW_MAP: dict[str, int] = {
    "claude-opus-4-6": 200000,
    "claude-sonnet-4-6": 200000,
    "claude-haiku-4-5": 200000,
    "gemini-2.0-flash": 1000000,
    "gemini-2.0-flash-lite": 1000000,
    "gemini-2.0-pro": 1000000,
    "gpt-4o-mini": 128000,
    "gpt-4o": 128000,
    "mlx:deepseek-coder-v2:33b": 128000,
    "mlx:deepseek-coder-v2:16b": 128000,
    "mlx:llama3.2:3b": 128000,
    "mlx:llama3.3:70b": 128000,
    "mlx:qwen3.6:35b": 262000,
    "mlx:mistral:7b": 32000,
}

TEMP_MAP: dict[str, float] = {
    "code": 0.2,
    "ops": 0.1,
    "analysis": 0.3,
    "creative": 0.8,
    "sales": 0.7,
    "support": 0.4,
}

# Best local model per domain (for starter tier override)
BEST_LOCAL_FOR_DOMAIN: dict[str, str] = {
    "code": "mlx:qwen3.6:35b",
    "creative": "mlx:qwen3.6:35b",
    "ops": "mlx:qwen3.6:35b",
    "analysis": "mlx:qwen3.6:35b",
    "sales": "mlx:qwen3.6:35b",
    "support": "mlx:qwen3.6:35b",
}

# Smaller local model fallback for VRAM pressure
LOCAL_DOWNGRADE: dict[str, str] = {
    "mlx:qwen3.6:35b": "mlx:qwen3.5:9b",
    "mlx:qwen3.5:27b": "mlx:qwen3.5:9b",
    "mlx:qwen3.5:9b": "mlx:qwen3.5:4b",
    "mlx:deepseek-coder-v2:33b": "mlx:qwen3.5:9b",
    "mlx:deepseek-coder-v2:16b": "mlx:qwen3.5:4b",
    "mlx:llama3.3:70b": "mlx:qwen3.5:27b",
    "mlx:mistral:7b": "mlx:qwen3.5:4b",
}


def detect_provider(model_id: str) -> str:
    """Detect the provider from a model ID."""
    if model_id.startswith("ollama:"):
        return "ollama"
    if model_id.startswith("mlx:"):
        return "mlx"
    if "claude" in model_id:
        return "anthropic"
    if "gemini" in model_id:
        return "google"
    if "gpt" in model_id:
        return "openai"
    return "unknown"


def _lookup_matrix(profile: TaskProfile) -> str | None:
    """Look up model from routing matrix with wildcard fallback."""
    key = (profile.agent_role, profile.complexity,
           profile.requires_reasoning, profile.data_sensitivity)

    # Exact match first
    if key in MODEL_ROUTING_MATRIX:
        return MODEL_ROUTING_MATRIX[key]

    # Wildcard sensitivity match
    wildcard_key = (profile.agent_role, profile.complexity,
                    profile.requires_reasoning, "*")
    if wildcard_key in MODEL_ROUTING_MATRIX:
        return MODEL_ROUTING_MATRIX[wildcard_key]

    # Wildcard complexity + sensitivity
    for comp in ["simple", "standard", "complex"]:
        for reasoning in [True, False]:
            wk = (profile.agent_role, comp, reasoning, "*")
            if wk in MODEL_ROUTING_MATRIX:
                return MODEL_ROUTING_MATRIX[wk]

    return None


def _env_override(profile: TaskProfile) -> ModelConfig | None:
    """Build a ModelConfig from the `LLM_MODEL` env var, or return None.

    Highest-priority selection path — lets operators force any model via env
    (e.g., local Ollama in dev) without touching the routing matrix.

    Sensitive-data guard: when `profile.data_sensitivity == "sensitive"`, only
    local prefixes (`ollama:`/`mlx:`) are allowed. Non-local overrides are
    silently ignored so the caller falls back to the normal matrix, which
    honours the sensitive→local-only rule.
    """
    import os
    env_model = os.environ.get("LLM_MODEL", "").strip()
    if not env_model:
        return None

    known_prefixes = ("ollama:", "mlx:", "claude", "gemini", "gpt")
    model_id = env_model if env_model.startswith(known_prefixes) else f"ollama:{env_model}"

    # Sensitive data → only allow local backends through override.
    if profile.data_sensitivity == "sensitive" and not model_id.startswith(("ollama:", "mlx:")):
        return None

    from src.core.cost_estimator import COST_TABLE
    ctx_window = CONTEXT_WINDOW_MAP.get(model_id, 32000)
    costs = COST_TABLE.get(model_id, (0.0, 0.0))
    return ModelConfig(
        model_id=model_id,
        provider=detect_provider(model_id),  # type: ignore[arg-type]
        max_tokens=int(ctx_window * 0.75),
        temperature=TEMP_MAP.get(profile.domain, 0.3),
        context_window=ctx_window,
        cost_per_mtok_input=costs[0],
        cost_per_mtok_output=costs[1],
    )


def select_model(profile: TaskProfile, state: SystemState) -> ModelConfig:
    """Select the best model for a task profile given system state.

    Args:
        profile: Classified task profile.
        state: Current system state.

    Returns:
        ModelConfig with selected model and parameters.
    """
    override = _env_override(profile)
    if override is not None:
        return override

    model_id = _lookup_matrix(profile) or "gemini-2.0-flash"

    # Step 2: Availability check
    if model_id.startswith("mlx:"):
        ollama_model = model_id.split(":", 1)[1] if ":" in model_id else model_id
        if not state.local_available:
            model_id = "gemini-2.0-flash"  # API fallback
        elif state.local_load > 0.85:
            model_id = LOCAL_DOWNGRADE.get(model_id, model_id)
        elif ollama_model not in state.local_models:
            model_id = "gemini-2.0-flash"  # model not pulled
    else:
        provider = detect_provider(model_id)
        if not state.api_keys.get(provider, False):
            # Try different provider
            if state.local_available:
                model_id = BEST_LOCAL_FOR_DOMAIN.get(profile.domain, "mlx:llama3.2:3b")
            else:
                model_id = "gemini-2.0-flash"  # last resort

    # Step 3: Tenant tier override
    if state.tenant_tier == "starter" and model_id == "claude-opus-4-6":
        model_id = "claude-sonnet-4-6"

    if (state.tenant_tier == "starter"
            and state.local_available
            and profile.domain not in ("code", "sales")):
        model_id = BEST_LOCAL_FOR_DOMAIN.get(profile.domain, model_id)

    # Step 4: Build ModelConfig
    ctx_window = CONTEXT_WINDOW_MAP.get(model_id, 128000)
    temperature = TEMP_MAP.get(profile.domain, 0.3)
    provider = detect_provider(model_id)

    from src.core.cost_estimator import COST_TABLE
    costs = COST_TABLE.get(model_id, (0.0, 0.0))

    return ModelConfig(
        model_id=model_id,
        provider=provider,  # type: ignore[arg-type]
        max_tokens=int(ctx_window * 0.75),
        temperature=temperature,
        context_window=ctx_window,
        cost_per_mtok_input=costs[0],
        cost_per_mtok_output=costs[1],
    )

# --- Task Complexity Override (Superpowers-inspired) ---
# When task is mechanical, use cheaper model regardless of agent role

# Smart routing: right model for right task on M1 Max 64GB
# qwen3.6-35b = primary local model (256 MoE experts, 262K context)
# qwen3.5:9b = lightweight fallback (6.6GB, fast)
# qwen3.5:4b = ultra-fast simple tasks
TASK_TIER_OVERRIDE: dict[str, str | None] = {
    "mechanical": "ollama:qwen3.6-35b",          # fast: simple tasks via Rapid-MLX
    "integration": "ollama:qwen3.6-35b",          # coding/agentic workflows
    "architecture": "ollama:qwen3.6-35b",         # broad reasoning + content
}


def select_model_with_tier(
    profile: TaskProfile,
    state: SystemState,
    task_tier: str = "integration",
) -> ModelConfig:
    """Tiered model selection — LLM_MODEL env override has highest priority.

    Args:
        profile: Classified task profile.
        state: Current system state.
        task_tier: "mechanical", "integration", or "architecture".

    Returns:
        ModelConfig — may override matrix selection for mechanical tasks.
    """
    env_override = _env_override(profile)
    if env_override is not None:
        return env_override

    override = TASK_TIER_OVERRIDE.get(task_tier)
    if override:
        # Use cheap model for mechanical tasks
        provider = detect_provider(override)
        from src.core.cost_estimator import COST_TABLE
        costs = COST_TABLE.get(override, (0.0, 0.0))
        ctx = CONTEXT_WINDOW_MAP.get(override, 128000)
        return ModelConfig(
            model_id=override,
            provider=provider,
            max_tokens=int(ctx * 0.75),
            temperature=0.2,
            context_window=ctx,
            cost_per_mtok_input=costs[0],
            cost_per_mtok_output=costs[1],
        )
    # Default: use existing matrix logic
    return select_model(profile, state)
