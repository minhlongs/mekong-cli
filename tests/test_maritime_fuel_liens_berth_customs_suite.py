"""
Unit & Integration Test Suite for Phases 275-278 Maritime Compliance, Port & Customs Suite.
Covers:
- Phase 275: MARPOL Annex VI Fuel Sulfur Cap & Port/ECA Fuel Oil Switchover Engine (MARPOL Annex VI Reg. 14, MEPC.1/Circ.864/Rev.1, Circular 39/2023/TT-BGTVT)
- Phase 276: Maritime Lien Priority Waterfall & Judicial Auction Proceeds Distribution Engine (VMC 2015 Arts. 37-43, Decree 62/2015/NĐ-CP)
- Phase 277: Seaport Berth Allocation Planning, Tidal Window UKC & Berth Occupancy Factor (BOR) Engine (Decree 58/2017 Arts. 53-61, Circular 39/2023, PIANC Report 158)
- Phase 278: Automated Customs Clearance Risk Channeling & Seaport VASSCM Clearance Engine (Law on Customs 2014 Arts. 16-17, Circular 38/2015 & 39/2018, Decisions 1399 & 2185/QĐ-TCHQ)

"""

import ast
import json
import pytest
from typer.testing import CliRunner

from src.core.maritime_fuel_liens_berth_customs_engine import (
    FuelSwitchoverEngine,
    FuelSwitchoverInput,
    FuelComplianceStatus,
    MaritimeLienWaterfallEngine,
    MaritimeClaimItem,
    ClaimType,
    LienTier,
    BerthPlanningUkcEngine,
    BerthAllocationInput,
    CustomsRiskVasscmEngine,
    CustomsRiskInput,
    CustomsChannel,
    EnterpriseComplianceLevel,
    VasscmGateCheckInput,
)
from src.cli.app_setup import build_app
import scripts.mcp_server as mcp_server


# ============================================================================
# 1. Zero External Dependencies Verification (AST Analysis)
# ============================================================================

def test_core_engine_zero_dependencies():
    """Verify that the core engine imports only Python standard library modules."""
    engine_file = "src/core/maritime_fuel_liens_berth_customs_engine.py"
    with open(engine_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_file)

    allowed_modules = {
        "math",
        "dataclasses",
        "typing",
        "enum",
        "datetime",
        "hashlib",
        "json",
    }

    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module.split(".")[0])

    unauthorized = imported_modules - allowed_modules
    assert not unauthorized, f"Unauthorized external dependencies found: {unauthorized}"


# ============================================================================
# 2. Phase 275: MARPOL Annex VI Fuel Switchover Engine Tests
# ============================================================================

def test_fuel_switchover_standard_calculation():
    """Test standard fuel switchover calculation from HFO (3.5%) to ULSFO/MGO (0.10%)."""
    data = FuelSwitchoverInput(
        vessel_name="MV MEKONG STAR",
        imo_number="9234567",
        system_volume_m3=3.6,
        fuel_consumption_m3_h=1.2,
        initial_sulfur_pct=3.50,
        low_sulfur_bunker_pct=0.08,
        target_sulfur_pct=0.10,
        initial_temp_c=135.0,
        target_temp_c=40.0,
        vessel_speed_knots=14.0,
        distance_to_boundary_nm=300.0,
        mgo_kinematic_viscosity_cst=2.8,
    )
    result = FuelSwitchoverEngine.calculate_switchover(data)

    assert result.status == FuelComplianceStatus.SWITCHOVER_FEASIBLE
    assert result.is_safe_to_execute is True
    assert result.dilution_duration_hours > 0.0
    assert result.thermal_ramp_duration_hours > 0.0
    assert result.required_switchover_distance_nm > 0.0
    assert result.remaining_distance_buffer_nm > 0.0
    assert result.cooling_rate_c_per_min <= 2.0


