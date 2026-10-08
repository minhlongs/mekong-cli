# -*- coding: utf-8 -*-
"""Comprehensive Test Suite for Phases 251-254.

Phases Covered:
- Phase 251: Maritime Domestic Cabotage Waiver & Foreign Vessel Licensing
- Phase 252: Maritime Liens Priority Waterfall & Judicial Ship Auction Proceeds
- Phase 253: Seafarer Medical Fitness Certification & STCW Reg. I/9 Compliance
- Phase 254: Seaport PPP Concession Contracts & Revenue-Sharing Waterfall
"""

import ast
import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.maritime_cabotage_liens_medical_concession_engine import (
    CabotagePermitType,
    CabotageWaiverReason,
    MedicalFitnessVerdict,
    MaritimeCabotageEngine,
    MaritimeClaimItem,
    MaritimeClaimTier,
    MaritimeLiensAuctionEngine,
    SeafarerDepartment,
    SeafarerMedicalEngine,
    SeaportConcessionEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_maritime_cabotage_evaluate,
    handle_maritime_liens_distribute,
    handle_seafarer_medical_evaluate,
    handle_seaport_ppp_evaluate,
)


# ==============================================================================
# 1. ZERO-DEPENDENCY AST ARCHITECTURAL INVARIANT TEST
# ==============================================================================

def test_core_engine_zero_dependencies():
    """Verify that core engine imports only Python standard library modules."""
    engine_path = Path("/Users/macbook/mekong-cli/src/core/maritime_cabotage_liens_medical_concession_engine.py")
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
# 2. PHASE 251: MARITIME CABOTAGE WAIVER ENGINE TESTS
# ==============================================================================

def test_cabotage_waiver_specialized_cargo_success():
    """Verify approval of specialized cargo waiver for foreign vessel within age limit."""
    res = MaritimeCabotageEngine.evaluate_cabotage_permit(
        application_id="CAB-TEST-001",
        vessel_name="PACIFIC_GAS",
        flag_state="PANAMA",
        gross_tonnage=20000.0,
        reason=CabotageWaiverReason.SPECIALIZED_CARGO,
        permit_type=CabotagePermitType.TIME_CHARTER_3_MONTHS,
        cargo_or_passenger_desc="Vận chuyển khí hóa lỏng LPG lạnh",
        domestic_fleet_available=False,
        vessel_age_years=12,
    )

    assert res.is_approved is True
    assert res.permit_duration_days == 90
    assert res.statutory_permit_fee_vnd > 0.0
    assert "Chấp thuận cấp giấy phép" in res.remarks


def test_cabotage_waiver_rejection_domestic_fleet_available():
    """Verify rejection when domestic Vietnamese fleet is available and capable."""
    res = MaritimeCabotageEngine.evaluate_cabotage_permit(
        application_id="CAB-TEST-002",
        vessel_name="ASIAN_CARRIER",
        flag_state="LIBERIA",
        gross_tonnage=10000.0,
        reason=CabotageWaiverReason.DOMESTIC_FLEET_DEFICIT,
        permit_type=CabotagePermitType.SINGLE_VOYAGE,
        cargo_or_passenger_desc="Vận chuyển xi măng bao nội địa",
        domestic_fleet_available=True,
        vessel_age_years=8,
    )

    assert res.is_approved is False
    assert "TỪ CHỐI CẤP PHÉP" in res.operational_conditions
    assert "Đội tàu quốc gia Việt Nam đáp ứng đủ" in res.remarks


def test_cabotage_waiver_rejection_vessel_age_limit():
    """Verify rejection when foreign vessel exceeds statutory age limit under Decree 58/2017."""
    res = MaritimeCabotageEngine.evaluate_cabotage_permit(
        application_id="CAB-TEST-003",
        vessel_name="OLD_CRUISE",
        flag_state="BAHAMAS",
        gross_tonnage=30000.0,
        reason=CabotageWaiverReason.INTERNATIONAL_CRUISE,
        permit_type=CabotagePermitType.SINGLE_VOYAGE,
        cargo_or_passenger_desc="Du khách quốc tế cập cảng Hạ Long - Đà Nẵng",
        domestic_fleet_available=False,
        vessel_age_years=18,  # Max for passenger cruise is 15 years
    )

    assert res.is_approved is False
    assert "vượt quá quy định tối đa" in res.remarks


