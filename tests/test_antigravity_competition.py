# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit, CLI, and MCP Integration Tests for Vietnamese Competition Law Suite (Phase 115)."""

import json
import pytest
from typer.testing import CliRunner

from src.core.competition_engine import CompetitionEngine
from src.cli.commands.competition_command import competition_app
from scripts.mcp_server import (
    handle_competition_merger,
    handle_competition_dominance,
    handle_competition_agreement,
    handle_competition_leniency,
    handle_competition_list,
    handle_competition_status,
)
from src.core.mcp_server import MekongMcpServer


@pytest.fixture
def temp_engine(tmp_path):
    db_file = tmp_path / "competition_test.db"
    return CompetitionEngine(db_path=str(db_file))


class TestCompetitionEngine:
    def test_assess_economic_concentration_safe_harbor_exempt(self, temp_engine):
        res = temp_engine.assess_economic_concentration(
            merger_name="M&A Deal Startup Small",
            acquiring_entity="Alpha Tech",
            target_entity="Beta App",
            total_assets_vnd=500_000_000_000.0,
            total_revenue_vnd=600_000_000_000.0,
            transaction_value_vnd=200_000_000_000.0,
            combined_market_share_pct=12.5,
            pre_hhi=600.0,
            post_hhi=850.0,
        )
        assert res["notification_required"] is False
        assert len(res["notification_reasons"]) == 0
        assert res["market_concentration_level"] == "UNCONCENTRATED"
        assert res["competition_impact_assessment"] == "SAFE_HARBOR_APPROVED"
        assert res["status"] == "EXEMPT_NO_NOTIFICATION"
        assert res["delta_hhi"] == 250.0

    def test_assess_economic_concentration_assets_threshold_met(self, temp_engine):
        res = temp_engine.assess_economic_concentration(
            merger_name="M&A Big Assets",
            acquiring_entity="Conglomerate A",
            target_entity="Chain B",
            total_assets_vnd=3_500_000_000_000.0,  # >= 3,000 billion VND
            total_revenue_vnd=1_000_000_000_000.0,
            transaction_value_vnd=400_000_000_000.0,
            combined_market_share_pct=15.0,
            pre_hhi=800.0,
            post_hhi=950.0,
        )
        assert res["notification_required"] is True
        assert any("Assets threshold met" in r for r in res["notification_reasons"])
        assert res["status"] == "NOTIFICATION_CLEARED_SAFE_HARBOR"

    def test_assess_economic_concentration_revenue_threshold_met(self, temp_engine):
        res = temp_engine.assess_economic_concentration(
            merger_name="M&A Big Revenue",
            acquiring_entity="Trader A",
            target_entity="Distributor B",
            total_assets_vnd=1_000_000_000_000.0,
            total_revenue_vnd=4_200_000_000_000.0,  # >= 3,000 billion VND
            transaction_value_vnd=300_000_000_000.0,
            combined_market_share_pct=18.0,
            pre_hhi=1200.0,
            post_hhi=1250.0,
        )
        assert res["notification_required"] is True
        assert any("Revenue threshold met" in r for r in res["notification_reasons"])

    def test_assess_economic_concentration_transaction_threshold_met(self, temp_engine):
        res = temp_engine.assess_economic_concentration(
            merger_name="M&A Big Transaction Value",
            acquiring_entity="Holdings A",
            target_entity="Brand B",
            total_assets_vnd=1_000_000_000_000.0,
            total_revenue_vnd=1_500_000_000_000.0,
            transaction_value_vnd=1_200_000_000_000.0,  # >= 1,000 billion VND
            combined_market_share_pct=10.0,
            pre_hhi=500.0,
            post_hhi=600.0,
        )
        assert res["notification_required"] is True
        assert any("Transaction value threshold met" in r for r in res["notification_reasons"])

    def test_assess_economic_concentration_market_share_threshold_met(self, temp_engine):
        res = temp_engine.assess_economic_concentration(
            merger_name="M&A Significant Share",
            acquiring_entity="Firm A",
            target_entity="Firm B",
            total_assets_vnd=500_000_000_000.0,
            total_revenue_vnd=500_000_000_000.0,
            transaction_value_vnd=200_000_000_000.0,
            combined_market_share_pct=26.5,  # >= 20%
            pre_hhi=1100.0,
            post_hhi=1180.0,
        )
        assert res["notification_required"] is True
        assert any("Combined market share threshold met" in r for r in res["notification_reasons"])

    def test_assess_economic_concentration_credit_institution(self, temp_engine):
        # Under credit institution rules, assets threshold is 12,000 billion VND
        res = temp_engine.assess_economic_concentration(
            merger_name="Banking Merger",
            acquiring_entity="Commercial Bank A",
            target_entity="Rural Bank B",
            total_assets_vnd=8_000_000_000_000.0,  # Below 12,000 billion VND
            total_revenue_vnd=5_000_000_000_000.0,  # Below 10,000 billion VND
            transaction_value_vnd=2_000_000_000_000.0,  # Below 3,000 billion VND
            combined_market_share_pct=14.0,  # Below 20%
            pre_hhi=800.0,
            post_hhi=950.0,
            is_credit_institution=True,
        )
        assert res["notification_required"] is False
        assert res["is_credit_institution"] is True

    def test_assess_economic_concentration_formal_appraisal_required(self, temp_engine):
        # 1000 <= Post-HHI <= 1800 and Delta HHI >= 100
        res = temp_engine.assess_economic_concentration(
            merger_name="M&A Moderate Market",
            acquiring_entity="Player 1",
            target_entity="Player 2",
            total_assets_vnd=4_000_000_000_000.0,
            total_revenue_vnd=5_000_000_000_000.0,
            transaction_value_vnd=2_000_000_000_000.0,
            combined_market_share_pct=30.0,
            pre_hhi=1200.0,
            post_hhi=1550.0,  # delta = 350 >= 100
        )
        assert res["competition_impact_assessment"] == "FORMAL_APPRAISAL_REQUIRED"
        assert res["status"] == "APPRAISAL_FORMAL_REQUIRED"

    def test_assess_economic_concentration_strict_scrutiny(self, temp_engine):
        # Post-HHI > 1800 and Delta HHI > 200
        res = temp_engine.assess_economic_concentration(
            merger_name="M&A Concentrated Market",
            acquiring_entity="Market Leader",
            target_entity="Challenger",
            total_assets_vnd=6_000_000_000_000.0,
            total_revenue_vnd=7_000_000_000_000.0,
            transaction_value_vnd=3_000_000_000_000.0,
            combined_market_share_pct=42.0,
            pre_hhi=1850.0,
            post_hhi=2200.0,  # delta = 350 > 200
        )
        assert res["market_concentration_level"] == "HIGHLY_CONCENTRATED"
        assert res["competition_impact_assessment"] == "STRICT_SCRUTINY_HIGH_RISK"
        assert res["status"] == "APPRAISAL_OFFICIAL_SCRUTINY"

    def test_assess_economic_concentration_prohibited_risk(self, temp_engine):
        # Combined share >= 50%
        res = temp_engine.assess_economic_concentration(
            merger_name="Mega Merger Near Monopoly",
            acquiring_entity="Dominant Firm",
            target_entity="Second Largest Firm",
            total_assets_vnd=10_000_000_000_000.0,
            total_revenue_vnd=12_000_000_000_000.0,
            transaction_value_vnd=5_000_000_000_000.0,
            combined_market_share_pct=54.5,  # >= 50%
            pre_hhi=2100.0,
            post_hhi=3200.0,
        )
        assert res["competition_impact_assessment"] == "PROHIBITED_CONCENTRATION_RISK"
        assert res["status"] == "APPRAISAL_STRICT_PROHIBITION_RISK"

    def test_assess_economic_concentration_invalid_inputs(self, temp_engine):
        with pytest.raises(ValueError, match="negative"):
            temp_engine.assess_economic_concentration(
                "Invalid Deal", "A", "B", -10.0, 100.0, 100.0, 20.0, 500.0, 700.0
            )

        with pytest.raises(ValueError, match="Combined market share"):
            temp_engine.assess_economic_concentration(
                "Invalid Deal", "A", "B", 100.0, 100.0, 100.0, 120.0, 500.0, 700.0
            )

        with pytest.raises(ValueError, match="Post-merger HHI cannot be less"):
            temp_engine.assess_economic_concentration(
                "Invalid Deal", "A", "B", 100.0, 100.0, 100.0, 20.0, 800.0, 600.0
            )

    def test_assess_market_dominance_single_enterprise_share(self, temp_engine):
        # Share >= 30% -> Single dominant enterprise
        res = temp_engine.assess_market_dominance(
            enterprise_name="Telecom Big A",
            market_share_pct=36.5,
        )
        assert res["dominance_type"] == "SINGLE_ENTERPRISE_DOMINANT"
        assert res["significant_market_power"] is True
        assert "Art 24 Clause 1" in res["statutory_basis"]
        assert len(res["prohibited_abuses"]) > 0

    def test_assess_market_dominance_essential_facility_smp(self, temp_engine):
        # Share < 30% but has essential facility -> SMP
        res = temp_engine.assess_market_dominance(
            enterprise_name="Infrastructure Gateway Port",
            market_share_pct=22.0,
            has_essential_facility=True,
        )
        assert res["dominance_type"] == "SINGLE_ENTERPRISE_DOMINANT"
        assert res["significant_market_power"] is True
        assert "Essential Facility Control" in res["statutory_basis"]

    def test_assess_market_dominance_group_cr2(self, temp_engine):
        # Top 2 >= 50%
        res = temp_engine.assess_market_dominance(
            enterprise_name="Company A",
            market_share_pct=28.0,
            cr_group_shares=[28.0, 26.0, 15.0, 10.0],
        )
        assert res["dominance_type"] == "GROUP_CR2_DOMINANT"
        assert res["significant_market_power"] is True
        assert "CR2 54.0% >= 50%" in res["statutory_basis"]

    def test_assess_market_dominance_group_cr3(self, temp_engine):
        # Top 2 < 50%, but top 3 >= 65%
        res = temp_engine.assess_market_dominance(
            enterprise_name="Company B",
            market_share_pct=22.0,
            cr_group_shares=[25.0, 22.0, 20.0, 10.0],  # CR2=47%, CR3=67% >= 65%
        )
        assert res["dominance_type"] == "GROUP_CR3_DOMINANT"
        assert res["significant_market_power"] is True
        assert "CR3 67.0% >= 65%" in res["statutory_basis"]

    def test_assess_market_dominance_group_cr4(self, temp_engine):
        # CR2 < 50%, CR3 < 65%, but CR4 >= 75%
        res = temp_engine.assess_market_dominance(
            enterprise_name="Company C",
            market_share_pct=18.0,
            cr_group_shares=[22.0, 20.0, 18.0, 16.0],  # CR2=42%, CR3=60%, CR4=76% >= 75%
        )
        assert res["dominance_type"] == "GROUP_CR4_DOMINANT"
        assert res["significant_market_power"] is True
        assert "CR4 76.0% >= 75%" in res["statutory_basis"]

    def test_assess_market_dominance_monopoly(self, temp_engine):
        res = temp_engine.assess_market_dominance(
            enterprise_name="National Grid Operator",
            market_share_pct=99.5,
        )
        assert res["dominance_type"] == "MONOPOLY"
        assert res["significant_market_power"] is True
        assert "Art 25" in res["statutory_basis"]

    def test_assess_market_dominance_non_dominant(self, temp_engine):
        res = temp_engine.assess_market_dominance(
            enterprise_name="Small Artisan Brand",
            market_share_pct=5.0,
            cr_group_shares=[12.0, 10.0, 8.0, 7.0],
        )
        assert res["dominance_type"] == "NON_DOMINANT"
        assert res["significant_market_power"] is False
        assert len(res["prohibited_abuses"]) == 0

    def test_assess_market_dominance_invalid_share(self, temp_engine):
        with pytest.raises(ValueError, match="Market share percentage"):
            temp_engine.assess_market_dominance("Invalid", -5.0)

    def test_review_anti_competitive_agreement_per_se_price_fixing(self, temp_engine):
        res = temp_engine.review_anti_competitive_agreement(
            agreement_title="Cement Price Fixing Pact",
            parties_count=5,
            agreement_type="PRICE_FIXING",
            is_horizontal=True,
            annual_revenue_vnd=200_000_000_000.0,
        )
        assert res["per_se_illegal"] is True
        assert res["legal_risk_level"] == "CRITICAL_PER_SE_PROHIBITED"
        assert res["max_fine_pct"] == 5.0
        assert res["max_fine_vnd"] == 10_000_000_000.0  # 5% of 200B
        assert res["status"] == "INVESTIGATION_WARRANTED"

    def test_review_anti_competitive_agreement_per_se_bid_rigging(self, temp_engine):
        res = temp_engine.review_anti_competitive_agreement(
            agreement_title="Tender Bid Rigging Syndicate",
            parties_count=3,
            agreement_type="BID_RIGGING",
            is_horizontal=True,
            annual_revenue_vnd=150_000_000_000.0,
        )
        assert res["per_se_illegal"] is True
        assert res["legal_risk_level"] == "CRITICAL_PER_SE_PROHIBITED"

    def test_review_anti_competitive_agreement_horizontal_other(self, temp_engine):
        res = temp_engine.review_anti_competitive_agreement(
            agreement_title="Joint Standard Agreement",
            parties_count=4,
            agreement_type="INPUT_PREVENTION",
            is_horizontal=True,
            annual_revenue_vnd=100_000_000_000.0,
        )
        assert res["per_se_illegal"] is False
        assert res["legal_risk_level"] == "HIGH_EFFECT_BASED_SCRUTINY"

    def test_review_anti_competitive_agreement_vertical_rpm(self, temp_engine):
        res = temp_engine.review_anti_competitive_agreement(
            agreement_title="Resale Price Maintenance Vertical Clause",
            parties_count=2,
            agreement_type="VERTICAL_RPM",
            is_horizontal=False,
            annual_revenue_vnd=80_000_000_000.0,
        )
        assert res["per_se_illegal"] is False
        assert res["legal_risk_level"] == "MEDIUM_VERTICAL_RULE_OF_REASON"
        assert res["status"] == "VERTICAL_COMPLIANCE_MONITORING"

    def test_review_anti_competitive_agreement_invalid(self, temp_engine):
        with pytest.raises(ValueError, match="at least 2 parties"):
            temp_engine.review_anti_competitive_agreement("Single firm pact", 1, "PRICE_FIXING", True, 100.0)

        with pytest.raises(ValueError, match="Invalid agreement type"):
            temp_engine.review_anti_competitive_agreement("Unknown", 3, "INVALID_TYPE", True, 100.0)

    def test_apply_leniency_order_1_full_immunity(self, temp_engine):
        res = temp_engine.apply_leniency(
            enterprise_name="Cement Producer First Confessor",
            violation_id="CARTEL-2026-001",
            submission_order=1,
            self_confessed=True,
            submitted_evidence=True,
        )
        assert res["exemption_rate_pct"] == 100.0
        assert res["leniency_status"] == "FULL_IMMUNITY_GRANTED"

    def test_apply_leniency_order_2_sixty_pct(self, temp_engine):
        res = temp_engine.apply_leniency(
            enterprise_name="Cement Producer Second Confessor",
            violation_id="CARTEL-2026-001",
            submission_order=2,
            self_confessed=True,
            submitted_evidence=True,
        )
        assert res["exemption_rate_pct"] == 60.0
        assert res["leniency_status"] == "PARTIAL_60_GRANTED"

    def test_apply_leniency_order_3_forty_pct(self, temp_engine):
        res = temp_engine.apply_leniency(
            enterprise_name="Cement Producer Third Confessor",
            violation_id="CARTEL-2026-001",
            submission_order=3,
            self_confessed=True,
            submitted_evidence=True,
        )
        assert res["exemption_rate_pct"] == 40.0
        assert res["leniency_status"] == "PARTIAL_40_GRANTED"

    def test_apply_leniency_order_4_ineligible(self, temp_engine):
        res = temp_engine.apply_leniency(
            enterprise_name="Cement Producer Fourth",
            violation_id="CARTEL-2026-001",
            submission_order=4,
            self_confessed=True,
            submitted_evidence=True,
        )
        assert res["exemption_rate_pct"] == 0.0
        assert res["leniency_status"] == "INELIGIBLE_ORDER_EXCEEDED"

    def test_apply_leniency_rejected_no_confession_or_evidence(self, temp_engine):
        res1 = temp_engine.apply_leniency(
            enterprise_name="Firm No Confession",
            violation_id="CARTEL-2026-001",
            submission_order=1,
            self_confessed=False,
            submitted_evidence=True,
        )
        assert res1["exemption_rate_pct"] == 0.0
        assert res1["leniency_status"] == "REJECTED_NO_CONFESSION_OR_EVIDENCE"

        res2 = temp_engine.apply_leniency(
            enterprise_name="Firm No Evidence",
            violation_id="CARTEL-2026-001",
            submission_order=1,
            self_confessed=True,
            submitted_evidence=False,
        )
        assert res2["exemption_rate_pct"] == 0.0
        assert res2["leniency_status"] == "REJECTED_NO_CONFESSION_OR_EVIDENCE"

    def test_apply_leniency_invalid_order(self, temp_engine):
        with pytest.raises(ValueError, match="Submission order must be 1 or greater"):
            temp_engine.apply_leniency("Bad Order", "CARTEL-01", 0, True, True)

    def test_list_competition_records_and_telemetry(self, temp_engine):
        temp_engine.assess_economic_concentration(
            "Merger List 1", "Buyer", "Target", 3.5e12, 1e12, 5e11, 22.0, 1000.0, 1200.0
        )
        temp_engine.assess_market_dominance("Firm Dom 1", 35.0)
        temp_engine.review_anti_competitive_agreement("Cartel List 1", 3, "PRICE_FIXING", True, 1e11)
        temp_engine.apply_leniency("Firm Len 1", "AGR-1", 1, True, True)

        all_records = temp_engine.list_competition_records("all")
        assert len(all_records["concentrations"]) == 1
        assert len(all_records["dominance"]) == 1
        assert len(all_records["agreements"]) == 1
        assert len(all_records["leniency"]) == 1

        conc_records = temp_engine.list_competition_records("concentrations")
        assert "concentrations" in conc_records
        assert "dominance" not in conc_records

        telemetry = temp_engine.get_competition_telemetry()
        assert telemetry["status"] == "HEALTHY"
        assert telemetry["economic_concentrations"]["total_assessed"] == 1
        assert telemetry["economic_concentrations"]["notification_required_count"] == 1
        assert telemetry["market_dominance"]["total_assessed"] == 1
        assert telemetry["market_dominance"]["dominant_or_monopoly_count"] == 1
        assert telemetry["anti_competitive_agreements"]["total_reviewed"] == 1
        assert telemetry["anti_competitive_agreements"]["per_se_cartels_prohibited"] == 1
        assert telemetry["leniency_program"]["total_applications"] == 1
        assert telemetry["leniency_program"]["full_immunity_granted"] == 1


