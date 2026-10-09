"""Unit tests for Maritime Phases 343-346 Micro-Engines.

Tests:
- EcdisPassagePlanningEngine (IMO Res. A.893(21), CATZOC, Squat, Safety Contour)
- BunkeringMfmEngine (SS 648:2019, MPE, Drive Gain cappuccino alert, MARPOL sulfur)
- BoilerWaterTreatmentEngine (BS 2486, pH, chloride, blowdown rate)
- PortAgencyDisbursementEngine (FONASBA, PDA/FDA reconciliation, balance settlement)
Strictly adheres to zero-mock and kept under 200 lines.
"""

from src.core.maritime_ecdis_mfm_boiler_agency_engine import (
    BoilerWaterInput,
    BoilerWaterTreatmentEngine,
    BunkeringMfmEngine,
    BunkeringMfmInput,
    EcdisPassagePlanningEngine,
    PassageLegInput,
    PortAgencyDisbursementEngine,
    PortAgencyDisbursementInput,
)


def test_ecdis_safe_passage_narrow():
    inp = PassageLegInput(
        leg_name="LEG-01",
        planned_speed_knots=10.0,
        static_draft_m=8.0,
        block_coefficient_cb=0.8,
        ukc_policy_m=1.0,
        height_of_tide_m=2.0,
        catzoc_category="A1",
        channel_depth_charted_m=12.0,
        channel_type="NARROW",
    )
    res = EcdisPassagePlanningEngine.evaluate(inp)
    assert res.squat_m == 1.6  # (0.8 * 100) / 50 = 1.6
    assert res.catzoc_allowance_m == 0.62  # 0.5 + 0.01 * 12
    assert res.safety_depth_m == round(8.0 + 1.6 + 1.0 + 0.62 - 2.0, 2)
    assert res.safety_contour_m == 10.0  # 9.22 <= 10.0
    assert res.cross_track_limit_m == 50.0
    assert res.is_safe_transit is True


def test_ecdis_shallow_water_grounding_risk():
    inp = PassageLegInput(
        leg_name="LEG-GROUNDING",
        planned_speed_knots=14.0,
        static_draft_m=10.5,
        block_coefficient_cb=0.85,
        ukc_policy_m=1.5,
        height_of_tide_m=0.5,
        catzoc_category="C",
        channel_depth_charted_m=10.0,
        channel_type="APPROACH",
    )
    res = EcdisPassagePlanningEngine.evaluate(inp)
    assert res.is_safe_transit is False
    assert any("GROUNDING RISK" in adv for adv in res.advisories)
    assert res.cross_track_limit_m == 100.0


def test_mfm_bunkering_accepted():
    inp = BunkeringMfmInput(
        bunker_id="BNK-OK",
        mfm_totalizer_mass_mt=500.0,
        vessel_sounding_mass_mt=498.5,
        average_drive_gain_pct=42.0,
        density_fluctuation_pct=0.3,
        sulfur_content_pct=0.45,
        is_eca_zone=False,
    )
    res = BunkeringMfmEngine.evaluate(inp)
    assert res.is_mpe_compliant is True
    assert res.cappuccino_effect_detected is False
    assert res.sulfur_compliant is True
    assert res.bunker_status == "ACCEPTED"
    assert res.notice_of_protest_required is False


def test_mfm_bunkering_cappuccino_and_dispute():
    inp = BunkeringMfmInput(
        bunker_id="BNK-AERATED",
        mfm_totalizer_mass_mt=600.0,
        vessel_sounding_mass_mt=580.0,  # 20 MT diff = 3.33% > 0.5%
        average_drive_gain_pct=88.5,  # > 80%
        density_fluctuation_pct=2.4,  # > 2%
        sulfur_content_pct=0.49,
        is_eca_zone=False,
    )
    res = BunkeringMfmEngine.evaluate(inp)
    assert res.is_mpe_compliant is False
    assert res.cappuccino_effect_detected is True
    assert res.bunker_status == "DISPUTED"
    assert res.notice_of_protest_required is True
    assert any("CAPPUCCINO EFFECT ALERT" in adv for adv in res.advisories)


