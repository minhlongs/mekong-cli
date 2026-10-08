"""Automated Test Suite for Phases 215-218 Maritime Engine, CLI & MCP Integration.

Covers:
- Phase 215: Maritime Passenger Transport & Athens Convention 2002 Liability (VMC Arts. 196-213)
- Phase 216: Ship Mortgage Foreclosure & Judicial Sale Auction Waterfall (VMC Arts. 37-42)
- Phase 217: Marine Bunkering & MARPOL Annex VI LSFO / Scrubber Compliance (Circular 40/2020)
- Phase 218: Maritime Pilotage Exemption & Navigational Safety (VMC Arts. 246-259)
"""

import ast
import json
import pytest
from typer.testing import CliRunner

from src.core.maritime_passenger_mortgage_bunker_pilot_engine import (
    MaritimePassengerCarrierLiabilityEngine,
    PassengerIncidentCategory,
    PassengerClaimItem,
    LuggageCategory,
    ShipMortgageForeclosureAuctionEngine,
    MortgagePriorityTier,
    ForeclosureClaimEntry,
    MarineBunkerFuelMarpolEngine,
    ScrubberType,
    BunkeringNavigationZone,
    MaritimePilotageExemptionEngine,
    VesselCargoRiskType,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_passenger_liability_assess,
    handle_ship_mortgage_foreclosure_auction,
    handle_marine_bunker_compliance_audit,
    handle_pilotage_exemption_evaluate,
)

runner = CliRunner()


