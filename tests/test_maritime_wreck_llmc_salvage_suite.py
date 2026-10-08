"""Comprehensive test suite for Maritime Wreck Removal, LLMC, Marine Salvage & Sanctions (Phases 199-202).

Validates:
- AST zero-dependency invariant (Pure Python Standard Library only).
- Phase 199: Maritime Wreck Removal, 30/60d Deadlines & Auction Waterfall (VMC Arts. 109-114).
- Phase 200: Limitation of Liability for Maritime Claims - LLMC (VMC Arts. 299-309).
- Phase 201: Marine Salvage, LOF 2024 & SCOPIC Remuneration (VMC Arts. 280-294).
- Phase 202: Port State Administrative Penalties & Sanctions (Decrees 162/2016 & 123/2021).
- CLI commands and aliases via Typer CliRunner.
- FastMCP tool handler invocations.
"""

import ast
import json
from typer.testing import CliRunner

from src.core.maritime_wreck_llmc_salvage_engine import (
    WreckStatus,
    MaritimeWreckRemovalEngine,
    MaritimeLLMCEngine,
    SalvageContractType,
    MaritimeSalvageSCOPICEngine,
    MaritimeViolationType,
    EntityType,
    MaritimePenaltiesEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_wreck_removal_audit,
    handle_llmc_calculate,
    handle_salvage_scopic_evaluate,
    handle_maritime_penalty_assess,
)


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================

