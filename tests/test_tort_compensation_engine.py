"""Unit tests for TortCompensationEngine (Phase 150)."""

import os
import pytest
from src.core.tort_compensation_engine import (
    BASE_SALARY_VND,
    CAP_MONTHS_CORPSE_DAMAGE,
    CAP_MONTHS_GRAVE_DAMAGE,
    CAP_MONTHS_HEALTH_DAMAGE,
    CAP_MONTHS_LIFE_DAMAGE,
    CAP_MONTHS_REPUTATION_DAMAGE,
    CaseStatus,
    DamageCategory,
    FaultType,
    LiabilityType,
    STATUTE_LIMITATION_YEARS,
    TortCompensationEngine,
)


@pytest.fixture
def engine():
    return TortCompensationEngine(db_path=":memory:")


class TestTortCompensationEngine:
    """Test suite for TortCompensationEngine core logic."""

    def test_constants_and_statutory_parameters(self):
        """Verify baseline statutory values per BLDS 2015 and Decree 73/2024/ND-CP."""
        assert BASE_SALARY_VND == 2_340_000.0
        assert CAP_MONTHS_HEALTH_DAMAGE == 50
        assert CAP_MONTHS_LIFE_DAMAGE == 100
        assert CAP_MONTHS_REPUTATION_DAMAGE == 10
        assert CAP_MONTHS_CORPSE_DAMAGE == 30
        assert CAP_MONTHS_GRAVE_DAMAGE == 10
        assert STATUTE_LIMITATION_YEARS == 3

    def test_create_case_and_statute_of_limitations(self, engine):
        """Test case creation and statute of limitations computation (Article 588)."""
        res = engine.create_case(
            incident_date="2026-01-15",
            incident_location="Quận 1, TP. Hồ Chí Minh",
            damage_category=DamageCategory.HEALTH,
            liability_type=LiabilityType.HIGH_RISK_SOURCE,
            description="Va chạm giao thông do xe cơ giới gây ra",
        )
        assert res["case_id"].startswith("TC-")
        assert res["damage_category"] == "HEALTH"
        assert res["liability_type"] == "HIGH_RISK_SOURCE"
        assert res["status"] == "REGISTERED"

        limitation = res["statute_of_limitations"]
        assert limitation["statute_years"] == 3
        assert limitation["is_expired"] is False
        assert limitation["days_remaining"] > 0

    def test_statute_of_limitations_expired(self, engine):
        """Test statute of limitations calculation when past 3 years."""
        res = engine.check_statute_of_limitations(
            discovery_date_str="2020-01-01",
            reference_date_str="2026-03-01",
        )
        assert res["is_expired"] is True
        assert res["days_remaining"] == 0

    def test_calculate_health_damage_without_disability(self, engine):
        """Test health damage calculation without permanent disability (Article 590)."""
        res = engine.calculate_health_damage(
            treatment_and_rehab_costs=20_000_000.0,
            lost_income_victim=15_000_000.0,
            caregiver_costs_and_lost_income=5_000_000.0,
            other_actual_expenses=2_000_000.0,
            disability_percentage=0.0,
        )
        breakdown = res["breakdown"]
        assert breakdown["total_material_damage"] == 42_000_000.0
        assert breakdown["emotional_distress_cap"] == 50 * BASE_SALARY_VND
        assert res["final_payable_compensation"] > 42_000_000.0

    def test_calculate_health_damage_with_disability_and_fault(self, engine):
        """Test health damage with permanent disability and victim comparative fault."""
        res = engine.calculate_health_damage(
            treatment_and_rehab_costs=30_000_000.0,
            lost_income_victim=20_000_000.0,
            caregiver_costs_and_lost_income=10_000_000.0,
            disability_percentage=40.0,
            victim_fault_percentage=20.0,
        )
        breakdown = res["breakdown"]
        assert breakdown["total_material_damage"] == 60_000_000.0
        assert res["victim_fault_percentage"] == 20.0
        assert res["victim_fault_deduction"] > 0
        assert res["final_payable_compensation"] > 0

    def test_calculate_life_damage(self, engine):
        """Test life damage calculation with dependents (Articles 591, 593)."""
        dependents = [
            {
                "full_name": "Nguyễn Văn Con",
                "relationship": "CHILD",
                "monthly_allowance": 2_340_000.0,
                "duration_months": 120,
            },
            {
                "full_name": "Nguyễn Thị Mẹ",
                "relationship": "PARENT",
                "monthly_allowance": 2_340_000.0,
                "duration_months": 60,
            },
        ]
        res = engine.calculate_life_damage(
            pre_death_treatment_costs=15_000_000.0,
            reasonable_funeral_expenses=35_000_000.0,
            dependents=dependents,
        )
        breakdown = res["breakdown"]
        assert breakdown["pre_death_treatment_costs"] == 15_000_000.0
        assert breakdown["reasonable_funeral_expenses"] == 35_000_000.0
        expected_dependents = (2_340_000.0 * 120) + (2_340_000.0 * 60)
        assert breakdown["total_dependent_allowances"] == expected_dependents
        assert breakdown["emotional_distress_cap"] == 100 * BASE_SALARY_VND
        assert res["final_payable_compensation"] > 0

    def test_calculate_property_damage(self, engine):
        """Test property damage calculation (Article 589)."""
        res = engine.calculate_property_damage(
            lost_or_destroyed_value=100_000_000.0,
            depreciation_or_repair_costs=10_000_000.0,
            lost_usufruct_and_earnings=20_000_000.0,
            mitigation_costs=5_000_000.0,
            victim_fault_percentage=10.0,
        )
        breakdown = res["breakdown"]
        assert breakdown["total_material_damage"] == 135_000_000.0
        # 10% fault deduction
        assert res["final_payable_compensation"] == 135_000_000.0 * 0.9

    def test_calculate_reputation_honor_damage(self, engine):
        """Test honor and reputation infringement damage (Article 592)."""
        res = engine.calculate_reputation_honor_damage(
            remedy_and_rectification_costs=5_000_000.0,
            lost_or_reduced_income=15_000_000.0,
            other_actual_losses=0.0,
        )
        breakdown = res["breakdown"]
        assert breakdown["total_material_damage"] == 20_000_000.0
        assert breakdown["emotional_distress_cap"] == 10 * BASE_SALARY_VND
        assert res["final_payable_compensation"] == 20_000_000.0 + (10 * BASE_SALARY_VND)

    def test_assess_special_liability_high_risk_source(self, engine):
        """Test strict liability for high-risk source (Article 601)."""
        res = engine.assess_special_liability(
            liability_type=LiabilityType.HIGH_RISK_SOURCE,
            direct_tortfeasor_info={"full_name": "Tài xế Nguyễn Văn A"},
            responsible_party_info={"full_name": "Công ty Vận tải Mekong"},
        )
        assert res["is_exempt_from_liability"] is False
        assert "601" in res["governing_rule"]

    def test_create_settlement_and_dossier(self, engine):
        """Test settlement creation and full legal dossier generation."""
        case_res = engine.create_case(
            incident_date="2026-02-01",
            incident_location="Hà Nội",
            damage_category=DamageCategory.PROPERTY,
            liability_type=LiabilityType.HIGH_RISK_SOURCE,
            description="Va quẹt xe container làm hư hỏng hàng hóa",
        )
        cid = case_res["case_id"]

        settle_res = engine.create_settlement_agreement(
            case_id=cid,
            total_agreed_amount=85_000_000.0,
            payment_terms="Chuyển khoản 100% trong 5 ngày làm việc",
            conciliator_name="Hòa giải viên Trung tâm Mekong",
            is_court_recognized=True,
        )
        assert settle_res["settlement_id"].startswith("SA-")
        assert settle_res["total_agreed_amount"] == 85_000_000.0
        assert settle_res["is_court_recognized"] is True

        dossier = engine.generate_assessment_dossier(case_id=cid)
        assert dossier["dossier_id"] == f"DOSSIER-{cid}"
        assert dossier["case_summary"]["status"] == "SETTLED"
        assert len(dossier["settlements"]) == 1
        assert dossier["compliance_rating"] == "EXCELLENT"
