"""Unit tests for Maritime PSC, Bulk Cargo, BWE & Vessel Arrest Suite.

Phases 315-318 zero-mock deterministic tests.
"""


from src.core.maritime_psc_bulk_bwe_arrest_engine import (
    FlagPerformance, RoPerformance, ShipRiskProfile, PscPriority,
    PscTargetingInput, PscTargetingEngine,
    ImsbcCargoGroup, BulkCargoInput, BulkCargoLiquefactionEngine,
    BwmStandard, BallastWaterInput, BallastWaterComplianceEngine,
    MaritimeClaimRank, MaritimeClaimItem, VesselArrestWaterfallEngine
)


# ==============================================================================
# Phase 315: Tokyo MoU PSC Targeting Tests
# ==============================================================================

def test_psc_targeting_low_risk_ship():
    inp = PscTargetingInput(
        imo_number="IMO9876543",
        vessel_name="MV MEKONG GREEN",
        flag="Panama",
        flag_performance=FlagPerformance.WHITE,
        recognized_org_performance=RoPerformance.HIGH,
        vessel_age_years=5,
        is_high_risk_ship_type=False,
        deficiencies_last_36m=2,
        detentions_last_36m=0,
        months_since_last_psc=6,
        critical_deficiency_present=False
    )
    res = PscTargetingEngine.evaluate_targeting(inp)
    assert res.ship_risk_profile == ShipRiskProfile.LRS
    assert res.risk_score_points <= 1
    assert res.priority_level == PscPriority.PRIORITY_III
    assert res.grounds_for_detention is False
    assert "9-18 months" in res.eligible_inspection_window


def test_psc_targeting_high_risk_ship_overdue():
    inp = PscTargetingInput(
        imo_number="IMO9123456",
        vessel_name="MV AGING TRADER",
        flag="Togo",
        flag_performance=FlagPerformance.BLACK,
        recognized_org_performance=RoPerformance.LOW,
        vessel_age_years=24,
        is_high_risk_ship_type=True,  # Chemical / Bulk
        deficiencies_last_36m=18,
        detentions_last_36m=2,
        months_since_last_psc=5,      # Window is 2-4 months -> 5 is overdue
        critical_deficiency_present=True
    )
    res = PscTargetingEngine.evaluate_targeting(inp)
    assert res.ship_risk_profile == ShipRiskProfile.HRS
    assert res.risk_score_points >= 6
    assert res.priority_level == PscPriority.PRIORITY_I
    assert res.grounds_for_detention is True
    assert "CẢNH BÁO" in res.remarks


# ==============================================================================
# Phase 316: IMSBC Solid Bulk Cargo Safety Tests
# ==============================================================================

def test_bulk_cargo_safe_within_tml():
    # Nickel ore (Group A). FMP = 35.0% -> TML = 31.5%. Actual MC = 28.5% <= 31.5%
    inp = BulkCargoInput(
        cargo_name="Indonesian Nickel Ore",
        cargo_group=ImsbcCargoGroup.GROUP_A,
        total_metric_tons=45000.0,
        flow_moisture_point_pct=35.0,
        actual_moisture_content_pct=28.5,
        certificate_age_days=3
    )
    res = BulkCargoLiquefactionEngine.evaluate_cargo_safety(inp)
    assert res.is_safe_to_load is True
    assert res.carriage_prohibited is False
    assert res.tml_pct == 31.5
    assert res.moisture_excess_pct == 0.0


def test_bulk_cargo_dangerous_exceeding_tml():
    # Iron ore fines (Group A). FMP = 12.0% -> TML = 10.8%. Actual MC = 11.5% > 10.8%
    inp = BulkCargoInput(
        cargo_name="Iron Ore Fines",
        cargo_group=ImsbcCargoGroup.GROUP_A,
        total_metric_tons=60000.0,
        flow_moisture_point_pct=12.0,
        actual_moisture_content_pct=11.5,
        certificate_age_days=2
    )
    res = BulkCargoLiquefactionEngine.evaluate_cargo_safety(inp)
    assert res.is_safe_to_load is False
    assert res.carriage_prohibited is True
    assert res.moisture_excess_pct > 0.0
    assert "CẤM XẾP HÀNG" in res.remarks


def test_bulk_cargo_group_c_non_hazardous():
    inp = BulkCargoInput(
        cargo_name="Crushed Granite Aggregates",
        cargo_group=ImsbcCargoGroup.GROUP_C,
        total_metric_tons=30000.0,
        flow_moisture_point_pct=0.0,
        actual_moisture_content_pct=2.0
    )
    res = BulkCargoLiquefactionEngine.evaluate_cargo_safety(inp)
    assert res.is_safe_to_load is True
    assert res.carriage_prohibited is False
    assert "Không có rủi ro hóa lỏng" in res.remarks


# ==============================================================================
# Phase 317: Ballast Water Management D-1 vs D-2 Tests
# ==============================================================================

