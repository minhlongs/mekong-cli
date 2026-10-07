# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Comprehensive Tests for Mekong International Trade, Transport & Trade Remedies Suite (Phases 163 - 166).

Covers:
1. Multimodal Transport (MTO) Engine (Phase 163)
2. Civil Aviation Carrier Liability & Montreal 1999 Engine (Phase 164)
3. CISG 1980 & Incoterms 2020 Engine (Phase 165)
4. Trade Remedies, Anti-Dumping & Safeguards Engine (Phase 166)
5. Trade CLI Commands & Subcommands
6. MCP JSON-RPC Server Trade Tool Handlers
"""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.trade_transport_engine import (
    MultimodalTransportEngine,
    AirCarrierLiabilityEngine,
    InternationalSalesIncotermsEngine,
    TradeRemediesEngine,
    IncotermsGroup,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_trade_mto_liability,
    handle_trade_aviation_liability,
    handle_trade_cisg_reduction,
    handle_trade_incoterms,
    handle_trade_anti_dumping,
)

runner = CliRunner()


# ============================================================================
# 1. AST Boundary & Zero-Dependency Purity Tests
# ============================================================================


class TestTradeTransportBoundary:
    """Verify trade_transport_engine is 100% Python Standard Library."""

    def test_pure_standard_library_imports(self) -> None:
        file_rel_path = "src/core/trade_transport_engine.py"
        source_path = pathlib.Path(file_rel_path)
        assert source_path.exists(), f"{file_rel_path} must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer", "rich"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed external import '{pkg}' in {file_rel_path}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed external from-import '{pkg}' in {file_rel_path}"


# ============================================================================
# 2. Phase 163: Multimodal Transport (MTO) Unit Tests
# ============================================================================


class TestMultimodalTransportEngine:
    """Unit tests for Multimodal Transport Operator liability under NĐ 87/2009/NĐ-CP."""

    def test_mto_loss_with_sea_leg_package_rule(self) -> None:
        # 1 package, 100 kg. Pkg rule = 666.67 SDR, weight rule = 200 SDR -> Max is 666.67 SDR
        # 666.67 * 34,500 = 23,000,115 VND
        res = MultimodalTransportEngine.calculate_unlocalized_loss_liability(
            packages_count=1,
            gross_weight_kg=100.0,
            actual_loss_vnd=50_000_000.0,
            has_sea_or_waterway_leg=True,
            sdr_rate_vnd=34_500.0,
        )
        assert res.statutory_ceiling_sdr == 666.67
        assert res.statutory_ceiling_vnd == pytest.approx(23_000_115.0, abs=1.0)
        assert res.operator_payable_vnd == pytest.approx(23_000_115.0, abs=1.0)
        assert res.is_limited is True

    def test_mto_loss_with_sea_leg_weight_rule(self) -> None:
        # 1 package, 1000 kg. Pkg rule = 666.67 SDR, weight rule = 2000 SDR -> Max is 2000 SDR
        res = MultimodalTransportEngine.calculate_unlocalized_loss_liability(
            packages_count=1,
            gross_weight_kg=1000.0,
            actual_loss_vnd=100_000_000.0,
            has_sea_or_waterway_leg=True,
            sdr_rate_vnd=34_500.0,
        )
        assert res.statutory_ceiling_sdr == 2000.0
        assert res.statutory_ceiling_vnd == 69_000_000.0
        assert res.operator_payable_vnd == 69_000_000.0
        assert res.is_limited is True

    def test_mto_loss_inland_only(self) -> None:
        # No sea leg: 8.33 SDR/kg
        # 500 kg * 8.33 = 4165 SDR. 4165 * 34,500 = 143,692,500 VND
        res = MultimodalTransportEngine.calculate_unlocalized_loss_liability(
            packages_count=10,
            gross_weight_kg=500.0,
            actual_loss_vnd=200_000_000.0,
            has_sea_or_waterway_leg=False,
            sdr_rate_vnd=34_500.0,
        )
        assert res.statutory_ceiling_sdr == 4165.0
        assert res.statutory_ceiling_vnd == pytest.approx(143_692_500.0, abs=1.0)
        assert res.operator_payable_vnd == pytest.approx(143_692_500.0, abs=1.0)
        assert res.is_limited is True

    def test_mto_loss_below_ceiling(self) -> None:
        res = MultimodalTransportEngine.calculate_unlocalized_loss_liability(
            packages_count=5,
            gross_weight_kg=1000.0,
            actual_loss_vnd=10_000_000.0,
            has_sea_or_waterway_leg=True,
        )
        assert res.is_limited is False
        assert res.operator_payable_vnd == 10_000_000.0

    def test_mto_delay_liability_capped(self) -> None:
        # Freight = 20M, Delay claim = 60M -> Capped at 2x freight = 40M
        res = MultimodalTransportEngine.calculate_delay_liability(
            freight_charge_vnd=20_000_000.0,
            delay_loss_claimed_vnd=60_000_000.0,
        )
        assert res.statutory_ceiling_vnd == 40_000_000.0
        assert res.payable_compensation_vnd == 40_000_000.0
        assert res.is_capped_at_double_freight is True

    def test_mto_delay_liability_below_cap(self) -> None:
        res = MultimodalTransportEngine.calculate_delay_liability(
            freight_charge_vnd=20_000_000.0,
            delay_loss_claimed_vnd=15_000_000.0,
        )
        assert res.payable_compensation_vnd == 15_000_000.0
        assert res.is_capped_at_double_freight is False

    def test_mto_limitation_check(self) -> None:
        # Within 270 days
        st_ok = MultimodalTransportEngine.check_claim_limitation("2026-05-01", "2026-08-01")
        assert st_ok.is_within_9_months is True
        assert st_ok.remaining_days > 0

        # Beyond 270 days (10 months)
        st_late = MultimodalTransportEngine.check_claim_limitation("2025-01-01", "2026-01-01")
        assert st_late.is_within_9_months is False
        assert st_late.remaining_days == 0
        assert "HẾT THỜI HIỆU" in st_late.advice_vn


# ============================================================================
# 3. Phase 164: Civil Aviation Carrier Liability Unit Tests
# ============================================================================


class TestAirCarrierLiabilityEngine:
    """Unit tests for Civil Aviation Carrier liability under Law on Civil Aviation & Montreal 1999."""

    def test_passenger_injury_strict_liability_tier1(self) -> None:
        # Claim 2 Billion VND < 128,821 SDR * 34,500 = 4,444,324,500 VND
        res = AirCarrierLiabilityEngine.calculate_passenger_injury_liability(
            actual_damage_claimed_vnd=2_000_000_000.0,
            sdr_rate_vnd=34_500.0,
        )
        assert res.tier1_strict_ceiling_sdr == 128_821.0
        assert res.carrier_payable_strict_vnd == 2_000_000_000.0
        assert res.requires_carrier_fault_for_excess is False

    def test_passenger_injury_excess_tier2(self) -> None:
        # Claim 6 Billion VND > 4.444 Billion VND
        res = AirCarrierLiabilityEngine.calculate_passenger_injury_liability(
            actual_damage_claimed_vnd=6_000_000_000.0,
            sdr_rate_vnd=34_500.0,
        )
        assert res.carrier_payable_strict_vnd == pytest.approx(4_444_324_500.0, abs=1.0)
        assert res.requires_carrier_fault_for_excess is True
        assert "vượt hạn mức" in res.advice_vn.lower()

    def test_air_cargo_liability(self) -> None:
        # 100 kg cargo -> Ceiling = 100 * 22 SDR = 2200 SDR * 34,500 = 75,900,000 VND
        res = AirCarrierLiabilityEngine.calculate_cargo_liability(
            gross_weight_kg=100.0,
            actual_loss_vnd=150_000_000.0,
            sdr_rate_vnd=34_500.0,
        )
        assert res.cargo_limit_sdr == 2200.0
        assert res.statutory_ceiling_vnd == 75_900_000.0
        assert res.carrier_payable_vnd == 75_900_000.0
        assert res.is_limited is True

    def test_baggage_and_delay_liability(self) -> None:
        # Baggage: 1288 SDR/pax * 34,500 = 44,436,000 VND
        bag_res = AirCarrierLiabilityEngine.calculate_baggage_or_delay_liability(
            claim_type="baggage",
            passengers_count=1,
            actual_loss_vnd=60_000_000.0,
            sdr_rate_vnd=34_500.0,
        )
        assert bag_res.statutory_limit_sdr == 1288.0
        assert bag_res.carrier_payable_vnd == 44_436_000.0
        assert bag_res.is_limited is True

        # Delay: 5346 SDR/pax * 34,500 = 184,437,000 VND
        delay_res = AirCarrierLiabilityEngine.calculate_baggage_or_delay_liability(
            claim_type="delay",
            passengers_count=2,
            actual_loss_vnd=200_000_000.0,
            sdr_rate_vnd=34_500.0,
        )
        assert delay_res.statutory_limit_sdr == 5346.0 * 2
        assert delay_res.is_limited is False
        assert delay_res.carrier_payable_vnd == 200_000_000.0

    def test_aviation_limitation_period(self) -> None:
        # Within 730 days (2 years)
        res_ok = AirCarrierLiabilityEngine.check_aviation_claim_limitation("2025-01-01", "2026-01-01")
        assert res_ok.is_within_2_years is True
        assert res_ok.remaining_days > 0

        # Over 730 days
        res_late = AirCarrierLiabilityEngine.check_aviation_claim_limitation("2023-01-01", "2026-01-01")
        assert res_late.is_within_2_years is False
        assert res_late.remaining_days == 0


# ============================================================================
# 4. Phase 165: CISG 1980 & Incoterms 2020 Unit Tests
# ============================================================================


class TestInternationalSalesIncotermsEngine:
    """Unit tests for CISG 1980 and Incoterms 2020."""

    def test_fundamental_breach_evaluation(self) -> None:
        res_fb = InternationalSalesIncotermsEngine.evaluate_fundamental_breach(
            substantially_deprives_expectation=True,
            was_foreseeable=True,
        )
        assert res_fb.is_fundamental_breach is True
        assert res_fb.entitled_to_avoid_contract is True

        res_unforeseeable = InternationalSalesIncotermsEngine.evaluate_fundamental_breach(
            substantially_deprives_expectation=True,
            was_foreseeable=False,
        )
        assert res_unforeseeable.is_fundamental_breach is False
        assert res_unforeseeable.entitled_to_avoid_contract is False

    def test_cisg_price_reduction(self) -> None:
        # Contract price = 1 Billion VND
        # Actual delivered value = 700 Million VND, Conforming value = 1 Billion VND
        # Ratio = 70%, Reduced price = 700 Million VND, Abatement = 300 Million VND
        res = InternationalSalesIncotermsEngine.calculate_cisg_price_reduction(
            agreed_contract_price_vnd=1_000_000_000.0,
            value_of_delivered_goods_vnd=700_000_000.0,
            value_if_conforming_vnd=1_000_000_000.0,
        )
        assert res.reduction_ratio_pct == 70.0
        assert res.reduced_price_payable_vnd == 700_000_000.0
        assert res.price_abatement_amount_vnd == 300_000_000.0

    def test_all_11_incoterms_rules_exist(self) -> None:
        expected_rules = ["EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP", "FAS", "FOB", "CFR", "CIF"]
        for rule_code in expected_rules:
            rule = InternationalSalesIncotermsEngine.lookup_incoterms_rule(rule_code)
            assert rule is not None, f"Rule {rule_code} must exist"
            assert rule.code == rule_code

    def test_cip_cif_insurance_requirements(self) -> None:
        cip = InternationalSalesIncotermsEngine.lookup_incoterms_rule("CIP")
        assert cip is not None
        assert cip.group == IncotermsGroup.ANY_MODE
        assert "ICC A" in cip.mandatory_insurance
        assert "110%" in cip.mandatory_insurance

        cif = InternationalSalesIncotermsEngine.lookup_incoterms_rule("CIF")
        assert cif is not None
        assert cif.group == IncotermsGroup.SEA_INLAND
        assert "ICC C" in cif.mandatory_insurance
        assert "110%" in cif.mandatory_insurance


# ============================================================================
# 5. Phase 166: Vietnamese Trade Remedies Unit Tests
# ============================================================================


class TestTradeRemediesEngine:
    """Unit tests for Vietnamese Trade Remedies under Law on Foreign Trade Management 2017."""

    def test_dumping_margin_calculation(self) -> None:
        # Normal Value = 12,000 VND, Export Price = 10,000 VND -> DM = (2,000 / 10,000) * 100% = 20.0%
        res = TradeRemediesEngine.calculate_dumping_margin(
            normal_value_vnd=12_000.0,
            export_price_vnd=10_000.0,
        )
        assert res.dumping_margin_pct == 20.0
        assert res.is_de_minimis is False
        assert res.is_subject_to_anti_dumping is True

    def test_dumping_margin_de_minimis(self) -> None:
        # Normal Value = 10,150 VND, Export Price = 10,000 VND -> DM = 1.5% (< 2.0%)
        res = TradeRemediesEngine.calculate_dumping_margin(
            normal_value_vnd=10_150.0,
            export_price_vnd=10_000.0,
        )
        assert res.dumping_margin_pct == 1.5
        assert res.is_de_minimis is True
        assert res.is_subject_to_anti_dumping is False
        assert "de minimis" in res.advice_vn.lower()

    def test_anti_dumping_assessment_eligible(self) -> None:
        res = TradeRemediesEngine.assess_anti_dumping_application(
            exporting_country="Country X",
            dumping_margin_pct=15.5,
            import_volume_share_pct=8.0,
        )
        assert res.can_impose_duty is True
        assert res.maximum_duty_rate_pct == 15.5
        assert res.max_duration_years == 5
        assert "ĐỦ ĐIỀU KIỆN" in res.advice_vn

    def test_anti_dumping_assessment_negligible_volume(self) -> None:
        res = TradeRemediesEngine.assess_anti_dumping_application(
            exporting_country="Country Y",
            dumping_margin_pct=25.0,
            import_volume_share_pct=1.8,  # < 3%
        )
        assert res.can_impose_duty is False
        assert res.is_volume_negligible is True
        assert "KHÔNG ĐƯỢC ÁP THUẾ" in res.advice_vn

    def test_safeguard_surge_assessment(self) -> None:
        # Base = 10,000 tons, Current = 15,000 tons (+50% surge >= 30%)
        res = TradeRemediesEngine.assess_safeguard_surge(
            base_import_quantity=10_000.0,
            current_import_quantity=15_000.0,
            threshold_surge_rate_pct=30.0,
        )
        assert res.surge_rate_pct == 50.0
        assert res.is_substantial_increase is True
        assert "đột biến" in res.advice_vn.lower()


# ============================================================================
# 6. CLI Commands & Options Tests
# ============================================================================


class TestTradeCLICommands:
    """Test suite for Typer CLI commands in trade_command.py."""

    @classmethod
    def setup_class(cls) -> None:
        cls.app = build_app()

    def test_cli_trade_summary(self) -> None:
        res = runner.invoke(self.app, ["trade"])
        assert res.exit_code == 0
        assert "MEKONG TRADE, TRANSPORT & TRADE REMEDIES SUITE" in res.output

        res_json = runner.invoke(self.app, ["trade", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["suite"] == "Mekong Trade, Transport & Remedies Suite"

    def test_cli_mto_liability(self) -> None:
        res = runner.invoke(
            self.app,
            ["trade", "mto-liability", "100000000", "--packages", "2", "--weight", "200"],
        )
        assert res.exit_code == 0
        assert "Bồi Thường Vận Tải Đa Phương Thức" in res.output

        res_json = runner.invoke(
            self.app,
            ["trade", "mto-liability", "100000000", "--packages", "2", "--json"],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "operator_payable_vnd" in data

    def test_cli_mto_delay(self) -> None:
        res = runner.invoke(self.app, ["trade", "mto-delay", "30000000", "70000000"])
        assert res.exit_code == 0
        assert "Bồi Thường Chậm Giao Hàng" in res.output

    def test_cli_mto_limitation(self) -> None:
        res = runner.invoke(
            self.app,
            ["trade", "mto-limitation", "2026-01-01", "--filing-date", "2026-05-01"],
        )
        assert res.exit_code == 0
        assert "Thời Hiệu Khởi Kiện Vận Tải Đa Phương Thức" in res.output

    def test_cli_aviation_injury(self) -> None:
        res = runner.invoke(self.app, ["trade", "aviation-injury", "3000000000"])
        assert res.exit_code == 0
        assert "Bồi Thường Tính Mạng / Sức Khỏe" in res.output

    def test_cli_aviation_cargo(self) -> None:
        res = runner.invoke(self.app, ["trade", "aviation-cargo", "200", "80000000"])
        assert res.exit_code == 0
        assert "Air Cargo" in res.output

    def test_cli_aviation_baggage(self) -> None:
        res = runner.invoke(
            self.app,
            ["trade", "aviation-baggage", "50000000", "--type", "baggage", "--passengers", "2"],
        )
        assert res.exit_code == 0
        assert "Hành Lý" in res.output

    def test_cli_aviation_limitation(self) -> None:
        res = runner.invoke(
            self.app,
            ["trade", "aviation-limitation", "2025-06-01", "--action-date", "2026-06-01"],
        )
        assert res.exit_code == 0
        assert "Thời Hiệu Khởi Kiện Hàng Không Dân Dụng" in res.output

    def test_cli_cisg_breach(self) -> None:
        res = runner.invoke(self.app, ["trade", "cisg-breach", "--deprived", "--foreseeable"])
        assert res.exit_code == 0
        assert "VI PHẠM CƠ BẢN" in res.output

    def test_cli_cisg_reduction(self) -> None:
        res = runner.invoke(self.app, ["trade", "cisg-reduction", "500000000", "300000000", "500000000"])
        assert res.exit_code == 0
        assert "Giảm Giá Hàng Hóa Không Phù Hợp" in res.output

    def test_cli_incoterms(self) -> None:
        res = runner.invoke(self.app, ["trade", "incoterms", "CIP"])
        assert res.exit_code == 0
        assert "Incoterms 2020: CIP" in res.output
        assert "ICC A" in res.output

        res_invalid = runner.invoke(self.app, ["trade", "incoterms", "XYZ"])
        assert res_invalid.exit_code == 0
        assert "Không tìm thấy quy tắc Incoterms" in res_invalid.output

    def test_cli_anti_dumping(self) -> None:
        res = runner.invoke(self.app, ["trade", "anti-dumping", "15000", "10000"])
        assert res.exit_code == 0
        assert "Biên Độ Bán Phá Giá" in res.output

    def test_cli_trade_remedy(self) -> None:
        res = runner.invoke(self.app, ["trade", "trade-remedy", "Japan", "12.5", "5.5"])
        assert res.exit_code == 0
        assert "Thẩm Tra Áp Thuế Chống Bán Phá Giá" in res.output

    def test_cli_safeguard_surge(self) -> None:
        res = runner.invoke(self.app, ["trade", "safeguard-surge", "1000", "1500", "--threshold", "25"])
        assert res.exit_code == 0
        assert "GIA TĂNG ĐỘT BIẾN" in res.output


# ============================================================================
# 7. MCP JSON-RPC Tool Handlers Tests
# ============================================================================


class TestTradeMCPHandlers:
    """Test suite for Trade MCP server tool handlers."""

    def test_mcp_mto_liability(self) -> None:
        raw = handle_trade_mto_liability({
            "packages_count": 5,
            "gross_weight_kg": 200.0,
            "actual_loss_vnd": 200_000_000.0,
            "has_sea_or_waterway_leg": True,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert "operator_payable_vnd" in data
        assert data["is_limited"] is True

    def test_mcp_aviation_liability(self) -> None:
        # Injury
        raw_inj = handle_trade_aviation_liability({
            "claim_type": "injury",
            "actual_loss_vnd": 1_000_000_000.0,
        })
        d_inj = json.loads(raw_inj)
        assert d_inj["ok"] is True
        assert d_inj["claim_type"] == "injury"

        # Cargo
        raw_cargo = handle_trade_aviation_liability({
            "claim_type": "cargo",
            "gross_weight_kg": 50.0,
            "actual_loss_vnd": 60_000_000.0,
        })
        d_cargo = json.loads(raw_cargo)
        assert d_cargo["ok"] is True
        assert d_cargo["cargo_limit_sdr"] == 1100.0

    def test_mcp_cisg_reduction(self) -> None:
        raw = handle_trade_cisg_reduction({
            "agreed_contract_price_vnd": 100_000_000.0,
            "value_of_delivered_goods_vnd": 60_000_000.0,
            "value_if_conforming_vnd": 100_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["reduced_price_payable_vnd"] == 60_000_000.0
        assert data["price_abatement_amount_vnd"] == 40_000_000.0

    def test_mcp_incoterms(self) -> None:
        raw_ok = handle_trade_incoterms({"term": "CIF"})
        d_ok = json.loads(raw_ok)
        assert d_ok["ok"] is True
        assert d_ok["code"] == "CIF"
        assert "ICC C" in d_ok["mandatory_insurance"]

        raw_bad = handle_trade_incoterms({"term": "UNKNOWN"})
        d_bad = json.loads(raw_bad)
        assert d_bad["ok"] is False
        assert "Invalid Incoterms rule" in d_bad["error"]

    def test_mcp_anti_dumping(self) -> None:
        raw = handle_trade_anti_dumping({
            "normal_value_vnd": 20_000.0,
            "export_price_vnd": 15_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["dumping_margin_pct"] == pytest.approx(33.33, abs=0.01)
        assert data["is_subject_to_anti_dumping"] is True
