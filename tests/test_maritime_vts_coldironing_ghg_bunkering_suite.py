"""Comprehensive Test Suite for Seaport VTS, Cold Ironing, Green Port GHG MRV & Marine Bunkering Suite (Phases 239-242).

Statutory & Standard References:
- Phase 239: Vietnam Maritime Code 2015 Arts. 104-111, Decree 58/2017/NĐ-CP & Circular 39/2023/TT-BGTVT (VTS, Fairway Speed, CPA/TCPA, Tariffs).
- Phase 240: Decision 876/QĐ-TTg, IEC/IEEE 80005-1 & Law on Environmental Protection 2020 Art. 136 (OPS Cold Ironing, SFC Losses, Emissions Abatement).
- Phase 241: MARPOL Annex VI Regs. 26-28, MEPC.352(78)-355(78), Decision 01/2022/QĐ-TTg & Circular 17/2022/TT-BTNMT (IMO CII A-E, SEEMP CAP, Green Port Discounts).
- Phase 242: MARPOL Annex VI Regs. 14 & 18, Decree 58/2017/NĐ-CP Arts. 100-104, QCVN 09:2019/BKHCN & ASTM 54B/54D (BDN Sulphur Cap, ESD Shutoff, ASTM VCF).
"""

import ast
import json
from pathlib import Path

from typer.testing import CliRunner

from src.cli.commands.maritime_vts_coldironing_ghg_bunkering_command import (
    coldironing_app,
    greenportghg_app,
    marinebunkering_app,
    vtsreporting_app,
)
from src.core.maritime_vts_coldironing_ghg_bunkering_engine import (
    BunkerGrade,
    CiiRatingGrade,
    CiiShipType,
    CollisionRiskLevel,
    ColdIroningEngine,
    GreenPortGhgCiiEngine,
    MarineBunkeringSafetyEngine,
    VesselTrafficServiceEngine,
    VtsReportingStatus,
)

runner = CliRunner()