def test_fuel_switchover_distance_deficit_warning():
    """Test warning triggered when remaining distance to ECA boundary is insufficient."""
    data = FuelSwitchoverInput(
        vessel_name="MV RUSHING TANKER",
        imo_number="9234568",
        system_volume_m3=4.0,
        fuel_consumption_m3_h=1.0,
        initial_sulfur_pct=2.50,
        low_sulfur_bunker_pct=0.05,
        target_sulfur_pct=0.10,
        initial_temp_c=130.0,
        target_temp_c=40.0,
        vessel_speed_knots=15.0,
        distance_to_boundary_nm=10.0,  # Far too close!
        mgo_kinematic_viscosity_cst=3.0,
    )
    result = FuelSwitchoverEngine.calculate_switchover(data)
    assert result.status == FuelComplianceStatus.DISTANCE_DEFICIT_WARNING
    assert result.is_safe_to_execute is False
    assert result.remaining_distance_buffer_nm < 0.0


def test_fuel_switchover_viscosity_safety_violation():
    """Test safety violation when fuel viscosity at engine inlet drops below 2.0 cSt (ISO 8217)."""
    data = FuelSwitchoverInput(
        vessel_name="MV COLD RUN",
        imo_number="9234569",
        system_volume_m3=2.0,
        fuel_consumption_m3_h=1.0,
        initial_sulfur_pct=0.50,
        low_sulfur_bunker_pct=0.08,
        target_sulfur_pct=0.10,
        initial_temp_c=90.0,
        target_temp_c=45.0,
        vessel_speed_knots=12.0,
        distance_to_boundary_nm=150.0,
        mgo_kinematic_viscosity_cst=1.6,  # Below 2.0 cSt
    )
    result = FuelSwitchoverEngine.calculate_switchover(data)
    assert result.status == FuelComplianceStatus.VISCOSITY_SAFETY_VIOLATION
    assert result.is_safe_to_execute is False


def test_fuel_switchover_target_unattainable_error():
    """Test error when bunker fuel sulfur exceeds target sulfur limit."""
    data = FuelSwitchoverInput(
        vessel_name="MV DIRTY BUNKER",
        imo_number="9234570",
        system_volume_m3=2.0,
        fuel_consumption_m3_h=1.0,
        initial_sulfur_pct=2.50,
        low_sulfur_bunker_pct=0.15,  # Exceeds target 0.10%
        target_sulfur_pct=0.10,
        initial_temp_c=100.0,
        target_temp_c=40.0,
        vessel_speed_knots=12.0,
        distance_to_boundary_nm=100.0,
        mgo_kinematic_viscosity_cst=3.0,
    )
    result = FuelSwitchoverEngine.calculate_switchover(data)
    assert result.status == FuelComplianceStatus.TARGET_UNATTAINABLE_ERROR
    assert result.is_safe_to_execute is False


def test_fuel_switchover_already_compliant():
    """Test vessel already running compliant fuel."""
    data = FuelSwitchoverInput(
        vessel_name="MV GREEN RUNNER",
        imo_number="9234571",
        system_volume_m3=2.0,
        fuel_consumption_m3_h=1.0,
        initial_sulfur_pct=0.08,  # Already below 0.10%
        low_sulfur_bunker_pct=0.08,
        target_sulfur_pct=0.10,
        initial_temp_c=40.0,
        target_temp_c=40.0,
        vessel_speed_knots=12.0,
        distance_to_boundary_nm=50.0,
        mgo_kinematic_viscosity_cst=2.5,
    )
    result = FuelSwitchoverEngine.calculate_switchover(data)
    assert result.status == FuelComplianceStatus.ALREADY_COMPLIANT
    assert result.is_safe_to_execute is True
    assert result.critical_duration_hours == 0.0


# ============================================================================
# 3. Phase 276: Maritime Lien Priority Waterfall & Proceeds Distribution Tests
# ============================================================================