# ==============================================================================
# 3. PHASE 252: MARITIME LIENS WATERFALL & AUCTION PROCEEDS TESTS
# ==============================================================================

def test_maritime_liens_auction_full_satisfaction():
    """Verify full payout and surplus when auction proceeds exceed all claims."""
    claims = [
        MaritimeClaimItem(
            claim_id="C-01",
            creditor_name="Thuyền bộ",
            tier=MaritimeClaimTier.TIER_1_CREW_WAGES,
            claim_amount_usd=200000.0,
            claim_date_str="2026-01-01",
        ),
        MaritimeClaimItem(
            claim_id="C-02",
            creditor_name="Ngân hàng Mortgage",
            tier=MaritimeClaimTier.TIER_6_SHIP_MORTGAGE,
            claim_amount_usd=800000.0,
            claim_date_str="2025-05-01",
        ),
        MaritimeClaimItem(
            claim_id="C-03",
            creditor_name="Đại lý hàng hải",
            tier=MaritimeClaimTier.TIER_7_GENERAL_CREDITORS,
            claim_amount_usd=100000.0,
            claim_date_str="2026-02-01",
        ),
    ]

    report = MaritimeLiensAuctionEngine.distribute_auction_proceeds(
        vessel_name="MV_FULL_SETTLE",
        gross_auction_proceeds_usd=1500000.0,
        claims=claims,
        court_custody_costs_usd=100000.0,
    )

    assert report.net_distributable_funds_usd == 1400000.0
    assert report.total_claims_demanded_usd == 1100000.0
    assert report.total_claims_paid_usd == 1100000.0
    assert report.surplus_to_shipowner_usd == 300000.0

    for dist in report.claims_distributions:
        assert dist.unpaid_balance_usd == 0.0
        assert dist.recovery_rate_pct == 100.0


def test_maritime_liens_auction_prorata_exhaustion():
    """Verify tier priority and pro-rata distribution when funds deplete mid-tier."""
    claims = [
        MaritimeClaimItem(
            claim_id="W-01",
            creditor_name="Thuyền viên",
            tier=MaritimeClaimTier.TIER_1_CREW_WAGES,
            claim_amount_usd=300000.0,
            claim_date_str="2026-01-01",
        ),
        MaritimeClaimItem(
            claim_id="M-01",
            creditor_name="Ngân hàng A",
            tier=MaritimeClaimTier.TIER_6_SHIP_MORTGAGE,
            claim_amount_usd=600000.0,
            claim_date_str="2025-01-01",
        ),
        MaritimeClaimItem(
            claim_id="M-02",
            creditor_name="Ngân hàng B",
            tier=MaritimeClaimTier.TIER_6_SHIP_MORTGAGE,
            claim_amount_usd=400000.0,
            claim_date_str="2025-02-01",
        ),
        MaritimeClaimItem(
            claim_id="G-01",
            creditor_name="Nhà cấp dầu",
            tier=MaritimeClaimTier.TIER_7_GENERAL_CREDITORS,
            claim_amount_usd=200000.0,
            claim_date_str="2026-01-15",
        ),
    ]

    report = MaritimeLiensAuctionEngine.distribute_auction_proceeds(
        vessel_name="MV_PRORATA",
        gross_auction_proceeds_usd=900000.0,
        claims=claims,
        court_custody_costs_usd=100000.0,
    )

    assert report.net_distributable_funds_usd == 800000.0
    assert report.total_claims_paid_usd == 800000.0
    assert report.surplus_to_shipowner_usd == 0.0

    d_w1 = next(d for d in report.claims_distributions if d.claim_id == "W-01")
    assert d_w1.allocated_payout_usd == 300000.0
    assert d_w1.unpaid_balance_usd == 0.0

    d_m1 = next(d for d in report.claims_distributions if d.claim_id == "M-01")
    assert d_m1.allocated_payout_usd == 300000.0
    assert d_m1.recovery_rate_pct == 50.0

    d_m2 = next(d for d in report.claims_distributions if d.claim_id == "M-02")
    assert d_m2.allocated_payout_usd == 200000.0
    assert d_m2.recovery_rate_pct == 50.0

    d_g1 = next(d for d in report.claims_distributions if d.claim_id == "G-01")
    assert d_g1.allocated_payout_usd == 0.0
    assert d_g1.recovery_rate_pct == 0.0