def test_ast_zero_external_dependencies():
    """Ensure engine module strictly uses Python standard library only."""
    with open("src/core/maritime_wreck_llmc_salvage_engine.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    allowed_modules = {
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
                assert root_pkg in allowed_modules, f"Disallowed external import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_modules, f"Disallowed external import from: {node.module}"


# ===========================================================================
# 2. Phase 199: Wreck Removal & Auction Waterfall Tests
# ===========================================================================

def test_wreck_removal_timely_salvage():
    """Verify timely submission of salvage plan (<30d) and timely commencement (<60d)."""
    eval_res = MaritimeWreckRemovalEngine.evaluate_wreck(
        vessel_name="MV SEA DRAGON",
        gross_tonnage=4500.0,
        location_description="Vung Tau Fairway Buoy #0",
        notice_date_iso="2026-08-01",
        assessment_date_iso="2026-09-15",
        plan_submitted=True,
        plan_submission_date_iso="2026-08-20",  # 19 days -> Pass (< 30)
        salvage_commenced=True,
        salvage_start_date_iso="2026-09-10",  # 40 days -> Pass (< 60)
        has_valid_wrc_insurance=True,
    )

    assert eval_res.is_plan_timely is True
    assert eval_res.is_commencement_timely is True
    assert eval_res.forced_salvage_triggered is False
    assert eval_res.wrc_insurance_valid is True
    assert eval_res.status == WreckStatus.SALVAGE_COMMENCED_60D
    assert "SALVAGE IN PROGRESS" in eval_res.verdict


def test_wreck_removal_defaulted_forced_salvage():
    """Verify forced salvage triggered when owner fails 30d plan or 60d commencement deadline."""
    eval_late = MaritimeWreckRemovalEngine.evaluate_wreck(
        vessel_name="MV SUNKEN BARGE",
        gross_tonnage=1200.0,
        location_description="Soai Rap Anchorage",
        notice_date_iso="2026-06-01",
        assessment_date_iso="2026-08-15",  # 75 days
        plan_submitted=False,
        plan_submission_date_iso=None,
        salvage_commenced=False,
        salvage_start_date_iso=None,
        has_valid_wrc_insurance=False,
    )

    assert eval_late.is_plan_timely is False
    assert eval_late.is_commencement_timely is False
    assert eval_late.forced_salvage_triggered is True
    assert eval_late.wrc_insurance_valid is False
    assert eval_late.status == WreckStatus.DEFAULTED_FORCED_SALVAGE
    assert "FORCED SALVAGE TRIGGERED" in eval_late.verdict


def test_wreck_removal_auction_waterfall_and_escrow():
    """Verify auction waterfall proceeds deduction and 1-year escrow ceiling."""
    eval_auction = MaritimeWreckRemovalEngine.evaluate_wreck(
        vessel_name="MV ABANDONED HULL",
        gross_tonnage=3500.0,
        location_description="Hai Phong Estuary",
        notice_date_iso="2025-06-01",
        assessment_date_iso="2026-05-01",  # 335 days
        plan_submitted=False,
        salvage_commenced=False,
        auction_gross_proceeds_vnd=50_000_000_000.0,
        direct_salvage_cost_vnd=20_000_000_000.0,
        port_marking_dues_vnd=3_000_000_000.0,
        admin_storage_cost_vnd=2_000_000_000.0,
    )

    # Net surplus: 50B - (20B + 3B + 2B) = 25B VND
    assert eval_auction.net_auction_surplus_vnd == 25_000_000_000.0
    assert eval_auction.status == WreckStatus.AUCTIONED
    assert eval_auction.escrow_days_remaining == 365 - eval_auction.days_since_notice


def test_wreck_removal_surplus_escheatment():
    """Verify surplus escheatment to State Treasury after 365 days."""
    eval_escheat = MaritimeWreckRemovalEngine.evaluate_wreck(
        vessel_name="MV DERELICT",
        gross_tonnage=2000.0,
        location_description="Quy Nhon Harbour",
        notice_date_iso="2024-01-01",
        assessment_date_iso="2026-01-02",  # > 365 days
        auction_gross_proceeds_vnd=10_000_000_000.0,
        direct_salvage_cost_vnd=5_000_000_000.0,
    )

    assert eval_escheat.escrow_days_remaining == 0
    assert eval_escheat.status == WreckStatus.SURPLUS_ESCHEATED
    assert "ESCHEATED" in eval_escheat.verdict


# ===========================================================================
# 3. Phase 200: LLMC Limitation of Liability Tests
# ===========================================================================

def test_llmc_standard_tonnage_calculation():
    """Verify statutory limitation funds for 25,000 GT vessel under VMC Arts. 302-303."""
    res = MaritimeLLMCEngine.calculate_limits(
        vessel_name="MV OCEAN FREIGHTER",
        gross_tonnage=25000.0,
        actual_life_claims_sdr=20_000_000.0,
        actual_property_claims_sdr=15_000_000.0,
        sdr_to_vnd_rate=33500.0,
        has_intentional_act_or_recklessness=False,
        fund_constituted=True,
    )

    # Life Limit: 3,020,000 + (25,000 - 2,000) * 1,208 = 30,804,000 SDR
    expected_life_sdr = 3_020_000.0 + (23_000.0 * 1_208.0)
    assert res.life_injury_limit_sdr == expected_life_sdr
    assert res.life_injury_limit_sdr == 30_804_000.0

    # Property Limit: 1,510,000 + (25,000 - 2,000) * 604 = 15,402,000 SDR
    expected_prop_sdr = 1_510_000.0 + (23_000.0 * 604.0)
    assert res.property_claims_limit_sdr == expected_prop_sdr
    assert res.property_claims_limit_sdr == 15_402_000.0

    assert res.total_fund_limit_sdr == expected_life_sdr + expected_prop_sdr
    assert res.can_limit_liability is True
    assert res.vessel_arrest_barred is True
    assert res.rollover_to_property_sdr == 0.0  # claims (20M) < limit (30.8M)


def test_llmc_concurrency_rollover():
    """Verify personal injury claims rollover into property fund under Art. 304."""
    res_rollover = MaritimeLLMCEngine.calculate_limits(
        vessel_name="MV PASSENGER FERRY",
        gross_tonnage=5000.0,
        actual_life_claims_sdr=15_000_000.0,  # exceeds life fund
        actual_property_claims_sdr=5_000_000.0,
    )

    # Life Fund for 5000 GT: 3,020,000 + 3,000 * 1,208 = 6,644,000 SDR
    # Rollover: 15,000,000 - 6,644,000 = 8,356,000 SDR
    assert res_rollover.life_injury_limit_sdr == 6_644_000.0
    assert res_rollover.rollover_to_property_sdr == 8_356_000.0
    assert res_rollover.total_effective_property_claims_sdr == 5_000_000.0 + 8_356_000.0
    assert res_rollover.effective_property_fund_sdr > 0.0


def test_llmc_conduct_barring_limitation():
    """Verify limitation broken by intentional act or recklessness under Art. 300(2)."""
    res_barred = MaritimeLLMCEngine.calculate_limits(
        vessel_name="MV ROGUE RUNNER",
        gross_tonnage=10000.0,
        has_intentional_act_or_recklessness=True,
        fund_constituted=True,
    )

    assert res_barred.can_limit_liability is False
    assert res_barred.vessel_arrest_barred is False
    assert "LIMITATION BROKEN" in res_barred.verdict


def test_llmc_large_tonnage_tiers():
    """Verify tier calculations for very large ships (>70,000 GT)."""
    res_vlc = MaritimeLLMCEngine.calculate_limits(
        vessel_name="MV MEKONG TITAN",
        gross_tonnage=100000.0,
    )

    # 100,000 GT spans all brackets:
    # 2,000 base + 28,000 tier2 + 40,000 tier3 + 30,000 tier4
    assert res_vlc.life_injury_limit_sdr > 70_000_000.0
    assert res_vlc.property_claims_limit_sdr > 35_000_000.0


# ===========================================================================
# 4. Phase 201: Marine Salvage & SCOPIC Tests
# ===========================================================================

def test_salvage_article13_no_cure_no_pay():
    """Verify Article 13 award bounded by salved fund value and failed salvage zero reward."""
    # Useful result achieved
    res_ok = MaritimeSalvageSCOPICEngine.evaluate_salvage(
        contract_type=SalvageContractType.NO_CURE_NO_PAY_ART13,
        ship_salved_val_usd=4_000_000.0,
        cargo_salved_val_usd=2_000_000.0,
        freight_bunker_salved_val_usd=500_000.0,
        prior_liens_usd=200_000.0,
        useful_result=True,
        base_salvor_expenses_usd=300_000.0,
    )
    # Fund = 4M + 2M + 0.5M - 0.2M = 6.3M USD
    assert res_ok.salved_fund_usd == 6_300_000.0
    assert res_ok.final_payable_salvor_usd > 0.0
    assert res_ok.final_payable_salvor_usd <= res_ok.salved_fund_usd

    # Failed salvage (No cure - No pay)
    res_failed = MaritimeSalvageSCOPICEngine.evaluate_salvage(
        contract_type=SalvageContractType.NO_CURE_NO_PAY_ART13,
        ship_salved_val_usd=4_000_000.0,
        useful_result=False,
    )
    assert res_failed.final_payable_salvor_usd == 0.0
    assert "ZERO SALVAGE REWARD" in res_failed.verdict


def test_salvage_scopic_remuneration_exceeds_art13():
    """Verify SCOPIC tariff remuneration (+25% bonus) when SCOPIC exceeds Article 13."""
    res_scopic = MaritimeSalvageSCOPICEngine.evaluate_salvage(
        contract_type=SalvageContractType.SCOPIC_INVOKED,
        ship_salved_val_usd=1_000_000.0,
        cargo_salved_val_usd=500_000.0,
        freight_bunker_salved_val_usd=100_000.0,
        prior_liens_usd=50_000.0,
        useful_result=True,
        scopic_tariff_costs_usd=800_000.0,
        out_of_pocket_expenses_usd=200_000.0,
    )

    # SCOPIC = (800k + 200k) * 1.25 = 1,250,000 USD
    assert res_scopic.scopic_remuneration_usd == 1_250_000.0
    assert res_scopic.subclause6_discount_usd == 0.0
    assert res_scopic.final_payable_salvor_usd == 1_250_000.0
    assert "SCOPIC REMUNERATION PAYABLE" in res_scopic.verdict


def test_salvage_scopic_subclause6_clawback_discount():
    """Verify Sub-Clause 6 25% discount when Article 13 award exceeds SCOPIC remuneration."""
    res_clawback = MaritimeSalvageSCOPICEngine.evaluate_salvage(
        contract_type=SalvageContractType.SCOPIC_INVOKED,
        ship_salved_val_usd=10_000_000.0,
        cargo_salved_val_usd=5_000_000.0,
        freight_bunker_salved_val_usd=1_000_000.0,
        useful_result=True,
        base_salvor_expenses_usd=500_000.0,
        scopic_tariff_costs_usd=400_000.0,
        out_of_pocket_expenses_usd=100_000.0,
    )

    # SCOPIC = (400k + 100k) * 1.25 = 625,000 USD
    # Art 13 is significantly higher due to large salved fund (16M USD)
    assert res_clawback.article13_assessed_reward_usd > res_clawback.scopic_remuneration_usd
    assert res_clawback.subclause6_discount_usd > 0.0
    # Final payable = Art13 - discount
    assert res_clawback.final_payable_salvor_usd == (
        res_clawback.article13_assessed_reward_usd - res_clawback.subclause6_discount_usd
    )
    assert "SUB-CLAUSE 6 DISCOUNT" in res_clawback.verdict


# ===========================================================================
# 5. Phase 202: Port State Administrative Penalties Tests
# ===========================================================================

def test_maritime_penalties_organization_vs_individual():
    """Verify fine doubles for organization vs individual (50% reduction for individual)."""
    res_org = MaritimePenaltiesEngine.assess_penalties(
        vessel_name="MV CARRIER",
        violator_name="Shipping Corp",
        entity_type=EntityType.ORGANIZATION,
        violations=[MaritimeViolationType.NO_PILOT],
        severity_ratio=0.5,
    )

    res_ind = MaritimePenaltiesEngine.assess_penalties(
        vessel_name="MV CARRIER",
        violator_name="Captain Nguyen",
        entity_type=EntityType.INDIVIDUAL,
        violations=[MaritimeViolationType.NO_PILOT],
        severity_ratio=0.5,
    )

    # NO_PILOT: 40M - 80M VND -> median = 60M VND for Org, 30M VND for Ind
    assert res_org.total_fine_vnd == 60_000_000.0
    assert res_ind.total_fine_vnd == 30_000_000.0


def test_maritime_penalties_departure_clearance_blocked_and_granted():
    """Verify departure clearance blocked until treasury receipt or bank guarantee."""
    res_blocked = MaritimePenaltiesEngine.assess_penalties(
        vessel_name="MV DETAINED",
        violator_name="Global Line Ltd",
        entity_type=EntityType.ORGANIZATION,
        violations=[MaritimeViolationType.ILLEGAL_DISCHARGE],
        has_kbnn_treasury_receipt=False,
        has_bank_or_pi_guarantee=False,
    )
    assert res_blocked.clearance_status == "CLEARANCE_BLOCKED"
    assert "DEPARTURE CLEARANCE REFUSED" in res_blocked.recommendation

    # Clearance granted via KBNN receipt
    res_cleared_receipt = MaritimePenaltiesEngine.assess_penalties(
        vessel_name="MV DETAINED",
        violator_name="Global Line Ltd",
        entity_type=EntityType.ORGANIZATION,
        violations=[MaritimeViolationType.ILLEGAL_DISCHARGE],
        has_kbnn_treasury_receipt=True,
    )
    assert res_cleared_receipt.clearance_status == "CLEARANCE_GRANTED"

    # Clearance granted via P&I guarantee
    res_cleared_guarantee = MaritimePenaltiesEngine.assess_penalties(
        vessel_name="MV DETAINED",
        violator_name="Global Line Ltd",
        entity_type=EntityType.ORGANIZATION,
        violations=[MaritimeViolationType.ILLEGAL_DISCHARGE],
        has_bank_or_pi_guarantee=True,
    )
    assert res_cleared_guarantee.clearance_status == "CLEARANCE_GRANTED"


# ===========================================================================
# 6. CLI Runner Invocation Tests
# ===========================================================================

def test_cli_wreck_commands():
    """Verify wreck and trucvot Typer CLI commands."""
    runner = CliRunner()
    app = build_app()

    res1 = runner.invoke(app, ["wreck", "evaluate", "--json"])
    assert res1.exit_code == 0
    data1 = json.loads(res1.stdout)
    assert data1["vessel_name"] == "MV SEA DRAGON"
    assert data1["status"] in ["SALVAGE_COMMENCED_60D", "REPORTED", "NOTICE_SERVED_30D"]

    res2 = runner.invoke(app, ["trucvot", "evaluate", "--json"])
    assert res2.exit_code == 0


def test_cli_llmc_commands():
    """Verify llmc and gioihanbt Typer CLI commands."""
    runner = CliRunner()
    app = build_app()

    res1 = runner.invoke(app, ["llmc", "calc", "--json"])
    assert res1.exit_code == 0
    data1 = json.loads(res1.stdout)
    assert data1["life_injury_limit_sdr"] > 0
    assert data1["can_limit_liability"] is True

    res2 = runner.invoke(app, ["gioihanbt", "calc", "--json"])
    assert res2.exit_code == 0


def test_cli_salvage_commands():
    """Verify salvage and cuuho Typer CLI commands."""
    runner = CliRunner()
    app = build_app()

    res1 = runner.invoke(app, ["salvage", "evaluate", "--json"])
    assert res1.exit_code == 0
    data1 = json.loads(res1.stdout)
    assert data1["contract_type"] == "SCOPIC_INVOKED"
    assert data1["final_payable_salvor_usd"] > 0

    res2 = runner.invoke(app, ["cuuho", "evaluate", "--json"])
    assert res2.exit_code == 0


def test_cli_maritimepen_commands():
    """Verify maritimepen and xuphatbien Typer CLI commands."""
    runner = CliRunner()
    app = build_app()

    res1 = runner.invoke(app, ["maritimepen", "assess", "--json"])
    assert res1.exit_code == 0
    data1 = json.loads(res1.stdout)
    assert data1["total_fine_vnd"] > 0
    assert data1["clearance_status"] == "CLEARANCE_BLOCKED"

    res2 = runner.invoke(app, ["xuphatbien", "assess", "--json"])
    assert res2.exit_code == 0


# ===========================================================================
# 7. FastMCP Handler Tests
# ===========================================================================

def test_mcp_wreck_removal_audit_handler():
    """Test handle_wreck_removal_audit FastMCP endpoint."""
    raw = handle_wreck_removal_audit({
        "vessel_name": "MV SEA DRAGON",
        "gross_tonnage": 4500.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["vessel_name"] == "MV SEA DRAGON"


def test_mcp_llmc_calculate_handler():
    """Test handle_llmc_calculate FastMCP endpoint."""
    raw = handle_llmc_calculate({
        "vessel_name": "MV OCEAN FREIGHTER",
        "gross_tonnage": 25000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["life_injury_limit_sdr"] > 0


def test_mcp_salvage_scopic_evaluate_handler():
    """Test handle_salvage_scopic_evaluate FastMCP endpoint."""
    raw = handle_salvage_scopic_evaluate({
        "contract_type": "SCOPIC_INVOKED",
        "ship_salved_val_usd": 3000000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["final_payable_salvor_usd"] > 0


def test_mcp_maritime_penalty_assess_handler():
    """Test handle_maritime_penalty_assess FastMCP endpoint."""
    raw = handle_maritime_penalty_assess({
        "vessel_name": "MV VIOLATOR",
        "violator_name": "Mekong Ocean Shipping Ltd",
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["clearance_status"] == "CLEARANCE_BLOCKED"


def test_mcp_invalid_args_handling():
    """Verify tool handlers return ok: False for invalid arguments."""
    assert json.loads(handle_wreck_removal_audit(None))["ok"] is False
    assert json.loads(handle_llmc_calculate(None))["ok"] is False
    assert json.loads(handle_salvage_scopic_evaluate(None))["ok"] is False
    assert json.loads(handle_maritime_penalty_assess(None))["ok"] is False
