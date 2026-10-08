"""Unit, AST Zero-Dependency, Integration & CLI Tests for Maritime Suite (Phases 211-214).

Covers:
- Phase 211: Marine Insurance & Subrogation (VMC Arts. 310-336, LKDBH 2022)
- Phase 212: Marine Casualty Investigation (IMO Res. MSC.255(84), Circular 01/2020/TT-BGTVT)
- Phase 213: Ship Sale & Purchase Escrow (BIMCO SALEFORM 2012, VMC Arts. 29-36)
- Phase 214: Seafarer Repatriation Contingency (MLC 2006 Standard A2.5, Circular 22/2017)
- AST Zero-Dependency Invariant
- Typer CLI commands & FastMCP tools
"""

import ast
import json
from typer.testing import CliRunner

from src.core.maritime_insurance_casualty_sp_repatriation_engine import (
    MaritimeInsuranceSubrogationEngine,
    MarineLossType,
    AbandonmentStatus,
    MarineCasualtyInvestigationEngine,
    MarineCasualtySeverity,
    ShipSalePurchaseEscrowEngine,
    SeafarerRepatriationContingencyEngine,
    RepatriationTrigger,
)
from src.cli.app_setup import build_app
import scripts.mcp_server as mcp_srv

runner = CliRunner()


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================

def test_maritime_insurance_casualty_ast_zero_dependency():
    """Verify src/core/maritime_insurance_casualty_sp_repatriation_engine.py has 0 external dependencies."""
    file_path = "src/core/maritime_insurance_casualty_sp_repatriation_engine.py"
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
# 2. Phase 211: Marine Insurance & Subrogation Tests
# ===========================================================================

def test_marine_insurance_actual_total_loss():
    """Verify Actual Total Loss pays full insured value minus deductible with subrogation."""
    res = MaritimeInsuranceSubrogationEngine.assess_marine_claim(
        policy_id="POL-ATL-01",
        vessel_name="MV SUNKEN GLORY",
        insured_value_usd=10_000_000.0,
        actual_total_loss=True,
        estimated_repair_cost_usd=0.0,
        policy_deductible_usd=100_000.0,
    )
    assert res.loss_type == MarineLossType.ACTUAL_TOTAL_LOSS
    assert res.indemnity_payable_usd == 10_000_000.0
    assert res.deductible_applied_usd == 100_000.0
    assert res.net_claim_payout_usd == 9_900_000.0
    assert res.subrogation_rights_acquired is True
    assert res.max_subrogation_recovery_usd == 9_900_000.0


def test_marine_insurance_ctl_accepted_abandonment():
    """Verify Constructive Total Loss with accepted notice of abandonment transfers salvage title."""
    # Repair cost 8.5M on 10M insured value = 85% >= 80% CTL threshold
    res = MaritimeInsuranceSubrogationEngine.assess_marine_claim(
        policy_id="POL-CTL-01",
        vessel_name="MV REEF STRAND",
        insured_value_usd=10_000_000.0,
        actual_total_loss=False,
        estimated_repair_cost_usd=8_500_000.0,
        salvage_value_usd=1_000_000.0,
        policy_deductible_usd=50_000.0,
        notice_of_abandonment_tendered=True,
        abandonment_days_since_casualty=45,
        abandonment_accepted_by_insurer=True,
    )
    assert res.loss_type == MarineLossType.CONSTRUCTIVE_TOTAL_LOSS
    assert res.is_constructive_total_loss is True
    assert res.abandonment_status == AbandonmentStatus.VALID_ACCEPTED
    assert res.indemnity_payable_usd == 10_000_000.0
    assert res.net_claim_payout_usd == 9_950_000.0
    assert res.insurer_salvage_title_acquired is True
    assert res.subrogation_rights_acquired is True
    assert res.max_subrogation_recovery_usd == 9_950_000.0


def test_marine_insurance_ctl_declined_abandonment_payout_maintained():
    """Verify CTL payout maintained even if insurer declines abandonment, but salvage title remains with owner."""
    res = MaritimeInsuranceSubrogationEngine.assess_marine_claim(
        policy_id="POL-CTL-02",
        vessel_name="MV PACIFIC EXPLORER",
        insured_value_usd=5_000_000.0,
        actual_total_loss=False,
        estimated_repair_cost_usd=4_200_000.0,
        salvage_value_usd=300_000.0,
        policy_deductible_usd=25_000.0,
        notice_of_abandonment_tendered=True,
        abandonment_days_since_casualty=60,
        abandonment_accepted_by_insurer=False,
    )
    assert res.loss_type == MarineLossType.CONSTRUCTIVE_TOTAL_LOSS
    assert res.abandonment_status == AbandonmentStatus.VALID_DECLINED_PAYOUT_MAINTAINED
    assert res.net_claim_payout_usd == 4_975_000.0
    assert res.insurer_salvage_title_acquired is False
    assert res.subrogation_rights_acquired is True