def test_maritime_liens_time_bar_extinction():
    """Verify that claims marked time-barred (statute of limitations 1 year) receive 0."""
    claims = [
        MaritimeClaimItem(
            claim_id="TB-01",
            creditor_name="Chủ hàng cũ",
            tier=MaritimeClaimTier.TIER_5_PROPERTY_DAMAGE,
            claim_amount_usd=200000.0,
            claim_date_str="2024-01-01",
            is_time_barred=True,
        )
    ]
    report = MaritimeLiensAuctionEngine.distribute_auction_proceeds(
        vessel_name="MV_TIME_BARRED",
        gross_auction_proceeds_usd=1000000.0,
        claims=claims,
        court_custody_costs_usd=50000.0,
    )
    dist = report.claims_distributions[0]
    assert dist.allocated_payout_usd == 0.0
    assert "HẾT HIỆU LỰC" in dist.status


# ==============================================================================
# 4. PHASE 253: SEAFARER MEDICAL FITNESS ENGINE TESTS
# ==============================================================================

def test_seafarer_medical_deck_officer_full_pass():
    """Verify deck officer meeting all criteria receives full fitness certificate."""
    cert = SeafarerMedicalEngine.evaluate_fitness(
        certificate_id="MED-D-001",
        seafarer_name="Lê Hoàng",
        date_of_birth="1990-08-20",
        department=SeafarerDepartment.DECK_OFFICER,
        visual_acuity_right=1.0,
        visual_acuity_left=0.9,
        color_vision_pass=True,
        hearing_threshold_db=15.0,
        blood_pressure_systolic=120,
        blood_pressure_diastolic=78,
        bmi=22.8,
        age_years=35,
        requires_corrective_lenses=False,
    )

    assert cert.verdict == MedicalFitnessVerdict.FIT_UNRESTRICTED
    assert cert.validity_months == 24
    assert cert.restriction_notes == "Không hạn chế"


def test_seafarer_medical_minor_validity():
    """Verify seafarer under 18 years receives 12-month certificate validity under STCW."""
    cert = SeafarerMedicalEngine.evaluate_fitness(
        certificate_id="MED-M-002",
        seafarer_name="Trần Thiếu Niên",
        date_of_birth="2009-02-10",
        department=SeafarerDepartment.ENGINE_RATING,
        visual_acuity_right=0.7,
        visual_acuity_left=0.6,
        color_vision_pass=True,
        hearing_threshold_db=20.0,
        blood_pressure_systolic=115,
        blood_pressure_diastolic=75,
        bmi=21.0,
        age_years=17,
        requires_corrective_lenses=False,
    )

    assert cert.verdict == MedicalFitnessVerdict.FIT_UNRESTRICTED
    assert cert.validity_months == 12


def test_seafarer_medical_deck_color_blind_unfit():
    """Verify deck officer failing Ishihara test is permanently unfit for navigational watch."""
    cert = SeafarerMedicalEngine.evaluate_fitness(
        certificate_id="MED-D-003",
        seafarer_name="Phạm Sĩ Quan",
        date_of_birth="1988-11-05",
        department=SeafarerDepartment.DECK_OFFICER,
        visual_acuity_right=1.0,
        visual_acuity_left=1.0,
        color_vision_pass=False,
        hearing_threshold_db=20.0,
        blood_pressure_systolic=130,
        blood_pressure_diastolic=85,
        bmi=24.0,
        age_years=37,
    )

    assert cert.verdict == MedicalFitnessVerdict.PERMANENTLY_UNFIT
    assert cert.validity_months == 0
    assert "MÙ MÀU" in cert.restriction_notes