def test_ast_zero_external_dependency_invariant() -> None:
    """Verify that the core maritime engine module maintains zero external dependencies."""
    engine_path = Path("src/core/maritime_vts_coldironing_ghg_bunkering_engine.py")
    assert engine_path.exists(), "Engine file must exist"

    tree = ast.parse(engine_path.read_text(encoding="utf-8"))
    allowed_standard_modules = {
        "dataclasses",
        "enum",
        "math",
        "typing",
        "hashlib",
        "datetime",
        "json",
        "re",
        "sys",
        "os",
        "pathlib",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                assert root_pkg in allowed_standard_modules, f"Disallowed import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_standard_modules, f"Disallowed from-import: {node.module}"


# ---------------------------------------------------------------------------
# Phase 239: Vessel Traffic Service (VTS) & Navigation Safety Zones
# ---------------------------------------------------------------------------


def test_vts_advance_reporting_compliance() -> None:
    """Verify statutory 2.0h advance reporting check under VMC 2015 & Decree 58/2017."""
    compliant = VesselTrafficServiceEngine.check_vts_reporting(
        hours_before_checkpoint=2.5,
        checkpoint_name="Vung Tau Pilot Station Point 0",
        required_advance_hours=2.0,
    )
    assert compliant.is_compliant is True
    assert compliant.status == VtsReportingStatus.ON_TIME
    assert compliant.discrepancy_hours == 0.0

    non_compliant = VesselTrafficServiceEngine.check_vts_reporting(
        hours_before_checkpoint=1.2,
        checkpoint_name="Vung Tau Pilot Station Point 0",
        required_advance_hours=2.0,
    )
    assert non_compliant.is_compliant is False
    assert non_compliant.status == VtsReportingStatus.NON_COMPLIANT
    assert non_compliant.discrepancy_hours == 0.8
    assert len(non_compliant.notes) > 0


def test_vts_fairway_speed_evaluation() -> None:
    """Verify speed compliance and wake wash hazard evaluation."""
    normal_speed = VesselTrafficServiceEngine.evaluate_fairway_speed(
        actual_speed_knots=11.0,
        max_allowed_speed_knots=12.0,
        fairway_zone="inner_channel",
    )
    assert normal_speed.is_speeding is False
    assert normal_speed.speed_excess_knots == 0.0
    assert normal_speed.wake_wash_hazard is True  # > 10.0 in inner_channel
    assert normal_speed.reprimand_level == "NONE"

    overspeed = VesselTrafficServiceEngine.evaluate_fairway_speed(
        actual_speed_knots=14.5,
        max_allowed_speed_knots=12.0,
        fairway_zone="inner_channel",
    )
    assert overspeed.is_speeding is True
    assert overspeed.wake_wash_hazard is True
    assert overspeed.speed_excess_knots == 2.5
    assert overspeed.reprimand_level == "PORT_AUTHORITY_FORMAL_CITATION"


def test_vts_cpa_tcpa_collision_calculation() -> None:
    """Verify relative motion geometry for Closest Point of Approach (CPA) & TCPA."""
    # Crossing collision scenario: Own ship heading East (90 deg) at 12 kts from (0, 0),
    # Target ship heading North (0 deg) at 12 kts from (2, -2).
    crit_res = VesselTrafficServiceEngine.calculate_cpa_tcpa(
        own_x=0.0,
        own_y=0.0,
        own_speed_knots=12.0,
        own_course_deg=90.0,
        target_x=2.0,
        target_y=-2.0,
        target_speed_knots=12.0,
        target_course_deg=0.0,
    )
    assert crit_res.cpa_nautical_miles < 0.1
    assert crit_res.tcpa_minutes > 0.0
    assert crit_res.risk_level == CollisionRiskLevel.CRITICAL
    assert "AVOIDANCE" in crit_res.action_required

    # Safe passing scenario: Target ship heading West (270 deg) at 10 kts from (0, 5)
    safe_res = VesselTrafficServiceEngine.calculate_cpa_tcpa(
        own_x=0.0,
        own_y=0.0,
        own_speed_knots=12.0,
        own_course_deg=90.0,
        target_x=0.0,
        target_y=5.0,
        target_speed_knots=10.0,
        target_course_deg=270.0,
    )
    assert safe_res.cpa_nautical_miles >= 1.0
    assert safe_res.risk_level == CollisionRiskLevel.SAFE
    assert safe_res.action_required == "KEEP_STANDARD_RADAR_WATCH"


def test_vts_statutory_tariff_calculation() -> None:
    """Verify VTS statutory navigation service tariff under Circular 39/2023/TT-BGTVT."""
    intl_calc = VesselTrafficServiceEngine.calculate_vts_tariff(
        gross_tonnage=35000.0,
        is_international=True,
        transit_distance_nm=18.0,
    )
    assert intl_calc.total_fee > 0.0
    assert intl_calc.currency == "USD"
    assert len(intl_calc.audit_hash) == 16

    dom_calc = VesselTrafficServiceEngine.calculate_vts_tariff(
        gross_tonnage=15000.0,
        is_international=False,
        transit_distance_nm=18.0,
    )
    assert dom_calc.currency == "VND"
    assert dom_calc.total_fee > 0.0


# ---------------------------------------------------------------------------
# Phase 240: Port Cold Ironing (OPS/AMP) & Emissions Abatement
# ---------------------------------------------------------------------------


def test_cold_ironing_energy_with_sfc_loss() -> None:
    """Verify electrical power calculation with Static Frequency Converter (50Hz to 60Hz) loss."""
    energy_calc = ColdIroningEngine.calculate_energy(
        hotel_power_mw=3.0,
        berth_duration_hours=20.0,
        grid_frequency_hz=50,
        ship_frequency_hz=60,
        converter_efficiency_pct=97.0,
    )
    assert energy_calc.total_energy_mwh == 60.0
    assert energy_calc.converter_loss_mwh > 0.0
    assert energy_calc.net_billed_mwh > energy_calc.total_energy_mwh

    # Identical frequency -> zero converter loss
    same_freq = ColdIroningEngine.calculate_energy(
        hotel_power_mw=3.0,
        berth_duration_hours=20.0,
        grid_frequency_hz=50,
        ship_frequency_hz=50,
    )
    assert same_freq.converter_loss_mwh == 0.0
    assert same_freq.net_billed_mwh == 60.0


def test_cold_ironing_emissions_avoidance() -> None:
    """Verify net GHG emissions abatement (MGO vs Shore Grid CO2, SOx, NOx, PM2.5)."""
    emissions = ColdIroningEngine.calculate_emissions_avoided(
        total_energy_mwh=50.0,
        net_billed_mwh=51.5,
    )
    assert emissions.baseline_mgo_tonnes > 0.0
    assert emissions.mgo_co2_tonnes > 0.0
    assert emissions.grid_co2_tonnes > 0.0
    assert emissions.net_co2_avoided_tonnes >= 0.0
    assert emissions.sox_avoided_tonnes > 0.0
    assert emissions.nox_avoided_tonnes > 0.0
    assert emissions.pm25_avoided_tonnes > 0.0


def test_cold_ironing_cost_savings() -> None:
    """Verify economic savings of shore power vs marine fuel consumption."""
    savings = ColdIroningEngine.evaluate_cost_savings(
        net_billed_mwh=40.0,
        baseline_mgo_tonnes=8.6,
        electricity_price_per_kwh_vnd=3200.0,
        green_infra_fee_vnd=2000000.0,
        mgo_price_per_tonne_usd=850.0,
        fx_usd_vnd=25400.0,
    )
    assert savings.total_shore_power_cost > 0.0
    assert savings.mgo_fuel_saved_cost > 0.0
    assert savings.net_financial_savings == round(savings.mgo_fuel_saved_cost - savings.total_shore_power_cost, 2)


# ---------------------------------------------------------------------------
# Phase 241: Green Port GHG MRV & IMO CII Rating Engine
# ---------------------------------------------------------------------------


def test_green_port_attained_cii_calculation() -> None:
    """Verify IMO Carbon Intensity Indicator (AER) calculation."""
    attained = GreenPortGhgCiiEngine.calculate_attained_cii(
        fuel_consumption_tonnes={"vlsfo": 2500.0, "mgo": 300.0},
        capacity_dwt=60000.0,
        distance_travelled_nm=40000.0,
    )
    # Total CO2: 2500 * 3.114 + 300 * 3.206 = 7785 + 961.8 = 8746.8 t CO2
    # AER = 8746.8 * 1e6 / (60000 * 40000) = 8746800000 / 2400000000 = 3.6445 gCO2 / DWT-NM
    assert round(attained, 2) == 3.64


def test_green_port_cii_rating_evaluation() -> None:
    """Verify 5-tier CII rating (A-E), SEEMP CAP triggers and green port discounts."""
    # Top efficiency -> Grade A
    res_a = GreenPortGhgCiiEngine.evaluate_cii_rating(
        ship_type=CiiShipType.CONTAINER,
        capacity_dwt=65000.0,
        distance_travelled_nm=45000.0,
        attained_cii=3.2,
        calendar_year=2026,
    )
    assert res_a.rating_grade in (CiiRatingGrade.A, CiiRatingGrade.B)
    assert res_a.corrective_action_plan_required is False
    assert res_a.port_tonnage_dues_discount_pct >= 15.0

    # Low efficiency -> Grade E -> Mandatory SEEMP CAP
    res_e = GreenPortGhgCiiEngine.evaluate_cii_rating(
        ship_type=CiiShipType.CONTAINER,
        capacity_dwt=65000.0,
        distance_travelled_nm=45000.0,
        attained_cii=18.0,
        calendar_year=2026,
    )
    assert res_e.rating_grade == CiiRatingGrade.E
    assert res_e.corrective_action_plan_required is True
    assert res_e.port_tonnage_dues_discount_pct == 0.0

    # Consecutive D ratings triggering SEEMP CAP
    res_consec_d = GreenPortGhgCiiEngine.evaluate_cii_rating(
        ship_type=CiiShipType.BULK_CARRIER,
        capacity_dwt=70000.0,
        distance_travelled_nm=50000.0,
        attained_cii=4.5,
        calendar_year=2026,
        prior_ratings=[CiiRatingGrade.D, CiiRatingGrade.D],
    )
    if res_consec_d.rating_grade == CiiRatingGrade.D:
        assert res_consec_d.corrective_action_plan_required is True


# ---------------------------------------------------------------------------
# Phase 242: Marine Bunkering Safety & BDN Sulphur Cap Compliance
# ---------------------------------------------------------------------------


def test_bdn_sulphur_cap_compliance_global_and_eca() -> None:
    """Verify Bunker Delivery Note compliance with 0.50% global and 0.10% ECA limits."""
    # Global VLSFO within limit
    vlsfo_ok = MarineBunkeringSafetyEngine.verify_bdn_compliance(
        product_grade=BunkerGrade.VLSFO,
        sulphur_content_pct=0.48,
        bdn_record_age_years=1.0,
        sample_seal_number="SEAL-001",
        is_operating_in_eca=False,
    )
    assert vlsfo_ok.is_valid_bdn is True
    assert vlsfo_ok.is_sulphur_compliant is True

    # Global VLSFO exceeding 95% confidence verification threshold (0.53%)
    vlsfo_fail = MarineBunkeringSafetyEngine.verify_bdn_compliance(
        product_grade=BunkerGrade.VLSFO,
        sulphur_content_pct=0.55,
        bdn_record_age_years=1.0,
        sample_seal_number="SEAL-002",
        is_operating_in_eca=False,
    )
    assert vlsfo_fail.is_valid_bdn is False
    assert vlsfo_fail.is_sulphur_compliant is False
    assert "Sulphur content" in vlsfo_fail.rejection_reasons[0]

    # ECA operation without scrubber
    eca_fail = MarineBunkeringSafetyEngine.verify_bdn_compliance(
        product_grade=BunkerGrade.VLSFO,
        sulphur_content_pct=0.45,
        bdn_record_age_years=1.0,
        sample_seal_number="SEAL-003",
        is_operating_in_eca=True,
        has_approved_scrubber=False,
    )
    assert eca_fail.is_valid_bdn is False
    assert eca_fail.is_sulphur_compliant is False

    # ECA operation with scrubber
    eca_ok = MarineBunkeringSafetyEngine.verify_bdn_compliance(
        product_grade=BunkerGrade.HSFO_SCRUBBER,
        sulphur_content_pct=2.5,
        bdn_record_age_years=1.0,
        sample_seal_number="SEAL-004",
        is_operating_in_eca=True,
        has_approved_scrubber=True,
    )
    assert eca_ok.is_valid_bdn is True
    assert eca_ok.is_sulphur_compliant is True


def test_bdn_three_year_record_retention() -> None:
    """Verify mandatory 3-year BDN record retention under MARPOL Annex VI Reg. 18."""
    retained_ok = MarineBunkeringSafetyEngine.verify_bdn_compliance(
        product_grade=BunkerGrade.MGO,
        sulphur_content_pct=0.08,
        bdn_record_age_years=2.5,
        sample_seal_number="SEAL-005",
    )
    assert retained_ok.is_valid_bdn is True
    assert retained_ok.is_retention_compliant is True

    expired_record = MarineBunkeringSafetyEngine.verify_bdn_compliance(
        product_grade=BunkerGrade.MGO,
        sulphur_content_pct=0.08,
        bdn_record_age_years=3.5,
        sample_seal_number="SEAL-006",
    )
    assert expired_record.is_valid_bdn is False
    assert expired_record.is_retention_compliant is False
    assert any("retention" in r.lower() for r in expired_record.rejection_reasons)


def test_bunkering_safety_operational_evaluation() -> None:
    """Verify bunkering ISGOTT safety parameters and Emergency Shutdown (ESD)."""
    safe_eval = MarineBunkeringSafetyEngine.evaluate_bunkering_safety(
        pumping_rate_m3_h=350.0,
        manifold_pressure_bar=3.5,
        esd_response_time_seconds=20.0,
        scupper_plugs_secured=True,
        sopep_spill_kit_ready=True,
        bonding_wire_secured=True,
    )
    assert safe_eval.is_cleared_for_bunkering is True
    assert safe_eval.is_esd_acceptable is True

    unsafe_eval = MarineBunkeringSafetyEngine.evaluate_bunkering_safety(
        pumping_rate_m3_h=700.0,
        manifold_pressure_bar=6.2,
        esd_response_time_seconds=45.0,  # > 30s limit
        scupper_plugs_secured=False,
        sopep_spill_kit_ready=False,
        bonding_wire_secured=True,
    )
    assert unsafe_eval.is_cleared_for_bunkering is False
    assert unsafe_eval.is_esd_acceptable is False
    assert len(unsafe_eval.violations) >= 3


def test_astm_table_54b_vcf_calculation() -> None:
    """Verify ASTM Table 54B Volume Correction Factor (VCF) and in-air metric tonnes."""
    astm_calc = MarineBunkeringSafetyEngine.calculate_volume_and_mass(
        observed_volume_m3=500.0,
        observed_temp_c=40.0,
        density_15c_kg_m3=985.0,
    )
    assert astm_calc.vcf_factor < 1.0  # warmer than 15C -> VCF < 1.0
    assert astm_calc.standard_volume_15c_m3 < 500.0
    assert astm_calc.metric_tonnes_in_air > 0.0


# ---------------------------------------------------------------------------
# CLI Command Integration Tests
# ---------------------------------------------------------------------------


def test_cli_vtsreporting_commands() -> None:
    """Verify Typer CLI commands for VTS reporting, fairway speed, collision and tariff."""
    res_rep = runner.invoke(vtsreporting_app, ["check", "--hours", "2.5", "--json"])
    assert res_rep.exit_code == 0
    assert "is_compliant" in res_rep.stdout

    res_speed = runner.invoke(vtsreporting_app, ["speed", "--speed", "10.5", "--limit", "12.0", "--json"])
    assert res_speed.exit_code == 0
    assert "is_speeding" in res_speed.stdout

    res_coll = runner.invoke(vtsreporting_app, ["cpa", "--target-x", "2.0", "--target-y", "2.0", "--json"])
    assert res_coll.exit_code == 0
    assert "risk_level" in res_coll.stdout

    res_tariff = runner.invoke(vtsreporting_app, ["tariff", "--gt", "30000.0", "--json"])
    assert res_tariff.exit_code == 0
    assert "total_fee" in res_tariff.stdout


def test_cli_coldironing_commands() -> None:
    """Verify Typer CLI commands for Cold Ironing shore power energy and emissions."""
    res_energy = runner.invoke(coldironing_app, ["energy", "--power", "2.5", "--hours", "24.0", "--json"])
    assert res_energy.exit_code == 0
    assert "net_billed_mwh" in res_energy.stdout

    res_emiss = runner.invoke(coldironing_app, ["emissions", "--mwh", "60.0", "--billed-mwh", "61.8", "--json"])
    assert res_emiss.exit_code == 0
    assert "net_co2_avoided_tonnes" in res_emiss.stdout


def test_cli_greenportghg_commands() -> None:
    """Verify Typer CLI commands for Green Port GHG MRV and IMO CII rating evaluation."""
    res_cii = runner.invoke(greenportghg_app, ["cii", "--type", "container", "--dwt", "65000.0", "--dist", "45000.0", "--mgo", "3200.0", "--json"])
    assert res_cii.exit_code == 0
    assert "rating_grade" in res_cii.stdout
    assert "attained_cii" in res_cii.stdout


def test_cli_marinebunkering_commands() -> None:
    """Verify Typer CLI commands for Marine Bunkering BDN and ASTM volume calculation."""
    res_bdn = runner.invoke(marinebunkering_app, ["bdn", "--sulphur", "0.48", "--seal", "SEAL-VN-99", "--json"])
    assert res_bdn.exit_code == 0
    assert "is_valid_bdn" in res_bdn.stdout

    res_volume = runner.invoke(marinebunkering_app, ["volume", "--volume", "500.0", "--temp", "40.0", "--json"])
    assert res_volume.exit_code == 0
    assert "vcf_factor" in res_volume.stdout


# ---------------------------------------------------------------------------
# MCP Handler Integration Tests
# ---------------------------------------------------------------------------


def test_mcp_vts_handler() -> None:
    """Verify MCP handler for mekong_vts_navigation_evaluate."""
    from scripts.mcp_server import handle_vts_navigation_evaluate

    raw = handle_vts_navigation_evaluate({
        "actual_speed_knots": 11.5,
        "gross_tonnage": 28000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert "vts_reporting" in res
    assert "fairway_speed" in res
    assert "cpa_tcpa" in res
    assert "vts_tariff" in res


def test_mcp_cold_ironing_handler() -> None:
    """Verify MCP handler for mekong_cold_ironing_power_evaluate."""
    from scripts.mcp_server import handle_cold_ironing_power_evaluate

    raw = handle_cold_ironing_power_evaluate({
        "hotel_power_mw": 2.0,
        "berth_duration_hours": 18.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert "energy_consumption" in res
    assert "emissions_avoided" in res
    assert "cost_evaluation" in res


def test_mcp_green_port_ghg_handler() -> None:
    """Verify MCP handler for mekong_green_port_ghg_cii_evaluate."""
    from scripts.mcp_server import handle_green_port_ghg_cii_evaluate

    raw = handle_green_port_ghg_cii_evaluate({
        "ship_type": "container",
        "capacity_dwt": 55000.0,
        "distance_travelled_nm": 42000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert "attained_cii" in res
    assert "cii_evaluation" in res
    assert "port_tonnage_dues" in res


def test_mcp_marine_bunkering_handler() -> None:
    """Verify MCP handler for mekong_marine_bunkering_safety_evaluate."""
    from scripts.mcp_server import handle_marine_bunkering_safety_evaluate

    raw = handle_marine_bunkering_safety_evaluate({
        "sulphur_content_pct": 0.45,
        "observed_volume_m3": 450.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert "bdn_verification" in res
    assert "safety_evaluation" in res
    assert "astm_measurement" in res