def test_marine_insurance_untimely_abandonment():
    """Verify notice of abandonment after 180 days is untimely under VMC Art. 320."""
    res = MaritimeInsuranceSubrogationEngine.assess_marine_claim(
        policy_id="POL-CTL-03",
        vessel_name="MV LATE NOTICE",
        insured_value_usd=4_000_000.0,
        actual_total_loss=False,
        estimated_repair_cost_usd=3_500_000.0,
        notice_of_abandonment_tendered=True,
        abandonment_days_since_casualty=210,  # > 180 days
    )
    assert res.abandonment_status == AbandonmentStatus.UNTIMELY_TENDERED


def test_marine_insurance_partial_damage_average():
    """Verify partial loss (< 80% insured value) pays repair cost minus deductible."""
    res = MaritimeInsuranceSubrogationEngine.assess_marine_claim(
        policy_id="POL-PART-01",
        vessel_name="MV DOCKED SHIP",
        insured_value_usd=10_000_000.0,
        actual_total_loss=False,
        estimated_repair_cost_usd=1_500_000.0,
        policy_deductible_usd=100_000.0,
    )
    assert res.loss_type == MarineLossType.PARTIAL_DAMAGE_AVERAGE
    assert res.is_constructive_total_loss is False
    assert res.indemnity_payable_usd == 1_500_000.0
    assert res.net_claim_payout_usd == 1_400_000.0
    assert res.max_subrogation_recovery_usd == 1_400_000.0


# ===========================================================================
# 3. Phase 212: Marine Casualty Investigation Protocols Tests
# ===========================================================================

def test_marine_casualty_very_serious_severity():
    """Verify Very Serious Marine Casualty triggered by loss of life or total loss."""
    rep = MarineCasualtyInvestigationEngine.evaluate_casualty(
        incident_id="CAS-VSMC-01",
        vessel_name="MV HAI PHONG STAR",
        imo_number="9123456",
        flag_state="Vietnam",
        total_loss_of_ship=False,
        fatalities_count=2,
        severe_pollution_occurred=False,
        structural_damage_severe=True,
        in_vietnam_internal_or_territorial_waters=True,
    )
    assert rep.severity == MarineCasualtySeverity.VERY_SERIOUS_MARINE_CASUALTY
    assert rep.mandatory_safety_investigation_required is True
    assert rep.initial_report_deadline_hours == 24
    assert rep.preliminary_report_deadline_days == 30
    assert rep.final_safety_report_deadline_days == 60
    assert rep.vdr_preservation_mandatory is True
    assert "Vietnam Maritime Administration" in rep.investigating_authority


def test_marine_casualty_serious_structural_damage():
    """Verify Serious Marine Casualty for severe structural immobilizing damage."""
    rep = MarineCasualtyInvestigationEngine.evaluate_casualty(
        incident_id="CAS-SMC-01",
        vessel_name="MV MEKONG WAVE",
        imo_number="9654321",
        flag_state="Panama",
        total_loss_of_ship=False,
        fatalities_count=0,
        severe_pollution_occurred=False,
        structural_damage_severe=True,
        in_vietnam_internal_or_territorial_waters=False,
    )
    assert rep.severity == MarineCasualtySeverity.SERIOUS_MARINE_CASUALTY
    assert rep.mandatory_safety_investigation_required is True
    assert rep.final_safety_report_deadline_days == 90
    assert "Panama" in rep.investigating_authority


def test_marine_casualty_less_serious_reporting():
    """Verify Less Serious Casualty deadlines and optional VDR."""
    rep = MarineCasualtyInvestigationEngine.evaluate_casualty(
        incident_id="CAS-LMC-01",
        vessel_name="MV MINOR TOUCH",
        imo_number="9888888",
        flag_state="Vietnam",
        total_loss_of_ship=False,
        fatalities_count=0,
        severe_pollution_occurred=False,
        structural_damage_severe=False,
    )
    assert rep.severity == MarineCasualtySeverity.LESS_SERIOUS_CASUALTY
    assert rep.mandatory_safety_investigation_required is False
    assert rep.initial_report_deadline_hours == 48
    assert rep.final_safety_report_deadline_days == 120
    assert rep.vdr_preservation_mandatory is False


# ===========================================================================
# 4. Phase 213: Ship Sale & Purchase Escrow Tests
# ===========================================================================

