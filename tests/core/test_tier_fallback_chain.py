"""Unit tests for src/core/tier_fallback_chain.py

Ground truth (from src/core/tier_fallback_chain.py):
  BASIC            primary=openai:gpt-4o-mini   fallback=gemini:gemini-1.5-flash
  PREMIUM          primary=openai:gpt-4o         fallback=gemini:gemini-2.0-flash
  ENTERPRISE       primary=gemini:gemini-2.5-pro  [openai:gpt-4o, openai:gpt-4o-mini]
  MASTER           primary=gemini:gemini-3-pro-high [gemini:gemini-2.5-pro, openai:gpt-4o]
"""

from __future__ import annotations

import pytest

from src.core.tier_fallback_chain import (
    FallbackCandidate,
    TierFallbackChain,
    resolve_tier_chain,
)


# ---------------------------------------------------------------------------
# FallbackCandidate
# ---------------------------------------------------------------------------

class TestFallbackCandidate:
    def test_model_ref_openai(self):
        c = FallbackCandidate(tier="BASIC", provider="openai", model="gpt-4o-mini")
        assert c.model_ref() == "openai:gpt-4o-mini"

    def test_model_ref_fable_5(self):
        c = FallbackCandidate(tier="ENTERPRISE", provider="fable-5", model="fable-5.5-pro")
        assert c.model_ref() == "fable-5:fable-5.5-pro"

    def test_reason_empty_by_default(self):
        c = FallbackCandidate(tier="BASIC", provider="openai", model="gpt-4o-mini")
        assert c.reason == ""

    def test_reason_set_when_provided(self):
        c = FallbackCandidate(
            tier="BASIC", provider="openai", model="fable-5o-mini", reason="primary"
        )
        assert c.reason == "primary"

    def test_frozen_dataclass(self):
        c = FallbackCandidate(tier="BASIC", provider="openai", model="gpt-4o-mini")
        with pytest.raises(AttributeError):
            c.model = "gpt-4o"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TierFallbackChain
# ---------------------------------------------------------------------------

class TestTierFallbackChain:
    def test_candidates_includes_primary_first(self):
        primary = FallbackCandidate(tier="X", provider="a", model="m1")
        fb = FallbackCandidate(tier="X", provider="b", model="m2")
        chain = TierFallbackChain(tier="X", primary=primary, fallbacks=(fb,))
        result = chain.candidates()
        assert result[0] is primary
        assert result[1] is fb
        assert len(result) == 2

    def test_candidates_no_fallbacks(self):
        primary = FallbackCandidate(tier="X", provider="a", model="m1")
        chain = TierFallbackChain(tier="X", primary=primary)
        result = chain.candidates()
        assert len(result) == 1
        assert result[0] is primary

    def test_select_returns_correct_candidate(self):
        primary = FallbackCandidate(tier="X", provider="a", model="m1")
        fb1 = FallbackCandidate(tier="X", provider="b", model="m2")
        fb2 = FallbackCandidate(tier="X", provider="c", model="m3")
        chain = TierFallbackChain(
            tier="X", primary=primary, fallbacks=(fb1, fb2)
        )
        assert chain.select(0) is primary
        assert chain.select(1) is fb1
        assert chain.select(2) is fb2

    def test_select_negative_index_raises(self):
        primary = FallbackCandidate(tier="X", provider="a", model="m1")
        chain = TierFallbackChain(tier="X", primary=primary)
        with pytest.raises(IndexError, match="out of range"):
            chain.select(-1)

    def test_select_past_end_raises(self):
        primary = FallbackCandidate(tier="X", provider="a", model="m1")
        chain = TierFallbackChain(tier="X", primary=primary)
        with pytest.raises(IndexError, match="out of range"):
            chain.select(1)

    def test_select_error_message_includes_tier_and_count(self):
        primary = FallbackCandidate(tier="PREMIUM", provider="a", model="m1")
        chain = TierFallbackChain(tier="PREMIUM", primary=primary)
        with pytest.raises(IndexError, match="PREMIUM.*1 candidate"):
            chain.select(5)

    def test_frozen_dataclass(self):
        primary = FallbackCandidate(tier="X", provider="a", model="m1")
        chain = TierFallbackChain(tier="X", primary=primary)
        with pytest.raises(AttributeError):
            chain.tier = "Y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# resolve_tier_chain — concrete values match src/core/tier_fallback_chain.py
# ---------------------------------------------------------------------------

class TestResolveTierChainBASIC:
    def test_primary_is_openai_gpt4o_mini(self):
        chain = resolve_tier_chain("BASIC")
        assert chain.primary.provider == "openai"
        assert chain.primary.model == "gpt-4o-mini"

    def test_fallback_is_gemini_1_5_flash(self):
        chain = resolve_tier_chain("BASIC")
        assert chain.fallbacks[0].provider == "gemini"
        assert chain.fallbacks[0].model == "gemini-1.5-flash"

    def test_two_candidates_total(self):
        chain = resolve_tier_chain("BASIC")
        assert len(chain.candidates()) == 2


