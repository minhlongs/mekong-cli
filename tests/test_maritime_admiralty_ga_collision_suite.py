"""Unit, AST Zero-Dependency, Integration & CLI Tests for Maritime Admiralty Suite (Phases 203-206).

Covers:
- Phase 203: Ship Arrest & Judicial Release (VMC Arts. 129-144)
- Phase 204: General Average Adjustment (York-Antwerp Rules 2016, VMC Arts. 295-298)
- Phase 205: Maritime Liens Priority Waterfall & Mortgages (VMC Arts. 37-42)
- Phase 206: Both-to-Blame Collision & Bunker Pollution 2001 (VMC Arts. 285-294)
- AST Zero-Dependency Invariant
- Typer CLI commands & FastMCP tools
"""

import ast
import json
from typer.testing import CliRunner

from src.core.maritime_admiralty_ga_collision_engine import (
    MaritimeShipArrestEngine,
    MaritimeClaimType,
    ArrestSecurityType,
    ArrestStatus,
    GeneralAverageYAREngine,
    GeneralAverageInterest,
    MaritimeLienPriorityEngine,
    MaritimeLienRank,
    LienClaimItem,
    CollisionAndBunkerPollutionEngine,
    CollisionVesselParticulars,
)
from src.cli.app_setup import build_app
import scripts.mcp_server as mcp_srv

runner = CliRunner()


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================

def test_maritime_admiralty_ga_collision_ast_zero_dependency():
    """Verify src/core/maritime_admiralty_ga_collision_engine.py has 0 external dependencies."""
    file_path = "src/core/maritime_admiralty_ga_collision_engine.py"
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
# 2. Phase 203: Ship Arrest & Judicial Release Tests
# ===========================================================================

def test_ship_arrest_counter_security_insufficient():
    """Test ship arrest rejection due to insufficient counter-security (< 15%)."""
    res = MaritimeShipArrestEngine.evaluate_arrest(
        vessel_name="MV BULK PIONEER",
        claim_type=MaritimeClaimType.COLLISION_OR_NAVIGATION_DAMAGE,
        claim_amount_usd=1000000.0,
        counter_security_provided_usd=100000.0,  # 10% < 15% required
        counter_security_type=ArrestSecurityType.BANK_GUARANTEE,
    )
    assert not res.is_counter_security_sufficient
    assert res.mandatory_counter_security_usd == 150000.0
    assert res.arrest_status == ArrestStatus.COUNTER_SECURITY_DEFICIENT
    assert "ARREST WARRANT DENIED" in res.verdict


def test_ship_arrest_ordered_detained():
    """Test valid counter-security leading to active arrest detention."""
    res = MaritimeShipArrestEngine.evaluate_arrest(
        vessel_name="MV PACIFIC TRADER",
        claim_type=MaritimeClaimType.CREW_WAGES_AND_REPATRIATION,
        claim_amount_usd=500000.0,
        counter_security_provided_usd=100000.0,  # 20% >= 15%
        counter_security_type=ArrestSecurityType.CASH_DEPOSIT_KBNN,
        arrest_date_iso="2026-09-01",
        assessment_date_iso="2026-09-10",
        court_action_commenced=False,
    )
    assert res.is_counter_security_sufficient
    assert res.days_under_arrest == 9
    assert not res.is_expired_30d_limit
    assert res.arrest_status == ArrestStatus.ARREST_ORDERED
    assert "ARREST WARRANT EXECUTED" in res.verdict


def test_ship_arrest_released_on_security():
    """Test prompt judicial release upon providing full security."""
    res = MaritimeShipArrestEngine.evaluate_arrest(
        vessel_name="MV OCEAN VOYAGER",
        claim_type=MaritimeClaimType.SALVAGE_OPERATIONS,
        claim_amount_usd=2000000.0,
        counter_security_provided_usd=300000.0,
        counter_security_type=ArrestSecurityType.BANK_GUARANTEE,
        security_for_release_provided_usd=2000000.0,  # 100% of claim
        release_security_type=ArrestSecurityType.PI_CLUB_LOU,
    )
    assert res.is_release_security_sufficient
    assert res.arrest_status == ArrestStatus.RELEASED_ON_SECURITY
    assert "SHIP RELEASE MANDATED" in res.verdict


def test_ship_arrest_expired_30d_limit():
    """Test automatic release when 30-day limit expires without court action."""
    res = MaritimeShipArrestEngine.evaluate_arrest(
        vessel_name="MV STAR HORIZON",
        claim_type=MaritimeClaimType.CHARTERPARTY_AGREEMENT,
        claim_amount_usd=800000.0,
        counter_security_provided_usd=120000.0,
        counter_security_type=ArrestSecurityType.BANK_GUARANTEE,
        arrest_date_iso="2026-08-01",
        assessment_date_iso="2026-09-15",  # 45 days > 30 days
        court_action_commenced=False,
    )
    assert res.is_expired_30d_limit
    assert res.days_under_arrest == 45
    assert res.arrest_status == ArrestStatus.RELEASED_EXPIRY
    assert "SHIP RELEASE MANDATED" in res.verdict