# ===========================================================================
# 1. AST Zero-External-Dependency Invariant Test
# ===========================================================================
def test_ast_zero_external_dependency_invariant():
    """Verify that maritime_passenger_mortgage_bunker_pilot_engine.py only uses standard library modules."""
    engine_path = "src/core/maritime_passenger_mortgage_bunker_pilot_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_path)

    allowed_modules = {
        "dataclasses",
        "datetime",
        "enum",
        "math",
        "typing",
        "json",
        "hashlib",
        "re",
        "__future__",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed_modules, f"Disallowed external import: {root}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                assert root in allowed_modules, f"Disallowed external import from: {root}"


# ===========================================================================
# 2. Phase 215: Maritime Passenger Transport & Athens Convention 2002 Tests
# ===========================================================================
def test_phase215_shipping_incident_strict_liability_cap():
    """Shipping incident injury claim respects 250,000 SDR strict liability cap per passenger when faultless."""
    # 250,000 SDR * 1.33 = $332,500 USD
    claim = PassengerClaimItem(
        passenger_id="PAX-001",
        passenger_name="Alice Smith",
        death_or_personal_injury=True,
        claimed_injury_amount_usd=500000.0,
        contributory_negligence_percentage=0.0,
    )
    res = MaritimePassengerCarrierLiabilityEngine.evaluate_passenger_claims(
        case_ref="PAX-TEST-01",
        vessel_name="MV RIVER SUN",
        licensed_passenger_capacity=100,
        incident_category=PassengerIncidentCategory.SHIPPING_INCIDENT,
        claims=[claim],
        sdr_usd_rate=1.33,
        carrier_proven_faultless_above_strict=True,
    )
    assert res.total_claimed_usd == 500000.0
    expected_strict_cap = 250000.0 * 1.33
    assert res.net_carrier_liability_usd == pytest.approx(expected_strict_cap, 0.01)
    assert res.compulsory_financial_security_required is True
    assert res.compulsory_security_minimum_usd == pytest.approx(expected_strict_cap * 100, 0.01)


def test_phase215_fault_liability_and_contributory_negligence():
    """Carrier fault proves above strict liability cap up to 400,000 SDR, reduced by passenger negligence."""
    # Claim: $600,000 USD. Fault cap: 400,000 SDR * 1.33 = $532,000 USD.
    # 20% contributory negligence deductions: $532,000 * 0.80 = $425,600 USD.
    claim = PassengerClaimItem(
        passenger_id="PAX-002",
        passenger_name="Bob Jones",
        death_or_personal_injury=True,
        claimed_injury_amount_usd=600000.0,
        contributory_negligence_percentage=20.0,
    )
    res = MaritimePassengerCarrierLiabilityEngine.evaluate_passenger_claims(
        case_ref="PAX-TEST-02",
        vessel_name="MV CRUISE STAR",
        licensed_passenger_capacity=50,
        incident_category=PassengerIncidentCategory.SHIPPING_INCIDENT,
        claims=[claim],
        sdr_usd_rate=1.33,
        carrier_proven_faultless_above_strict=False,
    )
    expected_fault_cap = 400000.0 * 1.33
    assert res.gross_carrier_payable_usd == pytest.approx(expected_fault_cap, 0.01)
    assert res.contributory_negligence_deductions_usd == pytest.approx(expected_fault_cap * 0.20, 0.01)
    assert res.net_carrier_liability_usd == pytest.approx(expected_fault_cap * 0.80, 0.01)


def test_phase215_luggage_liability_caps():
    """Cabin luggage (2,250 SDR) and vehicle luggage (12,700 SDR) caps apply correctly."""
    cabin_claim = PassengerClaimItem(
        passenger_id="PAX-003",
        passenger_name="Charlie Brown",
        death_or_personal_injury=False,
        luggage_category=LuggageCategory.CABIN_LUGGAGE,
        claimed_luggage_amount_usd=5000.0,
    )
    res = MaritimePassengerCarrierLiabilityEngine.evaluate_passenger_claims(
        case_ref="PAX-TEST-03",
        vessel_name="MV SEA QUEEN",
        licensed_passenger_capacity=20,
        incident_category=PassengerIncidentCategory.NON_SHIPPING_INCIDENT,
        claims=[cabin_claim],
        sdr_usd_rate=1.33,
    )
    expected_cabin_cap = 2250.0 * 1.33
    assert res.net_carrier_liability_usd == pytest.approx(expected_cabin_cap, 0.01)


def test_phase215_war_defense_and_timebar_defense():
    """Exoneration under force majeure war defense and VMC Art. 212 2-year timebar."""
    claim = PassengerClaimItem(
        passenger_id="PAX-004",
        passenger_name="David White",
        death_or_personal_injury=True,
        claimed_injury_amount_usd=100000.0,
    )
    res_war = MaritimePassengerCarrierLiabilityEngine.evaluate_passenger_claims(
        case_ref="PAX-TEST-04",
        vessel_name="MV DEFENDER",
        licensed_passenger_capacity=10,
        incident_category=PassengerIncidentCategory.SHIPPING_INCIDENT,
        claims=[claim],
        war_or_natural_catastrophe_defense=True,
    )
    assert res_war.net_carrier_liability_usd == 0.0
    assert "exonerated" in res_war.verdict.lower()

    # Timebar after 2 years (730 days)
    res_timebar = MaritimePassengerCarrierLiabilityEngine.evaluate_passenger_claims(
        case_ref="PAX-TEST-05",
        vessel_name="MV DEFENDER",
        licensed_passenger_capacity=10,
        incident_category=PassengerIncidentCategory.SHIPPING_INCIDENT,
        claims=[claim],
        days_since_disembarkation=740,
    )
    assert res_timebar.timebar_prescribed is True
    assert res_timebar.net_carrier_liability_usd == 0.0


# ===========================================================================
# 3. Phase 216: Ship Mortgage Foreclosure & Judicial Auction Waterfall Tests
# ===========================================================================
def test_phase216_priority_distribution_waterfall():
    """Test statutory priority waterfall: Tier 0 -> Tier 1 -> Tier 2 -> Tier 3 -> Tier 4."""
    claims = [
        ForeclosureClaimEntry("Court Costs", MortgagePriorityTier.TIER_0_COURT_AND_AUCTION_COSTS, 100000.0),
        ForeclosureClaimEntry("Crew Wage Liens", MortgagePriorityTier.TIER_1_MARITIME_LIENS, 200000.0, lien_age_days=180),
        ForeclosureClaimEntry("Shipyard Possessory Lien", MortgagePriorityTier.TIER_2_POSSESSORY_REPAIRER_LIEN, 150000.0),
        ForeclosureClaimEntry("Bank 1st Mortgage", MortgagePriorityTier.TIER_3_REGISTERED_MORTGAGES, 1000000.0, mortgage_registration_order=1),
        ForeclosureClaimEntry("Bank 2nd Mortgage", MortgagePriorityTier.TIER_3_REGISTERED_MORTGAGES, 500000.0, mortgage_registration_order=2),
        ForeclosureClaimEntry("Trade Creditors", MortgagePriorityTier.TIER_4_UNSECURED_CREDITORS, 400000.0),
    ]

    # Total claimed: 2,350,000 USD. Winning bid: 2,000,000 USD.
    res = ShipMortgageForeclosureAuctionEngine.execute_foreclosure_distribution(
        auction_case_ref="AUC-TEST-01",
        vessel_name="MV PACIFIC TRADER",
        reserve_price_usd=1800000.0,
        actual_winning_bid_usd=2000000.0,
        claims=claims,
    )
    assert res.total_proceeds_distributed_usd == 2000000.0
    assert res.residual_surplus_to_owner_usd == 0.0
    assert res.title_purged_of_encumbrances is True

    # Payouts:
    # Tier 0: 100k (balance: 1.9M)
    # Tier 1: 200k (balance: 1.7M)
    # Tier 2: 150k (balance: 1.55M)
    # Tier 3 (1st Mortgage): 1,000k (balance: 550k)
    # Tier 3 (2nd Mortgage): 500k (balance: 50k)
    # Tier 4: gets remaining 50k out of 400k (12.5% recovery)
    payout_map = {d.creditor_name: d.payout_usd for d in res.distributions}
    assert payout_map["Court Costs"] == 100000.0
    assert payout_map["Crew Wage Liens"] == 200000.0
    assert payout_map["Shipyard Possessory Lien"] == 150000.0
    assert payout_map["Bank 1st Mortgage"] == 1000000.0
    assert payout_map["Bank 2nd Mortgage"] == 500000.0
    assert payout_map["Trade Creditors"] == pytest.approx(50000.0, 0.01)


def test_phase216_maritime_lien_1year_extinction():
    """Maritime lien older than 365 days is extinguished under VMC Art. 40 and demoted to Tier 4."""
    claims = [
        ForeclosureClaimEntry("Old Wage Claim", MortgagePriorityTier.TIER_1_MARITIME_LIENS, 50000.0, lien_age_days=400),
    ]
    res = ShipMortgageForeclosureAuctionEngine.execute_foreclosure_distribution(
        auction_case_ref="AUC-TEST-02",
        vessel_name="MV COASTAL RUNNER",
        reserve_price_usd=100000.0,
        actual_winning_bid_usd=120000.0,
        claims=claims,
    )
    # Extinguished lien is demoted to Tier 4
    assert res.distributions[0].tier == MortgagePriorityTier.TIER_4_UNSECURED_CREDITORS


def test_phase216_surplus_returned_to_owner():
    """Surplus remaining after all claims are satisfied is remitted to original shipowner."""
    claims = [
        ForeclosureClaimEntry("Total Debts", MortgagePriorityTier.TIER_0_COURT_AND_AUCTION_COSTS, 50000.0),
    ]
    res = ShipMortgageForeclosureAuctionEngine.execute_foreclosure_distribution(
        auction_case_ref="AUC-TEST-03",
        vessel_name="MV RICH SHIP",
        reserve_price_usd=100000.0,
        actual_winning_bid_usd=200000.0,
        claims=claims,
    )
    assert res.total_proceeds_distributed_usd == 50000.0
    assert res.residual_surplus_to_owner_usd == 150000.0


# ===========================================================================
# 4. Phase 217: Marine Bunkering & MARPOL Annex VI Tests
# ===========================================================================
def test_phase217_compliant_lsfo_bunkering():
    """Compliant LSFO bunkering meets 0.50% sulphur cap, flashpoint >= 60C, sample sealed, 3yr retention."""
    res = MarineBunkerFuelMarpolEngine.audit_bunkering_compliance(
        bdn_number="BDN-OK-01",
        vessel_name="MV MEKONG WAVE",
        imo_number="9876543",
        bunker_supplier_name="Saigon Marine Fuel",
        fuel_sulphur_content_percent=0.45,
        fuel_flashpoint_celsius=65.0,
        navigation_zone=BunkeringNavigationZone.GLOBAL_HIGH_SEAS,
        scrubber_installed=ScrubberType.NONE,
        marpol_sample_sealed=True,
        bdn_retention_years=3.0,
    )
    assert res.is_compliant is True
    assert "compliant" in res.verdict.lower()
    assert "none" in res.action_required.lower()


def test_phase217_sulphur_and_flashpoint_violations():
    """High sulphur without scrubber and low flashpoint (<60C) triggers non-compliance and corrective actions."""
    res = MarineBunkerFuelMarpolEngine.audit_bunkering_compliance(
        bdn_number="BDN-FAIL-01",
        vessel_name="MV MEKONG VIOLATOR",
        imo_number="9123456",
        bunker_supplier_name="Dodgy Fuel Ltd",
        fuel_sulphur_content_percent=0.65,
        fuel_flashpoint_celsius=55.0,
        navigation_zone=BunkeringNavigationZone.GLOBAL_HIGH_SEAS,
        scrubber_installed=ScrubberType.NONE,
    )
    assert res.is_compliant is False
    assert "non_compliant" in res.verdict.lower()
    assert "flashpoint_fire_hazard" in res.action_required.lower()
    assert "excess_sulphur" in res.action_required.lower()


def test_phase217_open_loop_scrubber_vietnam_port_prohibition():
    """Open-loop scrubber washwater discharge prohibited in Vietnamese internal port waters."""
    res = MarineBunkerFuelMarpolEngine.audit_bunkering_compliance(
        bdn_number="BDN-SCRUB-01",
        vessel_name="MV FOREIGN TANKER",
        imo_number="9988776",
        bunker_supplier_name="Global Bunkering",
        fuel_sulphur_content_percent=2.5,
        fuel_flashpoint_celsius=68.0,
        navigation_zone=BunkeringNavigationZone.VIETNAMESE_INTERNAL_PORT_WATERS,
        scrubber_installed=ScrubberType.OPEN_LOOP,
        scrubber_active=True,
        scrubber_washwater_ph=6.8,
        scrubber_turbidity_ntu_increase=10.0,
    )
    assert res.is_compliant is False
    assert "open_loop_port_ban" in res.action_required.lower()


# ===========================================================================
# 5. Phase 218: Maritime Pilotage Exemption Tests
# ===========================================================================
def test_phase218_eligible_pilotage_exemption():
    """Eligible vessel (<=2,000 GT, >=4 transits, clean safety, non-hazardous cargo) approved."""
    res = MaritimePilotageExemptionEngine.evaluate_pilotage_exemption(
        request_ref="EX-TEST-01",
        vessel_name="MV HAIPHONG EXPRESS",
        gross_tonnage=1500.0,
        length_overall_meters=75.0,
        draft_meters=4.5,
        flag_state="Vietnam",
        navigation_zone_name="Hai Phong Access Channel",
        captain_name="Capt. Le Van Hai",
        captain_past_transits_count_12mo=5,
        has_safety_infractions_past_12mo=False,
        cargo_risk=VesselCargoRiskType.GENERAL_CARGO_OR_CONTAINER,
    )
    assert res.exemption_approved is True
    assert res.statutory_pilotage_due_percent == 10.0
    assert res.mandatory_escort_tugs_count == 0
    assert len(res.disqualification_reasons) == 0


def test_phase218_disqualification_due_to_tonnage_and_cargo():
    """Vessels >2,000 GT or carrying LPG/LNG are disqualified from pilotage exemption."""
    res = MaritimePilotageExemptionEngine.evaluate_pilotage_exemption(
        request_ref="EX-TEST-02",
        vessel_name="MV GAS GIANT",
        gross_tonnage=5000.0,
        length_overall_meters=160.0,
        draft_meters=10.0,
        flag_state="Panama",
        navigation_zone_name="Vung Tau - Thi Vai",
        captain_name="Capt. Mark Vance",
        captain_past_transits_count_12mo=2,
        has_safety_infractions_past_12mo=False,
        cargo_risk=VesselCargoRiskType.LPG_LNG_GAS_CARRIER,
    )
    assert res.exemption_approved is False
    assert res.statutory_pilotage_due_percent == 100.0
    assert res.mandatory_escort_tugs_count == 2
    assert any("tonnage" in r.lower() for r in res.disqualification_reasons)
    assert any("hazardous_cargo" in r.lower() for r in res.disqualification_reasons)


# ===========================================================================
# 6. Typer CLI Sub-Apps Execution Tests
# ===========================================================================
def test_cli_passenger_assess_command():
    """Verify `passenger assess` CLI command executes and outputs formatted table and JSON."""
    app = build_app()
    result = runner.invoke(app, ["passenger", "assess", "--vessel", "MV MEKONG SPLENDOR", "--injury-claim", "100000"])
    assert result.exit_code == 0
    assert "Passenger Carrier Liability Assessment" in result.stdout

    # JSON mode
    result_json = runner.invoke(app, ["passenger", "assess", "--vessel", "MV MEKONG SPLENDOR", "--json"])
    assert result_json.exit_code == 0
    data = json.loads(result_json.stdout)
    assert data["vessel_name"] == "MV MEKONG SPLENDOR"
    assert "net_carrier_liability_usd" in data


def test_cli_mortgage_auction_command():
    """Verify `mortgage auction` CLI command executes correctly."""
    app = build_app()
    result = runner.invoke(app, ["mortgage", "auction", "--vessel", "MV VIET TRADER", "--winning-bid", "5000000"])
    assert result.exit_code == 0
    assert "Judicial Sale Priority Waterfall" in result.stdout

    # Vietnamese alias `thechaptaubien`
    result_vn = runner.invoke(app, ["thechaptaubien", "auction", "--vessel", "MV VIET TRADER", "--json"])
    assert result_vn.exit_code == 0
    data = json.loads(result_vn.stdout)
    assert data["vessel_name"] == "MV VIET TRADER"


def test_cli_bunker_audit_command():
    """Verify `bunker audit` CLI command executes correctly."""
    app = build_app()
    result = runner.invoke(app, ["bunker", "audit", "--bdn", "BDN-TEST-99", "--sulphur", "0.42"])
    assert result.exit_code == 0
    assert "Bunkering & MARPOL Annex VI Audit" in result.stdout

    # Vietnamese alias `nhienlieuhanghai`
    result_vn = runner.invoke(app, ["nhienlieuhanghai", "audit", "--bdn", "BDN-TEST-99", "--json"])
    assert result_vn.exit_code == 0
    data = json.loads(result_vn.stdout)
    assert data["bdn_number"] == "BDN-TEST-99"


def test_cli_pilotwaiver_check_command():
    """Verify `pilotwaiver check` CLI command executes correctly."""
    app = build_app()
    result = runner.invoke(app, ["pilotwaiver", "check", "--vessel", "MV CAN THO PACIFIC", "--gt", "1600"])
    assert result.exit_code == 0
    assert "Pilotage Exemption Assessment" in result.stdout

    # Vietnamese alias `mientruhoatieu`
    result_vn = runner.invoke(app, ["mientruhoatieu", "check", "--vessel", "MV CAN THO PACIFIC", "--json"])
    assert result_vn.exit_code == 0
    data = json.loads(result_vn.stdout)
    assert data["vessel_name"] == "MV CAN THO PACIFIC"


# ===========================================================================
# 7. FastMCP & JSON-RPC Handlers Integration Tests
# ===========================================================================
def test_mcp_passenger_liability_handler():
    """Verify `handle_passenger_liability_assess` MCP handler parses payload and executes."""
    res_str = handle_passenger_liability_assess({
        "case_ref": "PAX-MCP-01",
        "vessel_name": "MV DELTA CHARM",
        "licensed_passenger_capacity": 150,
        "claimed_injury_amount_usd": 200000.0,
    })
    data = json.loads(res_str)
    assert data["ok"] is True
    assert data["case_ref"] == "PAX-MCP-01"
    assert data["net_carrier_liability_usd"] > 0


def test_mcp_ship_mortgage_auction_handler():
    """Verify `handle_ship_mortgage_foreclosure_auction` MCP handler."""
    res_str = handle_ship_mortgage_foreclosure_auction({
        "auction_case_ref": "AUC-MCP-01",
        "vessel_name": "MV GLOBAL GIANT",
        "actual_winning_bid_usd": 6000000.0,
    })
    data = json.loads(res_str)
    assert data["ok"] is True
    assert data["auction_case_ref"] == "AUC-MCP-01"
    assert "distributions" in data


def test_mcp_marine_bunker_audit_handler():
    """Verify `handle_marine_bunker_compliance_audit` MCP handler."""
    res_str = handle_marine_bunker_compliance_audit({
        "bdn_number": "BDN-MCP-01",
        "vessel_name": "MV DANANG PRIDE",
        "fuel_sulphur_content_percent": 0.35,
    })
    data = json.loads(res_str)
    assert data["ok"] is True
    assert data["bdn_number"] == "BDN-MCP-01"
    assert data["is_compliant"] is True


def test_mcp_pilotage_exemption_handler():
    """Verify `handle_pilotage_exemption_evaluate` MCP handler."""
    res_str = handle_pilotage_exemption_evaluate({
        "request_ref": "EX-MCP-01",
        "vessel_name": "MV QUI NHON STAR",
        "gross_tonnage": 1700.0,
    })
    data = json.loads(res_str)
    assert data["ok"] is True
    assert data["request_ref"] == "EX-MCP-01"
    assert data["exemption_approved"] is True