def test_ship_saleform_clean_closing():
    """Verify clean closing: balance payable = price - deposit - defect holdback + bunkers."""
    # Price: 10,000,000 USD
    # Deposit (10%): 1,000,000 USD
    # Defect deduction: 100,000 USD
    # Bunkers: 150,000 USD
    # Balance: 10M - 1M - 100k + 150k = 9,050,000 USD
    res = ShipSalePurchaseEscrowEngine.process_saleform_closing(
        contract_ref="MOA-2026-001",
        vessel_name="MV MEKONG HORIZON",
        contract_price_usd=10_000_000.0,
        deposit_percentage=10.0,
        underwater_defect_repair_deduction_usd=100_000.0,
        bunkers_and_luboils_value_usd=150_000.0,
    )
    assert res.deposit_amount_usd == 1_000_000.0
    assert res.balance_payable_on_delivery_usd == 9_050_000.0
    assert res.escrow_deposit_forfeited_usd == 0.0
    assert res.legal_title_transfer_approved is True
    assert len(res.closing_documents_verified) >= 5


def test_ship_saleform_buyer_default_forfeiture():
    """Verify buyer default forfeits 10% deposit and bars title transfer."""
    res = ShipSalePurchaseEscrowEngine.process_saleform_closing(
        contract_ref="MOA-DEFAULT-01",
        vessel_name="MV DEFAULTED DEAL",
        contract_price_usd=8_000_000.0,
        buyer_default=True,
    )
    assert res.deposit_amount_usd == 800_000.0
    assert res.escrow_deposit_forfeited_usd == 800_000.0
    assert res.balance_payable_on_delivery_usd == 0.0
    assert res.legal_title_transfer_approved is False
    assert "forfeited to Seller" in res.verdict


def test_ship_saleform_seller_default_cancelling_date():
    """Verify seller default refunds deposit with interest and damages."""
    res = ShipSalePurchaseEscrowEngine.process_saleform_closing(
        contract_ref="MOA-CANCEL-01",
        vessel_name="MV DELAYED DELIVERY",
        contract_price_usd=12_000_000.0,
        cancelling_date_breached=True,
        seller_default=True,
    )
    assert res.deposit_amount_usd == 1_200_000.0
    assert res.seller_liquidated_damages_usd == 60_000.0
    assert res.legal_title_transfer_approved is False
    assert "returned to Buyer" in res.verdict


# ===========================================================================
# 5. Phase 214: Seafarer Repatriation Contingency Tests
# ===========================================================================

def test_seafarer_repatriation_abandonment_with_valid_insurance():
    """Verify P&I Club covers flight, sustenance, medical, and back wages capped at 4 months."""
    # 10 seafarers, 10 stranded days @ $50/day = 5,000 USD
    # Flight: 10 * 1,000 = 10,000 USD
    # Monthly wage: 2,000 USD, claimed unpaid 5 months -> capped at 4 months = 10 * 2,000 * 4 = 80,000 USD
    # Medical: 3,000 USD
    # Total liability: 10,000 + 5,000 + 80,000 + 3,000 = 98,000 USD
    res = SeafarerRepatriationContingencyEngine.assess_repatriation(
        case_ref="REP-01",
        vessel_name="MV ABANDONED CREW",
        flag_state="Vietnam",
        seafarer_count=10,
        trigger_event=RepatriationTrigger.SHIPOWNER_INSOLVENCY_ABANDONMENT,
        compulsory_financial_security_valid=True,
        security_provider="Gard P&I Club",
        flight_cost_per_seafarer_usd=1000.0,
        sustenance_daily_usd=50.0,
        stranded_days=10,
        average_monthly_wage_usd=2000.0,
        unpaid_wage_months=5.0,  # exceeds 4-month MLC cap
        emergency_medical_usd=3000.0,
    )
    assert res.flight_tickets_total_usd == 10_000.0
    assert res.sustenance_and_accommodation_usd == 5_000.0
    assert res.outstanding_wages_covered_usd == 80_000.0  # capped at 4 months
    assert res.medical_stabilization_usd == 3_000.0
    assert res.total_repatriation_liability_usd == 98_000.0
    assert res.insurer_direct_guarantee_payout_usd == 98_000.0
    assert res.vietnam_consular_contingency_advance_usd == 0.0