# ===========================================================================
# 3. Phase 204: General Average Adjustment (YAR 2016) Tests
# ===========================================================================

def test_general_average_adjustment_mathematical_balance():
    """Verify GA ratio and exact zero net balance across interests."""
    ship = GeneralAverageInterest(
        name="SHIP",
        sound_value_usd=10000000.0,
        ga_sacrifice_usd=500000.0,
        ga_expenditure_usd=250000.0,
    )
    cargo = GeneralAverageInterest(
        name="CARGO",
        sound_value_usd=5000000.0,
        ga_sacrifice_usd=300000.0,
        ga_expenditure_usd=0.0,
    )
    freight = GeneralAverageInterest(
        name="FREIGHT",
        sound_value_usd=500000.0,
        ga_sacrifice_usd=0.0,
        ga_expenditure_usd=0.0,
    )

    res = GeneralAverageYAREngine.calculate_adjustment(
        ship_interest=ship,
        cargo_interest=cargo,
        freight_interest=freight,
        interest_rate_pct=5.0,
        adjustment_delay_years=1.0,
    )

    assert res.total_ga_sacrifice_usd == 800000.0
    assert res.total_ga_expenditure_usd == 250000.0
    assert res.commission_allowance_usd == 5000.0  # 2% on 250,000 exp
    assert res.interest_allowance_usd == 52750.0  # 5% on 1,055,000
    assert res.gross_general_average_pool_usd == 1107750.0

    # Contributory values: Sound - Sac + Made Good
    assert res.ship_contributory_val_usd == 10500000.0
    assert res.cargo_contributory_val_usd == 5300000.0
    assert res.freight_contributory_val_usd == 500000.0
    assert res.total_contributory_val_usd == 16300000.0

    # Net sum of settlement balances must equal 0 within rounding
    net_sum = sum(res.settlement_balances_usd.values())
    assert abs(net_sum) < 0.1
    assert res.settlement_balances_usd["SHIP"] > 0  # Ship receives net
    assert res.settlement_balances_usd["CARGO"] < 0  # Cargo pays net
    assert res.settlement_balances_usd["FREIGHT"] < 0  # Freight pays net
    assert res.adjuster_certified


def test_general_average_zero_losses():
    """Verify handling when no sacrifices or expenditures occurred."""
    ship = GeneralAverageInterest("SHIP", 5000000.0, 0.0, 0.0)
    cargo = GeneralAverageInterest("CARGO", 2000000.0, 0.0, 0.0)
    freight = GeneralAverageInterest("FREIGHT", 100000.0, 0.0, 0.0)

    res = GeneralAverageYAREngine.calculate_adjustment(ship, cargo, freight)
    assert res.gross_general_average_pool_usd == 0.0
    assert res.ga_contribution_ratio == 0.0
    assert all(bal == 0.0 for bal in res.settlement_balances_usd.values())


# ===========================================================================
# 4. Phase 205: Maritime Liens Priority Waterfall Tests
# ===========================================================================

def test_maritime_lien_waterfall_full_and_prorated():
    """Test priority waterfall: superior liens paid in full, mortgage prorated."""
    claims = [
        LienClaimItem("C-00", MaritimeLienRank.RANK_0_JUDICIAL_AUCTION_COSTS, "Sheriff", 100000.0, "2026-09-25"),
        LienClaimItem("C-01", MaritimeLienRank.RANK_1_CREW_WAGES_REPATRIATION, "Crew", 250000.0, "2026-07-01"),
        LienClaimItem("C-02", MaritimeLienRank.RANK_2_LOSS_OF_LIFE_PERSONAL_INJURY, "Injured Workers", 400000.0, "2026-05-15"),
        LienClaimItem("C-03", MaritimeLienRank.RANK_3_SALVAGE_AND_GENERAL_AVERAGE, "Salvors", 500000.0, "2026-06-20"),
        LienClaimItem("C-04", MaritimeLienRank.RANK_4_PORT_DUES_PILOTAGE_FEES, "Port Authority", 150000.0, "2026-08-10"),
        LienClaimItem("C-05", MaritimeLienRank.RANK_5_COLLISION_TORT_PHYSICAL_DAMAGE, "Wharf Owner", 300000.0, "2026-04-01"),
        LienClaimItem("C-06", MaritimeLienRank.RANK_6_REGISTERED_MORTGAGE, "Maritime Bank", 1500000.0, "2024-01-01"),
    ]

    res = MaritimeLienPriorityEngine.calculate_priority_waterfall(
        vessel_name="MV PACIFIC CARRIER",
        gross_auction_proceeds_usd=3000000.0,
        claims=claims,
        auction_date_iso="2026-10-01",
    )

    assert res.total_disbursed_usd == 3000000.0
    assert res.remaining_surplus_to_owner_usd == 0.0

    # Ranks 0 to 5 take 100k + 250k + 400k + 500k + 150k + 300k = 1,700,000 USD
    # Mortgage (Rank 6) receives remaining 3,000,000 - 1,700,000 = 1,300,000 USD (shortfall 200,000)
    for s in res.settlements[:-1]:
        assert s.status == "FULLY_SATISFIED"
        assert s.paid_amount_usd == s.original_claim_usd

    mortgage_settlement = res.settlements[-1]
    assert mortgage_settlement.status == "PRORATED_PARTIAL_PAYMENT"
    assert mortgage_settlement.paid_amount_usd == 1300000.0
    assert mortgage_settlement.shortfall_amount_usd == 200000.0
    assert not res.mortgage_satisfied