def test_maritime_lien_waterfall_full_distribution():
    """Test complete priority waterfall with court costs, statutory liens, mortgage, and unsecured claim."""
    claims = [
        MaritimeClaimItem(
            claim_id="CLM-01",
            claimant_name="Crew Union ABC",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_1_CREW_WAGES,
            claim_amount_vnd=1_000_000_000,
            claim_date_iso="2026-06-01",
        ),
        MaritimeClaimItem(
            claim_id="CLM-02",
            claimant_name="VietSal Marine Rescue",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_3_SALVAGE_GENERAL_AVERAGE,
            claim_amount_vnd=2_000_000_000,
            claim_date_iso="2026-08-01",
            salvage_timestamp_iso="2026-08-01T10:00:00",  # Newer salvage operation
        ),
        MaritimeClaimItem(
            claim_id="CLM-03",
            claimant_name="Old Salvage Co",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_3_SALVAGE_GENERAL_AVERAGE,
            claim_amount_vnd=1_500_000_000,
            claim_date_iso="2026-04-01",
            salvage_timestamp_iso="2026-04-01T10:00:00",  # Older salvage operation
        ),
        MaritimeClaimItem(
            claim_id="CLM-04",
            claimant_name="Haiphong Port Authority",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_4_PORT_SAFETY_DUES,
            claim_amount_vnd=500_000_000,
            claim_date_iso="2026-07-01",
        ),
        MaritimeClaimItem(
            claim_id="CLM-05",
            claimant_name="Maritime Commercial Bank (Mortgagee)",
            claim_type=ClaimType.SHIP_MORTGAGE,
            lien_tier=None,
            claim_amount_vnd=5_000_000_000,
            claim_date_iso="2025-01-01",
            mortgage_registration_iso="2025-01-01T08:00:00",
        ),
        MaritimeClaimItem(
            claim_id="CLM-06",
            claimant_name="Bunker Supplier XYZ (Unsecured)",
            claim_type=ClaimType.UNSECURED_MARITIME_CLAIM,
            lien_tier=None,
            claim_amount_vnd=2_000_000_000,
            claim_date_iso="2026-05-01",
        ),
    ]

    result = MaritimeLienWaterfallEngine.distribute_auction_proceeds(
        vessel_name="MV VIETNAM GLORY",
        gross_proceeds_vnd=10_000_000_000,
        auction_costs_vnd=500_000_000,
        claims=claims,
        auction_date_iso="2026-10-01",
    )

    assert result.net_distributable_funds_vnd == 9_500_000_000
    assert result.auction_enforcement_costs_vnd == 500_000_000
    assert result.total_statutory_liens_paid_vnd == 5_000_000_000
    assert result.total_mortgages_paid_vnd == 4_500_000_000
    assert result.total_unsecured_paid_vnd == 0
    assert result.unallocated_surplus_vnd == 0

    payout_map = {p.claim_id: p for p in result.claims_payout}
    assert payout_map["CLM-01"].paid_amount_vnd == 1_000_000_000
    assert payout_map["CLM-02"].paid_amount_vnd == 2_000_000_000
    assert payout_map["CLM-03"].paid_amount_vnd == 1_500_000_000
    assert payout_map["CLM-04"].paid_amount_vnd == 500_000_000
    assert payout_map["CLM-05"].paid_amount_vnd == 4_500_000_000
    assert payout_map["CLM-06"].paid_amount_vnd == 0


def test_maritime_lien_timebar_extinction():
    """Test statutory 1-year timebar under VMC 2015 Art. 39 extinguishing liens > 365 days without arrest."""
    claims = [
        MaritimeClaimItem(
            claim_id="CLM-EXPIRED",
            claimant_name="Stale Port Dues",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_4_PORT_SAFETY_DUES,
            claim_amount_vnd=800_000_000,
            claim_date_iso="2025-05-01",  # > 365 days before 2026-10-01
            arrest_prior_to_expiry=False,
        ),
        MaritimeClaimItem(
            claim_id="CLM-PRESERVED",
            claimant_name="Old Salvage with Arrest",
            claim_type=ClaimType.STATUTORY_LIEN,
            lien_tier=LienTier.TIER_3_SALVAGE_GENERAL_AVERAGE,
            claim_amount_vnd=1_000_000_000,
            claim_date_iso="2025-05-01",
            arrest_prior_to_expiry=True,  # Arrest preserves claim
            salvage_timestamp_iso="2025-05-01T12:00:00",
        ),
    ]

    result = MaritimeLienWaterfallEngine.distribute_auction_proceeds(
        vessel_name="MV TIMEBAR TEST",
        gross_proceeds_vnd=5_000_000_000,
        auction_costs_vnd=200_000_000,
        claims=claims,
        auction_date_iso="2026-10-01",
    )

    payout_map = {p.claim_id: p for p in result.claims_payout}
    assert payout_map["CLM-EXPIRED"].is_time_barred is True
    assert payout_map["CLM-EXPIRED"].paid_amount_vnd == 0
    assert payout_map["CLM-PRESERVED"].is_time_barred is False
    assert payout_map["CLM-PRESERVED"].paid_amount_vnd == 1_000_000_000


