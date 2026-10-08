"""Unit, AST Zero-Dependency, Integration & CLI Tests for Maritime Suite (Phases 207-210).

Covers:
- Phase 207: Cargo Claims & Bill of Lading (VMC Arts. 145-174, Hague-Visby, Hamburg)
- Phase 208: Charterparty Laytime, Demurrage & Dispatch Performance
- Phase 209: Seafarer Employment, MLC 2006 Wages & Statutory Disability
- Phase 210: Marine Pilotage Liability Cap & Towage Contract Allocation (VMC Arts. 246-270)
- AST Zero-Dependency Invariant
- Typer CLI commands & FastMCP tools
"""

import ast
import json
from typer.testing import CliRunner

from src.core.maritime_cargo_charterparty_seafarer_engine import (
    MaritimeCargoClaimsEngine,
    CarrierDefenseCategory,
    CharterpartyLaytimeEngine,
    LaytimeTerm,
    SeafarerMLCCompensationEngine,
    SeafarerRank,
    DisabilityDegree,
    MarinePilotageAndTowageEngine,
    TowageContractType,
    FlotillaCommandType,
)
from src.cli.app_setup import build_app
import scripts.mcp_server as mcp_srv

runner = CliRunner()


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================

def test_maritime_cargo_charterparty_ast_zero_dependency():
    """Verify src/core/maritime_cargo_charterparty_seafarer_engine.py has 0 external dependencies."""
    file_path = "src/core/maritime_cargo_charterparty_seafarer_engine.py"
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    allowed_stdlib = {
        "dataclasses",
        "datetime",
        "enum",
        "math",
        "typing",
        "json",
        "hashlib",
        "re",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                assert root_pkg in allowed_stdlib, f"Disallowed import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_stdlib, f"Disallowed from-import: {node.module}"


# ===========================================================================
# 2. Phase 207: Cargo Claims Tests
# ===========================================================================

def test_cargo_claim_package_vs_weight_higher_limit():
    """Verify dual statutory ceiling: higher of package vs weight is selected under VMC Art. 152."""
    # 100 packages, 10,000 kg gross weight, loss = 100,000 USD, 1 SDR = 1.35 USD
    # Package limit: 100 * 666.67 * 1.35 = 90,000.45 USD
    # Weight limit: 10,000 * 2.0 * 1.35 = 27,000.00 USD
    # Applicable limit should be package ceiling (90,000.45 USD)
    res = MaritimeCargoClaimsEngine.assess_cargo_claim(
        claim_id="CLM-01",
        cargo_description="AUTO_PARTS",
        number_of_packages=100,
        gross_weight_kg=10000.0,
        claimed_loss_usd=100000.0,
        sdr_to_usd_rate=1.35,
    )
    assert res.package_ceiling_usd == 90000.45
    assert res.weight_ceiling_usd == 27000.0
    assert res.applicable_statutory_limit_usd == 90000.45
    assert res.carrier_payout_liability_usd == 90000.45
    assert "CARRIER LIABLE" in res.verdict


def test_cargo_claim_weight_ceiling_higher_for_heavy_bulk():
    """Verify weight limit chosen when weight exceeds package threshold."""
    # 10 large machinery packages, 50,000 kg
    # Package limit: 10 * 666.67 * 1.35 = 9,000.05 USD
    # Weight limit: 50,000 * 2.0 * 1.35 = 135,000.00 USD -> Higher!
    res = MaritimeCargoClaimsEngine.assess_cargo_claim(
        claim_id="CLM-02",
        cargo_description="HEAVY_TURBINES",
        number_of_packages=10,
        gross_weight_kg=50000.0,
        claimed_loss_usd=200000.0,
        sdr_to_usd_rate=1.35,
    )
    assert res.applicable_statutory_limit_usd == 135000.0
    assert res.carrier_payout_liability_usd == 135000.0


def test_cargo_claim_statutory_defense_exemption():
    """Verify carrier exemption when statutory defense is proven with due diligence seaworthiness."""
    res = MaritimeCargoClaimsEngine.assess_cargo_claim(
        claim_id="CLM-03",
        cargo_description="FROZEN_SEAFOOD",
        number_of_packages=500,
        gross_weight_kg=20000.0,
        claimed_loss_usd=150000.0,
        carrier_defense=CarrierDefenseCategory.PERILS_OF_THE_SEA,
        due_diligence_seaworthy=True,
    )
    assert res.defense_valid is True
    assert res.carrier_payout_liability_usd == 0.0
    assert "CARRIER EXEMPT" in res.verdict


def test_cargo_claim_defense_overridden_by_unseaworthiness():
    """Verify carrier defense overridden when vessel was not seaworthy (Art. 150)."""
    res = MaritimeCargoClaimsEngine.assess_cargo_claim(
        claim_id="CLM-04",
        cargo_description="GRAIN_BULK",
        number_of_packages=1000,
        gross_weight_kg=50000.0,
        claimed_loss_usd=80000.0,
        carrier_defense=CarrierDefenseCategory.PERILS_OF_THE_SEA,
        due_diligence_seaworthy=False,  # Unseaworthy!
    )
    assert res.defense_valid is False
    assert res.carrier_payout_liability_usd == 80000.0


def test_cargo_claim_1year_prescription_extinction():
    """Verify claim extinction after 365 days under VMC Art. 169."""
    res = MaritimeCargoClaimsEngine.assess_cargo_claim(
        claim_id="CLM-05",
        cargo_description="TEXTILES",
        number_of_packages=200,
        gross_weight_kg=5000.0,
        claimed_loss_usd=50000.0,
        days_since_delivery=400,  # > 365 days
    )
    assert res.is_timebarred_1year_prescription is True
    assert res.carrier_payout_liability_usd == 0.0
    assert "CLAIM EXTINGUISHED" in res.verdict


# ===========================================================================
# 3. Phase 208: Charterparty Laytime, Demurrage & Dispatch Tests
# ===========================================================================

def test_laytime_demurrage_incurred_wwd():
    """Verify demurrage calculation when time used exceeds allowed hours under WWD terms."""
    # Allowed: 72 hours (3 days)
    # Actual working: 120 hours, weather delay: 12 hours, weekend delay: 12 hours
    # Net used: 120 - 12 - 12 = 96 hours
    # Demurrage: 96 - 72 = 24 hours (1.0 day) @ 15,000 USD/day = 15,000 USD
    res = CharterpartyLaytimeEngine.calculate_laytime(
        charter_ref="CP-01",
        vessel_name="MV BULK EXPRESS",
        total_allowed_laytime_hours=72.0,
        nor_tendered_hour=9,
        nor_tendered_iso="2026-10-01T09:00:00",
        actual_working_hours=120.0,
        weather_delay_hours=12.0,
        weekend_holiday_delay_hours=12.0,
        laytime_term=LaytimeTerm.WWD,
        demurrage_rate_per_day_usd=15000.0,
    )
    assert res.laytime_used_hours == 96.0
    assert res.demurrage_hours == 24.0
    assert res.demurrage_payable_usd == 15000.0
    assert res.dispatch_receivable_usd == 0.0
    assert res.settlement_party == "CHARTERER_OWES_DEMURRAGE"
    assert "DEMURRAGE INCURRED" in res.verdict


def test_laytime_dispatch_earned():
    """Verify dispatch calculation when loading finishes early (50% demurrage baseline)."""
    # Allowed: 72 hours
    # Net used: 48 hours -> Saved: 24 hours (1.0 day)
    # Demurrage: 20,000 USD/day -> Dispatch: 10,000 USD/day (50%)
    # Dispatch receivable: 10,000 USD
    res = CharterpartyLaytimeEngine.calculate_laytime(
        charter_ref="CP-02",
        vessel_name="MV FAST RUNNER",
        total_allowed_laytime_hours=72.0,
        nor_tendered_hour=14,  # Tendered afternoon -> starts next day 08:00
        nor_tendered_iso="2026-10-02T14:00:00",
        actual_working_hours=48.0,
        laytime_term=LaytimeTerm.SHINC,
        demurrage_rate_per_day_usd=20000.0,
    )
    assert res.time_saved_hours == 24.0
    assert res.dispatch_rate_per_day_usd == 10000.0
    assert res.dispatch_receivable_usd == 10000.0
    assert res.net_charter_settlement_usd == -10000.0
    assert res.settlement_party == "OWNER_OWES_DISPATCH"
    assert "DISPATCH EARNED" in res.verdict


# ===========================================================================
# 4. Phase 209: Seafarer Employment, Wages & Disability Tests
# ===========================================================================

def test_seafarer_wage_overtime_and_leave_audit():
    """Verify monthly overtime tiers (150%, 200%, 300%) and 2.5 days/month paid leave."""
    # Basic wage: 2,080 USD (~10 USD/hour on 208 hrs baseline)
    # Normal OT: 20 hrs * 10 * 1.5 = 300 USD
    # Rest OT: 10 hrs * 10 * 2.0 = 200 USD
    # Holiday OT: 5 hrs * 10 * 3.0 = 150 USD
    # Total monthly pay: 2,080 + 650 = 2,730 USD
    # 6 months service -> 15 leave days * (2,080 / 30 = 69.33) = 1,040 USD
    res = SeafarerMLCCompensationEngine.calculate_compensation(
        seafarer_name="TRAN DUC BO",
        rank=SeafarerRank.ABLE_SEAMAN,
        basic_monthly_wage_usd=2080.0,
        normal_overtime_hours=20.0,
        rest_day_overtime_hours=10.0,
        holiday_overtime_hours=5.0,
        months_of_service=6.0,
    )
    assert res.calculated_monthly_wage_usd == 2730.0
    assert res.leave_days_accrued == 15.0
    assert res.paid_leave_allowance_usd == 1040.0
    assert res.disability_compensation_usd == 0.0
    assert res.mlc_compliance_status == "COMPLIANT_WITH_MLC_2006_AND_VMC_2015"


def test_seafarer_severe_disability_compensation():
    """Verify permanent total disability compensation (36x monthly wage) and medical maintenance."""
    # Basic: 3,000 USD
    # Incapacity: 3 months full wage maintenance = 9,000 USD
    # Medical cost: 15,000 USD
    # Disability (Permanent Total > 80%): 36x 3,000 = 108,000 USD
    res = SeafarerMLCCompensationEngine.calculate_compensation(
        seafarer_name="LE VAN THANG",
        rank=SeafarerRank.CHIEF_ENGINEER,
        basic_monthly_wage_usd=3000.0,
        months_of_service=1.0,
        medical_treatment_cost_usd=15000.0,
        incapacity_months_during_treatment=3.0,
        disability_degree=DisabilityDegree.PERMANENT_TOTAL_ABOVE_80,
    )
    assert res.medical_wage_maintenance_usd == 9000.0
    assert res.disability_compensation_usd == 108000.0
    assert res.total_statutory_liability_usd == 3000.0 + 250.0 + 15000.0 + 9000.0 + 108000.0


# ===========================================================================
# 5. Phase 210: Marine Pilotage Liability Cap & Towage Contract Allocation Tests
# ===========================================================================

def test_pilotage_statutory_fee_liability_cap():
    """Verify pilotage organization liability is capped at service fee under VMC Art. 253."""
    # Loss: 500,000 USD, Pilot fee: 4,000 USD
    # Pilot liability strictly capped at 4,000 USD; Master/Owner bears residual 496,000 USD
    res = MarinePilotageAndTowageEngine.evaluate_liability(
        operation_id="PILOT-01",
        vessel_name="MV SEA VOYAGER",
        pilotage_fee_collected_usd=4000.0,
        total_marine_casualty_loss_usd=500000.0,
        pilot_error_proven=True,
    )
    assert res.statutory_pilot_liability_usd == 4000.0
    assert res.master_navigation_liability_usd == 496000.0
    assert any("VMC Art. 253" in art for art in res.applicable_articles)


def test_towage_allocation_under_towed_master_command():
    """Verify 100% liability assigned to towed vessel when under its Master's command (VMC Art. 263)."""
    res = MarinePilotageAndTowageEngine.evaluate_liability(
        operation_id="TOW-01",
        vessel_name="MV GIANT CARRIER",
        pilotage_fee_collected_usd=2000.0,
        total_marine_casualty_loss_usd=300000.0,
        pilot_error_proven=False,
        towage_type=TowageContractType.PORT_ASSIST_BERTHING,
        command_authority=FlotillaCommandType.TOWED_VESSEL_MASTER_COMMAND,
    )
    assert res.towed_vessel_allocated_liability_usd == 300000.0
    assert res.tug_allocated_liability_usd == 0.0


def test_towage_allocation_under_tug_master_command():
    """Verify 100% liability assigned to tug when under Tug Master's command (VMC Art. 263)."""
    res = MarinePilotageAndTowageEngine.evaluate_liability(
        operation_id="TOW-02",
        vessel_name="BARGE-99",
        pilotage_fee_collected_usd=0.0,
        total_marine_casualty_loss_usd=120000.0,
        pilot_error_proven=False,
        towage_type=TowageContractType.SEA_COASTAL_OCEAN_TOW,
        command_authority=FlotillaCommandType.TUG_MASTER_COMMAND,
    )
    assert res.tug_allocated_liability_usd == 120000.0
    assert res.towed_vessel_allocated_liability_usd == 0.0


# ===========================================================================
# 6. Typer CLI Integration Tests
# ===========================================================================

def test_cli_cargoclaim_assess():
    """Test CLI cargoclaim assess command."""
    app = build_app()
    result = runner.invoke(app, ["cargoclaim", "assess", "--claim-id", "CLI-01", "--packages", "300", "--weight", "9000", "--claimed-loss", "400000", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["claim_id"] == "CLI-01"
    assert data["applicable_statutory_limit_usd"] > 0
    assert data["carrier_payout_liability_usd"] > 0


def test_cli_laytime_calculate():
    """Test CLI laytime calculate command."""
    app = build_app()
    result = runner.invoke(app, ["laytime", "calculate", "--charter-ref", "CLI-CP-01", "--allowed-hours", "48", "--actual-hours", "60", "--weather-delay", "0", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["demurrage_hours"] == 12.0
    assert data["demurrage_payable_usd"] > 0


def test_cli_seafarerwage_audit():
    """Test CLI seafarerwage audit command."""
    app = build_app()
    result = runner.invoke(app, ["seafarerwage", "audit", "--name", "DOAN VAN HAU", "--basic-wage", "2500", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["seafarer_name"] == "DOAN VAN HAU"
    assert data["total_statutory_liability_usd"] >= 2500.0


def test_cli_towagepilot_assess():
    """Test CLI towagepilot assess command."""
    app = build_app()
    result = runner.invoke(app, ["towagepilot", "assess", "--op-id", "CLI-OPS-01", "--pilot-fee", "5000", "--loss", "200000", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["statutory_pilot_liability_usd"] == 5000.0
    assert data["master_navigation_liability_usd"] == 195000.0


# ===========================================================================
# 7. FastMCP Server Handler Tests
# ===========================================================================

def test_mcp_cargo_claim_handler():
    """Test FastMCP handle_cargo_claim_assess."""
    raw = mcp_srv.handle_cargo_claim_assess({
        "claim_id": "MCP-CLM-01",
        "number_of_packages": 200,
        "gross_weight_kg": 5000.0,
        "claimed_loss_usd": 150000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["claim_id"] == "MCP-CLM-01"
    assert res["applicable_statutory_limit_usd"] > 0


def test_mcp_laytime_handler():
    """Test FastMCP handle_laytime_calculate."""
    raw = mcp_srv.handle_laytime_calculate({
        "charter_ref": "MCP-CP-01",
        "total_allowed_laytime_hours": 72.0,
        "actual_working_hours": 96.0,
        "weather_delay_hours": 0.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["demurrage_hours"] == 24.0


def test_mcp_seafarer_wage_handler():
    """Test FastMCP handle_seafarer_wage_audit."""
    raw = mcp_srv.handle_seafarer_wage_audit({
        "seafarer_name": "VU VAN THANH",
        "basic_monthly_wage_usd": 2200.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["seafarer_name"] == "VU VAN THANH"


def test_mcp_pilotage_towage_handler():
    """Test FastMCP handle_pilotage_towage_assess."""
    raw = mcp_srv.handle_pilotage_towage_assess({
        "operation_id": "MCP-PILOT-01",
        "pilotage_fee_collected_usd": 3000.0,
        "total_marine_casualty_loss_usd": 100000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["statutory_pilot_liability_usd"] == 3000.0
