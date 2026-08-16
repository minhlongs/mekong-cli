"""ALGO 2 — Model Selector.

Selects the optimal LLM model based on TaskProfile and system state.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

from src.core.task_classifier import TaskProfile
from src.core.tier_fallback_chain import TierFallbackChain, resolve_tier_chain

logger = logging.getLogger(__name__)


# Compatibility: map legacy "starter" to BASIC billing tier.
# Preserves existing callers that pass "starter"; anything else is treated
# as a billing tier name (BASIC | PREMIUM | ENTERPRISE | MASTER).
LEGACY_TIER_TO_BILLING: dict[str, str] = {
    "starter": "BASIC",
    "basic": "BASIC",
    "premium": "PREMIUM",
    "enterprise": "ENTERPRISE",
    "master": "MASTER",
}


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


# (agent_role, complexity, requires_reasoning, data_sensitivity) -> model_id
MODEL_ROUTING_MATRIX: dict[tuple[str, str, str | bool, str], str] = {
    # CTO: CODE
    ("cto", "simple", False, "public"): "gemini:gemini-2.0-flash",
    ("cto", "simple", False, "internal"): "gemini:gemini-2.0-flash",
    ("cto", "simple", False, "sensitive"): "ollama:qwen3.6-35b",
    ("cto", "standard", False, "public"): "gemini:gemini-2.5-flash",
    ("cto", "standard", False, "internal"): "gemini:gemini-2.5-flash",
    ("cto", "standard", False, "sensitive"): "ollama:qwen3.6-35b",
    ("cto", "complex", False, "public"): "gemini:gemini-2.5-flash",
    ("cto", "complex", False, "internal"): "gemini:gemini-2.5-flash",
    ("cto", "complex", False, "sensitive"): "ollama:qwen3.6-35b",
    # CMO/EDITOR: CREATIVE
    ("cmo", "simple", False, "*"): "gemini:gemini-2.0-flash",
    ("cmo", "standard", False, "*"): "gemini:gemini-2.0-flash",
    ("cmo", "complex", True, "*"): "gemini:gemini-2.5-flash",
    ("editor", "simple", False, "*"): "gemini:gemini-2.0-flash",
    ("editor", "standard", False, "*"): "gemini:gemini-2.0-flash",
    ("editor", "complex", False, "*"): "gemini:gemini-2.0-flash",
    # COO: OPS (prefer local)
    ("coo", "simple", False, "*"): "ollama:qwen3.6-35b",
    ("coo", "standard", False, "*"): "ollama:qwen3.6-35b",
    ("coo", "complex", False, "*"): "ollama:qwen3.6-35b",
    # CFO/DATA: ANALYSIS
    ("cfo", "simple", False, "sensitive"): "ollama:qwen3.6-35b",
    ("cfo", "simple", False, "public"): "gemini:gemini-2.0-flash",
    ("cfo", "standard", False, "sensitive"): "ollama:qwen3.6-35b",
    ("cfo", "standard", False, "public"): "gemini:gemini-2.5-flash",
    ("cfo", "complex", False, "sensitive"): "ollama:qwen3.6-35b",
    ("cfo", "complex", False, "public"): "gemini:gemini-2.5-flash",
    ("data", "simple", False, "sensitive"): "ollama:qwen3.6-35b",
    ("data", "simple", False, "public"): "gemini:gemini-2.0-flash",
    ("data", "standard", False, "sensitive"): "ollama:qwen3.6-35b",
    ("data", "standard", False, "public"): "gemini:gemini-2.5-flash",
    ("data", "complex", False, "sensitive"): "ollama:qwen3.6-35b",
    ("data", "complex", False, "public"): "gemini:gemini-2.5-flash",
    # CS: SUPPORT
    ("cs", "simple", False, "*"): "ollama:qwen3.6-35b",
    ("cs", "standard", False, "*"): "gemini:gemini-2.5-flash",
    ("cs", "complex", True, "*"): "gemini:gemini-2.5-flash",
    # SALES
    ("sales", "simple", False, "*"): "gemini:gemini-2.0-flash",
    ("sales", "standard", False, "*"): "gemini:gemini-2.5-flash",
    ("sales", "complex", True, "*"): "gemini:gemini-2.5-flash",
}

CONTEXT_WINDOW_MAP: dict[str, int] = {
    "gemini:gemini-2.5-flash": 1048576,
    "gemini:gemini-2.0-flash": 1048576,
    "ollama:qwen3.6-35b": 32768,
    "ollama:qwen3.5:35b": 32768,
    "ollama:qwen3.5:9b": 32768,
    "ollama:qwen3.5:2b": 32768,
    "ollama:qwen3-fast": 4096,
    "ollama:qwen3-think": 4096,
}

COST_TABLE: dict[str, tuple[float, float]] = {
    "gemini:gemini-2.5-flash": (0.15, 0.6),
    "gemini:gemini-2.0-flash": (0.1, 0.4),
    "ollama:qwen3.6-35b": (0.0, 0.0),
    "ollama:qwen3.5:35b": (0.0, 0.0),
    "ollama:qwen3.5:9b": (0.0, 0.0),
    "ollama:qwen3.5:2b": (0.0, 0.0),
    "ollama:qwen3-fast": (0.0, 0.0),
    "ollama:qwen3-think": (0.0, 0.0),
}

TEMP_MAP: dict[str, float] = {
    "code": 0.2,
    "creative": 0.8,
    "grounded": 0.0,
    "ops": 0.1,
    "analytics": 0.3,
    "sales": 0.7,
    "support": 0.4,
}

BEST_LOCAL_FOR_DOMAIN: dict[str, str] = {
    "code": "ollama:qwen3.6-35b",
    "creative": "ollama:qwen3.6-35b",
    "grounded": "ollama:qwen3.6-35b",
    "ops": "ollama:qwen3.6-35b",
    "analytics": "ollama:qwen3.6-35b",
    "sales": "ollama:qwen3.6-35b",
    "support": "ollama:qwen3.6-35b",
}

LOCAL_DOWNGRADE: dict[str, str] = {
    "ollama:qwen3.6-35b": "ollama:qwen3.5:35b",
    "ollama:qwen3.5:35b": "ollama:qwen3.5:9b",
    "ollama:qwen3.5:9b": "ollama:qwen3.5:2b",
    "ollama:qwen3.5:2b": "ollama:qwen3-fast",
    "ollama:qwen3-fast": "ollama:qwen3-fast",
    "ollama:qwen3-think": "ollama:qwen3-fast",
}


def detect_provider(model_id: str) -> str:
    if model_id.startswith("ollama:"):
        return "ollama"
    if model_id.startswith("mlx:"):
        return "mlx"
    if model_id.startswith("gemini"):
        return "gemini"
    if model_id.startswith("gpt") or model_id.startswith("o1") or model_id.startswith("o3"):
        return "openai"
    if model_id.startswith("anthropic"):
        return "anthropic"
    if "claude" in model_id:
        return "anthropic"
    if model_id.startswith("gemini"):
        return "google"
    if model_id.startswith("gpt"):
        return "openai"
    return "unknown"


def _lookup_matrix(profile: TaskProfile) -> str | None:
    key = (profile.agent_role, profile.complexity,
           profile.requires_reasoning, profile.data_sensitivity)
    if key in MODEL_ROUTING_MATRIX:
        return MODEL_ROUTING_MATRIX[key]
    wildcard_key = (profile.agent_role, profile.complexity,
                    profile.requires_reasoning, "*")
    if wildcard_key in MODEL_ROUTING_MATRIX:
        return MODEL_ROUTING_MATRIX[wildcard_key]
    return None


def _env_override(profile: TaskProfile) -> ModelConfig | None:
    import os
    env_model = os.environ.get("LLM_MODEL", "").strip()
    if not env_model:
        return None
    known_prefixes = ("ollama:", "mlx:", "claude", "gemini", "gpt")
    model_id = env_model if env_model.startswith(known_prefixes) else f"ollama:{env_model}"
    if profile.data_sensitivity == "sensitive" and not model_id.startswith(("ollama:", "mlx:")):
        return None
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


def _billing_tier(tenant_tier: str) -> str:
    return LEGACY_TIER_TO_BILLING.get(tenant_tier.lower(), tenant_tier.upper())


def _model_ref_for_tier_chain(model_id: str) -> str:
    provider = detect_provider(model_id)
    model_part = model_id.split(":", 1)[1] if ":" in model_id else model_id
    model_part = model_part.replace("_", "-")
    # Tier chain uses registry/provider names that differ from raw detect_provider()
    # outputs for some providers (e.g. detect returns 'google' for gemini models).
    provider = {
        "google": "gemini",
    }.get(provider, provider)
    return f"{provider}:{model_part}"


def _model_ref_basename(model_ref: str) -> str:
    return model_ref.split(":", 1)[1] if ":" in model_ref else model_ref


def _enforce_tier_chain(
    model_config: ModelConfig,
    billing_tier: str,
) -> ModelConfig:
    """Return model_config as-is if allowed by tier, else downgrade to primary."""
    try:
        chain: TierFallbackChain = resolve_tier_chain(billing_tier)
    except ValueError:
        return model_config

    model_ref = _model_ref_for_tier_chain(model_config.model_id)
    allowed_refs = {c.model_ref() for c in chain.candidates()}

    if model_ref in allowed_refs:
        return model_config

    primary = chain.primary
    return ModelConfig(
        model_id=_model_ref_basename(primary.model_ref()),
        provider=primary.provider,  # type: ignore[arg-type]
        max_tokens=model_config.max_tokens,
        temperature=model_config.temperature,
        context_window=model_config.context_window,
        cost_per_mtok_input=model_config.cost_per_mtok_input,
        cost_per_mtok_output=model_config.cost_per_mtok_output,
    )


def select_model(profile: TaskProfile, state: SystemState) -> ModelConfig:
    """Select model from routing matrix with local/API fallbacks.

    Selection rules:
    1. LLM_MODEL env override (hard override unless sensitive path).
    2. MODEL_ROUTING_MATRIX lookup for the task/agent/sensitivity.
    3. Availability fallback: if selected model is not local or API key missing,
       fall back to alternative (local best or API default).
    4. Tenant tier capability override: starter/soft tier restricts to
       best-local for non-code/sales domains and downgrades from
       claude-opus to claude-sonnet.

    Returns:
        ModelConfig for a model that is expected to be available.
    """
    override = _env_override(profile)
    if override is not None:
        return override

    model_id = _lookup_matrix(profile) or "gemini:gemini-2.0-flash"
    logger.debug("select model matrix -> %s", model_id)

    # Local availability: validate local model availability
    if model_id.startswith("ollama:"):
        if not state.local_available:
            logger.debug("local model %s not available, falling back", model_id)
            model_id = "gemini:gemini-2.0-flash"
        elif state.local_load > 0.85:
            model_id = LOCAL_DOWNGRADE.get(model_id, model_id)
            logger.debug("VRAM pressure -> downgraded to %s", model_id)
        else:
            local_name = model_id.split(":", 1)[1]
            if local_name not in state.local_models:
                model_id = "gemini:gemini-2.0-flash"
                logger.debug("local model %s not pulled, fallback API", local_name)
    else:
        provider = detect_provider(model_id)
        logger.debug("provider detect %s -> %s", model_id, provider)
        if not state.api_keys.get(provider, False):
            logger.debug("provider %s key missing", provider)
            if state.local_available:
                model_id = BEST_LOCAL_FOR_DOMAIN.get(
                    profile.domain, "ollama:qwen3.6-35b")
                logger.debug("fallback local domain -> %s", model_id)
            else:
                model_id = "gemini:gemini-2.0-flash"
                logger.debug("fallback API default -> %s", model_id)

    if state.tenant_tier == "starter" and model_id == "claude-opus-4-6":
        model_id = "gemini:gemini-2.5-flash"
        logger.debug("starter tier downgrade opus -> %s", model_id)

    if (state.tenant_tier == "starter"
            and state.local_available
            and profile.domain not in ("code", "sales")):
        model_id = BEST_LOCAL_FOR_DOMAIN.get(profile.domain, model_id)
        logger.debug("starter local override domain=%s -> %s", profile.domain, model_id)

    ctx_window = CONTEXT_WINDOW_MAP.get(model_id, 128000)
    costs = COST_TABLE.get(model_id, (0.0, 0.0))
    provider = detect_provider(model_id)
    return ModelConfig(
        model_id=model_id,
        provider=provider,  # type: ignore[arg-type]
        max_tokens=int(ctx_window * 0.75),
        temperature=TEMP_MAP.get(profile.domain, 0.3),
        context_window=ctx_window,
        cost_per_mtok_input=costs[0],
        cost_per_mtok_output=costs[1],
    )


TASK_TIER_OVERRIDE: dict[str, str | None] = {
    "mechanical": "gemini:gemini-2.0-flash",
    "integration": "gemini:gemini-2.5-flash",
    "architecture": "gemini:gemini-2.5-flash",
}


def select_model_with_tier(
    profile: TaskProfile,
    state: SystemState,
    task_tier: str = "integration",
) -> ModelConfig:
    """Tiered model selection — LLM_MODEL env override has highest priority.

    Tier enforcement: if the chosen model is not in the billing tier's
    fallback chain, replace it with the tier's primary (highest-tier) contract.
    """
    env_override = _env_override(profile)
    if env_override is not None:
        return env_override

    override = TASK_TIER_OVERRIDE.get(task_tier)
    if override:
        from src.core.cost_estimator import COST_TABLE
        costs = COST_TABLE.get(override, (0.0, 0.0))
        ctx = CONTEXT_WINDOW_MAP.get(override, 128000)
        result = ModelConfig(
            model_id=override,
            provider=detect_provider(override),
            max_tokens=int(ctx * 0.75),
            temperature=0.2,
            context_window=ctx,
            cost_per_mtok_input=costs[0],
            cost_per_mtok_output=costs[1],
        )
        return _enforce_tier_chain(result, _billing_tier(state.tenant_tier))

    result = select_model(profile, state)
    return _enforce_tier_chain(result, _billing_tier(state.tenant_tier))