# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit tests for Vietnamese Administrative Sanctions & Violations Compliance Engine (Phase 151).

Statutory framework:
- Law on Handling of Administrative Violations 2012 (Law No. 15/2012/QH13), amended by Law No. 67/2020/QH14.
- Decree No. 118/2021/ND-CP detailing articles and implementation measures.
"""

import pytest
from src.core.adminsanction_engine import (
    AdminSanctionEngine,
    AuthorityBranch,
    EntityType,
    MAX_FINES_INDIVIDUAL_VND,
    RemedialMeasureType,
    SanctionType,
    TWO_YEAR_LIMITATION_SECTORS,
    ViolationStatus,
)


@pytest.fixture
def engine():
    return AdminSanctionEngine(db_path=":memory:")


class TestAdminSanctionEngine:
    """Test suite for AdminSanctionEngine core logic."""

    def test_statutory_constants(self):
        """Verify baseline statutory constants per Law on Handling of Administrative Violations."""
        assert "TAXATION" in MAX_FINES_INDIVIDUAL_VND
        assert "ENVIRONMENTAL_PROTECTION" in MAX_FINES_INDIVIDUAL_VND
        assert "TAXATION" in TWO_YEAR_LIMITATION_SECTORS
        assert "ENVIRONMENTAL_PROTECTION" in TWO_YEAR_LIMITATION_SECTORS
        assert MAX_FINES_INDIVIDUAL_VND["TAXATION"] == 100_000_000.0
        assert MAX_FINES_INDIVIDUAL_VND["ENVIRONMENTAL_PROTECTION"] == 1_000_000_000.0
        assert MAX_FINES_INDIVIDUAL_VND["SECURITIES_MARKET"] == 1_500_000_000.0

    def test_check_statute_of_limitations_standard_and_two_year(self, engine):
        """Test checking statute of limitations for standard (1-year) and extended (2-year) sectors (Article 6)."""
        # 1-year sector: TRAFFIC_ROAD_RAIL
        res1 = engine.check_statute_of_limitations(
            sector="TRAFFIC_ROAD_RAIL",
            violation_date="2026-02-15",
            violation_status="CONCLUDED",
            assessment_date="2026-03-01",
        )
        assert res1["statute_limit_years"] == 1
        assert res1["is_time_barred"] is False
        assert res1["days_remaining"] > 300

        # Expired standard violation
        res1_expired = engine.check_statute_of_limitations(
            sector="TRAFFIC_ROAD_RAIL",
            violation_date="2024-01-01",
            violation_status="CONCLUDED",
            assessment_date="2026-03-01",
        )
        assert res1_expired["statute_limit_years"] == 1
        assert res1_expired["is_time_barred"] is True
        assert res1_expired["days_remaining"] == 0

        # 2-year sector: TAXATION
        res2 = engine.check_statute_of_limitations(
            sector="TAXATION",
            violation_date="2024-08-01",
            violation_status="CONCLUDED",
            assessment_date="2026-03-01",
        )
        assert res2["statute_limit_years"] == 2
        assert res2["is_time_barred"] is False

        # Ongoing violation: calculated from discovery date (Article 6.1.b)
        res_ongoing = engine.check_statute_of_limitations(
            sector="CONSTRUCTION",
            violation_date="2023-01-01",
            discovery_date="2026-01-10",
            violation_status="ONGOING",
            assessment_date="2026-03-01",
        )
        assert res_ongoing["statute_limit_years"] == 2
        assert res_ongoing["is_time_barred"] is False

    def test_record_violation_case(self, engine):
        """Test recording violation case in sqlite database."""
        res = engine.record_violation_case(
            entity_type=EntityType.ORGANIZATION,
            violator_name="Công ty TNHH Hóa Chất Sao Mai",
            sector="TAXATION",
            violation_description="Khai sai dẫn đến thiếu số tiền thuế phải nộp",
            violation_date="2026-01-15",
            violation_status=ViolationStatus.CONCLUDED,
        )
        assert res["case_id"].startswith("VPHC-")
        assert res["violator_name"] == "Công ty TNHH Hóa Chất Sao Mai"
        assert res["entity_type"] == "ORGANIZATION"
        assert res["limitation_assessment"]["statute_limit_years"] == 2
        assert res["limitation_assessment"]["is_time_barred"] is False

    def test_calculate_fine_individual_vs_organization(self, engine):
        """Test fine calculation with 2x multiplier for organizations and average fine formula (Articles 23, 24)."""
        # Individual: statutory bracket 10M - 20M -> average 15M
        res_ind = engine.calculate_fine(
            entity_type=EntityType.INDIVIDUAL,
            statutory_min_fine_individual=10_000_000.0,
            statutory_max_fine_individual=20_000_000.0,
        )
        assert res_ind["multiplier"] == 1.0
        assert res_ind["final_payable_fine_vnd"] == 15_000_000.0

        # Organization: statutory bracket 10M - 20M -> applied bracket 20M - 40M -> average 30M
        res_org = engine.calculate_fine(
            entity_type=EntityType.ORGANIZATION,
            statutory_min_fine_individual=10_000_000.0,
            statutory_max_fine_individual=20_000_000.0,
        )
        assert res_org["multiplier"] == 2.0
        assert res_org["final_payable_fine_vnd"] == 30_000_000.0

    def test_calculate_fine_mitigating_and_aggravating(self, engine):
        """Test fine adjustments with mitigating and aggravating circumstances (Decree 118/2021/ND-CP)."""
        # 1 mitigating factor -> reduces from average towards min
        res_mit = engine.calculate_fine(
            entity_type=EntityType.INDIVIDUAL,
            statutory_min_fine_individual=10_000_000.0,
            statutory_max_fine_individual=20_000_000.0,
            mitigating_factors=["Tự nguyện khai báo, thành thật hối lỗi"],
        )
        assert res_mit["final_payable_fine_vnd"] < 15_000_000.0
        assert res_mit["final_payable_fine_vnd"] >= 10_000_000.0

        # 1 aggravating factor -> increases from average towards max
        res_agg = engine.calculate_fine(
            entity_type=EntityType.INDIVIDUAL,
            statutory_min_fine_individual=10_000_000.0,
            statutory_max_fine_individual=20_000_000.0,
            aggravating_factors=["Tái phạm vi phạm hành chính"],
        )
        assert res_agg["final_payable_fine_vnd"] > 15_000_000.0
        assert res_agg["final_payable_fine_vnd"] <= 20_000_000.0

        # Offsetting equal factors -> returns average
        res_bal = engine.calculate_fine(
            entity_type=EntityType.INDIVIDUAL,
            statutory_min_fine_individual=10_000_000.0,
            statutory_max_fine_individual=20_000_000.0,
            mitigating_factors=["Tự nguyện bồi thường"],
            aggravating_factors=["Tái phạm"],
        )
        assert res_bal["final_payable_fine_vnd"] == 15_000_000.0

    def test_assess_authority_jurisdiction(self, engine):
        """Test assessing sanctioning authority competence (Articles 38-51)."""
        # Chủ tịch UBND cấp Xã: fine cap is 5,000,000 VND, cannot suspend license
        res_xa = engine.assess_authority_jurisdiction(
            branch=AuthorityBranch.PEOPLE_COMMITTEE.value,
            officer_title="Chủ tịch UBND xã",
            proposed_fine_vnd=4_000_000.0,
            requires_license_suspension=False,
        )
        assert res_xa["is_competent"] is True

        # Exceeds fine limit of Chủ tịch Xã (e.g. 10M > 5M)
        res_xa_exceed = engine.assess_authority_jurisdiction(
            branch=AuthorityBranch.PEOPLE_COMMITTEE.value,
            officer_title="Chủ tịch UBND xã",
            proposed_fine_vnd=10_000_000.0,
            requires_license_suspension=False,
        )
        assert res_xa_exceed["is_competent"] is False
        assert any("Vượt quá mức phạt tối đa" in r for r in res_xa_exceed["jurisdiction_reasons"])

        # Chủ tịch UBND cấp Tỉnh: Fine cap up to max statutory sector limits, can suspend license & confiscate
        res_tinh = engine.assess_authority_jurisdiction(
            branch=AuthorityBranch.PEOPLE_COMMITTEE.value,
            officer_title="Chủ tịch UBND tỉnh",
            proposed_fine_vnd=500_000_000.0,
            requires_license_suspension=True,
            requires_confiscation=True,
            confiscated_value_vnd=1_000_000_000.0,
        )
        assert res_tinh["is_competent"] is True

    def test_calculate_remedial_measures(self, engine):
        """Test remedial measures and illegal profit disgorgement (Article 28 & Decree 118/2021)."""
        measures = [
            {
                "measure_type": RemedialMeasureType.RESTORE_ORIGINAL_STATE.value,
                "description": "Buộc khôi phục lại hiện trạng đất ban đầu",
                "deadline_days": 15,
            }
        ]
        # Revenue = 100M, legitimate deductible costs = 30M -> net illegal profit = 70M
        res = engine.calculate_remedial_measures(
            measures=measures,
            direct_illegal_revenue_vnd=100_000_000.0,
            legitimate_deductible_costs_vnd=30_000_000.0,
            dissipated_asset_value_vnd=10_000_000.0,
        )
        assert res["net_illegal_profit_vnd"] == 70_000_000.0
        assert res["total_remedial_financial_obligation_vnd"] == 80_000_000.0
        assert len(res["remedial_measures_list"]) == 3

    def test_generate_sanction_decision(self, engine):
        """Test formal administrative sanction decision generation and persistence."""
        case_res = engine.record_violation_case(
            entity_type=EntityType.ORGANIZATION,
            violator_name="Công ty TNHH Xuất Nhập Khẩu Bình Minh",
            sector="TRADE_COMMERCE",
            violation_description="Kinh doanh hàng nhập lậu",
            violation_date="2026-02-10",
        )
        decision = engine.generate_sanction_decision(
            case_id=case_res["case_id"],
            decision_number="12/QĐ-XPHC",
            issuing_authority="Cục Quản lý thị trường TP.HCM",
            issuing_officer_title="Cục trưởng",
            principal_sanction=SanctionType.FINE.value,
            fine_amount_vnd=60_000_000.0,
            illegal_profit_amount_vnd=20_000_000.0,
            execution_deadline_days=10,
        )
        assert decision["decision_id"].startswith("DEC-")
        assert decision["total_financial_obligation_vnd"] == 80_000_000.0
        assert "execution_terms" in decision
        assert decision["execution_terms"]["voluntary_execution_deadline_days"] == 10

    def test_assess_relief_eligibility(self, engine):
        """Test assessment for fine deferral, reduction, or exemption (Articles 76, 77)."""
        # Individual fine 10M (>= 2M) with economic distress -> eligible for deferral and reduction
        res_ind = engine.assess_relief_eligibility(
            entity_type=EntityType.INDIVIDUAL.value,
            fine_amount_vnd=10_000_000.0,
            has_severe_economic_distress=True,
            has_compensated_damages=True,
        )
        assert res_ind["eligible_for_deferral"] is True
        assert res_ind["eligible_for_reduction"] is True

        # Organization fine 50M (< 100M threshold) -> ineligible for deferral under Art 76
        res_org = engine.assess_relief_eligibility(
            entity_type=EntityType.ORGANIZATION.value,
            fine_amount_vnd=50_000_000.0,
            has_severe_economic_distress=True,
        )
        assert res_org["eligible_for_deferral"] is False

    def test_statutory_dashboard(self, engine):
        """Test statutory dashboard metrics."""
        engine.record_violation_case(
            entity_type=EntityType.INDIVIDUAL,
            violator_name="Trần Thị Lan",
            sector="TRADE_COMMERCE",
            violation_description="Kinh doanh hàng hóa nhập lậu",
            violation_date="2026-02-01",
        )
        dashboard = engine.get_statutory_dashboard()
        assert dashboard["total_cases_recorded"] >= 1
        assert "statutory_framework" in dashboard
        assert dashboard["statutory_framework"]["law_number"] == "15/2012/QH13 (amended by 67/2020/QH14)"
