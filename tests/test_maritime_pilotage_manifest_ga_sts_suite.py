"""Automated Test Suite for Maritime Pilotage Exemption, e-Manifest MLETR, General Average & STS Transshipment Suite (Phases 235-238).

Covers:
- Phase 235: Compulsory Maritime Pilotage Zones & Exemption Licensing (VMC 2015 Arts. 246-258, Circular 39/2023)
- Phase 236: Seaport Cargo Manifest Delivery, Electronic Bill of Lading (MLETR) & Tally Reconciliation (Decree 58/2017, Circular 39/2018)
- Phase 237: Marine Hull General Average (GA) Security & York-Antwerp Rules 2016 (VMC 2015 Arts. 290-302, YAR 2016)
- Phase 238: Seaport Ship-to-Ship (STS) Transfer Operations & Petroleum Transshipment Safety (Decree 58/2017, MARPOL Annex I)
- AST Zero-External-Dependency Verification
- Typer CLI command tests
- FastMCP tool handler tests
"""

import ast
import json
from typer.testing import CliRunner

from src.core.maritime_pilotage_manifest_ga_sts_engine import (
    MaritimePilotageEngine,
    PilotageZoneType,
    VesselTradeClass,
    CargoManifestMletrEngine,
    GeneralAverageAdjustingEngine,
    ShipToShipTransferEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_maritime_pilotage_evaluate,
    handle_cargo_manifest_mletr_process,
    handle_general_average_adjust,
    handle_ship_to_ship_transfer_evaluate,
)


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================
def test_ast_zero_external_dependency_invariant():
    """Verify engine relies purely on Python standard library modules."""
    engine_path = "src/core/maritime_pilotage_manifest_ga_sts_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_path)

    allowed_stdlib = {"dataclasses", "enum", "math", "typing", "json", "re", "hashlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_pkg = alias.name.split(".")[0]
                assert base_pkg in allowed_stdlib, f"Disallowed package import: {base_pkg}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_pkg = node.module.split(".")[0]
                assert base_pkg in allowed_stdlib, f"Disallowed from-import: {base_pkg}"


# ===========================================================================
# 2. Phase 235: Maritime Pilotage Exemption & Tariffs
# ===========================================================================
def test_pilotage_exemption_domestic_under_2000_gt():
    """Domestic vessel < 2,000 GT is exempt under VMC 2015 Art. 248."""
    res = MaritimePilotageEngine.check_pilotage_exemption(
        gross_tonnage=1800.0,
        trade_class=VesselTradeClass.DOMESTIC,
        is_hazardous_bulk=False,
    )
    assert res.is_exempt is True
    assert res.requires_pilot is False
    assert "2,000 GT" in res.exemption_reason


def test_pilotage_exemption_hazardous_bulk_not_exempt():
    """Vessel carrying hazardous bulk cargo is never exempt."""
    res = MaritimePilotageEngine.check_pilotage_exemption(
        gross_tonnage=1500.0,
        trade_class=VesselTradeClass.DOMESTIC,
        is_hazardous_bulk=True,
    )
    assert res.is_exempt is False
    assert res.requires_pilot is True
    assert "dangerous goods/oil in bulk" in res.exemption_reason


def test_pilotage_exemption_master_cert_with_10_calls():
    """Master with certificate and >= 10 port calls in 12 months is exempt."""
    res = MaritimePilotageEngine.check_pilotage_exemption(
        gross_tonnage=5000.0,
        trade_class=VesselTradeClass.DOMESTIC,
        master_has_exemption_cert=True,
        port_calls_last_12m=12,
    )
    assert res.is_exempt is True
    assert res.requires_pilot is False
    assert "Pilotage Exemption Certificate" in res.exemption_reason


def test_pilotage_exemption_master_cert_insufficient_calls():
    """Master with certificate but only 6 calls in 12 months is not exempt."""
    res = MaritimePilotageEngine.check_pilotage_exemption(
        gross_tonnage=5000.0,
        trade_class=VesselTradeClass.DOMESTIC,
        master_has_exemption_cert=True,
        port_calls_last_12m=6,
    )
    assert res.is_exempt is False
    assert res.requires_pilot is True


def test_pilotage_exemption_foreign_vessel_mandatory():
    """Foreign trade vessel must use pilot in compulsory zone."""
    res = MaritimePilotageEngine.check_pilotage_exemption(
        gross_tonnage=25000.0,
        trade_class=VesselTradeClass.INTERNATIONAL,
        zone_type=PilotageZoneType.COMPULSORY_INSHORE,
    )
    assert res.is_exempt is False
    assert res.requires_pilot is True


def test_pilotage_optional_anchorage_zone():
    """Optional anchorage zone does not require compulsory pilotage."""
    res = MaritimePilotageEngine.check_pilotage_exemption(
        gross_tonnage=30000.0,
        trade_class=VesselTradeClass.INTERNATIONAL,
        zone_type=PilotageZoneType.OPTIONAL_ANCHORAGE,
    )
    assert res.is_exempt is True
    assert res.requires_pilot is False


def test_pilotage_tariff_standby_and_late_cancellation():
    """Test pilotage tariff calculation with idle wait fee and cancellation penalty."""
    calc = MaritimePilotageEngine.calculate_pilotage_tariff(
        gross_tonnage=10000.0,
        trade_class=VesselTradeClass.INTERNATIONAL,
        distance_nautical_miles=15.0,
        idle_wait_hours=3.0,
        cancellation_notice_hours=1.0,
    )
    assert calc.currency == "USD"
    assert calc.base_tariff > 0.0
    # idle_wait_hours recorded as 3.0
    assert calc.wait_hours == 3.0
    # 3 hours wait minus 1 hour free grace = 2 hours chargeable @ $20/hr
    assert calc.standby_detention_fee == 40.0
    # cancellation notice < 2 hours triggers base minimum penalty ($150)
    assert calc.cancellation_penalty == 150.0
    assert calc.total_tariff == calc.base_tariff + 40.0 + 150.0
    assert len(calc.audit_hash) == 16


# ===========================================================================
# 3. Phase 236: Cargo Manifest Delivery & MLETR e-B/L
# ===========================================================================
def test_cargo_manifest_compliance_advance_notice():
    """Manifest submitted 26h in advance for long-sea complies with 24h statutory rule."""
    res = CargoManifestMletrEngine.check_advance_manifest(
        hours_before_arrival=26.0,
        is_short_sea_shipping=False,
    )
    assert res.is_compliant is True
    assert res.status.value == "on_time"


def test_cargo_manifest_non_compliance_advance_notice():
    """Manifest submitted 18h in advance for long-sea is non-compliant (< 24h)."""
    res = CargoManifestMletrEngine.check_advance_manifest(
        hours_before_arrival=18.0,
        is_short_sea_shipping=False,
    )
    assert res.is_compliant is False
    assert res.status.value == "late_submission"


def test_cargo_manifest_short_sea_14h():
    """Short sea shipping requires at least 12h advance notice."""
    res = CargoManifestMletrEngine.check_advance_manifest(
        hours_before_arrival=14.0,
        is_short_sea_shipping=True,
    )
    assert res.is_compliant is True


def test_tally_reconciliation_within_customs_tolerance():
    """Discrepancy 0.4% is within 0.5% tolerance threshold."""
    res = CargoManifestMletrEngine.reconcile_manifest_vs_tally(
        manifest_qty=10000.0,
        tally_qty=9960.0,
        customs_tolerance_pct=0.5,
    )
    assert res.is_matched is True
    assert res.discrepancy_pct == 0.4
    assert res.requires_customs_amendment is False


def test_tally_reconciliation_exceeds_tolerance_requires_amendment():
    """Discrepancy 2.0% exceeds 0.5% tolerance and triggers statutory amendment requirement."""
    res = CargoManifestMletrEngine.reconcile_manifest_vs_tally(
        manifest_qty=10000.0,
        tally_qty=9800.0,
        customs_tolerance_pct=0.5,
    )
    assert res.is_matched is False
    assert res.discrepancy_pct == 2.0
    assert res.requires_customs_amendment is True


def test_mletr_ebl_token_issuance_and_transfer():
    """Test UNCITRAL MLETR token hash uniqueness and state transfer."""
    initial = CargoManifestMletrEngine.issue_or_transfer_mletr_ebl(
        bl_number="BL-VN-100",
        carrier="Mekong Lines",
        shipper="Export Co",
        consignee="To Order",
        new_holder="Bank A",
    )
    assert len(initial.mletr_token) == 64
    assert initial.current_holder == "Bank A"
    assert initial.is_valid_transfer is True

    # Transfer to Bank B
    transferred = CargoManifestMletrEngine.issue_or_transfer_mletr_ebl(
        bl_number="BL-VN-100",
        carrier="Mekong Lines",
        shipper="Export Co",
        consignee="To Order",
        new_holder="Bank B",
        previous_token=initial.mletr_token,
    )
    assert transferred.current_holder == "Bank B"
    assert transferred.previous_hash == initial.mletr_token
    assert transferred.mletr_token != initial.mletr_token


# ===========================================================================
# 4. Phase 237: General Average (GA) Adjustment & Average Bond
# ===========================================================================
def test_general_average_contributory_values_calculation():
    """Calculate net contributory values of ship, cargo, and freight."""
    cv = GeneralAverageAdjustingEngine.calculate_contributory_values(
        ship_sound_value=20000000.0,
        ship_non_ga_damage=1000000.0,
        cargo_cif_value=30000000.0,
        cargo_damage_loss=500000.0,
        cargo_landing_charges=100000.0,
        freight_at_risk=2000000.0,
        freight_post_ga_expenses=200000.0,
    )
    assert cv.ship_value == 19000000.0
    assert cv.cargo_value == 29400000.0
    assert cv.freight_value == 1800000.0
    assert cv.total_contributory_value == 19000000.0 + 29400000.0 + 1800000.0


def test_general_average_adjustment_rules():
    """Test YAR 2016 Rule XX (2% commission), Rule XXI (7% p.a. interest) and apportionment."""
    cv = GeneralAverageAdjustingEngine.calculate_contributory_values(
        ship_sound_value=10000000.0,
        ship_non_ga_damage=0.0,
        cargo_cif_value=10000000.0,
        cargo_damage_loss=0.0,
        cargo_landing_charges=0.0,
        freight_at_risk=0.0,
        freight_post_ga_expenses=0.0,
    )
    # Total CV = 20,000,000
    res = GeneralAverageAdjustingEngine.adjust_general_average(
        ga_sacrifices=600000.0,
        ga_cash_disbursements=400000.0,
        contributory_values=cv,
        adjustment_days=365,
    )
    # Commission: 2% of 400,000 = 8,000
    assert res.commission_allowance == 8000.0
    # Subtotal before interest = 600,000 + 400,000 + 8,000 = 1,008,000
    # Interest: 7% p.a. for 365 days = 1,008,000 * 0.07 = 70,560
    assert round(res.interest_allowance, 2) == 70560.0
    # Total GA = 1,078,560. GA rate = 1,078,560 / 20,000,000 = 5.3928%
    assert round(res.ga_rate_pct, 4) == 5.3928
    assert round(res.ship_contribution + res.cargo_contribution, 2) == round(res.total_ga_sacrifice_expenditure, 2)
    # Cash deposit = Cargo contribution * 1.15
    assert round(res.cash_deposit_required, 2) == round(res.cargo_contribution * 1.15, 2)
    assert len(res.adjustment_hash) == 16


# ===========================================================================
# 5. Phase 238: Ship-to-Ship (STS) Transfer & Safety Limits
# ===========================================================================
def test_sts_berthing_energy_and_fender_adequacy():
    """Verify virtual mass and berthing energy against Yokohama fender rating."""
    res = ShipToShipTransferEngine.calculate_berthing_energy(
        displacement_tonnes=75000.0,
        draft_meters=12.0,
        beam_meters=32.0,
        approach_velocity_mps=0.12,
        fender_rated_energy_kNm=450.0,
        fender_standoff_distance_meters=3.5,
    )
    # virtual mass = 75000 * (1 + 2*12/32) = 75000 * 1.75 = 131,250 tonnes
    assert res.virtual_mass_tonnes == 131250.0
    assert res.is_fender_adequate is True
    assert res.berthing_energy_kNm < 450.0


def test_sts_berthing_energy_fender_inadequate():
    """High approach velocity exceeds rated fender absorption energy."""
    res = ShipToShipTransferEngine.calculate_berthing_energy(
        displacement_tonnes=150000.0,
        draft_meters=18.0,
        beam_meters=44.0,
        approach_velocity_mps=0.35,
        fender_rated_energy_kNm=400.0,
        fender_standoff_distance_meters=2.5,
    )
    assert res.is_fender_adequate is False


def test_sts_safety_evaluation_all_safe():
    """Optimal conditions allow STS transfer."""
    res = ShipToShipTransferEngine.evaluate_sts_safety(
        wind_speed_mps=8.0,
        significant_wave_height_meters=1.0,
        lightning_distance_nm=15.0,
        inert_gas_oxygen_pct=5.5,
        bonding_resistance_ohms=400.0,
        oil_boom_circumference_meters=500.0,
        vessel_a_loa_meters=200.0,
        vessel_b_loa_meters=180.0,
    )
    assert res.is_safe_to_operate is True
    assert res.weather_abort is False
    assert res.inert_gas_safe is True
    assert res.electrical_bonding_safe is True
    assert res.boom_circumference_adequate is True
    assert len(res.violations) == 0


def test_sts_safety_evaluation_violations():
    """Exceeding environmental thresholds aborts STS transfer."""
    res = ShipToShipTransferEngine.evaluate_sts_safety(
        wind_speed_mps=14.0,  # > 12 m/s
        significant_wave_height_meters=1.8,  # > 1.5 m
        lightning_distance_nm=3.0,  # <= 5.0 NM
        inert_gas_oxygen_pct=9.2,  # > 8.0%
        bonding_resistance_ohms=2_000_000.0,  # > 1M ohms
        oil_boom_circumference_meters=200.0,  # < 1.5 * 220 = 330m
        vessel_a_loa_meters=220.0,
        vessel_b_loa_meters=180.0,
    )
    assert res.is_safe_to_operate is False
    assert res.weather_abort is True
    assert res.inert_gas_safe is False
    assert res.electrical_bonding_safe is False
    assert res.boom_circumference_adequate is False
    assert len(res.violations) >= 5


# ===========================================================================
# 6. Typer CLI Command Execution Tests
# ===========================================================================
def test_cli_pilotagezone_check_and_tariff():
    """Test CLI commands pilotagezone check and tariff."""
    app = build_app()
    runner = CliRunner()

    res = runner.invoke(app, ["pilotagezone", "check", "--gt", "1500", "--trade", "domestic"])
    assert res.exit_code == 0
    assert "CÓ (Đủ điều kiện miễn)" in res.stdout

    res_json = runner.invoke(app, ["pilotagezone", "tariff", "--gt", "10000", "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.stdout)
    assert "total_tariff" in data


def test_cli_emanifest_check_and_reconcile():
    """Test CLI commands emanifest check, reconcile, and token."""
    app = build_app()
    runner = CliRunner()

    res = runner.invoke(app, ["emanifest", "check", "--hours", "30"])
    assert res.exit_code == 0
    assert "ON_TIME" in res.stdout

    res_rec = runner.invoke(app, ["emanifest", "reconcile", "--manifest", "5000", "--tally", "4900", "--json"])
    assert res_rec.exit_code == 0
    data = json.loads(res_rec.stdout)
    assert data["requires_customs_amendment"] is True

    res_tok = runner.invoke(app, ["emanifest", "token", "--bl", "BL-TEST-1", "--json"])
    assert res_tok.exit_code == 0
    data_tok = json.loads(res_tok.stdout)
    assert len(data_tok["mletr_token"]) == 64


def test_cli_generalaverage_and_ststransfer():
    """Test CLI commands generalaverage adjust and ststransfer energy."""
    app = build_app()
    runner = CliRunner()

    res_ga = runner.invoke(app, ["generalaverage", "adjust", "--ship", "10000000", "--cargo", "10000000", "--json"])
    assert res_ga.exit_code == 0
    data_ga = json.loads(res_ga.stdout)
    assert "ga_rate_pct" in data_ga

    res_sts = runner.invoke(app, ["ststransfer", "energy", "--displacement", "60000", "--json"])
    assert res_sts.exit_code == 0
    data_sts = json.loads(res_sts.stdout)
    assert "berthing_energy_kNm" in data_sts


# ===========================================================================
# 7. FastMCP Tool Handler Tests
# ===========================================================================
def test_mcp_pilotage_handler():
    """Test handle_maritime_pilotage_evaluate MCP tool handler."""
    raw = handle_maritime_pilotage_evaluate({
        "gross_tonnage": 1800.0,
        "trade_class": "DOMESTIC",
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["exemption"]["is_exempt"] is True


def test_mcp_cargo_manifest_handler():
    """Test handle_cargo_manifest_mletr_process MCP tool handler."""
    raw = handle_cargo_manifest_mletr_process({
        "hours_before_arrival": 28.0,
        "manifest_qty": 3000.0,
        "tally_qty": 3000.0,
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["advance_manifest"]["is_compliant"] is True
    assert data["tally_reconciliation"]["is_matched"] is True


def test_mcp_general_average_handler():
    """Test handle_general_average_adjust MCP tool handler."""
    raw = handle_general_average_adjust({
        "ship_sound_value": 15000000.0,
        "cargo_cif_value": 25000000.0,
        "ga_sacrifices": 500000.0,
        "ga_cash_disbursements": 200000.0,
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["adjustment"]["ga_rate_pct"] > 0.0


def test_mcp_ship_to_ship_transfer_handler():
    """Test handle_ship_to_ship_transfer_evaluate MCP tool handler."""
    raw = handle_ship_to_ship_transfer_evaluate({
        "displacement_tonnes": 70000.0,
        "wind_speed_mps": 7.0,
        "significant_wave_height_meters": 0.8,
    })
    data = json.loads(raw)
    assert data["ok"] is True
    assert data["safety_evaluation"]["is_safe_to_operate"] is True