def test_maritime_lien_pro_rata_unsecured_distribution():
    """Test pro-rata distribution for multiple unsecured creditors sharing remaining funds."""
    claims = [
        MaritimeClaimItem(
            claim_id="UNSEC-1",
            claimant_name="Supplier 1",
            claim_type=ClaimType.UNSECURED_MARITIME_CLAIM,
            lien_tier=None,
            claim_amount_vnd=2_000_000_000,
            claim_date_iso="2026-08-01",
        ),
        MaritimeClaimItem(
            claim_id="UNSEC-2",
            claimant_name="Supplier 2",
            claim_type=ClaimType.UNSECURED_MARITIME_CLAIM,
            lien_tier=None,
            claim_amount_vnd=2_000_000_000,
            claim_date_iso="2026-08-01",
        ),
    ]

    result = MaritimeLienWaterfallEngine.distribute_auction_proceeds(
        vessel_name="MV PRO RATA",
        gross_proceeds_vnd=3_000_000_000,
        auction_costs_vnd=1_000_000_000,
        claims=claims,
        auction_date_iso="2026-10-01",
    )

    assert result.net_distributable_funds_vnd == 2_000_000_000
    payout_map = {p.claim_id: p for p in result.claims_payout}
    assert payout_map["UNSEC-1"].paid_amount_vnd == 1_000_000_000
    assert payout_map["UNSEC-2"].paid_amount_vnd == 1_000_000_000


# ============================================================================
# 4. Phase 277: Seaport Berth Allocation Planning, Dynamic UKC & BOR Tests
# ============================================================================

def test_berth_allocation_safe_window():
    """Test berth allocation with adequate slot length, dynamic UKC and acceptable BOR."""
    data = BerthAllocationInput(
        berth_id="TCIT-01",
        berth_length_m=380.0,
        charted_depth_m=16.0,
        vessel_name="CMA CGM MEKONG",
        loa_m=300.0,
        beam_m=48.0,
        static_draft_m=13.5,
        block_coefficient=0.70,
        transit_speed_knots=10.0,
        channel_width_m=200.0,
        is_confined_channel=False,
        water_density_kg_l=1.025,
        wave_response_m=0.3,
        tide_high_water_m=3.5,
        tide_low_water_m=1.0,
        tide_cycle_hours=12.4,
        hour_of_transit=1.0,
        high_water_hour=0.0,
        total_service_hours_period=400.0,
        period_hours=720.0,
        active_berths_count=1,
    )
    result = BerthPlanningUkcEngine.evaluate_berth_plan(data)

    assert result.is_slot_length_adequate is True
    assert result.is_ukc_safe is True
    assert result.salinity_sinkage_m == 0.0  # Seawater density 1.025
    assert result.dynamic_squat_m > 0.0
    assert result.calculated_ukc_m >= result.minimum_required_ukc_m
    assert result.berth_occupancy_rate_pct < 65.0
    assert result.is_bor_congested is False
    assert result.safe_transit_window_hours > 0.0


def test_berth_allocation_confined_squat_and_freshwater_sinkage():
    """Test freshwater sinkage in river water and higher squat in confined canal."""
    data = BerthAllocationInput(
        berth_id="SAIGON-K1",
        berth_length_m=220.0,
        charted_depth_m=11.0,
        vessel_name="MV DONG NAI",
        loa_m=200.0,
        beam_m=32.0,
        static_draft_m=9.5,
        block_coefficient=0.80,
        transit_speed_knots=8.0,
        channel_width_m=100.0,
        is_confined_channel=True,
        water_density_kg_l=1.005,  # Brackish river water
        wave_response_m=0.2,
        tide_high_water_m=2.5,
        tide_low_water_m=0.8,
        tide_cycle_hours=12.4,
        hour_of_transit=6.0,  # Low tide
        high_water_hour=0.0,
        total_service_hours_period=520.0,
        period_hours=720.0,
        active_berths_count=1,
    )
    result = BerthPlanningUkcEngine.evaluate_berth_plan(data)

    assert result.salinity_sinkage_m > 0.15  # Significant sinkage due to lower salinity
    assert result.is_slot_length_adequate is True
    assert result.berth_occupancy_rate_pct > 65.0
    assert result.is_bor_congested is True