def test_seafarer_repatriation_abandonment_with_invalid_insurance():
    """Verify State/Consular emergency fund steps in when insurer certificate is missing/void."""
    res = SeafarerRepatriationContingencyEngine.assess_repatriation(
        case_ref="REP-02",
        vessel_name="MV ROGUE TRADER",
        flag_state="Vietnam",
        seafarer_count=5,
        trigger_event=RepatriationTrigger.SHIPOWNER_INSOLVENCY_ABANDONMENT,
        compulsory_financial_security_valid=False,
        flight_cost_per_seafarer_usd=800.0,
        sustenance_daily_usd=40.0,
        stranded_days=5,
        average_monthly_wage_usd=1500.0,
        unpaid_wage_months=2.0,
    )
    # Flight: 5 * 800 = 4,000
    # Food: 5 * 40 * 5 = 1,000
    # Wages: 5 * 1,500 * 2 = 15,000
    # Total: 20,000
    assert res.total_repatriation_liability_usd == 20_000.0
    assert res.insurer_direct_guarantee_payout_usd == 0.0
    assert res.vietnam_consular_contingency_advance_usd == 20_000.0
    assert res.owner_recourse_liability_usd == 20_000.0
    assert "NON_COMPLIANT" in res.mlc_standard_compliance


# ===========================================================================
# 6. Typer CLI Integration Tests
# ===========================================================================

def test_cli_maritimeins_assess():
    """Test CLI maritimeins assess command."""
    app = build_app()
    result = runner.invoke(app, ["maritimeins", "assess", "--policy-id", "CLI-POL-01", "--insured-val", "6000000", "--repair-cost", "5000000", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["policy_id"] == "CLI-POL-01"
    assert data["loss_type"] == "CONSTRUCTIVE_TOTAL_LOSS"
    assert data["net_claim_payout_usd"] > 0


def test_cli_casualty_investigate():
    """Test CLI casualty investigate command."""
    app = build_app()
    result = runner.invoke(app, ["casualty", "investigate", "--id", "CLI-CAS-01", "--vessel", "MV PACIFIC", "--severe-damage", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["incident_id"] == "CLI-CAS-01"
    assert data["severity"] == "SERIOUS_MARINE_CASUALTY"


def test_cli_shipsale_closing():
    """Test CLI shipsale closing command."""
    app = build_app()
    result = runner.invoke(app, ["shipsale", "closing", "--contract-ref", "CLI-MOA-01", "--price", "15000000", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["contract_ref"] == "CLI-MOA-01"
    assert data["deposit_amount_usd"] == 1_500_000.0


def test_cli_repatriate_audit():
    """Test CLI repatriate audit command."""
    app = build_app()
    result = runner.invoke(app, ["repatriate", "audit", "--case-ref", "CLI-REP-01", "--seafarers", "12", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["case_ref"] == "CLI-REP-01"
    assert data["total_repatriation_liability_usd"] > 0


def test_cli_vietnamese_aliases():
    """Verify Vietnamese command aliases function properly."""
    app = build_app()
    res1 = runner.invoke(app, ["thequyenbaohiem", "assess", "--help"])
    assert res1.exit_code == 0
    res2 = runner.invoke(app, ["tainanhanghai", "investigate", "--help"])
    assert res2.exit_code == 0
    res3 = runner.invoke(app, ["muabantau", "closing", "--help"])
    assert res3.exit_code == 0
    res4 = runner.invoke(app, ["hoihuong", "audit", "--help"])
    assert res4.exit_code == 0


# ===========================================================================
# 7. FastMCP Tool Handler Tests
# ===========================================================================

def test_mcp_marine_insurance_handler():
    """Test FastMCP handle_marine_insurance_assess."""
    raw = mcp_srv.handle_marine_insurance_assess({
        "policy_id": "MCP-POL-01",
        "insured_value_usd": 8_000_000.0,
        "estimated_repair_cost_usd": 7_000_000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["loss_type"] == "CONSTRUCTIVE_TOTAL_LOSS"


def test_mcp_marine_casualty_handler():
    """Test FastMCP handle_marine_casualty_investigate."""
    raw = mcp_srv.handle_marine_casualty_investigate({
        "incident_id": "MCP-CAS-01",
        "fatalities_count": 1,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["severity"] == "VERY_SERIOUS_MARINE_CASUALTY"


def test_mcp_ship_sale_closing_handler():
    """Test FastMCP handle_ship_sale_closing."""
    raw = mcp_srv.handle_ship_sale_closing({
        "contract_ref": "MCP-MOA-01",
        "contract_price_usd": 10_000_000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["balance_payable_on_delivery_usd"] > 0


def test_mcp_seafarer_repatriation_handler():
    """Test FastMCP handle_seafarer_repatriation_audit."""
    raw = mcp_srv.handle_seafarer_repatriation_audit({
        "case_ref": "MCP-REP-01",
        "seafarer_count": 15,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["total_repatriation_liability_usd"] > 0
