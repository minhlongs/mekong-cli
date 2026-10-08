import pytest

from src.core.maritime_air_charter_towage_sts_engine import (
    # Phase 295
    FuelType,
    CiiRating,
    BunkerSulphurLog,
    VesselCiiAssessmentInput,
    MarpolAirCiiEngine,
    # Phase 296
    OffHireReason,
    TimeCharterOffHireInput,
    VoyageLaytimeStatement,
    CharterPartyFinancialEngine,
    # Phase 297
    TowageTugPower,
    TowageServiceInput,
    DrydockRepairItem,
    TowageDrydockTariffEngine,
    # Phase 298
    StsOperationType,
    LighterVesselAllocation,
    StsPermitRecord,
    CustomsStsManifestEngine,
)

# ------------------------------------------------------------------------------
# Phase 295: MARPOL Annex VI Air Emissions & CII Engine Tests
# ------------------------------------------------------------------------------

def test_bunker_sulphur_log_compliance():
    # ECA compliant (<= 0.10)
    log_eca_pass = BunkerSulphurLog(
        bunker_id="BDN-001",
        fuel_type=FuelType.LSMGO,
        sulphur_content_pct=0.08,
        is_in_eca=True,
        bunker_date="2026-10-08",
        port_name="Rotterdam",
        supplier_name="Shell Marine"
    )
    assert log_eca_pass.is_compliant() is True

    # ECA non-compliant (> 0.10)
    log_eca_fail = BunkerSulphurLog(
        bunker_id="BDN-002",
        fuel_type=FuelType.VLSFO,
        sulphur_content_pct=0.45,
        is_in_eca=True,
        bunker_date="2026-10-08",
        port_name="Antwerp",
        supplier_name="BP"
    )
    assert log_eca_fail.is_compliant() is False

    # Global compliant (<= 0.50)
    log_global_pass = BunkerSulphurLog(
        bunker_id="BDN-003",
        fuel_type=FuelType.VLSFO,
        sulphur_content_pct=0.48,
        is_in_eca=False,
        bunker_date="2026-10-09",
        port_name="Singapore",
        supplier_name="Equinor"
    )
    assert log_global_pass.is_compliant() is True

def test_cii_rating_evaluation():
    # Test ship with good fuel economy (Should get Rating A or B)
    input_good = VesselCiiAssessmentInput(
        vessel_name="MV MEKONG ECO",
        imo_number="9800001",
        dwt=50000.0,
        distance_traveled_nm=80000.0,
        fuel_consumption_mt={FuelType.VLSFO: 3000.0, FuelType.LNG: 1000.0},
        historical_ratings=[CiiRating.RATING_B, CiiRating.RATING_C]
    )
    res_good = MarpolAirCiiEngine.evaluate(input_good)
    assert res_good.rating in [CiiRating.RATING_A, CiiRating.RATING_B, CiiRating.RATING_C]
    assert res_good.requires_seemp_corrective_action_plan is False

    # Test ship with terrible rating E (Immediate SEEMP)
    input_bad = VesselCiiAssessmentInput(
        vessel_name="MV OLD SMOKER",
        imo_number="9700002",
        dwt=20000.0,
        distance_traveled_nm=20000.0,  # low distance
        fuel_consumption_mt={FuelType.HFO: 5000.0},  # high consumption
    )
    res_bad = MarpolAirCiiEngine.evaluate(input_bad)
    assert res_bad.rating == CiiRating.RATING_E
    assert res_bad.requires_seemp_corrective_action_plan is True

    # Test ship with 3 consecutive D ratings (requires SEEMP)
    input_d3 = VesselCiiAssessmentInput(
        vessel_name="MV BORDERLINE",
        imo_number="9700003",
        dwt=40000.0,
        distance_traveled_nm=50000.0,
        fuel_consumption_mt={FuelType.VLSFO: 6500.0},
        historical_ratings=[CiiRating.RATING_C, CiiRating.RATING_D, CiiRating.RATING_D]
    )
    res_d3 = MarpolAirCiiEngine.evaluate(input_d3)
    assert res_d3.requires_seemp_corrective_action_plan is True
    assert "3 năm liên tiếp" in res_d3.seemp_reason


# ------------------------------------------------------------------------------
# Phase 296: Charter Party (CP) Financials Engine Tests
# ------------------------------------------------------------------------------

def test_time_charter_off_hire():
    req = TimeCharterOffHireInput(
        charter_id="CP-2026-TC-001",
        vessel_name="MV MEKONG PRIDE",
        daily_hire_rate_usd=24000.0,  # $1,000/hour
        off_hire_hours=36.0,  # 1.5 days
        reason=OffHireReason.ENGINE_BREAKDOWN,
        bunker_consumed_mt=15.0,
        bunker_price_usd_per_mt=600.0,
        auxiliary_diesel_consumed_mt=3.0,
        diesel_price_usd_per_mt=900.0
    )
    res = CharterPartyFinancialEngine.calculate_off_hire(req)

    # 1.5 days * 24000 = $36000
    assert res.off_hire_days == 1.5
    assert res.hire_deduction_usd == 36_000.0
    # (15 * 600) + (3 * 900) = 9000 + 2700 = $11700
    assert res.bunker_deduction_usd == 11_700.0
    assert res.total_deduction_usd == 47_700.0
    assert res.reason == OffHireReason.ENGINE_BREAKDOWN

