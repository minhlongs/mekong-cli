# -*- coding: utf-8 -*-
"""Comprehensive Test Suite for Phases 255-258.

Phases Covered:
- Phase 255: Maritime Ship Agency & Husbandry Disbursements (PDA/FDA) Accounting
- Phase 256: Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement
- Phase 257: Seafarer Repatriation & Abandonment Financial Security Guarantee
- Phase 258: Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives
"""

import ast
import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.maritime_agency_salvage_abandonment_cleanport_engine import (
    AbandonmentTrigger,
    DisbursementCategory,
    DisbursementItem,
    HarborCraftPropulsion,
    MaritimeSalvageEngine,
    SalvedPropertyValues,
    SalvageContractRegime,
    SCOPICExpenseItem,
    SeafarerAbandonmentClaim,
    SeafarerAbandonmentEngine,
    ShipAgencyDisbursementEngine,
    GreenHarborCraftEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_ship_agency_reconcile,
    handle_salvage_settlement_evaluate,
    handle_seafarer_abandonment_adjudicate,
    handle_green_harbor_craft_evaluate,
)


# ==============================================================================
# 1. ZERO-DEPENDENCY AST ARCHITECTURAL INVARIANT TEST
# ==============================================================================

def test_core_engine_zero_dependencies():
    """Verify that core engine imports only Python standard library modules."""
    engine_path = Path("/Users/macbook/mekong-cli/src/core/maritime_agency_salvage_abandonment_cleanport_engine.py")
    assert engine_path.exists(), "Engine file must exist"

    tree = ast.parse(engine_path.read_text(encoding="utf-8"))
    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split(".")[0])

    stdlib_modules = {
        "__future__",
        "dataclasses",
        "enum",
        "math",
        "typing",
        "json",
        "datetime",
        "sys",
        "os",
    }
    invalid_imports = imported_modules - stdlib_modules
    assert not invalid_imports, f"Core engine has external dependencies: {invalid_imports}"


# ==============================================================================
# 2. PHASE 255: SHIP AGENCY PDA/FDA ENGINE TESTS
# ==============================================================================

def test_agency_fee_gt_brackets():
    """Verify GT bracket tiering and duration scaling for statutory agency fees."""
    # Under 5,000 GT
    fee_small = ShipAgencyDisbursementEngine.calculate_statutory_agency_fee(3000.0, port_stay_days=2)
    assert fee_small == 800.0

    # 5,000 - 15,000 GT
    fee_med = ShipAgencyDisbursementEngine.calculate_statutory_agency_fee(10000.0, port_stay_days=2)
    assert fee_med == 1100.0

    # 15,000 - 30,000 GT
    fee_large = ShipAgencyDisbursementEngine.calculate_statutory_agency_fee(25000.0, port_stay_days=2)
    assert fee_large == 1600.0

    # > 50,000 GT with extended stay (> 2 days)
    # Extra days = 4 - 2 = 2 days * 150.0 = 300.0
    fee_vlarge = ShipAgencyDisbursementEngine.calculate_statutory_agency_fee(65000.0, port_stay_days=4)
    assert fee_vlarge == (2800.0 + 300.0)

    # Tanker dangerous surcharge (1.2x)
    fee_tanker = ShipAgencyDisbursementEngine.calculate_statutory_agency_fee(25000.0, port_stay_days=2, is_tanker_or_dangerous=True)
    assert fee_tanker == (1600.0 * 1.20)


def test_ship_agency_reconcile_refund():
    """Verify PDA vs FDA reconciliation resulting in refund to principal."""
    items = [
        DisbursementItem("D-01", DisbursementCategory.PORT_DUES, "Port dues", 10000.0, 9500.0),
        DisbursementItem("D-02", DisbursementCategory.PILOTAGE, "Pilotage", 4000.0, 3800.0),
        DisbursementItem("D-03", DisbursementCategory.TUGBOAT_SERVICES, "Tugs", 8000.0, 7500.0),
    ]

    report = ShipAgencyDisbursementEngine.reconcile_pda_fda(
        vessel_name="MV_SEA_OCEAN",
        call_id="CALL-001",
        port_name="Cảng Cái Mép",
        gross_tonnage=20000.0,
        advance_deposit_received_usd=30000.0,
        items=items,
        port_stay_days=2,
        collected_freight_usd=100000.0,
        freight_commission_rate_pct=1.25,
    )

    # Actual FDA = 9500 + 3800 + 7500 = 20,800 USD
    # Agency fee = 1600 USD (15k-30k GT)
    # Freight commission = 100,000 * 1.25% = 1250 USD
    # Net disbursement = 20,800 + 1,600 + 1,250 = 23,650 USD
    # Balance = 30,000 - 23,650 = 6,350 USD
    assert report.total_actual_fda_usd == 20800.0
    assert report.statutory_agency_fee_usd == 1600.0
    assert report.freight_commission_usd == 1250.0
    assert report.net_disbursement_total_usd == 23650.0
    assert report.balance_settlement_usd == 6350.0
    assert report.settlement_status == "REFUND_TO_PRINCIPAL"