# ============================================================================
# 5. Phase 278: Automated Customs Clearance & VASSCM Clearance Engine Tests
# ============================================================================

def test_customs_risk_channel_green():
    """Test low-risk declaration channeled to Green (Luồng Xanh) with SHA-256 token."""
    inp = CustomsRiskInput(
        declaration_number="105829104820",
        enterprise_tax_id="0101234567",
        enterprise_level=EnterpriseComplianceLevel.LEVEL_1_AEO_PRIORITY,
        hs_code="84713020",
        hs_risk_tier=0.15,
        origin_risk_tier=0.10,
        has_intelligence_alert=False,
        declared_value_usd=50000.0,
    )
    result = CustomsRiskVasscmEngine.evaluate_risk_channel(inp)

    assert result.channel == CustomsChannel.GREEN_CHANNEL
    assert result.risk_score < 0.35
    assert result.target_sla_hours < 0.01
    assert result.exempt_document_check is True
    assert result.exempt_physical_inspection is True
    assert result.release_token is not None
    assert len(result.release_token) == 24


def test_customs_risk_channel_yellow():
    """Test medium-risk declaration channeled to Yellow (Luồng Vàng)."""
    inp = CustomsRiskInput(
        declaration_number="105829104821",
        enterprise_tax_id="0309988776",
        enterprise_level=EnterpriseComplianceLevel.LEVEL_3_MEDIUM_COMPLIANCE,
        hs_code="61091010",
        hs_risk_tier=0.50,
        origin_risk_tier=0.50,
        has_intelligence_alert=False,
        declared_value_usd=80000.0,
    )
    result = CustomsRiskVasscmEngine.evaluate_risk_channel(inp)

    assert result.channel == CustomsChannel.YELLOW_CHANNEL
    assert 0.35 <= result.risk_score < 0.70
    assert result.target_sla_hours == 2.0
    assert result.exempt_document_check is False
    assert result.exempt_physical_inspection is True
    assert result.release_token is not None


def test_customs_risk_channel_red_due_to_alert():
    """Test immediate routing to Red (Luồng Đỏ) upon anti-smuggling alert."""
    inp = CustomsRiskInput(
        declaration_number="105829104822",
        enterprise_tax_id="0100000001",
        enterprise_level=EnterpriseComplianceLevel.LEVEL_1_AEO_PRIORITY,
        hs_code="84713020",
        hs_risk_tier=0.10,
        origin_risk_tier=0.10,
        has_intelligence_alert=True,  # Override by alert
        declared_value_usd=100000.0,
    )
    result = CustomsRiskVasscmEngine.evaluate_risk_channel(inp)

    assert result.channel == CustomsChannel.RED_CHANNEL
    assert result.target_sla_hours == 8.0
    assert result.exempt_physical_inspection is False


def test_vasscm_gate_verification_approved():
    """Test successful 3-way match gate-out clearance under Decision 2185/QĐ-TCHQ."""
    inp = VasscmGateCheckInput(
        declaration_number="105829104820",
        declaration_status="RELEASED",
        edo_number="EDO-VNM-202610-882",
        edo_is_valid=True,
        container_number="TCNU8839201",
        manifest_seal_number="VSS-99281A",
        gate_scanned_seal_number="VSS-99281A",
    )
    result = CustomsRiskVasscmEngine.verify_vasscm_gate_out(inp)

    assert result.is_gate_pass_approved is True
    assert result.match_status == "MATCH_SUCCESS"
    assert len(result.discrepancy_reasons) == 0
    assert len(result.vasscm_auth_hash) == 64