def test_seafarer_medical_corrective_lenses_restricted():
    """Verify fit with restriction when corrective lenses are required."""
    cert = SeafarerMedicalEngine.evaluate_fitness(
        certificate_id="MED-D-004",
        seafarer_name="Võ Kính Cận",
        date_of_birth="1995-04-12",
        department=SeafarerDepartment.ENGINE_OFFICER,
        visual_acuity_right=0.3,
        visual_acuity_left=0.4,
        color_vision_pass=True,
        hearing_threshold_db=20.0,
        blood_pressure_systolic=120,
        blood_pressure_diastolic=80,
        bmi=23.0,
        age_years=31,
        requires_corrective_lenses=True,
    )

    assert cert.verdict == MedicalFitnessVerdict.FIT_WITH_RESTRICTIONS
    assert "đeo kính" in cert.restriction_notes


# ==============================================================================
# 5. PHASE 254: SEAPORT PPP CONCESSION ENGINE TESTS
# ==============================================================================

def test_seaport_ppp_financials_viability():
    """Verify seaport PPP concession meets minimum equity ratio and DSCR benchmarks."""
    metrics = SeaportConcessionEngine.evaluate_ppp_financials(
        total_capex_vnd=10_000_000_000_000.0,
        equity_capital_vnd=2_000_000_000_000.0,
        debt_interest_rate_pct=9.0,
        loan_tenor_years=15,
        expected_annual_ebitda_vnd=1_250_000_000_000.0,
    )

    assert metrics.equity_ratio_pct == 20.0
    assert metrics.meets_equity_statutory_threshold is True
    assert metrics.average_dscr > 1.20
    assert metrics.financial_feasibility is True


def test_seaport_decree35_revenue_sharing_deficit_support():
    """Verify Decree 35 Art. 82 downside risk sharing (State pays 50% when revenue < 75%)."""
    settlement = SeaportConcessionEngine.calculate_decree35_revenue_sharing(
        year=2026,
        planned_revenue_vnd=1_000_000_000_000.0,
        actual_revenue_vnd=600_000_000_000.0,
    )

    assert settlement.revenue_ratio_pct == 60.0
    assert settlement.state_share_payout_to_investor_vnd == 75_000_000_000.0
    assert settlement.investor_share_payout_to_state_vnd == 0.0
    assert "CHIA SẺ GIẢM DOANH THU" in settlement.mechanism_triggered


def test_seaport_decree35_revenue_sharing_surplus_clawback():
    """Verify Decree 35 Art. 82 upside risk sharing (Private pays 50% when revenue > 125%)."""
    settlement = SeaportConcessionEngine.calculate_decree35_revenue_sharing(
        year=2027,
        planned_revenue_vnd=1_000_000_000_000.0,
        actual_revenue_vnd=1_450_000_000_000.0,
    )

    assert settlement.revenue_ratio_pct == 145.0
    assert settlement.investor_share_payout_to_state_vnd == 100_000_000_000.0
    assert settlement.state_share_payout_to_investor_vnd == 0.0
    assert "CHIA SẺ TĂNG DOANH THU" in settlement.mechanism_triggered


def test_seaport_decree35_revenue_sharing_neutral_band():
    """Verify Decree 35 Art. 82 neutral band (no revenue sharing between 75% and 125%)."""
    settlement = SeaportConcessionEngine.calculate_decree35_revenue_sharing(
        year=2028,
        planned_revenue_vnd=1_000_000_000_000.0,
        actual_revenue_vnd=1_100_000_000_000.0,
    )

    assert settlement.state_share_payout_to_investor_vnd == 0.0
    assert settlement.investor_share_payout_to_state_vnd == 0.0
    assert "VÙNG TRUNG HÒA" in settlement.mechanism_triggered


# ==============================================================================
# 6. CLI INTEGRATION TESTS
# ==============================================================================

@pytest.fixture
def cli_runner():
    return CliRunner()