def test_ship_agency_reconcile_supplementary():
    """Verify FDA exceeding PDA requiring top-up payment from principal."""
    items = [
        DisbursementItem("D-01", DisbursementCategory.PORT_DUES, "Port dues", 20000.0, 25000.0),
        DisbursementItem("D-02", DisbursementCategory.MISCELLANEOUS_PORT_EXPENSES, "Emergency launch", 5000.0, 15000.0),
    ]

    report = ShipAgencyDisbursementEngine.reconcile_pda_fda(
        vessel_name="MV_OVERSPENT",
        call_id="CALL-002",
        port_name="Cảng Hải Phòng",
        gross_tonnage=12000.0,
        advance_deposit_received_usd=30000.0,
        items=items,
        port_stay_days=3,  # 1100 + 150 = 1250 agency fee
    )

    # Actual FDA = 40,000 + 1,250 = 41,250
    # Balance = 30,000 - 41,250 = -11,250
    assert report.balance_settlement_usd < 0
    assert report.settlement_status == "SUPPLEMENTARY_DUE_FROM_PRINCIPAL"


# ==============================================================================
# 3. PHASE 256: MARITIME SALVAGE & SCOPIC SETTLEMENT TESTS
# ==============================================================================

def test_salved_property_fund_calculation():
    """Verify net salved fund deduction of damage repair costs."""
    props = SalvedPropertyValues(
        sound_ship_value_usd=10000000.0,
        damage_repair_costs_usd=2500000.0,
        cargo_cif_value_usd=5000000.0,
        unpaid_freight_at_risk_usd=500000.0,
    )
    # Net ship = 7.5M + 5M cargo + 0.5M freight = 13M
    assert props.net_salved_fund_usd == 13000000.0


def test_salvage_settlement_traditional_art13():
    """Verify traditional LOF Article 13 award without SCOPIC."""
    props = SalvedPropertyValues(
        sound_ship_value_usd=15000000.0,
        damage_repair_costs_usd=3000000.0,
        cargo_cif_value_usd=8000000.0,
        unpaid_freight_at_risk_usd=500000.0,
    )
    # Net fund = 12M + 8M + 0.5M = 20.5M
    res = MaritimeSalvageEngine.calculate_salvage_settlement(
        property_values=props,
        assessed_art13_award_percentage=10.0,
        regime=SalvageContractRegime.LOF_ARTICLE_13_ONLY,
    )

    assert res.net_salved_fund_usd == 20500000.0
    assert res.article_13_assessed_award_usd == 2050000.0
    assert res.final_salvor_remuneration_usd == 2050000.0
    assert res.property_underwriters_liability_usd == 2050000.0
    assert res.pni_club_liability_usd == 0.0