def test_vasscm_gate_verification_rejected():
    """Test gate-out rejection when container seal is tampered or customs clearance missing."""
    inp_tampered = VasscmGateCheckInput(
        declaration_number="105829104821",
        declaration_status="RELEASED",
        edo_number="EDO-VNM-202610-883",
        edo_is_valid=True,
        container_number="TCNU8839202",
        manifest_seal_number="VSS-11111",
        gate_scanned_seal_number="VSS-99999",  # Tampered seal
    )
    res_tampered = CustomsRiskVasscmEngine.verify_vasscm_gate_out(inp_tampered)
    assert res_tampered.is_gate_pass_approved is False
    assert any("Sai lệch số chì" in err for err in res_tampered.discrepancy_reasons)

    inp_uncleared = VasscmGateCheckInput(
        declaration_number="105829104822",
        declaration_status="PENDING",  # Not released
        edo_number="EDO-VNM-202610-884",
        edo_is_valid=True,
        container_number="TCNU8839203",
        manifest_seal_number="VSS-22222",
        gate_scanned_seal_number="VSS-22222",
    )
    res_uncleared = CustomsRiskVasscmEngine.verify_vasscm_gate_out(inp_uncleared)
    assert res_uncleared.is_gate_pass_approved is False
    assert any("chưa thông quan" in err for err in res_uncleared.discrepancy_reasons)


# ============================================================================
# 6. Typer CLI Integration Tests (All 4 Apps & Bilingual Aliases)
# ============================================================================

def test_cli_fuelswitch_calculate():
    """Test Typer fuelswitch calculate and doinhienlieu alias."""
    app = build_app()
    runner = CliRunner()

    result_en = runner.invoke(app, [
        "fuelswitch", "calculate",
        "--vessel", "MV PACIFIC",
        "--imo", "9551122",
        "--vol", "3.6",
        "--rate", "1.2",
        "--c0", "3.5",
        "--c-low", "0.08",
        "--target", "0.10",
        "--t0", "135.0",
        "--t-target", "40.0",
        "--speed", "14.0",
        "--dist", "300.0",
        "--visc", "2.8",
    ])
    assert result_en.exit_code == 0
    assert "TÍNH TOÁN CHUYỂN ĐỔI NHIÊN LIỆU MARPOL ANNEX VI" in result_en.stdout
    assert "MV PACIFIC" in result_en.stdout

    result_vn = runner.invoke(app, [
        "doinhienlieu", "calculate",
        "--vessel", "MV PACIFIC VN",
    ])
    assert result_vn.exit_code == 0
    assert "TÍNH TOÁN CHUYỂN ĐỔI NHIÊN LIỆU MARPOL ANNEX VI" in result_vn.stdout


def test_cli_maritimeliens_distribute():
    """Test Typer maritimeliens distribute and daugiahanghai alias."""
    app = build_app()
    runner = CliRunner()

    result_en = runner.invoke(app, [
        "maritimeliens", "distribute",
        "--vessel", "MV GLORY",
        "--gross", "80000000000",
        "--costs", "4000000000",
    ])
    assert result_en.exit_code == 0
    assert "PHÂN BỔ TIỀN BÁN ĐẤU GIÁ TÀU THEO QUYỀN CẦM GIỮ HÀNG HẢI" in result_en.stdout
    assert "MV GLORY" in result_en.stdout

    result_vn = runner.invoke(app, [
        "daugiahanghai", "distribute",
        "--vessel", "MV GLORY VN",
    ])
    assert result_vn.exit_code == 0
    assert "PHÂN BỔ TIỀN BÁN ĐẤU GIÁ TÀU" in result_vn.stdout


