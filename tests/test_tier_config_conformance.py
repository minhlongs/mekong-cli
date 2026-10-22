"""Conformance tests for Tier Configuration & Façade.

Validates:
- Re-export façade at engine.billing.tier_config exports all required symbols
- Tier is TierKey identity and complete enum membership
- Case-insensitive instantiation and legacy alias resolution
- RateLimitConfig and TierRateLimitConfig defaults and invariants
- get_tier_config and get_preset_config lookups across canonical and alias names
- Integration with LicenseEnforcer hierarchy (FREE -> TRIAL -> STARTER -> GROWTH -> PRO -> ENTERPRISE -> MASTER)
- Master is a canonical entitlement, not an alias folded onto pro
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

# Test re-export façade imports
from engine.billing.tier_config import (
    DEFAULT_TIER_CONFIGS,
    RateLimitConfig,
    Tier,
    TierKey,
    TierRateLimitConfig,
    get_preset_config,
    get_tier_config,
)
from engine.license.license_enforcer import LicenseEnforcer
import src.seed.config.tiers as canonical_tiers


class TestFaçadeIdentity:
    """Verify façade forwards directly to canonical module."""

    def test_tier_identity(self):
        assert Tier is TierKey
        assert Tier is canonical_tiers.Tier
        assert TierKey is canonical_tiers.TierKey

    def test_ratelimit_config_identity(self):
        assert RateLimitConfig is canonical_tiers.RateLimitConfig
        assert TierRateLimitConfig is canonical_tiers.TierRateLimitConfig

    def test_helper_functions_identity(self):
        assert get_tier_config is canonical_tiers.get_tier_config
        assert get_preset_config is canonical_tiers.get_preset_config
        assert DEFAULT_TIER_CONFIGS is canonical_tiers.DEFAULT_TIER_CONFIGS


class TestTierEnumAndAliases:
    """Verify TierKey members and case-insensitive/alias resolution."""

    def test_all_canonical_members_present(self):
        expected = ["free", "trial", "starter", "growth", "pro", "enterprise", "master"]
        assert [t.value for t in Tier] == expected

    def test_master_is_a_canonical_entitlement_not_an_alias(self):
        """Master must resolve through aliases() to its own canonical key.

        The entitlement layers rank licenses on aliases() output, so a folded
        MASTER alias silently serves the pro ladder to a master buyer even
        though the enum has a master member. Asserting through the alias map —
        not through TierKey(...) — is what actually pins the behaviour.
        """
        aliases = TierKey.aliases()

        assert aliases["MASTER"] == "master", "MASTER must not fold onto pro"
        assert aliases["master"] == "master"
        assert aliases["master_vn"] == "master"
        assert aliases["PRO"] == "pro", "asserting through the member API would miss this"

        # Every paid tier keeps its own bucket: no paid canonical key absorbs
        # another paid canonical key's aliases.
        for paid in ("pro", "enterprise", "master"):
            assert aliases[paid] == paid

        assert TierKey("MASTER") is TierKey.MASTER
        assert TierKey("master_vn") is TierKey.MASTER
        # master outranks enterprise on the canonical ladder
        assert [t.value for t in Tier].index("master") > [t.value for t in Tier].index("enterprise")

    @pytest.mark.parametrize(
        ("input_val", "expected_member"),
        [
            ("free", Tier.FREE),
            ("FREE", Tier.FREE),
            ("trial", Tier.TRIAL),
            ("TRIAL", Tier.TRIAL),
            ("starter", Tier.STARTER),
            ("STARTER", Tier.STARTER),
            ("basic", Tier.STARTER),
            ("BASIC", Tier.STARTER),
            ("growth", Tier.GROWTH),
            ("GROWTH", Tier.GROWTH),
            ("premium", Tier.GROWTH),
            ("PREMIUM", Tier.GROWTH),
            ("team", Tier.GROWTH),
            ("TEAM", Tier.GROWTH),
            ("pro", Tier.PRO),
            ("PRO", Tier.PRO),
            ("master", Tier.MASTER),
            ("MASTER", Tier.MASTER),
            ("enterprise", Tier.ENTERPRISE),
            ("ENTERPRISE", Tier.ENTERPRISE),
            ("enterprise_plus", Tier.ENTERPRISE),
        ],
    )
    def test_tier_resolution(self, input_val: str, expected_member: Tier):
        assert Tier(input_val) == expected_member
        assert TierKey(input_val) == expected_member

    def test_invalid_tier_raises_value_error(self):
        with pytest.raises(ValueError):
            Tier("nonexistent_tier_xyz")


class TestRateLimitConfigs:
    """Verify rate limit dataclasses and lookup functions."""

    def test_rate_limit_config_defaults(self):
        cfg = RateLimitConfig(requests_per_minute=10)
        assert cfg.requests_per_minute == 10
        assert cfg.burst_size == 10
        assert cfg.window_seconds == 60

    def test_rate_limit_config_custom(self):
        cfg = RateLimitConfig(requests_per_minute=10, burst_size=25, window_seconds=120)
        assert cfg.burst_size == 25
        assert cfg.window_seconds == 120

    def test_all_tiers_in_default_configs(self):
        for tier_member in Tier:
            assert tier_member in DEFAULT_TIER_CONFIGS
            cfg = DEFAULT_TIER_CONFIGS[tier_member]
            assert isinstance(cfg, TierRateLimitConfig)
            assert cfg.tier == tier_member
            assert cfg.auth_login.requests_per_minute > 0
            assert cfg.auth_callback.requests_per_minute > 0
            assert cfg.auth_refresh.requests_per_minute > 0
            assert cfg.api_default.requests_per_minute > 0

    @pytest.mark.parametrize("tier_input", [Tier.PRO, "pro", "PRO"])
    def test_get_tier_config_resolution(self, tier_input):
        cfg = get_tier_config(tier_input)
        assert cfg.tier == Tier.PRO
        assert cfg.api_default.requests_per_minute == 100
        assert cfg.api_default.burst_size == 150

    @pytest.mark.parametrize("tier_input", [Tier.MASTER, "master", "MASTER", "master_vn"])
    def test_get_tier_config_master_resolution(self, tier_input):
        cfg = get_tier_config(tier_input)
        assert cfg.tier == Tier.MASTER
        assert cfg.api_default.requests_per_minute == 1_000
        assert cfg.api_default.burst_size == 1_500

    def test_get_tier_config_invalid(self):
        with pytest.raises(ValueError, match="Invalid tier"):
            get_tier_config("unknown_tier")

    def test_get_preset_config(self):
        cfg = get_preset_config("enterprise", "api_default")
        assert cfg.requests_per_minute == 500
        assert cfg.burst_size == 750

    def test_get_preset_config_invalid_preset(self):
        with pytest.raises(ValueError, match="Invalid preset"):
            get_preset_config("pro", "invalid_preset_endpoint")


class TestLicenseEnforcerHierarchy:
    """Verify LicenseEnforcer gates with the full 6-tier hierarchy."""

    class FakeStore:
        def __init__(self, tier_value: str) -> None:
            self._tier = tier_value

        def get_active_license(self, user_id=None):
            class _Lic:
                tier = self._tier
            return _Lic()

    def _build_enforcer(self, tier_value: str) -> LicenseEnforcer:
        enforcer = LicenseEnforcer()
        enforcer._store = self.FakeStore(tier_value)
        return enforcer

    def test_hierarchy_monotonicity(self):
        tiers_in_order = [
            Tier.FREE,
            Tier.TRIAL,
            Tier.STARTER,
            Tier.GROWTH,
            Tier.PRO,
            Tier.ENTERPRISE,
            Tier.MASTER,
        ]
        for i, current in enumerate(tiers_in_order):
            enforcer = self._build_enforcer(current.value)
            # Must allow all tiers <= current
            for allowed in tiers_in_order[: i + 1]:
                enforcer.require_tier(allowed)  # does not raise

            # Must block all tiers > current
            for blocked in tiers_in_order[i + 1 :]:
                with pytest.raises(HTTPException) as exc:
                    enforcer.require_tier(blocked)
                assert exc.value.status_code == 402
                assert exc.value.detail["required"] == blocked.value
                assert exc.value.detail["current"] == current.value