def test_salvage_settlement_scopic_penalty_discount():
    """Verify SCOPIC Sub-clause 7 discount penalty when Art 13 > SCOPIC."""
    props = SalvedPropertyValues(
        sound_ship_value_usd=20000000.0,
        damage_repair_costs_usd=2000000.0,
        cargo_cif_value_usd=10000000.0,
        unpaid_freight_at_risk_usd=1000000.0,
    )
    # Net fund = 18M + 10M + 1M = 29M
    # Art 13 award at 10% = 2,900,000 USD
    # SCOPIC items: 10 days * 30,000 USD/day = 300,000 USD
    # SCOPIC bonus uplift (+25%) = 75,000 USD => total SCOPIC = 375,000 USD
    # Art 13 (2.9M) > SCOPIC (375k) => Difference = 2,525,000 USD
    # Discount penalty = 25% * 2,525,000 = 631,250 USD
    # Final Salvor Remuneration = 2.9M - 631,250 = 2,268,750 USD
    scopic_items = [SCOPICExpenseItem("Salvage Tug 100T BP", 30000.0, 10.0)]

    res = MaritimeSalvageEngine.calculate_salvage_settlement(
        property_values=props,
        assessed_art13_award_percentage=10.0,
        regime=SalvageContractRegime.SCOPIC_INVOKED,
        scopic_items=scopic_items,
    )

    assert res.total_scopic_remuneration_usd == 375000.0
    assert res.article_13_discount_penalty_usd == pytest.approx(631250.0, rel=1e-3)
    assert res.final_salvor_remuneration_usd == pytest.approx(2268750.0, rel=1e-3)
    assert res.pni_club_liability_usd == 0.0  # Property underwriters bear the Art 13 award


def test_salvage_settlement_scopic_exceeds_art13():
    """Verify P&I Club liability when SCOPIC remuneration exceeds Article 13 award."""
    props = SalvedPropertyValues(
        sound_ship_value_usd=2000000.0,
        damage_repair_costs_usd=1000000.0,
        cargo_cif_value_usd=500000.0,
        unpaid_freight_at_risk_usd=100000.0,
    )
    # Net fund = 1M + 500k + 100k = 1.6M
    # Art 13 award at 10% = 160,000 USD
    # SCOPIC items: 20 days * 25,000 USD = 500,000 USD
    # Uplift (+25%) = 125,000 USD => Total SCOPIC = 625,000 USD
    # SCOPIC (625k) > Art 13 (160k)
    # Final salvor remuneration = 625,000 USD
    # Property underwriters pay Art 13 = 160,000 USD
    # P&I Club pays excess = 625k - 160k = 465,000 USD
    scopic_items = [SCOPICExpenseItem("Heavy Crane Barge", 25000.0, 20.0)]

    res = MaritimeSalvageEngine.calculate_salvage_settlement(
        property_values=props,
        assessed_art13_award_percentage=10.0,
        regime=SalvageContractRegime.SCOPIC_INVOKED,
        scopic_items=scopic_items,
    )

    assert res.total_scopic_remuneration_usd == 625000.0
    assert res.final_salvor_remuneration_usd == 625000.0
    assert res.property_underwriters_liability_usd == 160000.0
    assert res.pni_club_liability_usd == 465000.0


# ==============================================================================
# 4. PHASE 257: SEAFARER ABANDONMENT ADJUDICATION TESTS
# ==============================================================================

def test_seafarer_abandonment_statutory_4month_cap():
    """Verify MLC 2006 Standard A2.5.2 wage cap of 4 months when 6 months claimed."""
    claims = [
        SeafarerAbandonmentClaim(
            seafarer_name="Thuyền trưởng Trần Văn Bảo",
            rank_or_role="Captain",
            nationality="Việt Nam",
            monthly_basic_wage_usd=3000.0,
            months_unpaid=6.0,
            actual_outstanding_wages_usd=18000.0,
            repatriation_home_country="Việt Nam",
            estimated_travel_cost_usd=1500.0,
            stranding_days_onboard=30,
        )
    ]

    report = SeafarerAbandonmentEngine.adjudicate_abandonment(
        vessel_name="MV_ABANDONED_BULK",
        imo_number="9123456",
        guarantor_pni_insurer="THE STANDARD CLUB",
        trigger=AbandonmentTrigger.UNPAID_WAGES_2_MONTHS,
        claims=claims,
    )

    # Claimed: 18,000 USD. Statutory capped: 3,000 * 4 = 12,000 USD.
    # Travel: 1,500 USD. Subsistence: 30 days * 30 USD = 900 USD.
    # Total payout: 12,000 + 1,500 + 900 = 14,400 USD.
    assert report.total_gross_wages_claimed_usd == 18000.0
    assert report.total_statutory_capped_wages_usd == 12000.0
    assert report.total_repatriation_transit_costs_usd == 1500.0
    assert report.total_subsistence_allowance_usd == 900.0
    assert report.total_guarantee_payout_usd == 14400.0
    assert report.shipowner_recourse_claim_usd == 14400.0
    assert "CHẤP THUẬN KÍCH HOẠT BẢO ĐẢM TÀI CHÍNH MLC 2006" in report.adjudication_verdict