class TestCompetitionCli:
    def setup_method(self):
        self.runner = CliRunner()

    def test_cli_main_dashboard(self):
        res = self.runner.invoke(competition_app, [])
        assert res.exit_code == 0
        assert "ỦY BAN CẠNH TRANH QUỐC GIA" in res.output or "NCC" in res.output

    def test_cli_main_dashboard_json(self):
        res = self.runner.invoke(competition_app, ["--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"
        assert "economic_concentrations" in data

    def test_cli_merger(self):
        res = self.runner.invoke(
            competition_app,
            [
                "merger",
                "Supermarket Chain Acquisition",
                "--buyer", "Mega Retail Corp",
                "--target", "Fresh Market Ltd",
                "--assets", "3800000000000",
                "--revenue", "4100000000000",
                "--value", "1200000000000",
                "--share", "24.5",
                "--pre-hhi", "1200",
                "--post-hhi", "1450",
            ],
        )
        assert res.exit_code == 0
        assert "KẾT QUẢ THẨM ĐỊNH TẬP TRUNG KINH TẾ" in res.output
        assert "Mega Retail Corp" in res.output

    def test_cli_merger_json(self):
        res = self.runner.invoke(
            competition_app,
            [
                "merger",
                "Pharma Deal",
                "--buyer", "Pharma A",
                "--target", "Pharma B",
                "--assets", "1000000000000",
                "--revenue", "1500000000000",
                "--value", "500000000000",
                "--share", "15.0",
                "--pre-hhi", "800",
                "--post-hhi", "900",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["merger_name"] == "Pharma Deal"
        assert data["notification_required"] is False

    def test_cli_dominance(self):
        res = self.runner.invoke(
            competition_app,
            [
                "dominance",
                "E-Commerce Platform Giant",
                "--share", "38.5",
                "--cr-shares", "38.5,22.0,18.0",
                "--essential-facility",
            ],
        )
        assert res.exit_code == 0
        assert "ĐÁNH GIÁ VỊ TRÍ THỐNG LĨNH THỊ TRƯỜNG" in res.output
        assert "SINGLE_ENTERPRISE_DOMINANT" in res.output

    def test_cli_dominance_json(self):
        res = self.runner.invoke(
            competition_app,
            [
                "dominance",
                "Fintech Leader",
                "--share", "32.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["enterprise_name"] == "Fintech Leader"
        assert data["significant_market_power"] is True

    def test_cli_agreement(self):
        res = self.runner.invoke(
            competition_app,
            [
                "agreement",
                "Regional Steel Price Fixing Cartel",
                "--parties", "4",
                "--type", "PRICE_FIXING",
                "--horizontal",
                "--revenue", "300000000000",
            ],
        )
        assert res.exit_code == 0
        assert "RÀ SOÁT THỎA THUẬN HẠN CHẾ CẠNH TRANH" in res.output
        assert "CẤM TUYỆT ĐỐI" in res.output

    def test_cli_agreement_json(self):
        res = self.runner.invoke(
            competition_app,
            [
                "agreement",
                "Distributor Exclusive Territory",
                "--parties", "2",
                "--type", "EXCLUSIVE_DISTRIBUTION",
                "--vertical",
                "--revenue", "50000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["per_se_illegal"] is False

    def test_cli_leniency(self):
        res = self.runner.invoke(
            competition_app,
            [
                "leniency",
                "Steel Mill Confessor Alpha",
                "--violation", "STEEL-CARTEL-2026",
                "--order", "1",
                "--confess",
                "--evidence",
            ],
        )
        assert res.exit_code == 0
        assert "KẾT QUẢ ÁP DỤNG CHÍNH SÁCH KHOAN HỒNG" in res.output
        assert "100%" in res.output

    def test_cli_leniency_json(self):
        res = self.runner.invoke(
            competition_app,
            [
                "leniency",
                "Steel Mill Confessor Beta",
                "--violation", "STEEL-CARTEL-2026",
                "--order", "2",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["exemption_rate_pct"] == 60.0
        assert data["leniency_status"] == "PARTIAL_60_GRANTED"

    def test_cli_list(self):
        res = self.runner.invoke(competition_app, ["list", "all"])
        assert res.exit_code == 0

    def test_cli_list_json(self):
        res = self.runner.invoke(competition_app, ["list", "all", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, dict)

    def test_cli_status(self):
        res = self.runner.invoke(competition_app, ["status"])
        assert res.exit_code == 0
        assert "CHỈ SỐ TELEMETRY" in res.output

    def test_cli_status_json(self):
        res = self.runner.invoke(competition_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"


class TestCompetitionMcp:
    def test_scripts_mcp_merger(self):
        res_str = handle_competition_merger({
            "merger_name": "MCP Merger Deal",
            "acquiring_entity": "Acquirer X",
            "target_entity": "Target Y",
            "total_assets_vnd": 3.2e12,
            "total_revenue_vnd": 1.5e12,
            "transaction_value_vnd": 8e11,
            "combined_market_share_pct": 21.5,
            "pre_hhi": 1000.0,
            "post_hhi": 1250.0,
        })
        data = json.loads(res_str)
        assert data["merger_name"] == "MCP Merger Deal"
        assert data["notification_required"] is True

    def test_scripts_mcp_dominance(self):
        res_str = handle_competition_dominance({
            "enterprise_name": "MCP Dominant Firm",
            "market_share_pct": 33.0,
            "cr_group_shares": "33.0, 20.0, 15.0",
        })
        data = json.loads(res_str)
        assert data["enterprise_name"] == "MCP Dominant Firm"
        assert data["significant_market_power"] is True

    def test_scripts_mcp_agreement(self):
        res_str = handle_competition_agreement({
            "agreement_title": "MCP Price Cartel",
            "parties_count": 3,
            "agreement_type": "PRICE_FIXING",
            "is_horizontal": True,
            "annual_revenue_vnd": 100_000_000_000.0,
        })
        data = json.loads(res_str)
        assert data["per_se_illegal"] is True

    def test_scripts_mcp_leniency(self):
        res_str = handle_competition_leniency({
            "enterprise_name": "MCP Confessor",
            "violation_id": "MCP-VIOL-01",
            "submission_order": 1,
            "self_confessed": True,
            "submitted_evidence": True,
        })
        data = json.loads(res_str)
        assert data["exemption_rate_pct"] == 100.0

    def test_scripts_mcp_list(self):
        res_str = handle_competition_list({"category": "all", "limit": 10})
        data = json.loads(res_str)
        assert isinstance(data, dict)

    def test_scripts_mcp_status(self):
        res_str = handle_competition_status({})
        data = json.loads(res_str)
        assert data["status"] == "HEALTHY"

    def test_core_mcp_server_handlers(self):
        server = MekongMcpServer()
        assert hasattr(server, "_handle_competition_merger")
        assert hasattr(server, "_handle_competition_dominance")
        assert hasattr(server, "_handle_competition_agreement")
        assert hasattr(server, "_handle_competition_leniency")
        assert hasattr(server, "_handle_competition_list")
        assert hasattr(server, "_handle_competition_status")

        status_str = server._handle_competition_status()
        status_data = json.loads(status_str)
        assert status_data["status"] == "HEALTHY"
