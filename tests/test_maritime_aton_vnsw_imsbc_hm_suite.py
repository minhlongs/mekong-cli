"""Zero-Mock Test Suite for Maritime Safety Phases 331-334.

Covers:
- Phase 331: IALA Maritime Buoyage (Region A/B, Cardinal/Lateral, Message 21 AtoN Telemetry)
- Phase 332: Vietnam National Single Window (VNSW) & IMO FAL 1-7 Port Clearance Automation
- Phase 333: IMSBC Code Group B Solid Bulk Chemical Hazards & Hold Atmosphere Safety
- Phase 334: Hull & Machinery (H&M) Marine Casualty Damage Survey & Adjuster Apportionment
- Central Facade, Typer CLI Groups & Vietnamese Bilingual Aliases
"""

import json
from typer.testing import CliRunner

from src.core.maritime_aton_vnsw_imsbc_hm_engine import (
    AtoNTelemetryInput,
    IalaAtoNEngine,
    ImoFalDeclarationInput,
    VNSWClearanceEngine,
    ImsbcGroupBInput,
    ImsbcGroupBEngine,
    HmDamageSurveyInput,
    HmDamageSurveyEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()
app = build_app()


# ===========================================================================
# Phase 331: IALA Buoyage & AIS AtoN Telemetry Tests
# ===========================================================================

def test_iala_aton_region_a_port_normal():
    """Region A port hand mark: Red, nominal within tolerance."""
    inp = AtoNTelemetryInput(
        mmsi_aton="995741001",
        region="A",
        mark_type="LATERAL_PORT",
        aton_type="REAL",
        nominal_lat=10.7500,
        nominal_lon=106.7000,
        current_lat=10.7501,
        current_lon=106.7001,
        battery_voltage=12.8,
        lantern_active=True,
    )
    res = IalaAtoNEngine.evaluate(inp)
    assert res.expected_color == "RED"
    assert "Fl R" in res.expected_rhythm
    assert res.operational_status == "OPERATIONAL"
    assert res.is_off_position is False
    assert res.drift_distance_m < 50.0
    assert len(res.advisories) == 0


def test_iala_aton_region_b_port_and_starboard():
    """Region B port hand mark is Green, Starboard hand mark is Red."""
    port_inp = AtoNTelemetryInput(
        mmsi_aton="995741002",
        region="B",
        mark_type="LATERAL_PORT",
        aton_type="REAL",
        nominal_lat=21.0000,
        nominal_lon=108.0000,
        current_lat=21.0000,
        current_lon=108.0000,
    )
    port_res = IalaAtoNEngine.evaluate(port_inp)
    assert port_res.expected_color == "GREEN"

    stbd_inp = AtoNTelemetryInput(
        mmsi_aton="995741003",
        region="B",
        mark_type="LATERAL_STARBOARD",
        aton_type="REAL",
        nominal_lat=21.0000,
        nominal_lon=108.0000,
        current_lat=21.0000,
        current_lon=108.0000,
    )
    stbd_res = IalaAtoNEngine.evaluate(stbd_inp)
    assert stbd_res.expected_color == "RED"


def test_iala_aton_cardinal_and_special_marks():
    """Cardinal North mark and Isolated Danger mark definitions."""
    cardinal_inp = AtoNTelemetryInput(
        mmsi_aton="995741004",
        region="A",
        mark_type="CARDINAL_NORTH",
        aton_type="REAL",
        nominal_lat=10.0,
        nominal_lon=107.0,
        current_lat=10.0,
        current_lon=107.0,
    )
    cardinal_res = IalaAtoNEngine.evaluate(cardinal_inp)
    assert cardinal_res.expected_color == "BLACK & YELLOW HORIZONTAL BANDS"
    assert "VQ or Q" in cardinal_res.expected_rhythm

    danger_inp = AtoNTelemetryInput(
        mmsi_aton="995741005",
        region="A",
        mark_type="ISOLATED_DANGER",
        aton_type="VIRTUAL",
        nominal_lat=10.0,
        nominal_lon=107.0,
        current_lat=10.0,
        current_lon=107.0,
    )
    danger_res = IalaAtoNEngine.evaluate(danger_inp)
    assert "BLACK WITH HORIZONTAL RED BANDS" in danger_res.expected_color
    assert "Fl(2) White" in danger_res.expected_rhythm


def test_iala_aton_drift_and_battery_alarms():
    """Drift > 50m triggers off-position, low voltage and dark lantern raise advisories."""
    inp = AtoNTelemetryInput(
        mmsi_aton="995741006",
        region="A",
        mark_type="LATERAL_PORT",
        aton_type="REAL",
        nominal_lat=10.0000,
        nominal_lon=107.0000,
        current_lat=10.0010,  # ~111m drift
        current_lon=107.0000,
        battery_voltage=11.2,
        lantern_active=False,
    )
    res = IalaAtoNEngine.evaluate(inp)
    assert res.is_off_position is True
    assert res.drift_distance_m > 50.0
    assert res.operational_status == "CRITICAL_OFF_POSITION"
    assert res.is_battery_low is True
    assert res.is_lantern_fault is True
    assert any("drifted" in a.lower() for a in res.advisories)
    assert any("battery" in a.lower() for a in res.advisories)
    assert any("lantern" in a.lower() for a in res.advisories)


def test_iala_aton_haversine_accuracy():
    """Verify spherical distance calculation between coordinates."""
    dist = IalaAtoNEngine.haversine_distance_m(10.0000, 106.0000, 10.0000, 106.0000)
    assert dist == 0.0

    dist_1deg_lat = IalaAtoNEngine.haversine_distance_m(10.0, 106.0, 11.0, 106.0)
    assert 111000.0 < dist_1deg_lat < 112000.0


# ===========================================================================
# Phase 332: VNSW & IMO FAL 1-7 Port Clearance Tests
# ===========================================================================

def test_vnsw_clearance_all_approved():
    """Fully compliant vessel receives VNSW Port Clearance with SHA-256 hash."""
    inp = ImoFalDeclarationInput(
        imo_number="9876543",
        vessel_name="MV MEKONG TRANSPORTER",
        call_sign="3WFA1",
        port_of_call="VNSGN",
        voyage_number="VOY-2026-08",
        fal1_general_dec=True,
        fal2_cargo_dec=True,
        fal3_stores_dec=True,
        fal4_crew_effects=True,
        fal5_crew_list_count=22,
        fal6_passengers_count=0,
        fal7_dangerous_goods_manifest=False,
        customs_status="CLEARED",
        quarantine_sanitary_cleared=True,
        immigration_cleared=True,
        harbour_dues_paid=True,
    )
    res = VNSWClearanceEngine.evaluate(inp)
    assert res.clearance_granted is True
    assert res.clearance_id.startswith("VNSW-PC-VNSGN-9876543-VOY-2026-08")
    assert len(res.missing_requirements) == 0
    assert len(res.audit_hash) == 64


def test_vnsw_clearance_rejected_deficiencies():
    """Deficiencies in customs, quarantine, or missing declarations reject clearance."""
    inp = ImoFalDeclarationInput(
        imo_number="9876543",
        vessel_name="MV DEFICIENT",
        call_sign="3WFA2",
        port_of_call="VNCLI",
        voyage_number="VOY-2026-09",
        fal1_general_dec=False,
        fal2_cargo_dec=True,
        fal3_stores_dec=True,
        fal4_crew_effects=True,
        fal5_crew_list_count=0,
        fal6_passengers_count=0,
        fal7_dangerous_goods_manifest=False,
        customs_status="PENDING_INSPECTION",
        quarantine_sanitary_cleared=False,
        immigration_cleared=True,
        harbour_dues_paid=False,
    )
    res = VNSWClearanceEngine.evaluate(inp)
    assert res.clearance_granted is False
    assert any("FAL Form 1" in req for req in res.missing_requirements)
    assert any("FAL Form 5" in req for req in res.missing_requirements)
    assert any("Customs" in req for req in res.missing_requirements)
    assert any("quarantine" in req.lower() for req in res.missing_requirements)
    assert any("dues" in req.lower() for req in res.missing_requirements)


def test_vnsw_dangerous_goods_manifest_validation():
    """Dangerous goods onboard requires FAL 7 declaration."""
    inp_missing_fal7 = ImoFalDeclarationInput(
        imo_number="9123456",
        vessel_name="MT CHEMICAL",
        call_sign="3WCHEM",
        port_of_call="VNDAD",
        voyage_number="VOY-05",
        fal1_general_dec=True,
        fal2_cargo_dec=True,
        fal3_stores_dec=True,
        fal4_crew_effects=True,
        fal5_crew_list_count=18,
        fal6_passengers_count=0,
        fal7_dangerous_goods_manifest=False,
        has_dangerous_goods=True,
        customs_status="CLEARED",
        quarantine_sanitary_cleared=True,
        immigration_cleared=True,
        harbour_dues_paid=True,
    )
    res = VNSWClearanceEngine.evaluate(inp_missing_fal7)
    assert res.clearance_granted is False
    assert any("FAL Form 7" in req for req in res.missing_requirements)


# ===========================================================================
# Phase 333: IMSBC Code Group B Chemical Hazards Tests
# ===========================================================================

def test_imsbc_group_b_coal_safe_conditions():
    """Normal coal hold condition: normal temp, low CO, low CH4."""
    inp = ImsbcGroupBInput(
        cargo_name="COAL",
        hold_number=2,
        cargo_temp_celsius=36.0,
        previous_temp_celsius=35.5,
        o2_pct_vol=20.8,
        co_ppm=12.0,
        ch4_pct_lel=2.5,
        h2_pct_lel=0.0,
        ph3_ppm=0.0,
    )
    res = ImsbcGroupBEngine.evaluate(inp)
    assert res.cargo_safe_to_carry is True
    assert res.is_self_heating_alert is False
    assert res.is_explosive_gas_hazard is False
    assert res.is_toxic_hazard is False
    assert res.is_oxygen_depleted is False
    assert res.recommended_ventilation == "CONTINUOUS_SURFACE"


def test_imsbc_group_b_thermal_runaway_and_gas_hazards():
    """Thermal runaway (temp > 55°C, CO > 50 ppm) triggers SEAL_AND_INERT."""
    inp = ImsbcGroupBInput(
        cargo_name="COAL",
        hold_number=3,
        cargo_temp_celsius=58.0,
        previous_temp_celsius=55.0,  # Rise rate = 3.0°C/day > 2.0
        o2_pct_vol=18.0,             # Asphyxiation (< 19.5%)
        co_ppm=85.0,                 # Excessive CO (> 50 ppm)
        ch4_pct_lel=24.0,            # Flammable (> 20% LEL)
        h2_pct_lel=5.0,
        ph3_ppm=0.5,                 # Toxic PH3 (> 0.3 ppm)
    )
    res = ImsbcGroupBEngine.evaluate(inp)
    assert res.cargo_safe_to_carry is False
    assert res.is_self_heating_alert is True
    assert res.is_explosive_gas_hazard is True
    assert res.is_toxic_hazard is True
    assert res.is_oxygen_depleted is True
    assert res.recommended_ventilation == "SEAL_AND_INERT"
    assert len(res.hazards_detected) >= 4


def test_imsbc_group_b_inert_cargo_ventilation():
    """Inert cargo defaults to NO_VENTILATION unless heating occurs."""
    inp = ImsbcGroupBInput(
        cargo_name="IRON_ORE",
        hold_number=4,
        cargo_temp_celsius=28.0,
        previous_temp_celsius=28.0,
        o2_pct_vol=20.9,
        co_ppm=0.0,
        ch4_pct_lel=0.0,
        h2_pct_lel=0.0,
        ph3_ppm=0.0,
    )
    res = ImsbcGroupBEngine.evaluate(inp)
    assert res.recommended_ventilation == "NO_VENTILATION"
    assert res.cargo_safe_to_carry is True


# ===========================================================================
# Phase 334: Hull & Machinery Marine Casualty Survey Tests
# ===========================================================================

def test_hm_damage_survey_standard_claim():
    """Standard PA claim without depreciation."""
    inp = HmDamageSurveyInput(
        incident_id="INC-2026-01",
        vessel_name="MV INDOCHINA PROSPECT",
        insured_hull_value_usd=15000000.0,
        deductible_usd=100000.0,
        particular_average_repair_usd=400000.0,
        general_average_sacrifice_usd=50000.0,
        salvage_award_usd=25000.0,
        surveyor_fee_usd=10000.0,
        vessel_age_years=4,
        new_for_old_deduction_applicable=False,
    )
    res = HmDamageSurveyEngine.evaluate(inp)
    assert res.gross_adjusted_loss_usd == 485000.0
    assert res.new_for_old_depreciation_usd == 0.0
    assert res.applied_deductible_usd == 100000.0
    assert res.net_insurers_payable_usd == 385000.0
    assert res.is_constructive_total_loss is False
    assert len(res.audit_hash) == 64


def test_hm_damage_survey_new_for_old_sliding_scale():
    """New for Old depreciation tiers: 6-10y=15%, 11-15y=25%, >15y=33%."""
    inp_8y = HmDamageSurveyInput(
        incident_id="INC-2026-02",
        vessel_name="MV OLD TIMER",
        insured_hull_value_usd=10000000.0,
        deductible_usd=50000.0,
        particular_average_repair_usd=100000.0,
        general_average_sacrifice_usd=0.0,
        vessel_age_years=8,
        new_for_old_deduction_applicable=True,
    )
    res_8y = HmDamageSurveyEngine.evaluate(inp_8y)
    assert res_8y.new_for_old_depreciation_usd == 15000.0
    assert res_8y.net_insurers_payable_usd == 35000.0

    inp_14y = HmDamageSurveyInput(
        incident_id="INC-2026-03",
        vessel_name="MV OLD TIMER",
        insured_hull_value_usd=10000000.0,
        deductible_usd=0.0,
        particular_average_repair_usd=100000.0,
        general_average_sacrifice_usd=0.0,
        vessel_age_years=14,
        new_for_old_deduction_applicable=True,
    )
    res_14y = HmDamageSurveyEngine.evaluate(inp_14y)
    assert res_14y.new_for_old_depreciation_usd == 25000.0

    inp_20y = HmDamageSurveyInput(
        incident_id="INC-2026-04",
        vessel_name="MV VETERAN",
        insured_hull_value_usd=10000000.0,
        deductible_usd=0.0,
        particular_average_repair_usd=100000.0,
        general_average_sacrifice_usd=0.0,
        vessel_age_years=20,
        new_for_old_deduction_applicable=True,
    )
    res_20y = HmDamageSurveyEngine.evaluate(inp_20y)
    assert res_20y.new_for_old_depreciation_usd == 33000.0


def test_hm_damage_survey_constructive_total_loss():
    """Repair cost exceeding 80% insured value triggers CTL."""
    inp = HmDamageSurveyInput(
        incident_id="INC-2026-05",
        vessel_name="MV SHIPWRECK",
        insured_hull_value_usd=10000000.0,
        deductible_usd=100000.0,
        particular_average_repair_usd=8500000.0,
        general_average_sacrifice_usd=0.0,
    )
    res = HmDamageSurveyEngine.evaluate(inp)
    assert res.is_constructive_total_loss is True


# ===========================================================================
# CLI Execution & Vietnamese Alias Integration Tests
# ===========================================================================

def test_cli_aton_command_and_vietnamese_alias():
    """CLI execution for mekong aton eval and mekong phaotieu eval."""
    result = runner.invoke(
        app,
        [
            "aton", "eval",
            "--mmsi", "995741099",
            "--region", "A",
            "--mark-type", "LATERAL_PORT",
            "--aton-type", "REAL",
            "--nom-lat", "10.75",
            "--nom-lon", "106.70",
            "--cur-lat", "10.75",
            "--cur-lon", "106.70",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["mmsi_aton"] == "995741099"
    assert data["expected_color"] == "RED"

    # Vietnamese alias: phaotieu
    alias_res = runner.invoke(
        app,
        [
            "phaotieu", "eval",
            "--mmsi", "995741099",
            "--nom-lat", "10.75",
            "--nom-lon", "106.70",
            "--cur-lat", "10.75",
            "--cur-lon", "106.70",
        ],
    )
    assert alias_res.exit_code == 0


def test_cli_vnsw_command_and_vietnamese_alias():
    """CLI execution for mekong vnsw clearance and mekong motcua clearance."""
    result = runner.invoke(
        app,
        [
            "vnsw", "clearance",
            "--imo", "9999999",
            "--name", "MV PACIFIC VOYAGER",
            "--port", "VNSGN",
            "--voyage", "V-01",
            "--crew-count", "25",
            "--customs", "CLEARED",
            "--quarantine",
            "--immigration",
            "--dues",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["clearance_granted"] is True

    # Vietnamese alias: motcua
    alias_res = runner.invoke(
        app,
        [
            "motcua", "clearance",
            "--imo", "9999999",
            "--name", "MV PACIFIC VOYAGER",
            "--customs", "CLEARED",
        ],
    )
    assert alias_res.exit_code == 0


def test_cli_imsbc_command_and_vietnamese_alias():
    """CLI execution for mekong imsbc assess and mekong hangnguyhiem assess."""
    result = runner.invoke(
        app,
        [
            "imsbc", "assess",
            "--cargo", "COAL",
            "--hold", "1",
            "--temp", "38.0",
            "--prev-temp", "37.5",
            "--o2", "20.5",
            "--co", "10.0",
            "--ch4-lel", "1.0",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["cargo_safe_to_carry"] is True

    # Vietnamese alias: hangnguyhiem
    alias_res = runner.invoke(
        app,
        [
            "hangnguyhiem", "assess",
            "--cargo", "COAL",
        ],
    )
    assert alias_res.exit_code == 0


def test_cli_hm_command_and_vietnamese_alias():
    """CLI execution for mekong hmsurvey survey and mekong giamdinhtau survey."""
    result = runner.invoke(
        app,
        [
            "hmsurvey", "survey",
            "--incident", "INC-TEST-01",
            "--vessel", "MV VISHIP",
            "--hull-value", "5000000",
            "--deductible", "50000",
            "--pa-cost", "200000",
            "--surveyor-fee", "0",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["net_insurers_payable_usd"] == 150000.0

    # Vietnamese alias: giamdinhtau
    alias_res = runner.invoke(
        app,
        [
            "giamdinhtau", "survey",
            "--incident", "INC-TEST-01",
            "--vessel", "MV VISHIP",
            "--hull-value", "5000000",
            "--deductible", "50000",
            "--pa-cost", "200000",
            "--surveyor-fee", "0",
        ],
    )
    assert alias_res.exit_code == 0
