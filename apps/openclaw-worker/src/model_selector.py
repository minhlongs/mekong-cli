"""Hybrid LLM Router - Model Selector (ALGO 2) - Stub for testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .task_classifier import TaskProfile


@dataclass
class SystemState:
    """System state cho model selection."""

    local_available: bool
    local_models: list[str]
    api_keys: dict[str, bool]
    local_load: float
    tenant_tier: str


@dataclass
class ModelConfig:
    """Model configuration."""

    model_id: str
    provider: Literal["ollama", "anthropic", "google", "openai"]
    max_tokens: int
    temperature: float
    context_window: int
    cost_per_mtok_input: float
    cost_per_mtok_output: float


class ModelSelector:
    """ALGO 2: Select model per agent+tier."""

    # Routing matrix
    ROUTING_MATRIX = {
        # (agent_role, complexity, requires_reasoning, data_sensitivity) → model
        # CTO: CODE
        ("cto", "simple", False, "public"): "gemini-2.0-flash",
        ("cto", "simple", False, "sensitive"): "ollama:deepseek-coder-v2:16b",
        ("cto", "standard", True, "public"): "claude-sonnet-4-6",
        ("cto", "standard", True, "sensitive"): "ollama:deepseek-coder-v2:33b",
        ("cto", "complex", True, "public"): "claude-opus-4-6",
        ("cto", "complex", True, "sensitive"): "ollama:deepseek-coder-v2:33b",
        # CMO/EDITOR: CREATIVE
        ("cmo", "simple", False, "public"): "gemini-2.0-flash",
        ("cmo", "simple", False, "internal"): "gemini-2.0-flash",
        ("cmo", "standard", True, "public"): "gemini-2.0-flash",
        ("cmo", "complex", True, "public"): "gemini-2.0-pro",
        ("editor", "simple", False, "public"): "gemini-2.0-flash",
        # COO: OPS
        ("coo", "simple", False, "public"): "ollama:llama3.2:3b",
        ("coo", "standard", False, "public"): "ollama:llama3.2:3b",
        ("coo", "complex", False, "public"): "ollama:llama3.2:3b",
        # CFO/DATA: ANALYSIS
        ("cfo", "simple", False, "sensitive"): "ollama:qwen2.5:7b",
        ("cfo", "standard", False, "public"): "gemini-2.0-flash-lite",
        ("data", "simple", False, "sensitive"): "ollama:qwen2.5:7b",
        ("data", "standard", False, "public"): "gemini-2.0-flash-lite",
        # CS: SUPPORT
        ("cs", "simple", False, "public"): "ollama:mistral:7b",
        ("cs", "standard", False, "public"): "claude-haiku-4-5",
        ("cs", "complex", True, "public"): "claude-haiku-4-5",
        # SALES
        ("sales", "simple", False, "public"): "claude-haiku-4-5",
        ("sales", "standard", True, "public"): "claude-sonnet-4-6",
        ("sales", "complex", True, "public"): "claude-sonnet-4-6",
    }

    COST_TABLE = {
        "claude-opus-4-6": (15.0, 75.0),
        "claude-sonnet-4-6": (3.0, 15.0),
        "claude-haiku-4-5": (0.25, 1.25),
        "gemini-2.0-flash": (0.075, 0.30),
        "gemini-2.0-flash-lite": (0.02, 0.08),
        "gemini-2.0-pro": (1.25, 5.0),
        "ollama:deepseek-coder-v2:33b": (0.0, 0.0),
        "ollama:deepseek-coder-v2:16b": (0.0, 0.0),
        "ollama:llama3.2:3b": (0.0, 0.0),
        "ollama:qwen2.5:7b": (0.0, 0.0),
        "ollama:mistral:7b": (0.0, 0.0),
    }

    CONTEXT_WINDOW_MAP = {
        "claude-opus-4-6": 200000,
        "claude-sonnet-4-6": 200000,
        "claude-haiku-4-5": 200000,
        "gemini-2.0-flash": 1000000,
        "gemini-2.0-pro": 2000000,
        "ollama:deepseek-coder-v2:33b": 128000,
        "ollama:llama3.2:3b": 8000,
    }

    TEMP_MAP = {
        "code": 0.2,
        "ops": 0.1,
        "analysis": 0.3,
        "creative": 0.8,
        "sales": 0.7,
        "support": 0.4,
    }

    def select(
        self, profile: TaskProfile, state: SystemState
    ) -> ModelConfig:
        """Select model dựa trên profile và system state."""
        # STEP 1: Lookup matrix
        key = (
            profile.agent_role,
            profile.complexity,
            profile.requires_reasoning,
            profile.data_sensitivity,
        )

        model_id = self.ROUTING_MATRIX.get(key)

        # Fallback với sensitivity wildcard
        if not model_id:
            wildcard_key = (
                profile.agent_role,
                profile.complexity,
                profile.requires_reasoning,
                "*",
            )
            model_id = self.ROUTING_MATRIX.get(wildcard_key)

        # Default fallback
        if not model_id:
            model_id = "gemini-2.0-flash"

        # STEP 2: Availability check
        if model_id.startswith("ollama:"):
            if not state.local_available:
                model_id = self._fallback_to_api(profile)
            elif state.local_load > 0.85:
                model_id = self._downgrade_local(model_id)
            else:
                model_name = model_id.split(":")[1]
                if model_name not in state.local_models:
                    model_id = self._fallback_to_api(profile)

        # STEP 3: Tenant tier override
        if state.tenant_tier == "starter" and model_id == "claude-opus-4-6":
            model_id = "claude-sonnet-4-6"

        # STEP 4: Build ModelConfig
        provider = self._detect_provider(model_id)
        costs = self.COST_TABLE.get(model_id, (0.0, 0.0))
        context = self.CONTEXT_WINDOW_MAP.get(model_id, 128000)
        temp = self.TEMP_MAP.get(profile.domain, 0.5)

        return ModelConfig(
            model_id=model_id,
            provider=provider,
            max_tokens=int(context * 0.75),
            temperature=temp,
            context_window=context,
            cost_per_mtok_input=costs[0],
            cost_per_mtok_output=costs[1],
        )

    def _detect_provider(self, model_id: str) -> Literal["ollama", "anthropic", "google", "openai"]:
        """Detect provider từ model_id."""
        if "ollama" in model_id:
            return "ollama"
        if "claude" in model_id:
            return "anthropic"
        if "gemini" in model_id:
            return "google"
        if "gpt" in model_id:
            return "openai"
        return "anthropic"  # Default

    def _fallback_to_api(self, profile: TaskProfile) -> str:
        """Fallback từ local → API."""
        if profile.domain == "code":
            return "claude-sonnet-4-6"
        return "gemini-2.0-flash"

    def _downgrade_local(self, model_id: str) -> str:
        """Downgrade local model do VRAM pressure."""
        # Simple downgrade: 70b → 33b → 7b → 3b
        if "70b" in model_id:
            return "ollama:deepseek-coder-v2:33b"
        if "33b" in model_id:
            return "ollama:qwen2.5:7b"
        return "ollama:llama3.2:3b"
