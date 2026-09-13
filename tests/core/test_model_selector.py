# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for ALGO 2 — Model Selector (src/core/model_selector.py).

Provides full test coverage for provider detection, routing matrix lookups,
environment overrides, local model downgrade/fallbacks, cost strategy selection,
and billing tier enforcement.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.core.model_selector import (
    CONTEXT_WINDOW_MAP,
    COST_TABLE,
    CostStrategy,
    ModelConfig,
    SystemState,
    _cost_eligible,
    _env_override,
    _lookup_matrix,
    _model_config_from_id,
    cost_strategy_for,
    detect_provider,
    select_model,
    select_model_with_tier,
)
from src.core.task_classifier import TaskProfile


@pytest.fixture(autouse=True)
def clean_llm_model_env():
    """Ensure LLM_MODEL env var is cleared for model selector tests."""
    with patch.dict(os.environ):
        if "LLM_MODEL" in os.environ:
            del os.environ["LLM_MODEL"]
        yield


def _make_profile(**overrides) -> TaskProfile:
    """Helper to create TaskProfile with defaults."""
    defaults = {
        "complexity": "simple",
        "domain": "code",
        "agent_role": "cto",
        "requires_reasoning": False,
        "requires_creativity": False,
        "data_sensitivity": "public",
        "estimated_tokens": 1200,
        "mcu_cost": 1,
        "preferred_tier": "api_cheap",
    }
    defaults.update(overrides)
    return TaskProfile(**defaults)


def _make_state(**overrides) -> SystemState:
    """Helper to create SystemState with defaults."""
    defaults = {
        "local_available": True,
        "local_models": [
            "deepseek-coder-v2:16b",
            "llama3.2:3b",
            "qwen2.5:7b",
            "mistral:7b",
            "qwen3.6-35b",
            "qwen3.5:35b",
        ],
        "api_keys": {"anthropic": True, "google": True, "openai": True, "gemini": True},
        "local_load": 0.3,
        "tenant_tier": "starter",
    }
    defaults.update(overrides)
    return SystemState(**defaults)


# ===========================================================================
# detect_provider
# ===========================================================================

class TestDetectProvider:
    def test_ollama_provider(self):
        assert detect_provider("ollama:llama3.2:3b") == "ollama"

    def test_mlx_provider(self):
        assert detect_provider("mlx:llama3.2:3b") == "mlx"

    def test_gemini_provider(self):
        assert detect_provider("gemini-2.0-flash") == "gemini"
        assert detect_provider("gemini:gemini-2.5-flash") == "gemini"

    def test_openai_providers(self):
        assert detect_provider("gpt-4o") == "openai"
        assert detect_provider("gpt-4o-mini") == "openai"
        assert detect_provider("o1-preview") == "openai"
        assert detect_provider("o3-mini") == "openai"

    def test_anthropic_providers(self):
        assert detect_provider("anthropic:claude-3-5") == "anthropic"
        assert detect_provider("claude-sonnet-4-6") == "anthropic"
        assert detect_provider("claude-opus-4-6") == "anthropic"

    def test_unknown_provider(self):
        assert detect_provider("unknown-custom-model") == "unknown"


# ===========================================================================
# _lookup_matrix
# ===========================================================================

class TestLookupMatrix:
    def test_exact_match(self):
        profile = _make_profile(
            agent_role="cto", complexity="simple", requires_reasoning=False, data_sensitivity="public"
        )
        assert _lookup_matrix(profile) == "gemini:gemini-2.0-flash"

    def test_sensitive_cto(self):
        profile = _make_profile(
            agent_role="cto", complexity="simple", requires_reasoning=False, data_sensitivity="sensitive"
        )
        assert _lookup_matrix(profile) == "ollama:qwen3.6-35b"

    def test_wildcard_sensitivity(self):
        profile = _make_profile(
            agent_role="cmo", complexity="simple", requires_reasoning=False, data_sensitivity="internal"
        )
        assert _lookup_matrix(profile) == "gemini:gemini-2.0-flash"

    def test_no_match_returns_none(self):
        profile = _make_profile(agent_role="nonexistent_role", complexity="extreme")
        assert _lookup_matrix(profile) is None


# ===========================================================================
# _env_override
# ===========================================================================