def test_maritime_lien_prescription_extinction():
    """Test 1-year prescription extinction under VMC Art. 40."""
    claims = [
        # Claim arose on 2025-05-01, auction on 2026-10-01 (> 365 days) -> Extinguished!
        LienClaimItem("C-OLD", MaritimeLienRank.RANK_1_CREW_WAGES_REPATRIATION, "Former Crew", 200000.0, "2025-05-01"),
        # Current claim within 1 year
        LienClaimItem("C-NEW", MaritimeLienRank.RANK_1_CREW_WAGES_REPATRIATION, "Current Crew", 150000.0, "2026-06-01"),
    ]

    res = MaritimeLienPriorityEngine.calculate_priority_waterfall(
        vessel_name="MV AGED CARRIER",
        gross_auction_proceeds_usd=500000.0,
        claims=claims,
        auction_date_iso="2026-10-01",
    )

    old_s = next(s for s in res.settlements if s.claim_id == "C-OLD")
    new_s = next(s for s in res.settlements if s.claim_id == "C-NEW")

    assert old_s.is_extinguished_by_prescription
    assert old_s.status == "EXTINGUISHED_BY_1YEAR_PRESCRIPTION"
    assert old_s.paid_amount_usd == 0.0

    assert not new_s.is_extinguished_by_prescription
    assert new_s.status == "FULLY_SATISFIED"
    assert new_s.paid_amount_usd == 150000.0
    assert res.remaining_surplus_to_owner_usd == 350000.0


# ===========================================================================
# 5. Phase 206: Both-to-Blame Collision & Bunker 2001 Tests
# ===========================================================================

def test_collision_both_to_blame_cross_liabilities():
    """Verify proportional cross-liability calculation and personal injury recourse."""
    v_a = CollisionVesselParticulars(
        name="MV VIET DRAGON",
        gross_tonnage=12000.0,
        physical_damage_usd=800000.0,
        cargo_damage_usd=200000.0,
        demurrage_loss_usd=50000.0,
        bodily_injury_claims_paid_usd=300000.0,  # Paid all 300k
        has_valid_bunker_blue_card=True,
    )
    v_b = CollisionVesselParticulars(
        name="MV NORDIC TRADER",
        gross_tonnage=18000.0,
        physical_damage_usd=500000.0,
        cargo_damage_usd=100000.0,
        demurrage_loss_usd=40000.0,
        bodily_injury_claims_paid_usd=0.0,
        has_valid_bunker_blue_card=True,
    )

    res = CollisionAndBunkerPollutionEngine.assess_collision(
        vessel_a=v_a,
        vessel_b=v_b,
        fault_percentage_a=70.0,
        total_bodily_injury_pool_usd=300000.0,
    )

    assert res.fault_ratio_a == 0.70
    assert res.fault_ratio_b == 0.30

    # Total loss A = 800k + 200k + 50k = 1,050,000 USD
    # Total loss B = 500k + 100k + 40k = 640,000 USD
    assert res.total_loss_a_usd == 1050000.0
    assert res.total_loss_b_usd == 640000.0

    # A owes B: 70% of 640,000 = 448,000 USD
    # B owes A: 30% of 1,050,000 = 315,000 USD
    assert res.liability_a_to_b_usd == 448000.0
    assert res.liability_b_to_a_usd == 315000.0

    # Net: 448k - 315k = 133,000 USD payable by A
    assert res.net_cross_liability_usd == 133000.0
    assert res.net_paying_vessel == "MV VIET DRAGON"

    # Bodily injury: A paid 300k, A's fault share is 70% (210k).
    # Recourse against B for B's 30% share (90,000 USD)
    assert res.bodily_injury_recourse_usd == 90000.0
    assert res.recourse_claimant == "MV VIET DRAGON"
    assert res.bunker_convention_compliant


