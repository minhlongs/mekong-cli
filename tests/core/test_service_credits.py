"""Tests for src/core/service_credits.py — credit lookup từ pricing.json."""

from src.core.service_credits import (
    DEFAULT_CREDIT_COST,
    credits_for_command,
    get_vn_tier,
    is_vn_command,
    list_vn_commands,
)


class TestCreditsForCommand:
    def test_ke_toan_costs_1(self):
        assert credits_for_command("ke-toan") == 1

    def test_thue_dnvn_costs_1(self):
        assert credits_for_command("thue-dnvn") == 1

    def test_zalo_oa_costs_2(self):
        assert credits_for_command("zalo-oa") == 2

    def test_bhxh_costs_2(self):
        assert credits_for_command("bhxh") == 2

    def test_annual_costs_5_from_services(self):
        assert credits_for_command("annual") == 5

    def test_unknown_command_returns_default(self):
        assert credits_for_command("unknown-cmd-xyz") == DEFAULT_CREDIT_COST

    def test_leading_slash_stripped(self):
        assert credits_for_command("/ke-toan") == 1

    def test_case_insensitive(self):
        assert credits_for_command("KE-TOAN") == 1

    def test_empty_command_returns_default(self):
        assert credits_for_command("") == DEFAULT_CREDIT_COST


class TestVNCommandDetection:
    def test_ke_toan_is_vn(self):
        assert is_vn_command("ke-toan") is True

    def test_annual_is_not_vn(self):
        assert is_vn_command("annual") is False

    def test_unknown_is_not_vn(self):
        assert is_vn_command("foobar") is False


class TestListVNCommands:
    def test_includes_core_vn_commands(self):
        cmds = list_vn_commands()
        assert "ke-toan" in cmds
        assert "thue-dnvn" in cmds
        assert "zalo-oa" in cmds
        assert "vietqr" in cmds
        assert "bhxh" in cmds

    def test_excludes_english_services(self):
        cmds = list_vn_commands()
        assert "annual" not in cmds
        assert "competitor" not in cmds


class TestGetVNTier:
    def test_starter_vn_exists(self):
        tier = get_vn_tier("starter_vn")
        assert tier is not None
        assert tier["price_display_vnd"] == "199.000₫"
        assert tier["credits_per_month"] == 200

    def test_growth_vn_exists(self):
        tier = get_vn_tier("growth_vn")
        assert tier["price_display_vnd"] == "499.000₫"
        assert tier["credits_per_month"] == 800

    def test_pro_vn_exists(self):
        tier = get_vn_tier("pro_vn")
        assert tier["credits_per_month"] == 3000

    def test_unknown_tier_returns_none(self):
        assert get_vn_tier("nonexistent") is None