def test_voyage_laytime_demurrage():
    req = VoyageLaytimeStatement(
        charter_id="CP-2026-VC-002",
        vessel_name="MV MEKONG BULKER",
        allowed_laytime_hours=120.0,
        actual_time_used_hours=144.0,  # Over by 24 hours
        demurrage_rate_per_day_usd=12000.0,
        despatch_rate_ratio=0.5
    )
    res = CharterPartyFinancialEngine.calculate_demurrage(req)

    assert res.is_demurrage is True
    assert res.is_despatch is False
    assert res.time_difference_hours == 24.0
    assert res.demurrage_amount_usd == 12_000.0  # 1 full day
    assert res.net_financial_impact_usd == 12_000.0

def test_voyage_laytime_despatch():
    req = VoyageLaytimeStatement(
        charter_id="CP-2026-VC-003",
        vessel_name="MV MEKONG BULKER",
        allowed_laytime_hours=120.0,
        actual_time_used_hours=72.0,  # Saved 48 hours (2 days)
        demurrage_rate_per_day_usd=12000.0,
        despatch_rate_ratio=0.5
    )
    res = CharterPartyFinancialEngine.calculate_demurrage(req)

    assert res.is_demurrage is False
    assert res.is_despatch is True
    assert res.time_difference_hours == -48.0
    # Despatch rate is usually half of demurrage ($6,000/day). Saved 2 days = $12,000.
    assert res.despatch_amount_usd == 12_000.0
    assert res.net_financial_impact_usd == -12_000.0


# ------------------------------------------------------------------------------
# Phase 297: Towage Dues & Drydock Budget Variance Engine Tests
# ------------------------------------------------------------------------------

def test_towage_service_tariff():
    req = TowageServiceInput(
        vessel_name="MV EVERGREEN",
        vessel_gt=60000.0,
        tug_power=TowageTugPower.HP_3000_TO_3999,
        tug_quantity=2,
        operation_hours=2.5,
        is_international=True,
        is_holiday_or_night=True,  # 30% surcharge
    )
    res = TowageDrydockTariffEngine.calculate_towage(req)

    # 3000-3999 HP intl base rate is $420
    assert res.base_rate_per_tug_hour == 420.0
    assert res.surcharge_rate == 0.30

    # effective rate = 420 * 1.3 = 546
    # Total = 546 * 2 tugs * 2.5 hrs = 2730
    assert abs(res.total_towage_charge - 2730.0) < 0.01
    assert res.currency == "USD"

def test_drydock_variance_report():
    items = [
        DrydockRepairItem(category="Hull Blasting & Painting", budgeted_cost_usd=50000, actual_cost_usd=55000),
        DrydockRepairItem(category="Main Engine Overhaul", budgeted_cost_usd=120000, actual_cost_usd=110000),
        DrydockRepairItem(category="Propeller Polishing", budgeted_cost_usd=10000, actual_cost_usd=25000)
    ]
    res = TowageDrydockTariffEngine.evaluate_drydock_variance(
        vessel_name="MV MEKONG REPAIR",
        shipyard_name="Hyundai Vinashin",
        repair_items=items
    )

    assert res.total_budgeted_usd == 180_000.0
    assert res.total_actual_usd == 190_000.0
    assert res.variance_amount_usd == 10_000.0
    assert res.is_over_budget is True
    assert res.variance_percentage == (10000/180000 * 100)
    assert len(res.items_breakdown) == 3


# ------------------------------------------------------------------------------
# Phase 298: Customs STS Permit & Split Manifest Engine Tests
# ------------------------------------------------------------------------------

def test_split_manifest_balanced():
    permit = StsPermitRecord(
        permit_number="STS-HQ-2026-001",
        mother_vessel_name="MV MEKONG MOTHER",
        mother_imo="9100000",
        operation_type=StsOperationType.LIGHTERAGE_DISCHARGE,
        anchor_location_zone="Hon Gai STS Zone",
        total_cargo_weight_mt=35000.0,
        total_packages=0,
        valid_from="2026-10-08",
        valid_until="2026-10-15"
    )

    allocations = [
        LighterVesselAllocation("BARGE SG-01", "3WAA", 10000.0, 0, "HaiQuan_DongNai"),
        LighterVesselAllocation("BARGE SG-02", "3WAB", 15000.0, 0, "HaiQuan_BinhDuong"),
        LighterVesselAllocation("BARGE SG-03", "3WAC", 10000.0, 0, "HaiQuan_TPHCM"),
    ]

    res = CustomsStsManifestEngine.split_manifest(permit, allocations)

    assert res.total_mother_weight_mt == 35000.0
    assert res.total_transferred_weight_mt == 35000.0
    assert res.remaining_weight_on_mother_mt == 0.0
    assert res.is_balanced is True
    assert len(res.sub_manifests) == 3
    assert "hoàn tất" in res.discrepancy_remarks

def test_split_manifest_over_allocated():
    permit = StsPermitRecord(
        permit_number="STS-HQ-2026-002",
        mother_vessel_name="MV MEKONG MOTHER",
        mother_imo="9100000",
        operation_type=StsOperationType.LIGHTERAGE_DISCHARGE,
        anchor_location_zone="Go Gia STS Zone",
        total_cargo_weight_mt=20000.0,
        total_packages=0,
        valid_from="2026-10-08",
        valid_until="2026-10-15"
    )

    allocations = [
        LighterVesselAllocation("BARGE SG-04", "3WAD", 15000.0, 0, "HaiQuan_TPHCM"),
        LighterVesselAllocation("BARGE SG-05", "3WAE", 6000.0, 0, "HaiQuan_TPHCM"), # Total 21000 > 20000
    ]

    res = CustomsStsManifestEngine.split_manifest(permit, allocations)

    assert res.total_transferred_weight_mt == 21000.0
    assert res.remaining_weight_on_mother_mt == -1000.0
    assert res.is_balanced is False
    assert "CẢNH BÁO HẢI QUAN" in res.discrepancy_remarks
