"""Tests for Phases 183-186 Vietnam Maritime Operations, Pilotage, Ship Agency, P&I & Tokyo MOU PSC Suite."""

import ast
import json
import pytest
from typer.testing import CliRunner

from src.core.maritime_operations_engine import (
    PilotageArea,
    TugboatClass,
    PilotageTugboatTariffEngine,
    ShipAgencyCrewMLCEngine,
    MarineInsuranceRiskEngine,
    PortStateControlPSCEngine,
    PSCShipRiskProfile,
    PSCFlagStateStatus,
    PSCDetentionAction,
    SeafarerRank,
    DailyRestLog,
    MLCComplianceStatus,
    MarineInsuranceClaimType,
)
from src.cli.commands.maritime_operations_command import (
    pilotage_app,
    shipagency_app,
    marineins_app,
    psc_app,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# AST Purity Test
# ---------------------------------------------------------------------------


def test_maritime_operations_engine_ast_purity():
    """Verify src/core/maritime_operations_engine.py has zero third-party dependencies."""
    engine_path = "src/core/maritime_operations_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_path)

    allowed_modules = {
        "dataclasses",
        "enum",
        "math",
        "typing",
        "datetime",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                assert root_pkg in allowed_modules, f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_modules, f"Forbidden import from: {node.module}"


# ---------------------------------------------------------------------------
# Phase 183: Maritime Pilotage & Tugboat Assistance Tariffs
# ---------------------------------------------------------------------------


def test_pilotage_tariff_calculation_international():
    """Test standard international vessel pilotage calculation with minimum GT rule."""
    res = PilotageTugboatTariffEngine.calculate_pilotage(
        vessel_gt=1500.0,  # Below 2,000 GT min threshold for international
        distance_nm=10.0,
        area=PilotageArea.AREA_III,
        is_international=True,
        is_night_shift=False,
    )
    assert res.billed_gt == 2000.0
    assert res.total_pilotage_fee_usd > 0
    assert res.surcharge_multiplier == 1.0


def test_pilotage_tariff_surcharges():
    """Test dead ship and night pilotage surcharges."""
    # Dead ship (+150% -> 2.50x)
    dead_res = PilotageTugboatTariffEngine.calculate_pilotage(
        vessel_gt=20000.0,
        distance_nm=15.0,
        area=PilotageArea.AREA_I,
        is_international=True,
        is_dead_ship=True,
    )
    assert dead_res.surcharge_multiplier == 2.50

    # Night shift (+50% -> 1.50x) & Hazardous cargo (+10% -> 1.65x)
    night_res = PilotageTugboatTariffEngine.calculate_pilotage(
        vessel_gt=20000.0,
        distance_nm=15.0,
        area=PilotageArea.AREA_I,
        is_international=True,
        is_night_shift=True,
        is_hazardous_cargo=True,
        detention_hours=3.5,  # 3.5 - 1.0 free = 2.5 billable * $10 = $25
    )
    assert round(night_res.surcharge_multiplier, 2) == 1.65
    assert night_res.detention_fee_usd == 25.0


def test_tugboat_assistance_calculation():
    """Test tugboat assistance with minimum 2-hour rule and holiday surcharge."""
    res = PilotageTugboatTariffEngine.calculate_tugboat_assistance(
        vessel_gt=30000.0,
        vessel_loa_meters=185.0,
        tugs_request=[
            {"tug_class": "CLASS_C", "quantity": 2, "duration_hours": 1.5},
        ],
        is_holiday_or_weekend=True,  # +30%
        is_dead_ship_escort=False,
    )
    assert res.surcharge_multiplier == 1.30
    assert res.tugs[0].duration_hours == 2.0  # Min 2-hour rule applied
    assert res.total_tugboat_fee_usd == round(2 * 2.0 * 210.0 * 1.30, 2)


# ---------------------------------------------------------------------------
# Phase 184: Ship Agency Husbandry & Seafarer MLC 2006 Compliance
# ---------------------------------------------------------------------------


def test_shipagency_disbursement_calculation():
    """Test ship agency disbursement with prolonged stay and CTM commission."""
    res = ShipAgencyCrewMLCEngine.calculate_agency_disbursement(
        vessel_name="MV MEKONG TRANSPORTER",
        vessel_gt=30000.0,
        port_stay_days=5,  # 3 base + 2 prolonged ($150/day = $300)
        crew_changes_count=4,  # 4 * $100 = $400
        ctm_amount_usd=20000.0,  # 1.5% = $300
    )
    assert res.base_agency_fee_usd == 1500.0
    assert res.extra_day_husbandry_usd == 300.0
    assert res.ctm_commission_usd == 300.0
    assert res.crew_change_fee_usd == 400.0
    assert res.total_agency_disbursement_usd == 1500 + 300 + 300 + 400


def test_seafarer_mlc_compliance():
    """Test seafarer rest hours audit and 11-month repatriation threshold."""
    # Compliant crew logs (7 days >= 10h/day, total 77h)
    compliant_logs = [
        DailyRestLog(log_date=f"2026-10-0{i}", total_rest_hours_24h=11.0, longest_continuous_rest_hours=7.0, rest_periods_count=2)
        for i in range(1, 8)
    ]
    pass_res = ShipAgencyCrewMLCEngine.assess_seafarer_mlc(
        seafarer_name="Tran Van A",
        rank=SeafarerRank.MASTER,
        consecutive_sea_days=200,
        daily_rest_logs=compliant_logs,
    )
    assert pass_res.status == MLCComplianceStatus.COMPLIANT
    assert pass_res.is_repatriation_due is False

    # Non-compliant crew logs (Rest < 10h/24h and Service > 330 days)
    fatigued_logs = [
        DailyRestLog(log_date=f"2026-10-0{i}", total_rest_hours_24h=8.0, longest_continuous_rest_hours=4.0, rest_periods_count=3)
        for i in range(1, 8)
    ]
    fail_res = ShipAgencyCrewMLCEngine.assess_seafarer_mlc(
        seafarer_name="Le Van B",
        rank=SeafarerRank.OFFICER,
        consecutive_sea_days=340,
        daily_rest_logs=fatigued_logs,
    )
    assert fail_res.status == MLCComplianceStatus.MANDATORY_REPATRIATION
    assert fail_res.is_repatriation_due is True
    assert len(fail_res.violations) >= 3


# ---------------------------------------------------------------------------
# Phase 185: Marine Insurance (H&M / P&I) & Constructive Total Loss
# ---------------------------------------------------------------------------


def test_hull_insurance_claim_and_ctl():
    """Test H&M claim assessment and Constructive Total Loss (CTL >= 80%)."""
    # Partial Loss
    partial_res = MarineInsuranceRiskEngine.assess_hull_claim(
        policy_id="POL-001",
        agreed_insured_value_usd=10000000.0,
        estimated_repair_and_salvage_usd=500000.0,
        policy_deductible_usd=50000.0,
    )
    assert partial_res.is_constructive_total_loss is False
    assert partial_res.net_payable_claim_usd == 450000.0
    assert partial_res.loss_ratio_percent == 5.0
    assert partial_res.claim_type == MarineInsuranceClaimType.PARTICULAR_AVERAGE

    # Constructive Total Loss
    ctl_res = MarineInsuranceRiskEngine.assess_hull_claim(
        policy_id="POL-002",
        agreed_insured_value_usd=10000000.0,
        estimated_repair_and_salvage_usd=8500000.0,
        policy_deductible_usd=50000.0,
        casualty_date_iso="2026-08-01",
        assessment_date_iso="2026-09-01",
    )
    assert ctl_res.is_constructive_total_loss is True
    assert ctl_res.loss_ratio_percent == 85.0
    assert ctl_res.net_payable_claim_usd == 10000000.0  # Full agreed value payable on CTL
    assert ctl_res.notice_deadline_days_remaining is not None
    assert ctl_res.notice_deadline_days_remaining < 180


def test_pi_bunker_pollution_liability_limit():
    """Test Bunkers Convention 2001 tiered SDR pollution liability limit."""
    res = MarineInsuranceRiskEngine.calculate_pi_bunker_pollution_limit(
        vessel_gt=50000.0,
        sdr_usd_rate=1.33,
    )
    # Calculation check:
    # Up to 2,000 GT: 1,510,000 SDR
    # 2,001 to 30,000 GT (28,000 GT * 604 SDR): 16,912,000 SDR
    # 30,001 to 50,000 GT (20,000 GT * 453 SDR): 9,060,000 SDR
    # Total = 1,510,000 + 16,912,000 + 9,060,000 = 27,482,000 SDR
    assert res.liability_limit_sdr == 27482000.0
    assert res.liability_limit_usd == 27482000.0 * 1.33
    assert res.is_compulsory_clc_cert_required is True


# ---------------------------------------------------------------------------
# Phase 186: Port State Control (PSC) Tokyo MOU NIR & Deficiency Matrix
# ---------------------------------------------------------------------------


def test_tokyo_mou_ship_risk_profile_srs_hrs():
    """Test Tokyo MOU New Inspection Regime (NIR) Ship Risk Profile scoring."""
    # Standard Risk Ship (SRS)
    srs_res = PortStateControlPSCEngine.evaluate_ship_risk_profile(
        vessel_imo="9123456",
        vessel_type="GENERAL_CARGO",
        vessel_age_years=15,  # 15y (>12) -> +1 pt; GENERAL_CARGO -> +1 pt -> Total 2 pts (SRS)
        flag_status=PSCFlagStateStatus.WHITE_LIST,
        ro_performance_low=False,
        detentions_last_36m=0,
        deficiencies_last_36m=2,
    )
    assert srs_res.risk_profile == PSCShipRiskProfile.SRS
    assert "5 to 8 months" in srs_res.next_inspection_window_months

    # High Risk Ship (HRS) due to Black List flag & 2 detentions
    hrs_res = PortStateControlPSCEngine.evaluate_ship_risk_profile(
        vessel_imo="9654321",
        vessel_type="CHEMICAL_TANKER",
        vessel_age_years=16,
        flag_status=PSCFlagStateStatus.BLACK_LIST_HIGH,
        ro_performance_low=True,
        detentions_last_36m=2,
        deficiencies_last_36m=12,
    )
    assert hrs_res.risk_profile == PSCShipRiskProfile.HRS
    assert hrs_res.total_risk_points >= 6
    assert "2 to 4 months" in hrs_res.next_inspection_window_months


def test_psc_deficiency_assessment():
    """Test Tokyo MOU deficiency assessment and Code 30 detention triggering."""
    res = PortStateControlPSCEngine.evaluate_deficiencies(
        vessel_imo="9123456",
        deficiency_codes=["07105", "14104", "01101"],
        has_solas_fire_or_lifesaving_breach=True,
    )
    assert res.is_code_30_detention is True
    assert res.recommended_action == PSCDetentionAction.CODE_30_DETENTION
    assert "Code 30" in res.action_notes


# ---------------------------------------------------------------------------
# CLI Commands Execution Tests
# ---------------------------------------------------------------------------


def test_cli_pilotage_commands():
    """Test pilotage and tugboat CLI commands with JSON output."""
    result = runner.invoke(
        pilotage_app,
        ["tariff", "25000", "20", "--area", "AREA_III", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["vessel_gt"] == 25000.0

    result_tug = runner.invoke(
        pilotage_app,
        ["tugboat", "35000", "200", "--class", "CLASS_D", "--hours", "3", "--json"],
    )
    assert result_tug.exit_code == 0
    data_tug = json.loads(result_tug.stdout)
    assert data_tug["vessel_gt"] == 35000.0


def test_cli_shipagency_commands():
    """Test ship agency disbursement and MLC check CLI commands."""
    result_disb = runner.invoke(
        shipagency_app,
        ["disbursement", "MV TEST", "18000", "--days", "4", "--json"],
    )
    assert result_disb.exit_code == 0
    data_disb = json.loads(result_disb.stdout)
    assert data_disb["port_stay_days"] == 4

    result_mlc = runner.invoke(
        shipagency_app,
        ["mlc-check", "Nguyen Van C", "--rank", "MASTER", "--sea-days", "150", "--rest-24h", "11.0", "--block", "7.0", "--json"],
    )
    assert result_mlc.exit_code == 0
    data_mlc = json.loads(result_mlc.stdout)
    assert data_mlc["status"] == "COMPLIANT"


def test_cli_marineins_commands():
    """Test marine insurance H&M and P&I CLI commands."""
    result_claim = runner.invoke(
        marineins_app,
        ["hull-claim", "POL-100", "5000000", "4200000", "--json"],
    )
    assert result_claim.exit_code == 0
    data_claim = json.loads(result_claim.stdout)
    assert data_claim["is_constructive_total_loss"] is True

    result_pi = runner.invoke(
        marineins_app,
        ["pi-pollution", "10000", "--json"],
    )
    assert result_pi.exit_code == 0
    data_pi = json.loads(result_pi.stdout)
    assert data_pi["liability_limit_sdr"] > 0


def test_cli_psc_commands():
    """Test PSC risk profile and deficiency CLI commands."""
    result_srp = runner.invoke(
        psc_app,
        ["risk-profile", "9988776", "BULK_CARRIER", "8", "--json"],
    )
    assert result_srp.exit_code == 0
    data_srp = json.loads(result_srp.stdout)
    assert data_srp["vessel_imo"] == "9988776"

    result_def = runner.invoke(
        psc_app,
        ["deficiency", "9988776", "--codes", "07105,01101", "--solas-fire", "--json"],
    )
    assert result_def.exit_code == 0
    data_def = json.loads(result_def.stdout)
    assert data_def["is_code_30_detention"] is True