def test_seafarer_abandonment_under_4month_wages():
    """Verify seafarer claiming 2 months of wages receives full 2 months without deduction."""
    claims = [
        SeafarerAbandonmentClaim(
            seafarer_name="Thủy thủ Nguyễn Văn Cường",
            rank_or_role="Able Seaman",
            nationality="Việt Nam",
            monthly_basic_wage_usd=1500.0,
            months_unpaid=2.0,
            actual_outstanding_wages_usd=3000.0,
            repatriation_home_country="Việt Nam",
            estimated_travel_cost_usd=1000.0,
            stranding_days_onboard=10,
        )
    ]

    report = SeafarerAbandonmentEngine.adjudicate_abandonment(
        vessel_name="MV_FEEDER_STRANDED",
        imo_number="9555123",
        guarantor_pni_insurer="UK P&I CLUB",
        trigger=AbandonmentTrigger.FAILURE_TO_REPATRIATE,
        claims=claims,
    )

    # Capped equals claimed = 3000 USD
    assert report.total_statutory_capped_wages_usd == 3000.0
    # Travel = 1000 USD, Subsistence = 10 * 30 = 300 USD
    assert report.total_guarantee_payout_usd == 4300.0


# ==============================================================================
# 5. PHASE 258: GREEN HARBOR CRAFT TRANSITION TESTS
# ==============================================================================

def test_green_harbor_craft_battery_electric():
    """Verify 80% emission reduction, 20% port rebate, and payback for electric tug."""
    res = GreenHarborCraftEngine.evaluate_transition(
        craft_name="TÀU LAI XANH CÁI MÉP 01",
        bollard_pull_tonnes=70.0,
        propulsion=HarborCraftPropulsion.PURE_BATTERY_ELECTRIC,
        annual_operating_hours=2500.0,
        capex_green_premium_usd=2000000.0,
        annual_port_dues_paid_usd=100000.0,
    )

    assert res.abatement_ratio_pct == 80.0
    assert res.abated_co2_tonnes_per_year == pytest.approx(res.baseline_mgo_co2_tonnes_per_year * 0.80, rel=1e-3)
    assert res.annual_green_tariff_rebate_usd == 20000.0  # 20% of 100k
    assert res.statutory_incentive_compliance is True
    assert res.simple_payback_years > 0.0


def test_green_harbor_craft_hybrid_diesel():
    """Verify 22% emission reduction and 10% tariff rebate for hybrid tug."""
    res = GreenHarborCraftEngine.evaluate_transition(
        craft_name="TÀU LAI HYBRID ĐÀ NẴNG",
        bollard_pull_tonnes=50.0,
        propulsion=HarborCraftPropulsion.HYBRID_DIESEL_ELECTRIC,
        annual_operating_hours=2000.0,
        capex_green_premium_usd=800000.0,
        annual_port_dues_paid_usd=50000.0,
    )

    assert res.abatement_ratio_pct == 22.0
    assert res.annual_green_tariff_rebate_usd == 5000.0  # 10% of 50k
    assert res.statutory_incentive_compliance is True


def test_green_harbor_craft_conventional_fails():
    """Verify conventional diesel tug achieves 0% abatement and fails statutory incentives."""
    res = GreenHarborCraftEngine.evaluate_transition(
        craft_name="TÀU LAI DIESEL CŨ",
        bollard_pull_tonnes=50.0,
        propulsion=HarborCraftPropulsion.CONVENTIONAL_DIESEL,
        annual_operating_hours=2000.0,
        capex_green_premium_usd=0.0,
        annual_port_dues_paid_usd=50000.0,
    )

    assert res.abatement_ratio_pct == 0.0
    assert res.annual_green_tariff_rebate_usd == 0.0
    assert res.annual_fuel_cost_savings_usd == 0.0
    assert res.statutory_incentive_compliance is False


# ==============================================================================
# 6. TYPER CLI SUBCOMMAND TESTS
# ==============================================================================

