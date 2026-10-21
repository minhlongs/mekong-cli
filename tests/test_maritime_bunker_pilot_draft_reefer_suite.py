import pytest

from src.core.maritime_bunker_pilot_draft_reefer_engine import (
    BunkerDisputeInput, BunkerMfmDisputeEngine,
    HourlyTide, PilotageWindowInput, PilotageTidalWindowEngine,
    DraftMarks, DraftSurveyInput, DraftSurveyEngine,
    ReeferCargoType, ReeferTempLog, ReeferClaimInput, ReeferClaimEngine
)


# ------------------------------------------------------------------------------
# Phase 311: Bunker MFM Dispute Tests
# ------------------------------------------------------------------------------

def test_bunker_dispute_within_tolerance():
    inp = BunkerDisputeInput(
        bunker_delivery_note_no="BDN-2026-SG-001",
        vessel_name="MV MEKONG PRIDE",
        barge_name="SAIGON BARGE 02",
        fuel_grade="VLSFO 0.5%",
        mfm_delivered_mt=500.0,
        vessel_received_mt=498.5,  # Diff = 1.5 MT (0.3% <= 0.5%)
        bdn_density_kg_m3=985.0,
        ship_measured_density_kg_m3=984.5
    )
    res = BunkerMfmDisputeEngine.evaluate_discrepancy(inp)
    assert res.is_disputed is False
    assert res.dispute_level == "NORMAL"
    assert res.notice_of_protest_required is False
    assert res.cappuccino_suspected is False
    assert res.discrepancy_pct < 0.5


def test_bunker_dispute_cappuccino_protest():
    inp = BunkerDisputeInput(
        bunker_delivery_note_no="BDN-2026-SG-002",
        vessel_name="MV OCEAN VOYAGER",
        barge_name="VUNG TAU BARGE 05",
        fuel_grade="VLSFO 0.5%",
        mfm_delivered_mt=1000.0,
        vessel_received_mt=982.0,  # Diff = 18 MT (1.8% > 1.0%)
        bdn_density_kg_m3=990.0,
        ship_measured_density_kg_m3=984.0  # Drop = 6.0 kg/m3 (>= 3.0 kg/m3) -> Cappuccino
    )
    res = BunkerMfmDisputeEngine.evaluate_discrepancy(inp)
    assert res.is_disputed is True
    assert res.dispute_level == "FORMAL_PROTEST"
    assert res.notice_of_protest_required is True
    assert res.cappuccino_suspected is True
    assert "CẢNH BÁO BỌT KHÍ" in res.remarks


# ------------------------------------------------------------------------------
# Phase 312: Pilotage & Tidal Window Tests
# ------------------------------------------------------------------------------

def test_pilotage_tidal_window_success():
    tides = [
        HourlyTide(hour=h, tide_height_m=3.5 if 10 <= h <= 16 else 1.2)
        for h in range(24)
    ]
    # Static draft = 10.0m, Datum = 8.5m, Speed = 10 kts -> Squat = 0.5m, UKC = 1.0m
    # Depth needed = 10.0 + 0.5 + 1.0 = 11.5m
    # Available at high tide = 8.5 + 3.5 = 12.0m (>= 11.5m -> Eligible)
    # Available at low tide = 8.5 + 1.2 = 9.7m (< 11.5m)
    inp = PilotageWindowInput(
        vessel_name="MV MEKONG PHOENIX",
        grt=35000.0,
        static_draft_m=10.0,
        channel_depth_datum_m=8.5,
        speed_knots=10.0,
        transit_duration_hours=2,
        channel_distance_nm=25.0,
        hourly_tides=tides
    )
    res = PilotageTidalWindowEngine.evaluate_clearance_and_booking(inp)
    assert res.is_clearance_granted is True
    assert res.min_water_depth_needed_m == 11.5
    assert 10 in res.eligible_transit_hours
    assert 11 in res.eligible_transit_hours
    assert 2 not in res.eligible_transit_hours
    assert res.estimated_pilot_dues_vnd > 3_000_000.0


def test_pilotage_tidal_window_rejected_shallow():
    tides = [HourlyTide(hour=h, tide_height_m=1.0) for h in range(24)]
    inp = PilotageWindowInput(
        vessel_name="MV DEEP DRAFT",
        grt=50000.0,
        static_draft_m=13.0,
        channel_depth_datum_m=9.0,
        hourly_tides=tides
    )
    res = PilotageTidalWindowEngine.evaluate_clearance_and_booking(inp)
    assert res.is_clearance_granted is False
    assert len(res.eligible_transit_hours) == 0
    assert "TỪ CHỐI QUA LUỒNG" in res.remarks