class TestEnvOverride:
    def test_no_env_set(self):
        profile = _make_profile()
        assert _env_override(profile) is None

    def test_env_set_with_known_prefix(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        profile = _make_profile(domain="creative")
        cfg = _env_override(profile)
        assert cfg is not None
        assert cfg.model_id == "gpt-4o"
        assert cfg.provider == "openai"
        assert cfg.temperature == 0.8  # creative domain

    def test_env_set_without_prefix_defaults_to_ollama(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "my-custom-model")
        profile = _make_profile()
        cfg = _env_override(profile)
        assert cfg is not None
        assert cfg.model_id == "ollama:my-custom-model"
        assert cfg.provider == "ollama"

    def test_sensitive_data_blocks_non_local_env_override(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "claude-opus-4-6")
        profile = _make_profile(data_sensitivity="sensitive")
        assert _env_override(profile) is None

    def test_sensitive_data_allows_local_env_override(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "ollama:qwen3.6-35b")
        profile = _make_profile(data_sensitivity="sensitive")
        cfg = _env_override(profile)
        assert cfg is not None
        assert cfg.model_id == "ollama:qwen3.6-35b"


# ===========================================================================
# Cost Eligibility & Strategy
# ===========================================================================

class TestCostEligibilityAndStrategy:
    def test_cost_eligible_free_model(self):
        assert _cost_eligible("ollama:qwen3.6-35b", "simple") is True

    def test_cost_eligible_paid_model(self):
        assert _cost_eligible("gemini:gemini-2.0-flash", "simple") is True
        assert _cost_eligible("gemini:gemini-2.0-flash", "complex") is False

    def test_cost_eligible_without_colon(self):
        assert _cost_eligible("gpt-4o", "simple") is True
        assert _cost_eligible("unknown-model", "simple") is True

    def test_model_config_from_id_valid(self):
        cfg = _model_config_from_id("gemini:gemini-2.0-flash")
        assert cfg is not None
        assert cfg.model_id == "gemini:gemini-2.0-flash"
        assert cfg.provider == "gemini"

    def test_model_config_from_id_unknown(self):
        assert _model_config_from_id("unknown-xyz") is None

    def test_cost_strategy_for(self):
        strat = cost_strategy_for("starter")
        assert isinstance(strat, CostStrategy)
        assert strat.min_complexity == "simple"
        assert strat.max_cost_cap == 1.0

    def test_cost_strategy_select_candidates(self):
        strat = CostStrategy(max_cost_cap=1.0, min_complexity="simple", allow_free=True)
        profile = _make_profile(agent_role="cto", complexity="simple")
        state = _make_state(
            local_available=True,
            local_models=["qwen3.6-35b", "qwen3.5:35b", "qwen3.5:9b"],
        )
        chosen = strat.select(profile, state)
        assert isinstance(chosen, ModelConfig)
        # Should pick cheapest free local or low-cost model
        assert chosen.cost_per_mtok_input + chosen.cost_per_mtok_output <= 1.0

    def test_cost_strategy_is_available_ollama_not_available(self):
        strat = CostStrategy(max_cost_cap=1.0, min_complexity="simple", allow_free=True)
        cfg = _model_config_from_id("ollama:qwen3.6-35b")
        assert cfg is not None
        state_no_local = _make_state(local_available=False)
        assert strat._is_available(cfg, state_no_local) is False

    def test_cost_strategy_collect_candidates_skips_invalid_config(self):
        strat = CostStrategy(max_cost_cap=1.0, min_complexity="simple", allow_free=True)
        profile = _make_profile(agent_role="cto", complexity="simple")
        state = _make_state()
        with patch.dict(COST_TABLE, {"unknown-custom-model": (0.01, 0.02)}):
            candidates = strat._collect_candidates(profile, state)
            assert isinstance(candidates, list)
            assert not any(c.model_id == "unknown-custom-model" for c in candidates)

    def test_cost_strategy_select_fallback_when_no_candidates(self):
        strat = CostStrategy(max_cost_cap=0.0001, min_complexity="simple", allow_free=False)
        profile = _make_profile(agent_role="cto", complexity="simple")
        state = _make_state(
            local_available=False,
            api_keys={"google": False, "openai": False, "anthropic": False, "gemini": False},
        )
        chosen = strat.select(profile, state)
        assert isinstance(chosen, ModelConfig)


# ===========================================================================
# select_model & Fallback Rules
# ===========================================================================

class TestSelectModel:
    def test_basic_selection(self):
        profile = _make_profile(
            agent_role="cto", complexity="simple", requires_reasoning=False, data_sensitivity="public"
        )
        state = _make_state()
        config = select_model(profile, state)
        assert isinstance(config, ModelConfig)
        assert config.model_id == "gemini:gemini-2.0-flash"

    def test_env_override_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        profile = _make_profile()
        state = _make_state()
        config = select_model(profile, state)
        assert config.model_id == "gpt-4o"

    def test_local_unavailable_falls_back_to_gemini(self):
        profile = _make_profile(
            agent_role="cto", complexity="simple", requires_reasoning=False, data_sensitivity="sensitive"
        )
        state = _make_state(local_available=False)
        config = select_model(profile, state)
        assert config.model_id == "gemini:gemini-2.0-flash"

    def test_vram_pressure_downgrades_local_model(self):
        profile = _make_profile(
            agent_role="cto", complexity="simple", requires_reasoning=False, data_sensitivity="sensitive"
        )
        # High local load > 0.85
        state = _make_state(local_available=True, local_load=0.9)
        config = select_model(profile, state)
        # ollama:qwen3.6-35b downgrades to ollama:qwen3.5:35b
        assert config.model_id == "ollama:qwen3.5:35b"

    def test_local_model_not_pulled_falls_back_to_gemini(self):
        profile = _make_profile(
            agent_role="cto", complexity="simple", requires_reasoning=False, data_sensitivity="sensitive"
        )
        # Target local model qwen3.6-35b not in local_models
        state = _make_state(local_available=True, local_models=["mistral:7b"])
        config = select_model(profile, state)
        assert config.model_id == "gemini:gemini-2.0-flash"

    def test_missing_api_key_with_local_available_uses_best_local(self):
        profile = _make_profile(
            agent_role="cto", domain="code", complexity="simple", data_sensitivity="public"
        )
        # Provider gemini has no API key, but local is available
        state = _make_state(
            local_available=True,
            api_keys={"gemini": False, "google": False, "anthropic": False, "openai": False},
        )
        config = select_model(profile, state)
        assert config.model_id == "ollama:qwen3.6-35b"

    def test_missing_api_key_without_local_available_falls_back_to_gemini(self):
        profile = _make_profile(
            agent_role="cto", domain="code", complexity="simple", data_sensitivity="public"
        )
        state = _make_state(
            local_available=False,
            api_keys={"gemini": False, "google": False, "anthropic": False, "openai": False},
        )
        config = select_model(profile, state)
        assert config.model_id == "gemini:gemini-2.0-flash"

    def test_starter_downgrades_claude_opus(self):
        profile = _make_profile(
            agent_role="cto", complexity="simple", data_sensitivity="public"
        )
        state = _make_state(tenant_tier="starter")
        with patch("src.core.model_selector._lookup_matrix", return_value="claude-opus-4-6"):
            config = select_model(profile, state)
            assert config.model_id == "gemini:gemini-2.5-flash"

    def test_starter_local_override_for_non_code_domains(self):
        profile = _make_profile(
            agent_role="cmo", domain="creative", complexity="simple", data_sensitivity="public"
        )
        state = _make_state(tenant_tier="starter", local_available=True)
        config = select_model(profile, state)
        assert config.model_id == "ollama:qwen3.6-35b"

    def test_max_tokens_and_costs_calculated(self):
        profile = _make_profile(agent_role="cto", complexity="simple")
        state = _make_state()
        config = select_model(profile, state)
        assert config.max_tokens == int(CONTEXT_WINDOW_MAP["gemini:gemini-2.0-flash"] * 0.75)
        costs = COST_TABLE["gemini:gemini-2.0-flash"]
        assert config.cost_per_mtok_input == costs[0]
        assert config.cost_per_mtok_output == costs[1]


# ===========================================================================
# select_model_with_tier
# ===========================================================================

class TestSelectModelWithTier:
    def test_env_override_with_tier(self, monkeypatch):
        monkeypatch.setenv("LLM_MODEL", "gpt-4o")
        profile = _make_profile()
        state = _make_state()
        config = select_model_with_tier(profile, state)
        assert config.model_id == "gpt-4o"

    def test_task_tier_override_mechanical(self):
        profile = _make_profile()
        state = _make_state(tenant_tier="premium")
        config = select_model_with_tier(profile, state, task_tier="mechanical")
        assert config.model_id == "gemini:gemini-2.0-flash"

    def test_task_tier_unrecognized_falls_back_to_select_model(self):
        profile = _make_profile(agent_role="cto", complexity="simple")
        state = _make_state(tenant_tier="master")
        config = select_model_with_tier(profile, state, task_tier="unknown_tier")
        assert isinstance(config, ModelConfig)
        assert config.model_id in ["gemini:gemini-2.0-flash", "gemini-3-pro-high"]