def test_cli_shipagency_reconcile():
    """Test `shipagency reconcile` command with JSON output."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, [
        "shipagency", "reconcile",
        "--vessel", "MV_VIET_TEST",
        "--call-id", "CALL-2026-X",
        "--gt", "20000",
        "--advance", "40000",
        "--port-dues", "15000",
        "--pilotage", "5000",
        "--tugboat", "10000",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["vessel_name"] == "MV_VIET_TEST"
    assert data["gross_tonnage"] == 20000.0


def test_cli_dailytaubien_alias():
    """Test Vietnamese alias `dailytaubien reconcile`."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, [
        "dailytaubien", "reconcile",
        "--vessel", "MV_VIET_ALIAS",
        "--gt", "10000",
        "--advance", "30000",
    ])
    assert result.exit_code == 0
    assert "QUYẾT TOÁN TÀI KHOẢN GIẢI NGÂN ĐẠI LÝ" in result.output


def test_cli_salvagescopic_settle():
    """Test `salvagescopic settle` command."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, [
        "salvagescopic", "settle",
        "--sound-val", "12000000",
        "--repairs", "2000000",
        "--cargo", "6000000",
        "--freight", "400000",
        "--award-pct", "10",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["net_salved_fund_usd"] == 16400000.0
    assert data["regime"] == "scopic_invoked"


def test_cli_abandonment_adjudicate():
    """Test `abandonment adjudicate` command."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, [
        "abandonment", "adjudicate",
        "--vessel", "MV_STRANDED_TEST",
        "--imo", "9876543",
        "--crew-count", "10",
        "--avg-wage", "2000",
        "--unpaid-months", "4",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_seafarers_stranded"] == 10
    assert data["total_statutory_capped_wages_usd"] == 80000.0


def test_cli_greentug_evaluate():
    """Test `greentug evaluate` command."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, [
        "greentug", "evaluate",
        "--craft", "TÀU KÉO XANH 02",
        "--bp", "65",
        "--tech", "pure_battery_electric",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["craft_name"] == "TÀU KÉO XANH 02"
    assert data["abatement_ratio_pct"] == 80.0


# ==============================================================================
# 7. FASTMCP SERVER HANDLER TESTS
# ==============================================================================

def test_fastmcp_ship_agency_handler():
    """Verify FastMCP handler for ship agency reconcile."""
    raw = handle_ship_agency_reconcile({
        "vessel_name": "MV_MCP_TEST",
        "gross_tonnage": 30000.0,
        "advance_deposit_received_usd": 60000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["disbursement_account_report"]["vessel_name"] == "MV_MCP_TEST"


def test_fastmcp_salvage_settlement_handler():
    """Verify FastMCP handler for salvage settlement evaluate."""
    raw = handle_salvage_settlement_evaluate({
        "sound_ship_value_usd": 20000000.0,
        "damage_repair_costs_usd": 4000000.0,
        "cargo_cif_value_usd": 10000000.0,
        "unpaid_freight_at_risk_usd": 500000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    # Net fund = 16M + 10M + 0.5M = 26.5M
    assert res["salvage_settlement"]["net_salved_fund_usd"] == 26500000.0


def test_fastmcp_abandonment_handler():
    """Verify FastMCP handler for seafarer abandonment adjudicate."""
    raw = handle_seafarer_abandonment_adjudicate({
        "vessel_name": "MV_MCP_ABANDONED",
        "imo_number": "9112233",
        "crew_count": 12,
        "avg_monthly_wage_usd": 2500.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["abandonment_adjudication"]["total_seafarers_stranded"] == 12


def test_fastmcp_green_harbor_craft_handler():
    """Verify FastMCP handler for green harbor craft evaluate."""
    raw = handle_green_harbor_craft_evaluate({
        "craft_name": "TÀU LAI MCP XANH",
        "bollard_pull_tonnes": 80.0,
        "propulsion": "green_hydrogen_fc",
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["green_craft_evaluation"]["abatement_ratio_pct"] == 95.0


def test_fastmcp_invalid_inputs_graceful():
    """Verify FastMCP handlers gracefully return error for non-dict inputs."""
    res1 = json.loads(handle_ship_agency_reconcile("invalid_type"))
    assert res1["ok"] is False
    assert "Invalid arguments object" in res1["error"]

    res2 = json.loads(handle_salvage_settlement_evaluate(None))
    assert res2["ok"] is False