# ------------------------------------------------------------------------------
# Phase 313: Draft Survey Calculation Tests
# ------------------------------------------------------------------------------

def test_draft_survey_displacement_calculation():
    marks = DraftMarks(
        fwd_port=8.10, fwd_stbd=8.14,  # Fwd mean = 8.12
        mid_port=8.50, mid_stbd=8.52,  # Mid mean = 8.51
        aft_port=8.90, aft_stbd=8.94   # Aft mean = 8.92
    )
    # D_QM = (8.12 + 6 * 8.51 + 8.92) / 8 = (8.12 + 51.06 + 8.92) / 8 = 68.10 / 8 = 8.5125 m
    # Apparent trim = 8.92 - 8.12 = +0.80 m
    # LCF = 2.5 m, TPC = 45.0, LBP = 180.0 m
    # First Trim Corr = (0.80 * 2.5 * 45.0 * 100) / 180.0 = 9000 / 180 = 50.0 MT
    # Table Disp = 30,000 MT -> Trim Corr Disp = 30,050 MT
    # Measured density = 1.020 t/m3 -> Density Corr Disp = 30,050 * (1.020 / 1.025) = 29,903.41 MT
    # Deductible weights = 4,500 MT -> Net Disp = 25,403.41 MT
    inp = DraftSurveyInput(
        survey_id="DS-2026-HCM-01",
        vessel_name="MV BULK PHOENIX",
        draft_marks=marks,
        table_displacement_mt=30000.0,
        tpc=45.0,
        lcf_m=2.5,
        lbp_m=180.0,
        measured_water_density=1.020,
        deductible_weights_mt=4500.0
    )
    res = DraftSurveyEngine.calculate_draft_survey(inp)
    assert abs(res.quarter_mean_draft_m - 8.5125) < 0.001
    assert abs(res.apparent_trim_m - 0.80) < 0.001
    assert abs(res.first_trim_correction_mt - 50.0) < 0.01
    assert abs(res.density_corrected_disp_mt - 29903.41) < 1.0
    assert abs(res.net_displacement_mt - 25403.41) < 1.0


# ------------------------------------------------------------------------------
# Phase 314: Reefer Claim Tests
# ------------------------------------------------------------------------------

def test_reefer_claim_terminal_liability():
    # Frozen Seafood target -20°C (tolerance +2°C -> upper limit -18°C)
    logs = [
        ReeferTempLog(0, -20.0, "GATE_IN"),
        ReeferTempLog(1, -12.0, "YARD_STACK"),  # Excursion +6°C
        ReeferTempLog(2, -10.0, "YARD_STACK"),  # Excursion +8°C
        ReeferTempLog(3, -11.0, "YARD_STACK"),  # Excursion +7°C
        ReeferTempLog(4, -13.0, "YARD_STACK"),  # Excursion +5°C
        ReeferTempLog(5, -19.5, "VESSEL_VOYAGE")
    ]
    inp = ReeferClaimInput(
        container_no="TEMU9876543",
        cargo_type=ReeferCargoType.FROZEN_SEAFOOD,
        set_point_c=-20.0,
        tolerance_c=2.0,
        temp_logs=logs,
        cargo_invoice_value_usd=80000.0
    )
    res = ReeferClaimEngine.analyze_claim(inp)
    assert res.is_claim_valid is True
    assert res.liable_party == "TERMINAL"
    assert res.excursion_hours == 4
    assert res.accumulated_degree_hours == 26.0
    assert res.recommended_compensation_usd > 0.0


def test_reefer_claim_warm_stuffing_shipper_liability():
    logs = [
        ReeferTempLog(0, -5.0, "GATE_IN"),  # Set-point -18°C + 2°C = -16°C. Actual -5°C (Warm stuffing!)
        ReeferTempLog(1, -6.0, "YARD_STACK"),
        ReeferTempLog(2, -8.0, "YARD_STACK"),
        ReeferTempLog(3, -10.0, "VESSEL_VOYAGE")
    ]
    inp = ReeferClaimInput(
        container_no="TEMU1122334",
        cargo_type=ReeferCargoType.FROZEN_MEAT,
        set_point_c=-18.0,
        tolerance_c=2.0,
        temp_logs=logs,
        cargo_invoice_value_usd=65000.0
    )
    res = ReeferClaimEngine.analyze_claim(inp)
    assert res.is_claim_valid is True
    assert res.liable_party == "SHIPPER"
    assert "Warm Stuffing" in res.remarks
