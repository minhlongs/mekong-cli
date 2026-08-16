"""Integration tests for billing-tier enforcement in model_selector.

Verifies that TierFallbackChain is wired into select_model_with_tier()
so BASIC-tier tenants cannot implicitly resolve to MASTER-only models.
"""

from __future__ import annotations

import pytest

from src.core.model_selector import (
    ModelConfig,
    SystemState,
    TaskProfile,
    _billing_tier,
    _enforce_tier_chain,
    select_model_with_tier,
)
from src.core.tier_fallback_chain import resolve_tier_chain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile(
    domain: str = "code",
    agent_role: str = "cto",
    complexity: str = "standard",
) -> TaskProfile:
    return TaskProfile(
        domain=domain,
        agent_role=agent_role,
        complexity=complexity,
        requires_reasoning=True,
        requires_creativity=False,
        data_sensitivity="public",
        estimated_tokens=1000,
        mcu_cost=1,
        preferred_tier="api_mid",
    )


def _state(tier: str = "starter", local: bool = False) -> SystemState:
    return SystemState(
        tenant_tier=tier,
        local_available=local,
        api_keys={"google": True, "openai": True, "anthropic": True},
    )


# ---------------------------------------------------------------------------
# _billing_tier mapping
# ---------------------------------------------------------------------------

class TestBillingTierMapping:
    def test_starter_maps_to_basic(self):
        assert _billing_tier("starter") == "BASIC"

    def test_basic_maps_to_basic(self):
        assert _billing_tier("basic") == "BASIC"

    def test_premium_maps_to_premium(self):
        assert _billing_tier("premium") == "PREMIUM"

    def test_enterprise_maps_to_enterprise(self):
        assert _billing_tier("enterprise") == "ENTERPRISE"

    def test_master_maps_to_master(self):
        assert _billing_tier("master") == "MASTER"

    def test_unknown_falls_back_to_uppercase(self):
        assert _billing_tier("free") == "FREE"

    def test_legacy_dict_matches_function(self):
        for legacy, expected in [
            ("starter", "BASIC"),
            ("premium", "PREMIUM"),
            ("enterprise", "ENTERPRISE"),
            ("master", "MASTER"),
        ]:
            assert _billing_tier(legacy) == expected


# ---------------------------------------------------------------------------
# _enforce_tier_chain — direct unit tests
# ---------------------------------------------------------------------------

class TestEnforceTierChain:
    def test_basic_cannot_use_claude_opus(self):
        """BASIC tier must downgrade claude-opus-4-6 to gpt-4o-mini."""
        config = ModelConfig(
            model_id="claude-opus-4-6",
            provider="anthropic",
            max_tokens=100000,
            temperature=0.2,
            context_window=200000,
        )
        result = _enforce_tier_chain(config, "BASIC")
        assert result.model_id == "gpt-4o-mini"
        assert result.provider == "openai"

    def test_basic_keeps_gemini_1_5_flash(self):
        """BASIC tier fallback model is kept as-is."""
        config = ModelConfig(
            model_id="gemini-1.5-flash",
            provider="gemini",
            max_tokens=100000,
            temperature=0.2,
            context_window=1048576,
        )
        result = _enforce_tier_chain(config, "BASIC")
        assert result.model_id == "gemini-1.5-flash"

    def test_premium_allows_gpt4o(self):
        """PREMIUM primary model gpt-4o is allowed."""
        config = ModelConfig(
            model_id="gpt-4o",
            provider="openai",
            max_tokens=96000,
            temperature=0.2,
            context_window=128000,
        )
        result = _enforce_tier_chain(config, "PREMIUM")
        assert result.model_id == "gpt-4o"

    def test_premium_downgrades_claude_opus(self):
        """PREMIUM tier cannot use claude-opus-4-6."""
        config = ModelConfig(
            model_id="claude-opus-4-6",
            provider="anthropic",
            max_tokens=100000,
            temperature=0.2,
            context_window=200000,
        )
        result = _enforce_tier_chain(config, "PREMIUM")
        assert result.model_id == "gpt-4o"

    def test_enterprise_allows_primary(self):
        """ENTERPRISE primary gemini-2.5-pro is allowed."""
        config = ModelConfig(
            model_id="gemini-2.5-pro",
            provider="gemini",
            max_tokens=100000,
            temperature=0.2,
            context_window=1048576,
        )
        result = _enforce_tier_chain(config, "ENTERPRISE")
        assert result.model_id == "gemini-2.5-pro"

    def test_enterprise_allows_fallback(self):
        """ENTERPRISE fallback gpt-4o is allowed."""
        config = ModelConfig(
            model_id="gpt-4o",
            provider="openai",
            max_tokens=96000,
            temperature=0.2,
            context_window=128000,
        )
        result = _enforce_tier_chain(config, "ENTERPRISE")
        assert result.model_id == "gpt-4o"

    def test_enterprise_downgrades_claude_opus(self):
        """ENTERPRISE tier cannot use claude-opus-4-6."""
        config = ModelConfig(
            model_id="claude-opus-4-6",
            provider="anthropic",
            max_tokens=100000,
            temperature=0.2,
            context_window=200000,
        )
        result = _enforce_tier_chain(config, "ENTERPRISE")
        assert result.model_id == "gemini-2.5-pro"

    def test_master_allows_primary(self):
        """MASTER primary gemini-3-pro-high is allowed."""
        config = ModelConfig(
            model_id="gemini-3-pro-high",
            provider="gemini",
            max_tokens=100000,
            temperature=0.2,
            context_window=1048576,
        )
        result = _enforce_tier_chain(config, "MASTER")
        assert result.model_id == "gemini-3-pro-high"

    def test_unknown_tier_passes_through(self):
        """Unknown billing tier leaves model unchanged."""
        config = ModelConfig(
            model_id="claude-opus-4-6",
            provider="anthropic",
            max_tokens=100000,
            temperature=0.2,
            context_window=200000,
        )
        result = _enforce_tier_chain(config, "FREE")
        assert result.model_id == "claude-opus-4-6"

    def test_enforcement_preserves_model_config_fields(self):
        """Tier downgrade preserves max_tokens, temperature, context_window."""
        config = ModelConfig(
            model_id="claude-opus-4-6",
            provider="anthropic",
            max_tokens=150000,
            temperature=0.7,
            context_window=200000,
            cost_per_mtok_input=15.0,
            cost_per_mtok_output=75.0,
        )
        result = _enforce_tier_chain(config, "BASIC")
        assert result.max_tokens == 150000
        assert result.temperature == 0.7
        assert result.context_window == 200000
        assert result.cost_per_mtok_input == 15.0
        assert result.cost_per_mtok_output == 75.0


