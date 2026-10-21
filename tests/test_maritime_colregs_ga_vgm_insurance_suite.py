"""Unit Tests for Maritime COLREGs, General Average, Container VGM & Insurance Suite.

Phases 319-322 Zero-Mock, Deterministic Tests.
"""

import pytest

from src.core.maritime_colregs_ga_vgm_insurance_engine import (
    ColregsActionObligation,
    ColregsAssessmentResult,
    ColregsNavigationEngine,
    ColregsTargetInput,
    ContainerVgmComplianceEngine,
    ContainerVgmInput,
    ContainerVgmResult,
    EncounterSituation,
    GaAdjustmentResult,
    GaContributoryItem,
    GaInterestParty,
    GeneralAverageAdjustmentEngine,
    HullLossType,
    ItcHullsClaimEngine,
    ItcHullsClaimInput,
    ItcHullsClaimResult,
    VgmMethod,
)


def test_colregs_head_on_situation():
    """Phase 319: Test Rule 14 Head-on meeting situation and mutual starboard alteration."""
    inp = ColregsTargetInput(
        own_vessel_name="MEKONG_PRIDE",
        own_course_deg=0.0,
        own_speed_knots=15.0,
        target_vessel_name="PACIFIC_VOYAGER",
        target_bearing_deg=2.0,  # Nearly dead ahead
        target_range_nm=6.0,
        target_course_deg=180.0, # Reciprocal course
        target_speed_knots=15.0,
        safe_cpa_distance_nm=1.5,
        safe_tcpa_time_min=20.0,
    )
    res: ColregsAssessmentResult = ColregsNavigationEngine.evaluate_encounter(inp)

    assert res.situation == EncounterSituation.HEAD_ON
    assert res.action_obligation == ColregsActionObligation.MUTUAL_STARBOARD
    assert res.risk_of_collision is True
    assert res.cpa_distance_nm < 1.0
    assert 10.0 <= res.tcpa_minutes <= 14.0
    assert "starboard" in res.recommended_maneuver.lower()
    assert len(res.audit_hash) == 16
    assert isinstance(res.to_dict(), dict)


def test_colregs_crossing_give_way_and_stand_on():
    """Phase 319: Test Rule 15 Crossing situation for both give-way (starboard) and stand-on (port)."""
    # 1. Target on Starboard side -> Own vessel is Give-way
    give_way_inp = ColregsTargetInput(
        own_vessel_name="MEKONG_PRIDE",
        own_course_deg=0.0,
        own_speed_knots=12.0,
        target_vessel_name="EVER_OCEAN",
        target_bearing_deg=45.0,  # 45 deg on starboard bow
        target_range_nm=5.0,
        target_course_deg=270.0, # Crossing from right to left
        target_speed_knots=14.0,
    )
    res_gw = ColregsNavigationEngine.evaluate_encounter(give_way_inp)
    assert res_gw.situation == EncounterSituation.CROSSING_GIVE_WAY
    assert res_gw.action_obligation == ColregsActionObligation.GIVE_WAY
    assert res_gw.risk_of_collision is True

    # 2. Target on Port side -> Own vessel is Stand-on
    stand_on_inp = ColregsTargetInput(
        own_vessel_name="MEKONG_PRIDE",
        own_course_deg=0.0,
        own_speed_knots=14.0,
        target_vessel_name="NORDIC_STAR",
        target_bearing_deg=315.0, # 45 deg on port bow
        target_range_nm=5.0,
        target_course_deg=90.0,  # Crossing from left to right
        target_speed_knots=12.0,
    )
    res_so = ColregsNavigationEngine.evaluate_encounter(stand_on_inp)
    assert res_so.situation == EncounterSituation.CROSSING_STAND_ON
    assert res_so.action_obligation == ColregsActionObligation.STAND_ON


def test_colregs_safe_passing():
    """Phase 319: Test safe passing where CPA is outside safety perimeter."""
    safe_inp = ColregsTargetInput(
        own_vessel_name="MEKONG_PRIDE",
        own_course_deg=90.0,
        own_speed_knots=10.0,
        target_vessel_name="MEKONG_DELTA_1",
        target_bearing_deg=180.0,
        target_range_nm=8.0,
        target_course_deg=90.0,  # Parallel course
        target_speed_knots=10.0,
        safe_cpa_distance_nm=1.5,
    )
    res_safe = ColregsNavigationEngine.evaluate_encounter(safe_inp)
    assert res_safe.risk_of_collision is False
    assert res_safe.situation == EncounterSituation.SAFE_PASSING
    assert res_safe.action_obligation == ColregsActionObligation.NONE_REQUIRED