class TestResolveTierChainPREMIUM:
    def test_primary_is_openai_gpt4o(self):
        chain = resolve_tier_chain("PREMIUM")
        assert chain.primary.provider == "openai"
        assert chain.primary.model == "gpt-4o"

    def test_fallback_is_gemini_2_0_flash(self):
        chain = resolve_tier_chain("PREMIUM")
        assert chain.fallbacks[0].provider == "gemini"
        assert chain.fallbacks[0].model == "gemini-2.0-flash"

    def test_two_candidates_total(self):
        chain = resolve_tier_chain("PREMIUM")
        assert len(chain.candidates()) == 2


class TestResolveTierChainENTERPRISE:
    def test_primary_is_gemini_gpt4o_5_pro(self):
        chain = resolve_tier_chain("ENTERPRISE")
        assert chain.primary.provider == "gemini"
        assert chain.primary.model == "gemini-2.5-pro"

    def test_first_fallback_is_openai_gpt4o(self):
        chain = resolve_tier_chain("ENTERPRISE")
        assert chain.fallbacks[0].provider == "openai"
        assert chain.fallbacks[0].model == "gpt-4o"

    def test_second_fallback_is_openai_gpt4o_mini(self):
        chain = resolve_tier_chain("ENTERPRISE")
        assert chain.fallbacks[1].provider == "openai"
        assert chain.fallbacks[1].model == "gpt-4o-mini"

    def test_three_candidates_total(self):
        chain = resolve_tier_chain("ENTERPRISE")
        assert len(chain.candidates()) == 3


class TestResolveTierChainMASTER:
    def test_primary_is_gemini_3_pro_high(self):
        chain = resolve_tier_chain("MASTER")
        assert chain.primary.provider == "gemini"
        assert chain.primary.model == "gemini-3-pro-high"

    def test_first_fallback_is_gemini_fable_5_5_pro(self):
        chain = resolve_tier_chain("MASTER")
        assert chain.fallbacks[0].provider == "gemini"
        assert chain.fallbacks[0].model == "gemini-2.5-pro"

    def test_second_fallback_is_openai_gpt4o(self):
        chain = resolve_tier_chain("MASTER")
        assert chain.fallbacks[1].provider == "openai"
        assert chain.fallbacks[1].model == "gpt-4o"

    def test_three_candidates_total(self):
        chain = resolve_tier_chain("MASTER")
        assert len(chain.candidates()) == 3


# ---------------------------------------------------------------------------
# resolve_tier_chain — unknown tier
# ---------------------------------------------------------------------------

class TestResolveTierChainUnknown:
    def test_unknown_tier_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown billing tier 'FREE'"):
            resolve_tier_chain("FREE")

    def test_lowercase_raises(self):
        with pytest.raises(ValueError):
            resolve_tier_chain("basic")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            resolve_tier_chain("")

    def test_error_message_lists_valid_tiers(self):
        with pytest.raises(ValueError, match="BASIC.*PREMIUM.*ENTERPRISE.*MASTER"):
            resolve_tier_chain("INVALID")


# ---------------------------------------------------------------------------
# Chain candidates() integration with real tier chains
# ---------------------------------------------------------------------------

class TestChainCandidatesIntegration:
    def test_all_candidates_have_model_ref(self):
        for tier in ("BASIC", "PREMIUM", "ENTERPRISE", "MASTER"):
            chain = resolve_tier_chain(tier)
            for candidate in chain.candidates():
                ref = candidate.model_ref()
                assert ":" in ref, f"model_ref missing colon for {tier}: {ref}"

    def test_candidate_count_by_tier(self):
        assert len(resolve_tier_chain("BASIC").candidates()) == 2
        assert len(resolve_tier_chain("PREMIUM").candidates()) == 2
        assert len(resolve_tier_chain("ENTERPRISE").candidates()) == 3
        assert len(resolve_tier_chain("MASTER").candidates()) == 3


# ---------------------------------------------------------------------------
# Tier fallback chain selection integration
# ---------------------------------------------------------------------------

class TestChainSelectDegradation:
    def test_select_next_candidate(self):
        chain = resolve_tier_chain("ENTERPRISE")
        primary = chain.select(0)
        first_fallback = chain.select(1)
        assert primary.model_ref() == "gemini:gemini-2.5-pro"
        assert first_fallback.model_ref() == "openai:gpt-4o"

    def test_select_degraded_fallback(self):
        chain = resolve_tier_chain("MASTER")
        third = chain.select(2)
        assert third.model_ref() == "openai:gpt-4o"