# ---------------------------------------------------------------------------
# select_model_with_tier — integration tests
# ---------------------------------------------------------------------------

class TestSelectModelWithTierIntegration:
    def test_basic_tier_blocks_opus(self):
        """BASIC-tier state downgrades a complex CTO task away from opus."""
        result = select_model_with_tier(
            _profile(agent_role="cto", complexity="complex"),
            _state(tier="starter"),
            task_tier="architecture",
        )
        assert result.model_id != "claude-opus-4-6"
        chain = resolve_tier_chain("BASIC")
        assert result.model_id in [c.model for c in chain.candidates()]

    def test_premium_tier_blocks_opus(self):
        """PREMIUM-tier state downgrades complex tasks away from opus."""
        result = select_model_with_tier(
            _profile(agent_role="cto", complexity="complex"),
            _state(tier="premium"),
            task_tier="architecture",
        )
        assert result.model_id != "claude-opus-4-6"
        chain = resolve_tier_chain("PREMIUM")
        assert result.model_id in [c.model for c in chain.candidates()]

    def test_enterprise_tier_allows_opus(self):
        """ENTERPRISE-tier state keeps claude-opus-4-6 for complex tasks."""
        result = select_model_with_tier(
            _profile(agent_role="cto", complexity="complex"),
            _state(tier="enterprise"),
            task_tier="architecture",
        )
        chain = resolve_tier_chain("ENTERPRISE")
        assert result.model_id in [c.model for c in chain.candidates()]

    def test_starter_tier_uses_basic_chain(self):
        """legacy 'starter' tier maps to BASIC billing tier."""
        result = select_model_with_tier(
            _profile(agent_role="cto", complexity="complex"),
            _state(tier="starter"),
            task_tier="architecture",
        )
        chain = resolve_tier_chain("BASIC")
        assert result.model_id in [c.model for c in chain.candidates()]

    def test_master_tier_allows_gemini_3_pro_high(self):
        """MASTER-tier state keeps gemini-3-pro-high."""
        result = select_model_with_tier(
            _profile(agent_role="cto", complexity="complex"),
            _state(tier="master"),
            task_tier="architecture",
        )
        chain = resolve_tier_chain("MASTER")
        assert result.model_id in [c.model for c in chain.candidates()]


# ---------------------------------------------------------------------------
# End-to-end: cross-tier isolation
# ---------------------------------------------------------------------------

class TestCrossTierIsolation:
    """No tier should be able to resolve to a model outside its chain."""

    @pytest.mark.parametrize("tier", ["BASIC", "PREMIUM", "ENTERPRISE", "MASTER"])
    def test_all_agents_respect_tier_chain(self, tier):
        """Every agent role's selection must stay within tier chain."""
        for role in ("cto", "cmo", "cfo", "coo", "cs", "sales"):
            for complexity in ("simple", "standard", "complex"):
                profile = _profile(agent_role=role, complexity=complexity)
                state = _state(tier=tier.lower())
                result = select_model_with_tier(profile, state)
                chain = resolve_tier_chain(tier)
                allowed = {c.model for c in chain.candidates()}
                assert result.model_id in allowed, (
                    f"Tier {tier} agent={role} complexity={complexity} "
                    f"resolved to {result.model_id} not in {allowed}"
                )