def test_mfm_bunkering_eca_sulfur_violation():
    inp = BunkeringMfmInput(
        bunker_id="BNK-ECA-FAIL",
        mfm_totalizer_mass_mt=300.0,
        vessel_sounding_mass_mt=300.0,
        average_drive_gain_pct=30.0,
        density_fluctuation_pct=0.2,
        sulfur_content_pct=0.35,  # ECA limit is 0.10%
        is_eca_zone=True,
    )
    res = BunkeringMfmEngine.evaluate(inp)
    assert res.sulfur_compliant is False
    assert res.bunker_status == "REJECTED"
    assert any("MARPOL ANNEX VI VIOLATION" in adv for adv in res.advisories)


def test_boiler_water_optimal():
    inp = BoilerWaterInput(
        boiler_id="BLR-01",
        boiler_type="AUXILIARY",
        water_ph=10.4,
        chloride_ppm=80.0,
        p_alkalinity_ppm=180.0,
        phosphate_ppm=35.0,
        hydrazine_ppm=0.15,
        feedwater_chloride_ppm=4.0,
    )
    res = BoilerWaterTreatmentEngine.evaluate(inp)
    assert res.ph_compliant is True
    assert res.chloride_compliant is True
    assert res.overall_status == "OPTIMAL"
    assert res.recommended_blowdown_pct > 0.0


def test_boiler_water_critical_chloride_and_acid():
    inp = BoilerWaterInput(
        boiler_id="BLR-CRIT",
        boiler_type="AUXILIARY",
        water_ph=8.8,  # Acidic < 9.0
        chloride_ppm=350.0,  # > 300 ppm
        p_alkalinity_ppm=80.0,
        phosphate_ppm=10.0,
        hydrazine_ppm=0.01,
        feedwater_chloride_ppm=15.0,
    )
    res = BoilerWaterTreatmentEngine.evaluate(inp)
    assert res.ph_compliant is False
    assert res.chloride_compliant is False
    assert res.overall_status == "CRITICAL_ACTION_REQUIRED"
    assert any("Dose alkaline booster" in act for act in res.chemical_actions)
    assert any("CHLORIDE CORROSION ALERT" in adv for adv in res.advisories)


def test_port_agency_reconciliation_surplus():
    inp = PortAgencyDisbursementInput(
        call_id="CALL-01",
        vessel_name="MV PACIFIC",
        advance_received_usd=40000.0,
        tonnage_dues_usd=4000.0,
        pilotage_dues_usd=5000.0,
        towage_dues_usd=8000.0,
        berthage_dues_usd=3000.0,
        linesmen_and_mooring_usd=1000.0,
        garbage_freshwater_usd=1000.0,
        agency_fee_usd=3000.0,
        proforma_total_usd=25000.0,
    )
    # Total actual = 22000 + 3000 = 25000.
    # Advance = 40000. Diff = +15000 refund
    res = PortAgencyDisbursementEngine.evaluate(inp)
    assert res.actual_port_costs_usd == 22000.0
    assert res.total_fda_amount_usd == 25000.0
    assert res.balance_amount_usd == 15000.0
    assert res.settlement_status == "REFUND_TO_PRINCIPAL"
    assert res.variance_from_pda_pct == 0.0
    assert res.audit_flag is False


def test_port_agency_reconciliation_deficit_and_audit():
    inp = PortAgencyDisbursementInput(
        call_id="CALL-02",
        vessel_name="MV MEKONG",
        advance_received_usd=20000.0,
        tonnage_dues_usd=5000.0,
        pilotage_dues_usd=6000.0,
        towage_dues_usd=10000.0,
        berthage_dues_usd=4000.0,
        linesmen_and_mooring_usd=1500.0,
        garbage_freshwater_usd=1500.0,
        agency_fee_usd=3500.0,
        proforma_total_usd=28000.0,
    )
    # Total costs = 28000 + 3500 = 31500.
    # Variance = (31500 - 28000)/28000 = +12.5% (> 5%)
    res = PortAgencyDisbursementEngine.evaluate(inp)
    assert res.total_fda_amount_usd == 31500.0
    assert res.balance_amount_usd == 11500.0
    assert res.settlement_status == "DUE_FROM_PRINCIPAL"
    assert res.variance_from_pda_pct == 12.5
    assert res.audit_flag is True
    assert any("BUDGET VARIANCE WARNING" in adv for adv in res.advisories)