def test_general_average_adjustment_full_apportionment():
    """Phase 320: Test York-Antwerp Rules 2016 General Average apportionment and net settlement."""
    items = [
        # Tàu: Giá trị 10M, tổn thất riêng 200k, hy sinh máy 100k, chi phí cứu hộ 150k
        GaContributoryItem(
            item_id="VESSEL_01",
            party=GaInterestParty.SHIPOWNER,
            name="M/V Mekong Star",
            sound_value_usd=10000000.0,
            non_ga_damage_deduction_usd=200000.0,
            ga_sacrifice_amount_usd=100000.0,
            ga_direct_expenditure_usd=150000.0,
        ),
        # Chủ hàng A: Hàng 4M, không bị hy sinh
        GaContributoryItem(
            item_id="CARGO_A",
            party=GaInterestParty.CARGO_OWNER,
            name="Coffee Containers Consignment A",
            sound_value_usd=4000000.0,
            non_ga_damage_deduction_usd=0.0,
            ga_sacrifice_amount_usd=0.0,
            ga_direct_expenditure_usd=0.0,
        ),
        # Chủ hàng B: Hàng 1M, bị vứt bỏ hy sinh 300k (Jettison)
        GaContributoryItem(
            item_id="CARGO_B",
            party=GaInterestParty.CARGO_OWNER,
            name="Rice Containers Consignment B",
            sound_value_usd=1000000.0,
            non_ga_damage_deduction_usd=0.0,
            ga_sacrifice_amount_usd=300000.0,
            ga_direct_expenditure_usd=0.0,
        ),
        # Cước phí: 200k
        GaContributoryItem(
            item_id="FREIGHT_01",
            party=GaInterestParty.CHARTERER,
            name="At-risk Freight Voyage #12",
            sound_value_usd=200000.0,
            non_ga_damage_deduction_usd=0.0,
            ga_sacrifice_amount_usd=0.0,
            ga_direct_expenditure_usd=0.0,
        ),
    ]

    res: GaAdjustmentResult = GeneralAverageAdjustmentEngine.calculate_adjustment("GA-2026-001", items)

    # 1. Total Contributory Value = (10M - 200k + 100k) + 4M + (1M + 300k) + 200k = 9.9M + 4M + 1.3M + 0.2M = 15.4M
    assert res.total_contributory_value_usd == 15400000.0
    # 2. Total GA Losses = (100k + 150k) + 0 + 300k + 0 = 550,000
    assert res.total_ga_loss_usd == 550000.0
    # 3. GA Rate = 550,000 / 15,400,000 = ~3.5714%
    expected_rate = (550000.0 / 15400000.0) * 100.0
    assert pytest.approx(res.ga_contribution_rate_pct, 0.001) == expected_rate

    # 4. Kiểm tra nguyên lý bảo toàn quỹ GA: Tổng số tiền thu = Tổng số tiền chi -> sum(net_balance) == 0
    net_balances_sum = sum(s.net_balance_usd for s in res.settlements)
    assert pytest.approx(net_balances_sum, abs=0.01) == 0.0
    assert len(res.settlements) == 4
    assert res.to_dict()["incident_ref"] == "GA-2026-001"


def test_general_average_empty_validation():
    """Phase 320: Test exception handling when GA items list is empty."""
    with pytest.raises(ValueError, match="không được để trống"):
        GeneralAverageAdjustmentEngine.calculate_adjustment("GA-ERR", [])


def test_container_vgm_method_1_and_2_compliant():
    """Phase 321: Test compliant container VGM verification under Method 1 and Method 2."""
    inp = ContainerVgmInput(
        container_no="TEMU1234567",
        booking_no="BKG-SGN-2026-88",
        vgm_method=VgmMethod.METHOD_1,
        tare_weight_kg=3800.0,
        max_gross_weight_kg=30480.0,
        declared_vgm_kg=26500.0,
        terminal_scale_weight_kg=26700.0, # Lệch +200 kg (+0.75%), nằm trong dung sai 5%
        weighing_cert_verified=True,
    )
    res: ContainerVgmResult = ContainerVgmComplianceEngine.verify_vgm(inp)

    assert res.is_loading_permitted is True
    assert res.within_tolerance is True
    assert res.is_overweight is False
    assert res.weight_variance_kg == 200.0
    assert res.weight_variance_pct < 1.0
    assert len(res.rejection_reasons) == 0
    assert "ĐẠT CHUẨN VGM" in res.remarks
    assert len(res.audit_hash) == 16