def test_collision_bunker_blue_card_deficiency():
    """Verify non-compliance flag when vessel > 1,000 GT lacks Blue Card."""
    v_a = CollisionVesselParticulars(
        name="MV NON_COMPLIANT",
        gross_tonnage=5000.0,
        physical_damage_usd=100000.0,
        cargo_damage_usd=0.0,
        demurrage_loss_usd=0.0,
        bodily_injury_claims_paid_usd=0.0,
        has_valid_bunker_blue_card=False,  # DEFICIENT
    )
    v_b = CollisionVesselParticulars(
        name="MV INNOCENT",
        gross_tonnage=2000.0,
        physical_damage_usd=50000.0,
        cargo_damage_usd=0.0,
        demurrage_loss_usd=0.0,
        bodily_injury_claims_paid_usd=0.0,
        has_valid_bunker_blue_card=True,
    )

    res = CollisionAndBunkerPollutionEngine.assess_collision(
        vessel_a=v_a,
        vessel_b=v_b,
        fault_percentage_a=100.0,
        total_bodily_injury_pool_usd=0.0,
    )

    assert not res.bunker_convention_compliant
    assert "DEFICIENT CERTIFICATION" in res.verdict


# ===========================================================================
# 6. Typer CLI Integration Tests
# ===========================================================================

def test_cli_shiparrest_audit():
    """Test CLI shiparrest audit command."""
    app = build_app()
    result = runner.invoke(app, ["shiparrest", "audit", "--vessel", "MV VIMC GLORY", "--amount", "2000000", "--counter-sec", "300000", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["vessel_name"] == "MV VIMC GLORY"
    assert data["mandatory_counter_security_usd"] == 300000.0
    assert data["is_counter_security_sufficient"] is True


def test_cli_genaverage_adjust():
    """Test CLI genaverage adjust command."""
    app = build_app()
    result = runner.invoke(app, ["genaverage", "adjust", "--ship-sound", "8000000", "--cargo-sound", "4000000", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["adjuster_certified"] is True
    assert "settlement_balances_usd" in data


def test_cli_lienpriority_waterfall():
    """Test CLI lienpriority waterfall command."""
    app = build_app()
    result = runner.invoke(app, ["lienpriority", "waterfall", "--vessel", "MV AUCTIONED", "--proceeds", "2500000", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["gross_auction_proceeds_usd"] == 2500000.0
    assert len(data["settlements"]) == 7


def test_cli_collision_assess():
    """Test CLI collision assess command."""
    app = build_app()
    result = runner.invoke(app, ["collision", "assess", "--vessel-a", "SHIP_A", "--vessel-b", "SHIP_B", "--fault-a", "60", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["fault_ratio_a"] == 0.6
    assert data["fault_ratio_b"] == 0.4
    assert data["net_paying_vessel"] == "SHIP_B"


# ===========================================================================
# 7. FastMCP Server Handler Tests
# ===========================================================================

def test_mcp_ship_arrest_handler():
    """Test FastMCP handle_ship_arrest_evaluate."""
    raw = mcp_srv.handle_ship_arrest_evaluate({
        "vessel_name": "MV FAST_MCP",
        "claim_amount_usd": 500000.0,
        "counter_security_provided_usd": 75000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["vessel_name"] == "MV FAST_MCP"
    assert res["is_counter_security_sufficient"] is True


def test_mcp_general_average_handler():
    """Test FastMCP handle_general_average_adjust."""
    raw = mcp_srv.handle_general_average_adjust({
        "ship_sound_value_usd": 6000000.0,
        "cargo_sound_value_usd": 3000000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["adjuster_certified"] is True


def test_mcp_maritime_lien_handler():
    """Test FastMCP handle_maritime_lien_waterfall."""
    raw = mcp_srv.handle_maritime_lien_waterfall({
        "vessel_name": "MV MCP_AUCTION",
        "gross_auction_proceeds_usd": 1500000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["gross_auction_proceeds_usd"] == 1500000.0


def test_mcp_collision_bunker_handler():
    """Test FastMCP handle_collision_bunker_assess."""
    raw = mcp_srv.handle_collision_bunker_assess({
        "vessel_a_name": "MV MCP_A",
        "vessel_b_name": "MV MCP_B",
        "fault_percentage_a": 80.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["fault_ratio_a"] == 0.8