def test_cli_cabotage_evaluate(cli_runner):
    """Test 'cabotage evaluate' CLI command and json flag."""
    app = build_app()
    result = cli_runner.invoke(app, [
        "cabotage", "evaluate",
        "--id", "CAB-CLI-01",
        "--vessel", "PACIFIC_GAS",
        "--flag", "PANAMA",
        "--gt", "18000",
        "--reason", "specialized_cargo",
        "--permit", "single_voyage",
        "--age", "10",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["application_id"] == "CAB-CLI-01"
    assert data["is_approved"] is True


def test_cli_liens_distribute(cli_runner):
    """Test 'liens distribute' CLI command and alias."""
    app = build_app()
    result = cli_runner.invoke(app, [
        "liens", "distribute",
        "--vessel", "MV_AUCTION_TEST",
        "--proceeds", "3000000",
        "--court-costs", "200000",
        "--wages", "500000",
        "--injury", "200000",
        "--mortgage", "1500000",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["net_distributable_funds_usd"] == 2800000.0
    assert data["total_claims_paid_usd"] > 0


def test_cli_seafarer_med_evaluate(cli_runner):
    """Test 'seafarer-med evaluate' CLI command and alias."""
    app = build_app()
    result = cli_runner.invoke(app, [
        "seafarer-med", "evaluate",
        "--id", "MED-CLI-01",
        "--name", "Nguyen Van Hai",
        "--dept", "deck_officer",
        "--var", "1.0",
        "--val", "0.9",
        "--sys", "120",
        "--dia", "80",
        "--age", "28",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["verdict"] == "fit_unrestricted"
    assert data["validity_months"] == 24


def test_cli_seaport_ppp_commands(cli_runner):
    """Test 'seaport-ppp financials' and 'seaport-ppp sharing' CLI commands."""
    app = build_app()
    res_fin = cli_runner.invoke(app, [
        "seaport-ppp", "financials",
        "--capex", "6000000000000",
        "--equity", "1200000000000",
        "--json",
    ])
    assert res_fin.exit_code == 0
    data_fin = json.loads(res_fin.output)
    assert data_fin["equity_ratio_pct"] == 20.0

    res_share = cli_runner.invoke(app, [
        "seaport-ppp", "sharing",
        "--year", "2026",
        "--plan", "1000000000000",
        "--act", "700000000000",
        "--json",
    ])
    assert res_share.exit_code == 0
    data_share = json.loads(res_share.output)
    assert "CHIA SẺ GIẢM DOANH THU" in data_share["mechanism_triggered"]


# ==============================================================================
# 7. FASTMCP HANDLER TESTS
# ==============================================================================

def test_fastmcp_maritime_cabotage_evaluate():
    """Verify FastMCP handler for cabotage waiver evaluation."""
    raw = handle_maritime_cabotage_evaluate({
        "application_id": "CAB-MCP-01",
        "vessel_name": "STAR_CHEMICAL",
        "flag_state": "SINGAPORE",
        "gross_tonnage": 12000.0,
        "reason": "specialized_cargo",
        "permit_type": "time_charter_6m",
        "domestic_fleet_available": False,
        "vessel_age_years": 9,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["evaluation"]["is_approved"] is True
    assert res["evaluation"]["statutory_permit_fee_vnd"] > 0


def test_fastmcp_maritime_liens_distribute():
    """Verify FastMCP handler for maritime liens auction distribution."""
    raw = handle_maritime_liens_distribute({
        "vessel_name": "MV_MCP_AUCTION",
        "gross_auction_proceeds_usd": 2000000.0,
        "court_custody_costs_usd": 100000.0,
        "wages_claim_usd": 300000.0,
        "salvage_claim_usd": 200000.0,
        "mortgage_claim_usd": 1000000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["auction_report"]["net_distributable_funds_usd"] == 1900000.0


def test_fastmcp_seafarer_medical_evaluate():
    """Verify FastMCP handler for seafarer medical fitness."""
    raw = handle_seafarer_medical_evaluate({
        "certificate_id": "MED-MCP-01",
        "seafarer_name": "Trần Thị Mai",
        "department": "catering",
        "visual_acuity_right": 0.8,
        "visual_acuity_left": 0.8,
        "color_vision_pass": True,
        "age_years": 26,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["certificate"]["verdict"] == "fit_unrestricted"


def test_fastmcp_seaport_ppp_evaluate():
    """Verify FastMCP handler for seaport PPP concession evaluation."""
    raw = handle_seaport_ppp_evaluate({
        "total_capex_vnd": 4000000000000.0,
        "equity_capital_vnd": 800000000000.0,
        "planned_revenue_vnd": 800000000000.0,
        "actual_revenue_vnd": 500000000000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["financial_metrics"]["equity_ratio_pct"] == 20.0
    assert "CHIA SẺ GIẢM DOANH THU" in res["revenue_sharing_settlement"]["mechanism_triggered"]