def test_cli_berthplan_evaluate():
    """Test Typer berthplan evaluate and dieudocau alias."""
    app = build_app()
    runner = CliRunner()

    result_en = runner.invoke(app, [
        "berthplan", "evaluate",
        "--berth", "TCIT-01",
        "--length", "380.0",
        "--depth", "16.0",
        "--vessel", "MV VINASHIP",
        "--loa", "200.0",
        "--beam", "32.0",
        "--draft", "10.5",
        "--density", "1.025",
    ])
    assert result_en.exit_code == 0
    assert "KẾ HOẠCH ĐIỀU ĐỘ CẦU BẾN & TÍNH TOÁN D-UKC THEO THỦY TRIỀU" in result_en.stdout
    assert "TCIT-01" in result_en.stdout

    result_vn = runner.invoke(app, [
        "dieudocau", "evaluate",
        "--berth", "DANANG-T2",
    ])
    assert result_vn.exit_code == 0
    assert "KẾ HOẠCH ĐIỀU ĐỘ CẦU BẾN" in result_vn.stdout


def test_cli_customsvasscm_channel_and_gate():
    """Test Typer customsvasscm channel, gate-out and haiquancang alias."""
    app = build_app()
    runner = CliRunner()

    # Risk channeling
    res_channel = runner.invoke(app, [
        "customsvasscm", "channel",
        "--decl", "109928374610",
        "--mst", "0109998881",
        "--level", "1",
        "--hs", "8471.30",
        "--hs-risk", "0.15",
        "--org-risk", "0.15",
        "--val", "50000.0",
    ])
    assert res_channel.exit_code == 0
    assert "PHÂN LUỒNG RỦI RO HẢI QUAN TỰ ĐỘNG" in res_channel.stdout
    assert "Luồng Xanh" in res_channel.stdout

    # Gate verification
    res_gate = runner.invoke(app, [
        "customsvasscm", "gate-out",
        "--decl", "109928374610",
        "--status", "RELEASED",
        "--edo", "EDO-202610-001",
        "--cntr", "MSKU9081234",
        "--m-seal", "SEAL-A1",
        "--g-seal", "SEAL-A1",
    ])
    assert res_gate.exit_code == 0
    assert "ĐỐI SOÁT 3 BÊN TẠI CỔNG RA CẢNG BIỂN - VASSCM" in res_gate.stdout
    assert "CHO PHÉP XUẤT CẢNG (PASS)" in res_gate.stdout

    # VN alias
    res_vn = runner.invoke(app, [
        "haiquancang", "channel",
        "--decl", "109928374610",
    ])
    assert res_vn.exit_code == 0
    assert "PHÂN LUỒNG RỦI RO HẢI QUAN TỰ ĐỘNG" in res_vn.stdout


# ============================================================================
# 7. FastMCP Server Tools & Handlers Integration Tests
# ============================================================================

def test_mcp_marpol_fuel_switchover_calculate():
    """Test MCP handler handle_marpol_fuel_switchover_calculate."""
    args = {
        "vessel_name": "MV PACIFIC HORIZON",
        "imo_number": "9123456",
        "system_volume_m3": 4.0,
        "fuel_consumption_m3_h": 1.2,
        "initial_sulfur_pct": 3.5,
        "low_sulfur_bunker_pct": 0.08,
        "target_sulfur_pct": 0.10,
        "initial_temp_c": 135.0,
        "target_temp_c": 40.0,
        "vessel_speed_knots": 14.0,
        "distance_to_boundary_nm": 300.0,
        "mgo_kinematic_viscosity_cst": 2.8,
    }
    raw = mcp_server.handle_marpol_fuel_switchover_calculate(args)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["fuel_switchover"]["status"] == "switchover_feasible"
    assert res["fuel_switchover"]["is_safe_to_execute"] is True
    assert res["fuel_switchover"]["required_switchover_distance_nm"] > 0


def test_mcp_maritime_lien_waterfall_distribute():
    """Test MCP handler handle_maritime_lien_waterfall_distribute."""
    args = {
        "vessel_name": "MV PACIFIC HORIZON",
        "gross_proceeds_vnd": 6_000_000_000,
        "auction_enforcement_costs_vnd": 300_000_000,
        "auction_date_iso": "2026-10-01",
        "claims": [
            {
                "claim_id": "CLM-M1",
                "claimant_name": "Seafarers Union",
                "claim_type": "statutory_lien",
                "lien_tier": 1,
                "claim_amount_vnd": 1_500_000_000,
                "claim_date_iso": "2026-06-01",
            },
            {
                "claim_id": "CLM-M2",
                "claimant_name": "Salvage Tug Saigon",
                "claim_type": "statutory_lien",
                "lien_tier": 3,
                "claim_amount_vnd": 2_000_000_000,
                "claim_date_iso": "2026-08-01",
                "salvage_timestamp_iso": "2026-08-01T08:00:00",
            }
        ]
    }
    raw = mcp_server.handle_maritime_lien_waterfall_distribute(args)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["lien_waterfall"]["net_distributable_funds_vnd"] == 5_700_000_000
    assert len(res["lien_waterfall"]["claims_payout"]) == 2