def test_bwe_d1_exchange_compliant():
    # 3x volume pumped, 250 NM offshore, 800m depth -> Fully compliant
    inp = BallastWaterInput(
        vessel_name="MV MEKONG CHALLENGER",
        standard_applied=BwmStandard.D1_EXCHANGE,
        tank_capacity_m3=5000.0,
        pumped_volume_m3=15000.0,  # 3x volume
        distance_from_land_nm=250.0,
        water_depth_m=800.0
    )
    res = BallastWaterComplianceEngine.evaluate_compliance(inp)
    assert res.is_discharge_permitted is True
    assert res.exchange_efficiency_pct == 100.0
    assert res.distance_compliant is True
    assert res.depth_compliant is True
    assert "ĐẠT CHUẨN D-1" in res.remarks


def test_bwe_d1_exchange_violation_shallow_coastal():
    # Only 30 NM offshore (< 50 NM min) and 80m depth (< 200m)
    inp = BallastWaterInput(
        vessel_name="MV MEKONG CHALLENGER",
        standard_applied=BwmStandard.D1_EXCHANGE,
        tank_capacity_m3=5000.0,
        pumped_volume_m3=10000.0,
        distance_from_land_nm=30.0,
        water_depth_m=80.0
    )
    res = BallastWaterComplianceEngine.evaluate_compliance(inp)
    assert res.is_discharge_permitted is False
    assert res.distance_compliant is False
    assert res.depth_compliant is False
    assert "CẤM XẢ NƯỚC DẰN" in res.remarks


def test_bwe_d2_bwms_treatment_operational():
    inp = BallastWaterInput(
        vessel_name="MV PACIFIC STAR",
        standard_applied=BwmStandard.D2_TREATMENT,
        tank_capacity_m3=6000.0,
        pumped_volume_m3=6000.0,
        distance_from_land_nm=12.0,  # In port / territorial waters
        water_depth_m=18.0,
        bwms_operational=True,
        active_substance_tro_ppm=0.4
    )
    res = BallastWaterComplianceEngine.evaluate_compliance(inp)
    assert res.is_discharge_permitted is True
    assert "ĐẠT CHUẨN D-2" in res.remarks


# ==============================================================================
# Phase 318: Maritime Lien & Vessel Arrest Waterfall Tests
# ==============================================================================

def test_vessel_arrest_waterfall_settlement():
    # Auction proceeds: 50,000,000,000 VND
    # Rank 0 (Court costs): 2,000,000,000 VND -> Paid 100%
    # Rank 1 (Crew wages): 5,000,000,000 VND -> Paid 100%
    # Rank 4 (Port dues): 3,000,000,000 VND -> Paid 100%
    # Rank 6 (Mortgage): 60,000,000,000 VND -> Remainder 40B VND -> Paid ~66.67%
    # Rank 7 (Unsecured bunker): 10,000,000,000 VND -> Paid 0%
    claims = [
        MaritimeClaimItem("CLM-001", "Tòa án Nhân dân TP. Hải Phòng", MaritimeClaimRank.RANK_0_COURT_CUSTODY, 2_000_000_000.0),
        MaritimeClaimItem("CLM-002", "Tập thể 18 Thuyền viên", MaritimeClaimRank.RANK_1_CREW_WAGES, 5_000_000_000.0),
        MaritimeClaimItem("CLM-003", "Cảng vụ Hàng hải Hải Phòng", MaritimeClaimRank.RANK_4_PORT_DUES, 3_000_000_000.0),
        MaritimeClaimItem("CLM-004", "Ngân hàng Ngoại thương Vietcombank", MaritimeClaimRank.RANK_6_MORTGAGE, 60_000_000_000.0),
        MaritimeClaimItem("CLM-005", "Đại lý cấp nhiên liệu Petrolimex", MaritimeClaimRank.RANK_7_UNSECURED, 10_000_000_000.0),
    ]
    res = VesselArrestWaterfallEngine.calculate_waterfall(
        vessel_name="MV OCEAN PHOENIX",
        auction_proceeds_vnd=50_000_000_000.0,
        claims=claims
    )
    assert res.total_auction_proceeds_vnd == 50_000_000_000.0
    assert res.total_payout_vnd == 50_000_000_000.0
    assert res.remaining_balance_vnd == 0.0

    # Verify rank recoveries
    s_map = {s.claim_id: s for s in res.settlements}
    assert s_map["CLM-001"].recovery_rate_pct == 100.0
    assert s_map["CLM-002"].recovery_rate_pct == 100.0
    assert s_map["CLM-003"].recovery_rate_pct == 100.0
    assert abs(s_map["CLM-004"].paid_amount_vnd - 40_000_000_000.0) < 1.0
    assert abs(s_map["CLM-004"].recovery_rate_pct - 66.67) < 0.1
    assert s_map["CLM-005"].paid_amount_vnd == 0.0
    assert s_map["CLM-005"].recovery_rate_pct == 0.0