def test_container_vgm_non_compliant_scenarios():
    """Phase 321: Test non-compliant VGM (Overweight, excessive variance, missing cert)."""
    # 1. Quá tải MGW
    overweight_inp = ContainerVgmInput(
        container_no="MAEU9988776",
        booking_no="BKG-SGN-2026-99",
        vgm_method=VgmMethod.METHOD_2,
        tare_weight_kg=4000.0,
        max_gross_weight_kg=30480.0,
        declared_vgm_kg=32000.0, # Vượt quá 30,480 kg
        terminal_scale_weight_kg=32100.0,
        weighing_cert_verified=True,
    )
    res_ow = ContainerVgmComplianceEngine.verify_vgm(overweight_inp)
    assert res_ow.is_loading_permitted is False
    assert res_ow.is_overweight is True
    assert any("vượt quá tải trọng thiết kế MGW" in r for r in res_ow.rejection_reasons)

    # 2. Sai số vượt dung sai 5% / 1000 kg
    discrepancy_inp = ContainerVgmInput(
        container_no="CMAU5544332",
        booking_no="BKG-HPH-2026-11",
        vgm_method=VgmMethod.METHOD_1,
        tare_weight_kg=3800.0,
        max_gross_weight_kg=30480.0,
        declared_vgm_kg=20000.0,
        terminal_scale_weight_kg=22500.0, # Lệch 2,500 kg (12.5%)
        weighing_cert_verified=True,
    )
    res_disc = ContainerVgmComplianceEngine.verify_vgm(discrepancy_inp)
    assert res_disc.is_loading_permitted is False
    assert res_disc.within_tolerance is False
    assert any("vượt ngưỡng dung sai" in r for r in res_disc.rejection_reasons)


def test_itc_hulls_actual_total_loss():
    """Phase 322: Test Actual Total Loss (ATL) 100% settlement with deductible waived."""
    inp = ItcHullsClaimInput(
        claim_id="HULL-ATL-2026",
        vessel_name="M/V VIET_OCEAN",
        agreed_insured_value_usd=5000000.0,
        repair_costs_usd=0.0,
        salvage_recovery_costs_usd=0.0,
        is_actual_total_loss=True,
        policy_deductible_usd=50000.0,
    )
    res: ItcHullsClaimResult = ItcHullsClaimEngine.calculate_claim_settlement(inp)

    assert res.loss_classification == HullLossType.ACTUAL_TOTAL_LOSS
    assert res.hull_insurer_payout_usd == 5000000.0
    assert res.deductible_applied_usd == 0.0
    assert "Actual Total Loss" in res.remarks


def test_itc_hulls_constructive_total_loss():
    """Phase 322: Test Constructive Total Loss (CTL) when repair + salvage >= insured value."""
    inp = ItcHullsClaimInput(
        claim_id="HULL-CTL-2026",
        vessel_name="M/V INDOCHINA",
        agreed_insured_value_usd=4000000.0,
        repair_costs_usd=2800000.0,
        salvage_recovery_costs_usd=1500000.0, # Tổng = 4.3M >= 4.0M
        is_actual_total_loss=False,
        policy_deductible_usd=30000.0,
    )
    res = ItcHullsClaimEngine.calculate_claim_settlement(inp)

    assert res.loss_classification == HullLossType.CONSTRUCTIVE_TOTAL_LOSS
    assert res.hull_insurer_payout_usd == 4000000.0
    assert res.deductible_applied_usd == 0.0
    assert "Constructive Total Loss" in res.remarks


def test_itc_hulls_particular_average_and_3_4_rdc():
    """Phase 322: Test Particular Average with Deductible and 3/4 RDC collision liability."""
    inp = ItcHullsClaimInput(
        claim_id="HULL-PA-RDC-2026",
        vessel_name="M/V MEKONG_VOYAGER",
        agreed_insured_value_usd=6000000.0,
        repair_costs_usd=400000.0,
        salvage_recovery_costs_usd=50000.0,
        third_party_collision_damage_usd=200000.0, # Đâm va gây hại cho tàu bạn
        policy_deductible_usd=35000.0,
        sue_and_labour_costs_usd=15000.0,
    )
    res = ItcHullsClaimEngine.calculate_claim_settlement(inp)

    assert res.loss_classification == HullLossType.COLLISION_LIABILITY_3_4
    assert res.deductible_applied_usd == 35000.0
    # Net repair = 400,000 - 35,000 = 365,000
    # 3/4 RDC Hull = 200,000 * 0.75 = 150,000
    # 1/4 RDC P&I = 200,000 * 0.25 = 50,000
    # Sue & Labour = 15,000
    # Total Hull insurer payout = 365k + 150k + 15k = 530,000
    assert res.rdc_hull_3_4_payout_usd == 150000.0
    assert res.rdc_pni_1_4_liability_usd == 50000.0
    assert res.sue_and_labour_payout_usd == 15000.0
    assert res.hull_insurer_payout_usd == 530000.0
    assert "3/4 RDC" in res.remarks
    assert isinstance(res.to_dict(), dict)