def test_mcp_berth_allocation_ukc_evaluate():
    """Test MCP handler handle_berth_allocation_ukc_evaluate."""
    args = {
        "berth_id": "TCIT-02",
        "berth_length_m": 400.0,
        "charted_depth_m": 16.5,
        "vessel_name": "MV MAERSK HANOI",
        "loa_m": 330.0,
        "beam_m": 48.0,
        "static_draft_m": 14.2,
        "transit_speed_knots": 11.0,
        "channel_width_m": 220.0,
        "is_confined_channel": False,
    }
    raw = mcp_server.handle_berth_allocation_ukc_evaluate(args)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["berth_ukc_evaluation"]["is_slot_length_adequate"] is True


def test_mcp_customs_risk_vasscm_verify():
    """Test MCP handler handle_customs_risk_vasscm_verify for risk-channel and gate-check modes."""
    # Risk-channel mode
    args_channel = {
        "action": "risk-channel",
        "declaration_number": "109887766554",
        "enterprise_tax_id": "0102030405",
        "enterprise_level": 1,
        "hs_code": "84713020",
        "hs_risk_tier": 0.15,
        "origin_risk_tier": 0.10,
        "declared_value_usd": 60000.0,
    }
    raw_channel = mcp_server.handle_customs_risk_vasscm_verify(args_channel)
    res_channel = json.loads(raw_channel)
    assert res_channel["ok"] is True
    assert res_channel["customs_channel"]["channel"] == 1  # GREEN_CHANNEL
    assert res_channel["customs_channel"]["release_token"] is not None

    # Gate-check mode
    args_gate = {
        "action": "gate-check",
        "declaration_number": "109887766554",
        "declaration_status": "RELEASED",
        "edo_number": "EDO-202610-101",
        "edo_is_valid": True,
        "container_number": "TCNU9988112",
        "manifest_seal_number": "SEAL-998",
        "gate_scanned_seal_number": "SEAL-998",
    }
    raw_gate = mcp_server.handle_customs_risk_vasscm_verify(args_gate)
    res_gate = json.loads(raw_gate)
    assert res_gate["ok"] is True
    assert res_gate["vasscm_gate_out"]["is_gate_pass_approved"] is True


def test_mcp_server_spec_and_core_handlers_registered():
    """Verify all 4 new tools exist in CORE_TOOLS_SPEC and CORE_HANDLERS."""
    tool_names = {t["name"] for t in mcp_server.CORE_TOOLS_SPEC}
    assert "mekong_marpol_fuel_switchover_calculate" in tool_names
    assert "mekong_maritime_lien_waterfall_distribute" in tool_names
    assert "mekong_berth_allocation_ukc_evaluate" in tool_names
    assert "mekong_customs_risk_vasscm_verify" in tool_names

    assert "mekong_marpol_fuel_switchover_calculate" in mcp_server.CORE_HANDLERS
    assert "marpol_fuel_switchover_calculate" in mcp_server.CORE_HANDLERS
    assert "mekong_maritime_lien_waterfall_distribute" in mcp_server.CORE_HANDLERS
    assert "maritime_lien_waterfall_distribute" in mcp_server.CORE_HANDLERS
    assert "mekong_berth_allocation_ukc_evaluate" in mcp_server.CORE_HANDLERS
    assert "berth_allocation_ukc_evaluate" in mcp_server.CORE_HANDLERS
    assert "mekong_customs_risk_vasscm_verify" in mcp_server.CORE_HANDLERS
    assert "customs_risk_vasscm_verify" in mcp_server.CORE_HANDLERS
