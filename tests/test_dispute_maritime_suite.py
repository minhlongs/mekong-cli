# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Comprehensive Tests for Mekong Dispute Resolution & Maritime Law Suite (Phases 159 - 162).
Covers:
1. Commercial Arbitration & VIAC 2024 Engine (Phase 159)
2. Civil Judgment Enforcement Engine (Phase 160)
3. Court Litigation & Civil Procedure Engine (Phase 161)
4. Vietnam Maritime Law & General Average Engine (Phase 162)
5. Dispute CLI Commands & Subcommands
6. MCP JSON-RPC Server Dispute Tool Handlers
"""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.dispute_engine import (
    ArbitrationTribunalType,
    CivilEnforcementEngine,
    CommercialArbitrationEngine,
    CourtLevel,
    CourtLitigationEngine,
)
from src.core.maritime_law_engine import (
    GeneralAverageInterest,
    MaritimeClaimCategory,
    MaritimeLawEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_dispute_court_fee,
    handle_dispute_enforcement_priority,
    handle_dispute_general_average,
    handle_dispute_maritime_liability,
    handle_dispute_viac_fee,
)

runner = CliRunner()


# ============================================================================
# 1. AST Boundary & Zero-Dependency Purity Tests
# ============================================================================


class TestDisputeMaritimeBoundary:
    """Verify dispute_engine and maritime_law_engine are 100% Python Standard Library."""

    @pytest.mark.parametrize(
        "file_rel_path",
        [
            "src/core/dispute_engine.py",
            "src/core/maritime_law_engine.py",
        ],
    )
    def test_pure_standard_library_imports(self, file_rel_path: str) -> None:
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
# 2. Commercial Arbitration & VIAC Engine (Phase 159) Tests
# ============================================================================


class TestCommercialArbitrationEngine:
    """Tests for Law on Commercial Arbitration 2010 & VIAC 2024 Rules."""

    def test_validate_arbitration_clause_valid(self) -> None:
        text = "Mọi tranh chấp phát sinh từ hợp đồng này sẽ được giải quyết chung thẩm tại Trung tâm Trọng tài Quốc tế Việt Nam (VIAC)."
        res = CommercialArbitrationEngine.validate_arbitration_clause(text, dispute_type="commercial")
        assert res.is_valid is True
        assert "VIAC" in res.arbitration_institution
        assert len(res.risk_factors) == 0

    def test_validate_arbitration_clause_incapacitated_or_non_commercial(self) -> None:
        text = "Tranh chấp ly hôn giải quyết tại VIAC."
        res = CommercialArbitrationEngine.validate_arbitration_clause(
            text, dispute_type="family", parties_have_capacity=False
        )
        assert res.is_valid is False
        assert len(res.risk_factors) >= 2

    def test_validate_arbitration_clause_ambiguous_court_or_arbitration(self) -> None:
        text = "Tranh chấp sẽ được giải quyết tại Tòa án hoặc Trọng tài VIAC."
        res = CommercialArbitrationEngine.validate_arbitration_clause(text, dispute_type="commercial")
        assert any("Tòa án hoặc Trọng tài" in r for r in res.risk_factors)

    @pytest.mark.parametrize(
        "claim,expected_fee_3",
        [
            (300_000_000, 38_000_000.0),
            (800_000_000, 38_000_000.0 + 0.04 * 300_000_000),  # 50,000,000
            (2_000_000_000, 58_000_000.0 + 0.03 * 1_000_000_000),  # 88,000,000
            (6_000_000_000, 178_000_000.0 + 0.02 * 1_000_000_000),  # 198,000,000
            (20_000_000_000, 278_000_000.0 + 0.005 * 10_000_000_000),  # 328,000,000
            (60_000_000_000, 478_000_000.0 + 0.001 * 10_000_000_000),  # 488,000,000
        ],
    )
    def test_calculate_viac_fee_brackets(self, claim: float, expected_fee_3: float) -> None:
        res_3 = CommercialArbitrationEngine.calculate_viac_fee(
            claim, tribunal_type=ArbitrationTribunalType.THREE_ARBITRATORS
        )
        assert res_3.arbitration_fee_vnd == pytest.approx(expected_fee_3, 0.01)
        assert res_3.sole_discount_applied is False

        # Sole arbitrator discount (70% of 3-arbitrator fee)
        res_sole = CommercialArbitrationEngine.calculate_viac_fee(
            claim, tribunal_type=ArbitrationTribunalType.SOLE_ARBITRATOR
        )
        assert res_sole.arbitration_fee_vnd == pytest.approx(expected_fee_3 * 0.7, 0.01)
        assert res_sole.sole_discount_applied is True

    def test_check_limitation_period(self) -> None:
        # Within 2 years (e.g. 100 days)
        res_ok = CommercialArbitrationEngine.check_limitation_period("2026-01-01", "2026-04-11")
        assert res_ok.is_within_limitation is True
        assert res_ok.days_passed == 100
        assert res_ok.remaining_days == 630

        # Expired (over 730 days)
        res_exp = CommercialArbitrationEngine.check_limitation_period("2023-01-01", "2026-01-01")
        assert res_exp.is_within_limitation is False
        assert res_exp.remaining_days == 0
        assert "HẾT THỜI HIỆU" in res_exp.advice_vn


# ============================================================================
# 3. Civil Judgment Enforcement Engine (Phase 160) Tests
# ============================================================================


class TestCivilEnforcementEngine:
    """Tests for Law on Civil Judgment Enforcement 2014 & Circular 216/2016/TT-BTC."""

    def test_check_enforcement_limitation(self) -> None:
        # Within 5 years (1825 days)
        res_ok = CivilEnforcementEngine.check_enforcement_limitation("2024-01-01", "2026-01-01")
        assert res_ok.is_within_5_years is True
        assert res_ok.days_passed == 731
        assert res_ok.remaining_days == 1825 - 731

        # Expired
        res_exp = CivilEnforcementEngine.check_enforcement_limitation("2018-01-01", "2026-01-01")
        assert res_exp.is_within_5_years is False
        assert "QUÁ THỜI HIỆU" in res_exp.statutory_notice

    def test_calculate_enforcement_fee_and_cap(self) -> None:
        # Under cap: 100M * 3% = 3M
        res_1 = CivilEnforcementEngine.calculate_enforcement_fee(100_000_000)
        assert res_1.actual_fee_payable_vnd == 3_000_000.0
        assert res_1.is_capped_at_200m is False

        # Over cap (10 Billion * 3% = 300M > 200M cap)
        res_cap = CivilEnforcementEngine.calculate_enforcement_fee(10_000_000_000)
        assert res_cap.calculated_fee_vnd == 300_000_000.0
        assert res_cap.actual_fee_payable_vnd == 200_000_000.0
        assert res_cap.is_capped_at_200m is True

    def test_distribute_payment_priority_full_and_partial(self) -> None:
        # Case 1: Insufficient funds (partial liquidation)
        # 100M total recovered: Alimony 30M, Labor 50M, Court 40M, Other 50M
        dist = CivilEnforcementEngine.distribute_payment_priority(
            total_recovered_amount=100_000_000,
            alimony_due=30_000_000,
            labor_salary_due=50_000_000,
            court_fees_due=40_000_000,
            other_claims_due=50_000_000,
        )
        assert dist.alimony_paid == 30_000_000.0
        assert dist.labor_paid == 50_000_000.0
        assert dist.court_fee_paid == 20_000_000.0  # Remaining 20M out of 40M
        assert dist.other_claims_paid == 0.0
        assert dist.remaining_surplus == 0.0
        assert dist.is_fully_satisfied is False

        # Case 2: Surplus funds
        dist_surplus = CivilEnforcementEngine.distribute_payment_priority(
            total_recovered_amount=200_000_000,
            alimony_due=20_000_000,
            labor_salary_due=30_000_000,
            court_fees_due=10_000_000,
            other_claims_due=40_000_000,
        )
        assert dist_surplus.alimony_paid == 20_000_000.0
        assert dist_surplus.labor_paid == 30_000_000.0
        assert dist_surplus.court_fee_paid == 10_000_000.0
        assert dist_surplus.other_claims_paid == 40_000_000.0
        assert dist_surplus.remaining_surplus == 100_000_000.0
        assert dist_surplus.is_fully_satisfied is True


# ============================================================================
# 4. Court Litigation & Civil Procedure Engine (Phase 161) Tests
# ============================================================================


class TestCourtLitigationEngine:
    """Tests for Civil Procedure Code 2015 & Resolution 326/2016/UBTVQH14."""

    def test_resolve_jurisdiction(self) -> None:
        # Domestic standard dispute -> District Court
        res_dist = CourtLitigationEngine.resolve_jurisdiction(
            has_foreign_element=False,
            is_intellectual_property=False,
            is_maritime=False,
            province="TP. Hà Nội",
        )
        assert res_dist.court_level == CourtLevel.DISTRICT
        assert "Cấp Huyện" in res_dist.competent_forum_vn

        # Foreign element / IP / Maritime -> Provincial Court
        res_prov_ip = CourtLitigationEngine.resolve_jurisdiction(
            is_intellectual_property=True,
            province="TP. Hồ Chí Minh",
        )
        assert res_prov_ip.court_level == CourtLevel.PROVINCIAL
        assert "Cấp Tỉnh" in res_prov_ip.competent_forum_vn

        res_prov_maritime = CourtLitigationEngine.resolve_jurisdiction(
            is_maritime=True,
            province="Hải Phòng",
        )
        assert res_prov_maritime.court_level == CourtLevel.PROVINCIAL

    @pytest.mark.parametrize(
        "claim,expected_fee",
        [
            (5_000_000, 300_000.0),
            (200_000_000, 0.05 * 200_000_000),  # 10,000,000
            (600_000_000, 20_000_000.0 + 0.04 * 200_000_000),  # 28,000,000
            (1_500_000_000, 36_000_000.0 + 0.03 * 700_000_000),  # 57,000,000
            (3_000_000_000, 72_000_000.0 + 0.02 * 1_000_000_000),  # 92,000,000
            (10_000_000_000, 112_000_000.0 + 0.001 * 6_000_000_000),  # 118,000,000
        ],
    )
    def test_calculate_court_fee(self, claim: float, expected_fee: float) -> None:
        res = CourtLitigationEngine.calculate_court_fee(claim)
        assert res.first_instance_fee_vnd == pytest.approx(expected_fee, 0.01)
        assert res.advance_payment_vnd == pytest.approx(expected_fee * 0.5, 0.01)


# ============================================================================
# 5. Vietnam Maritime Law & General Average Engine (Phase 162) Tests
# ============================================================================


class TestMaritimeLawEngine:
    """Tests for Vietnam Maritime Code 2015 & York-Antwerp Rules 2016."""

    def test_calculate_carrier_liability_package_vs_weight_limit(self) -> None:
        # 10 packages @ 666.67 SDR = 6,666.7 SDR
        # 1,000 kg @ 2.0 SDR = 2,000 SDR
        # Max applied SDR = 6,666.7 SDR * 34,500 = 230,001,150 VND
        # Actual loss 500,000,000 VND -> limited to ceiling
        res_pkg = MaritimeLawEngine.calculate_carrier_liability(
            packages_count=10,
            gross_weight_kg=1000,
            actual_loss_vnd=500_000_000,
            sdr_rate_vnd=34500.0,
        )
        assert res_pkg.package_limit_sdr == 6666.7
        assert res_pkg.weight_limit_sdr == 2000.0
        assert res_pkg.applicable_limit_sdr == 6666.7
        assert res_pkg.is_limited is True
        assert res_pkg.carrier_payable_vnd == pytest.approx(6666.7 * 34500.0, 1.0)

        # Heavy weight dominates: 1 package, 10,000 kg
        # Package SDR = 666.67, Weight SDR = 20,000 SDR
        res_weight = MaritimeLawEngine.calculate_carrier_liability(
            packages_count=1,
            gross_weight_kg=10000,
            actual_loss_vnd=100_000_000,
            sdr_rate_vnd=34500.0,
        )
        assert res_weight.applicable_limit_sdr == 20000.0
        assert res_weight.is_limited is False  # Actual loss < ceiling
        assert res_weight.carrier_payable_vnd == 100_000_000.0

    def test_check_cargo_claim_limitation(self) -> None:
        res_ok = MaritimeLawEngine.check_cargo_claim_limitation("2026-01-01", "2026-06-01")
        assert res_ok.is_within_1_year is True
        assert res_ok.days_passed == 151
        assert res_ok.remaining_days == 365 - 151

        res_exp = MaritimeLawEngine.check_cargo_claim_limitation("2024-01-01", "2026-01-01")
        assert res_exp.is_within_1_year is False
        assert "HẾT THỜI HIỆU" in res_exp.advice_vn

    def test_calculate_general_average_zero_sum_equilibrium(self) -> None:
        interests = [
            GeneralAverageInterest(interest_name="Ship", contributory_value_vnd=10_000_000_000, sacrifice_incurred_vnd=500_000_000),
            GeneralAverageInterest(interest_name="Cargo A", contributory_value_vnd=4_000_000_000, sacrifice_incurred_vnd=100_000_000),
            GeneralAverageInterest(interest_name="Cargo B", contributory_value_vnd=5_000_000_000, sacrifice_incurred_vnd=0.0),
            GeneralAverageInterest(interest_name="Freight", contributory_value_vnd=1_000_000_000, sacrifice_incurred_vnd=0.0),
        ]
        # Total Contributory Value = 20 Billion VND
        # Total GA Loss = 600 Million VND
        # Ratio = 600M / 20B = 3.0%
        res = MaritimeLawEngine.calculate_general_average(interests)
        assert res.total_contributory_value_vnd == 20_000_000_000.0
        assert res.total_general_average_loss_vnd == 600_000_000.0
        assert res.contribution_ratio_pct == 3.0
        assert res.is_zero_sum_balanced is True

        # Check net settlements
        # Ship: Gross = 300M, Sacrifice = 500M -> Net = -200M (Receives 200M)
        # Cargo A: Gross = 120M, Sacrifice = 100M -> Net = +20M (Pays 20M)
        # Cargo B: Gross = 150M, Sacrifice = 0 -> Net = +150M (Pays 150M)
        # Freight: Gross = 30M, Sacrifice = 0 -> Net = +30M (Pays 30M)
        net_sum = sum(p.net_settlement_vnd for p in res.participants)
        assert abs(net_sum) < 1.0

    def test_assess_salvage_reward_no_cure_no_pay_and_cap(self) -> None:
        # Case 1: No useful result
        res_no_cure = MaritimeLawEngine.assess_salvage_reward(
            salvaged_property_value_vnd=10_000_000_000,
            agreed_or_claimed_reward_vnd=500_000_000,
            has_useful_result=False,
        )
        assert res_no_cure.statutory_approved_reward_vnd == 0.0
        assert "No Cure No Pay" in res_no_cure.advice_vn

        # Case 2: Claim exceeds property value -> capped
        res_capped = MaritimeLawEngine.assess_salvage_reward(
            salvaged_property_value_vnd=300_000_000,
            agreed_or_claimed_reward_vnd=500_000_000,
            has_useful_result=True,
        )
        assert res_capped.statutory_approved_reward_vnd == 300_000_000.0
        assert res_capped.is_capped_by_property_value is True

    def test_rank_maritime_claims_statutory_priority(self) -> None:
        claims = [
            {"claim_id": "C-01", "description": "Thế chấp tàu", "category": "ship_mortgage", "claim_amount_vnd": 5_000_000_000},
            {"claim_id": "C-02", "description": "Lương thuyền viên", "category": "crew_wages", "claim_amount_vnd": 300_000_000},
            {"claim_id": "C-03", "description": "Phí cảng biển", "category": "port_dues", "claim_amount_vnd": 100_000_000},
            {"claim_id": "C-04", "description": "Thù lao cứu hộ", "category": "salvage_reward", "claim_amount_vnd": 400_000_000},
            {"claim_id": "C-05", "description": "Thiệt hại va chạm", "category": "collision_damage", "claim_amount_vnd": 800_000_000},
        ]
        ranked = MaritimeLawEngine.rank_maritime_claims(claims)
        # Order should strictly be:
        # 1. Crew wages (Rank 1)
        # 2. Port dues (Rank 3)
        # 3. Salvage reward (Rank 4)
        # 4. Collision damage (Rank 5)
        # 5. Ship mortgage (Rank 6 - ordinary mortgage outranked by maritime liens)
        categories_in_order = [r.category for r in ranked]
        assert categories_in_order == [
            MaritimeClaimCategory.CREW_WAGES,
            MaritimeClaimCategory.PORT_DUES,
            MaritimeClaimCategory.SALVAGE_REWARD,
            MaritimeClaimCategory.COLLISION_DAMAGE,
            MaritimeClaimCategory.SHIP_MORTGAGE,
        ]
        assert ranked[0].is_maritime_lien is True
        assert ranked[-1].is_maritime_lien is False


# ============================================================================
# 6. Typer CLI Commands & Rich Presentation Tests
# ============================================================================


class TestDisputeCliCommands:
    """CLI invocation tests for dispute command group."""

    def setup_method(self) -> None:
        self.app = build_app()

    def test_cli_dispute_viac_fee(self) -> None:
        result = runner.invoke(self.app, ["dispute", "viac-fee", "1500000000", "--sole"])
        assert result.exit_code == 0
        assert "VIAC 2024" in result.output
        assert "51,100,000" in result.output  # (58M + 0.03*500M) * 0.7 = 73M * 0.7 = 51.1M

    def test_cli_dispute_viac_fee_json(self) -> None:
        result = runner.invoke(self.app, ["dispute", "viac-fee", "1000000000", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["claim_amount_vnd"] == 1000000000.0
        assert data["arbitration_fee_vnd"] == 58000000.0

    def test_cli_dispute_enforcement_priority(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "dispute",
                "enforcement-priority",
                "100000000",
                "--alimony",
                "20000000",
                "--labor",
                "30000000",
                "--court",
                "10000000",
                "--other",
                "20000000",
            ],
        )
        assert result.exit_code == 0
        assert "Phân Bổ Thứ Tự Ưu Tiên Thanh Toán" in result.output
        assert "20,000,000" in result.output

    def test_cli_dispute_court_fee(self) -> None:
        result = runner.invoke(self.app, ["dispute", "court-fee", "500000000"])
        assert result.exit_code == 0
        assert "Án phí sơ thẩm" in result.output
        assert "24,000,000" in result.output
        assert "12,000,000" in result.output  # 50% advance

    def test_cli_dispute_court_jurisdiction(self) -> None:
        result = runner.invoke(self.app, ["dispute", "court-jurisdiction", "--foreign", "--province", "Đà Nẵng"])
        assert result.exit_code == 0
        assert "Tòa án nhân dân Đà Nẵng (Cấp Tỉnh)" in result.output

    def test_cli_dispute_carrier_liability(self) -> None:
        result = runner.invoke(self.app, ["dispute", "carrier-liability", "10", "2000", "500000000"])
        assert result.exit_code == 0
        assert "Giới Hạn Trách Nhiệm Vận Chuyển Hàng Hải" in result.output

    def test_cli_dispute_general_average(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "dispute",
                "general-average",
                "--ship-val",
                "1000000000",
                "--cargo-val",
                "500000000",
                "--ship-loss",
                "50000000",
            ],
        )
        assert result.exit_code == 0
        assert "Bảng Phân Bổ Tổn Thất Chung" in result.output
        assert "Tàu biển" in result.output
        assert "Hàng hóa" in result.output


# ============================================================================
# 7. MCP JSON-RPC Server Dispute Tool Handlers Tests
# ============================================================================


class TestDisputeMcpHandlers:
    """Verify dispute tool handlers return valid JSON output."""

    def test_mcp_handle_dispute_viac_fee(self) -> None:
        raw = handle_dispute_viac_fee({"claim_amount_vnd": 500000000, "sole_arbitrator": False})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["arbitration_fee_vnd"] == 38000000.0

    def test_mcp_handle_dispute_enforcement_priority(self) -> None:
        raw = handle_dispute_enforcement_priority({
            "total_recovered_amount": 50000000,
            "alimony_due": 20000000,
            "labor_salary_due": 40000000,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["alimony_paid"] == 20000000.0
        assert data["labor_paid"] == 30000000.0
        assert data["remaining_surplus"] == 0.0

    def test_mcp_handle_dispute_court_fee(self) -> None:
        raw = handle_dispute_court_fee({"claim_amount_vnd": 100000000})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["first_instance_fee_vnd"] == 5000000.0
        assert data["advance_payment_vnd"] == 2500000.0

    def test_mcp_handle_dispute_maritime_liability(self) -> None:
        raw = handle_dispute_maritime_liability({
            "packages_count": 5,
            "gross_weight_kg": 100,
            "actual_loss_vnd": 200000000,
            "sdr_rate_vnd": 34500,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["applicable_limit_sdr"] == pytest.approx(5 * 666.67, 0.01)

    def test_mcp_handle_dispute_general_average(self) -> None:
        raw = handle_dispute_general_average({
            "interests": [
                {"interest_name": "Ship", "contributory_value_vnd": 2000000000, "sacrifice_incurred_vnd": 100000000},
                {"interest_name": "Cargo", "contributory_value_vnd": 1000000000, "sacrifice_incurred_vnd": 0},
            ]
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["is_zero_sum_balanced"] is True
        assert len(data["participants"]) == 2
