"""Test suite for Phases 279-282 Maritime BWMS, Ship Mortgage, Pilotage & FTZ Suite.

Zero-mock comprehensive test suite covering:
- Phase 279: Ballast Water Management System (BWMS) D-2 biological limits, D-1 exchange & TRO neutralization.
- Phase 280: Ship Mortgage Enforcement waterfall, statutory notice & Civil Code Art. 468 interest cap.
- Phase 281: Maritime Pilotage Service Allocation, Tariff (TT 39/2023) & SOLAS V/23 ladder safety.
- Phase 282: Seaport Free Trade Zone (FTZ) transshipment dwell limits & GPS E-seal corridor supervision.
- Typer CLI integration & FastMCP handlers integration.
"""

import json
import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    handle_bwms_d2_compliance_calculate,
    handle_maritime_pilotage_dues_calculate,
    handle_seaport_ftz_transshipment_verify,
    handle_ship_mortgage_enforcement_distribute,
)
from src.cli.app_setup import build_app
from src.core.maritime_bwms_mortgage_pilot_ftz_engine import (
    BwmComplianceStatus,
    BwmExchangeMethod,
    BwmSampleInput,
    BwmsComplianceEngine,
    ESealSecurityState,
    FtzDwellStatus,
    GeoCoordinate,
    MaritimePilotageDuesEngine,
    MortgageClaimCategory,
    PilotageZone,
    PilotLadderType,
    SeaportFtzTransshipmentEngine,
    ShipMortgageClaim,
    ShipMortgageEnforcementEngine,
    TransshipmentCargoInput,
)

app = build_app()
runner = CliRunner()


# ==============================================================================
# Phase 279: Ballast Water Management System (BWMS) Engine Tests
# ==============================================================================

def test_bwms_full_d2_compliance_pass():
    """Verify standard compliant sample passes D-2 biological and TRO discharge limits."""
    sample = BwmSampleInput(
        viable_organisms_ge_50um_per_m3=2.5,
        viable_organisms_10_to_50um_per_ml=4.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        e_coli_cfu_per_100ml=50.0,
        intestinal_enterococci_cfu_per_100ml=15.0,
        raw_tro_mg_l=3.0,
        neutralized_tro_mg_l=0.04,
        discharge_flow_rate_m3_h=1500.0,
    )
    result = BwmsComplianceEngine.evaluate_compliance("MV MEKONG STAR", "9812345", sample)

    assert result.d2_biological_pass is True
    assert result.tro_discharge_compliant is True
    assert result.compliance_status == BwmComplianceStatus.D2_COMPLIANT
    assert result.contingency_action is None
    assert result.required_neutralizer_rate_kg_h > 0
    assert len(result.verification_hash) == 24


def test_bwms_organism_large_fail():
    """Verify violation when organisms >= 50um exceed 10/m3 limit."""
    sample = BwmSampleInput(
        viable_organisms_ge_50um_per_m3=14.5,
        viable_organisms_10_to_50um_per_ml=3.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        e_coli_cfu_per_100ml=20.0,
        intestinal_enterococci_cfu_per_100ml=10.0,
        raw_tro_mg_l=2.0,
        neutralized_tro_mg_l=0.03,
    )
    result = BwmsComplianceEngine.evaluate_compliance("MV MEKONG STAR", "9812345", sample)

    assert result.d2_biological_pass is False
    assert result.compliance_status == BwmComplianceStatus.NON_COMPLIANT
    assert "BWM.2/Circ.62" in result.contingency_action


def test_bwms_microbial_indicators_fail():
    """Verify violation when pathogenic microbes (Vibrio cholerae, E. coli) exceed limits."""
    sample = BwmSampleInput(
        viable_organisms_ge_50um_per_m3=1.0,
        viable_organisms_10_to_50um_per_ml=2.0,
        vibrio_cholerae_cfu_per_100ml=2.0,  # Limit is < 1
        e_coli_cfu_per_100ml=300.0,         # Limit is < 250
        intestinal_enterococci_cfu_per_100ml=10.0,
        raw_tro_mg_l=2.0,
        neutralized_tro_mg_l=0.05,
    )
    result = BwmsComplianceEngine.evaluate_compliance("MV MEKONG STAR", "9812345", sample)

    assert result.d2_biological_pass is False
    assert result.compliance_status == BwmComplianceStatus.NON_COMPLIANT


def test_bwms_tro_neutralization_fail():
    """Verify violation when neutralized TRO at discharge exceeds 0.10 mg/L limit."""
    sample = BwmSampleInput(
        viable_organisms_ge_50um_per_m3=2.0,
        viable_organisms_10_to_50um_per_ml=3.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        e_coli_cfu_per_100ml=10.0,
        intestinal_enterococci_cfu_per_100ml=5.0,
        raw_tro_mg_l=4.5,
        neutralized_tro_mg_l=0.25,  # Exceeds 0.10 mg/L
    )
    result = BwmsComplianceEngine.evaluate_compliance("MV MEKONG STAR", "9812345", sample)

    assert result.d2_biological_pass is True
    assert result.tro_discharge_compliant is False
    assert result.compliance_status == BwmComplianceStatus.NON_COMPLIANT
    assert "BWM.2/Circ.62" in result.contingency_action


def test_bwms_d1_exchange_sequential_pass():
    """Verify D-1 sequential exchange passes when distance >= 200 NM and depth >= 200 m."""
    sample = BwmSampleInput(
        viable_organisms_ge_50um_per_m3=15.0,  # Fails D-2, but D-1 applies
        viable_organisms_10_to_50um_per_ml=20.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        e_coli_cfu_per_100ml=0.0,
        intestinal_enterococci_cfu_per_100ml=0.0,
        exchange_method=BwmExchangeMethod.SEQUENTIAL,
        exchange_volume_flushed_ratio=1.0,
        distance_from_land_nm=220.0,
        water_depth_m=250.0,
        raw_tro_mg_l=0.0,
        neutralized_tro_mg_l=0.0,
    )
    result = BwmsComplianceEngine.evaluate_compliance("MV MEKONG STAR", "9812345", sample)

    assert result.d1_exchange_pass is True
    assert result.compliance_status == BwmComplianceStatus.D1_COMPLIANT


def test_bwms_d1_exchange_flow_through():
    """Verify D-1 flow-through exchange requires 3x volume pumped for 95% efficiency."""
    # Ratio = 2.0 (below 3.0) -> fails 95%
    sample_low = BwmSampleInput(
        viable_organisms_ge_50um_per_m3=20.0,
        viable_organisms_10_to_50um_per_ml=20.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        e_coli_cfu_per_100ml=0.0,
        intestinal_enterococci_cfu_per_100ml=0.0,
        exchange_method=BwmExchangeMethod.FLOW_THROUGH,
        exchange_volume_flushed_ratio=2.0,
        distance_from_land_nm=250.0,
        water_depth_m=500.0,
    )
    result_low = BwmsComplianceEngine.evaluate_compliance("MV MEKONG STAR", "9812345", sample_low)
    assert result_low.d1_exchange_pass is False

    # Ratio = 3.2 -> passes
    sample_ok = BwmSampleInput(
        viable_organisms_ge_50um_per_m3=20.0,
        viable_organisms_10_to_50um_per_ml=20.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        e_coli_cfu_per_100ml=0.0,
        intestinal_enterococci_cfu_per_100ml=0.0,
        exchange_method=BwmExchangeMethod.FLOW_THROUGH,
        exchange_volume_flushed_ratio=3.2,
        distance_from_land_nm=250.0,
        water_depth_m=500.0,
    )
    result_ok = BwmsComplianceEngine.evaluate_compliance("MV MEKONG STAR", "9812345", sample_ok)
    assert result_ok.d1_exchange_pass is True


def test_bwms_d1_exchange_location_fail():
    """Verify D-1 exchange fails if distance or depth is insufficient."""
    sample = BwmSampleInput(
        viable_organisms_ge_50um_per_m3=25.0,  # Fails D-2
        viable_organisms_10_to_50um_per_ml=30.0,
        vibrio_cholerae_cfu_per_100ml=0.0,
        e_coli_cfu_per_100ml=0.0,
        intestinal_enterococci_cfu_per_100ml=0.0,
        exchange_method=BwmExchangeMethod.SEQUENTIAL,
        distance_from_land_nm=35.0,  # Below 50 NM fallback
        water_depth_m=100.0,         # Below 200 m
    )
    result = BwmsComplianceEngine.evaluate_compliance("MV MEKONG STAR", "9812345", sample)
    assert result.d1_exchange_pass is False
    assert result.compliance_status == BwmComplianceStatus.NON_COMPLIANT


# ==============================================================================
# Phase 280: Ship Mortgage Enforcement Engine Tests
# ==============================================================================

def test_mortgage_waterfall_full_recovery():
    """Verify statutory priority waterfall when gross proceeds exceed all claims."""
    claims = [
        ShipMortgageClaim("C1", "Court Auction Bailiff", MortgageClaimCategory.ENFORCEMENT_COSTS, 0, 2_000_000_000.0),
        ShipMortgageClaim("L1", "Seafarers Wage Claims (Art. 37)", MortgageClaimCategory.MARITIME_LIEN, 0, 8_000_000_000.0),
        ShipMortgageClaim("M1", "Maritime Bank 1st Rank", MortgageClaimCategory.REGISTERED_MORTGAGE, 1, 40_000_000_000.0, 3_000_000_000.0, annual_interest_rate_pct=10.0),
        ShipMortgageClaim("M2", "Saigon Commercial Bank 2nd Rank", MortgageClaimCategory.REGISTERED_MORTGAGE, 2, 10_000_000_000.0, 500_000_000.0, annual_interest_rate_pct=12.0),
    ]

    report = ShipMortgageEnforcementEngine.process_enforcement_waterfall(
        vessel_name="MV MEKONG CARRIER",
        vessel_registry_no="VN-3399-HP",
        gross_proceeds_vnd=70_000_000_000.0,
        notice_period_days=18,
        claims=claims,
    )

    assert report.statutory_notice_valid is True
    assert report.total_claims_satisfied_vnd == 63_500_000_000.0
    assert report.shipowner_residual_vnd == 6_500_000_000.0
    assert len(report.allocations) == 4
    for a in report.allocations:
        assert a.unpaid_balance_vnd == 0.0


def test_mortgage_waterfall_deficit_partial_allocation():
    """Verify priority waterfall haircuts lower rank mortgages when proceeds are insufficient."""
    claims = [
        ShipMortgageClaim("C1", "Enforcement Costs", MortgageClaimCategory.ENFORCEMENT_COSTS, 0, 3_000_000_000.0),
        ShipMortgageClaim("L1", "Maritime Liens", MortgageClaimCategory.MARITIME_LIEN, 0, 10_000_000_000.0),
        ShipMortgageClaim("M1", "Rank 1 Bank", MortgageClaimCategory.REGISTERED_MORTGAGE, 1, 30_000_000_000.0),
        ShipMortgageClaim("M2", "Rank 2 Bank", MortgageClaimCategory.REGISTERED_MORTGAGE, 2, 20_000_000_000.0),
    ]

    # Gross proceeds: 35 billion (Costs: 3b, Liens: 10b, Rank 1: 22b remaining out of 30b, Rank 2: 0b)
    report = ShipMortgageEnforcementEngine.process_enforcement_waterfall(
        vessel_name="MV MEKONG DEFICIT",
        vessel_registry_no="VN-1122-SG",
        gross_proceeds_vnd=35_000_000_000.0,
        notice_period_days=15,
        claims=claims,
    )

    assert report.allocations[0].allocated_amount_vnd == 3_000_000_000.0
    assert report.allocations[1].allocated_amount_vnd == 10_000_000_000.0
    assert report.allocations[2].allocated_amount_vnd == 22_000_000_000.0
    assert report.allocations[2].unpaid_balance_vnd == 8_000_000_000.0
    assert report.allocations[3].allocated_amount_vnd == 0.0
    assert report.allocations[3].unpaid_balance_vnd == 20_000_000_000.0
    assert report.shipowner_residual_vnd == 0.0


def test_mortgage_civil_code_interest_cap():
    """Verify Civil Code 2015 Art. 468 20% cap trims excess contractual interest."""
    claims = [
        ShipMortgageClaim(
            claim_id="M1",
            creditor_name="Usurious Private Lender",
            category=MortgageClaimCategory.REGISTERED_MORTGAGE,
            registration_rank=1,
            principal_vnd=10_000_000_000.0,
            contractual_interest_vnd=3_000_000_000.0,  # 30% interest claimed
            annual_interest_rate_pct=30.0,
        )
    ]

    report = ShipMortgageEnforcementEngine.process_enforcement_waterfall(
        vessel_name="MV MEKONG DEBTOR",
        vessel_registry_no="VN-7788-DN",
        gross_proceeds_vnd=20_000_000_000.0,
        notice_period_days=20,
        claims=claims,
    )

    # Claimed principal + interest was 13.0b, capped interest admitted at 20% -> allocated 12.0b
    alloc = report.allocations[0]
    assert alloc.claimed_amount_vnd == 13_000_000_000.0
    assert alloc.allocated_amount_vnd == 12_000_000_000.0
    assert alloc.interest_haircut_vnd == 1_000_000_000.0
    assert report.interest_cap_enforced is True


def test_mortgage_notice_period_invalid():
    """Verify notice period < 15 days triggers statutory violation flag under VMC Art. 34."""
    claims = [
        ShipMortgageClaim("C1", "Court", MortgageClaimCategory.ENFORCEMENT_COSTS, 0, 1_000_000_000.0)
    ]
    report = ShipMortgageEnforcementEngine.process_enforcement_waterfall(
        vessel_name="MV MEKONG SPEEDY",
        vessel_registry_no="VN-0011-HP",
        gross_proceeds_vnd=10_000_000_000.0,
        notice_period_days=10,  # Statutory minimum is 15 days
        claims=claims,
    )
    assert report.statutory_notice_valid is False


# ==============================================================================
# Phase 281: Maritime Pilotage Service & SOLAS V/23 Engine Tests
# ==============================================================================

def test_pilot_ladder_single_arrangement_safe():
    """Verify safe single pilot ladder when freeboard <= 9m and climbing height in range."""
    safety = MaritimePilotageDuesEngine.evaluate_pilot_ladder(
        freeboard_m=6.5,
        climbing_height_m=5.0,
        accommodation_angle_deg=40.0,
    )
    assert safety.required_arrangement == PilotLadderType.SINGLE_PILOT_LADDER
    assert safety.is_safe is True
    assert len(safety.violations) == 0


def test_pilot_ladder_combination_required_and_safe():
    """Verify combination arrangement is mandated when freeboard > 9m."""
    safety = MaritimePilotageDuesEngine.evaluate_pilot_ladder(
        freeboard_m=11.2,
        climbing_height_m=6.0,
        accommodation_angle_deg=40.0,
    )
    assert safety.required_arrangement == PilotLadderType.COMBINATION_ARRANGEMENT
    assert safety.is_safe is True


def test_pilot_ladder_violations_unsafe_height_and_angle():
    """Verify violations when climbing height exceeds 9m or ladder angle exceeds 55 degrees."""
    safety = MaritimePilotageDuesEngine.evaluate_pilot_ladder(
        freeboard_m=12.0,
        climbing_height_m=10.5,  # Exceeds 9m
        accommodation_angle_deg=60.0,  # Exceeds 55 degrees
    )
    assert safety.is_safe is False
    assert any("9.0m" in v for v in safety.violations)
    assert any("55 độ" in v for v in safety.violations)


def test_pilotage_dues_calculation_standard_zone_i():
    """Verify Circular 39/2023 tariff calculation with night and weather standby surcharges."""
    calc = MaritimePilotageDuesEngine.calculate_pilotage_dues(
        vessel_name="MV PACIFIC DISCOVERY",
        gross_tonnage=20000.0,
        distance_nm=25.0,
        zone=PilotageZone.ZONE_I,
        freeboard_m=8.5,
        climbing_height_m=5.5,
        is_night_transit=True,
        weather_standby_hours=3.0,
    )
    # Zone I rate = 0.0035 USD / GT-NM
    # Base = 20,000 * 25 * 0.0035 = 1,750.0 USD
    # Night (+40%) = 700.0 USD
    # Weather standby = 3 * 20.0 = 60.0 USD
    # Total = 1750 + 700 + 60 = 2,510.0 USD
    assert calc.base_charge_usd == pytest.approx(1750.0, 0.01)
    assert calc.night_surcharge_usd == pytest.approx(700.0, 0.01)
    assert calc.weather_standby_charge_usd == pytest.approx(60.0, 0.01)
    assert calc.total_dues_usd == pytest.approx(2510.0, 0.01)
    assert calc.is_exempt is False


def test_pilotage_statutory_exemption_domestic_tonnage():
    """Verify domestic vessel < 2000 GT exemption under VMC 2015 Art. 248."""
    calc = MaritimePilotageDuesEngine.calculate_pilotage_dues(
        vessel_name="MV MEKONG COASTAL",
        gross_tonnage=1500.0,
        distance_nm=15.0,
        zone=PilotageZone.ZONE_II,
        freeboard_m=3.0,
        climbing_height_m=2.5,
        is_domestic_exempt=True,
    )
    assert calc.is_exempt is True
    assert calc.total_dues_usd == 0.0
    assert "2,000 GT" in calc.exemption_reason


def test_pilotage_statutory_exemption_master_experience():
    """Verify certified master with >= 10 calls in last 12 months exemption."""
    calc = MaritimePilotageDuesEngine.calculate_pilotage_dues(
        vessel_name="MV MEKONG FREQUENT",
        gross_tonnage=5000.0,
        distance_nm=15.0,
        zone=PilotageZone.ZONE_I,
        freeboard_m=5.0,
        climbing_height_m=3.5,
        qualifying_calls_last_12m=12,
    )
    assert calc.is_exempt is True
    assert calc.total_dues_usd == 0.0
    assert ">= 10" in calc.exemption_reason


def test_pilotage_cancellation_penalty():
    """Verify pilotage cancellation fee based on notification lead time."""
    # Under 2 hours notice: 80% of minimum base charge ($160 for Zone I $200 min)
    calc_late = MaritimePilotageDuesEngine.calculate_pilotage_dues(
        vessel_name="MV MEKONG CANCEL",
        gross_tonnage=1000.0,
        distance_nm=5.0,
        zone=PilotageZone.ZONE_I,
        freeboard_m=4.0,
        climbing_height_m=3.0,
        late_cancellation_hours=1.0,
    )
    assert calc_late.cancellation_penalty_usd == pytest.approx(160.0, 0.01)

    # 3 hours notice: 10% of minimum base charge ($20)
    calc_early = MaritimePilotageDuesEngine.calculate_pilotage_dues(
        vessel_name="MV MEKONG CANCEL",
        gross_tonnage=1000.0,
        distance_nm=5.0,
        zone=PilotageZone.ZONE_I,
        freeboard_m=4.0,
        climbing_height_m=3.0,
        late_cancellation_hours=3.0,
    )
    assert calc_early.cancellation_penalty_usd == pytest.approx(20.0, 0.01)


# ==============================================================================
# Phase 282: Seaport FTZ Transshipment Cargo Supervision Engine Tests
# ==============================================================================

def test_ftz_cargo_normal_dwell_and_secure_corridor():
    """Verify cargo within 30 days and inside GPS corridor receives clearance."""
    cargo = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC11223",
        container_no="TEMU1234567",
        discharge_date="2026-09-25",
        current_date="2026-10-08",  # 13 days dwell
        current_coordinate=GeoCoordinate(10.6420, 106.8427),
        e_seal_cable_intact=True,
        e_seal_tamper_switch=False,
        battery_level_pct=90.0,
    )
    result = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo)

    assert result.dwell_days == 13
    assert result.dwell_status == FtzDwellStatus.NORMAL
    assert result.e_seal_status == ESealSecurityState.SECURE
    assert result.statutory_clearance_granted is True
    assert "thời hạn lưu bãi" in result.action_required
    assert len(result.integrity_token) == 24


def test_ftz_cargo_warning_and_urgent_dwell_milestones():
    """Verify warning (20-24 days) and urgent (25-30 days) dwell status."""
    # 22 days -> WARNING
    cargo_warn = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC11224",
        container_no="TEMU1234568",
        discharge_date="2026-09-16",
        current_date="2026-10-08",
        current_coordinate=GeoCoordinate(10.6420, 106.8427),
    )
    res_warn = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo_warn)
    assert res_warn.dwell_days == 22
    assert res_warn.dwell_status == FtzDwellStatus.WARNING

    # 28 days -> URGENT
    cargo_urg = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC11225",
        container_no="TEMU1234569",
        discharge_date="2026-09-10",
        current_date="2026-10-08",
        current_coordinate=GeoCoordinate(10.6420, 106.8427),
    )
    res_urg = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo_urg)
    assert res_urg.dwell_days == 28
    assert res_urg.dwell_status == FtzDwellStatus.URGENT


def test_ftz_cargo_overstay_without_extension():
    """Verify cargo exceeding 30 days without extension is flagged overstay."""
    cargo = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC99001",
        container_no="TEMU9999999",
        discharge_date="2026-08-25",
        current_date="2026-10-08",  # 44 days dwell
        extension_approved=False,
        current_coordinate=GeoCoordinate(10.6420, 106.8427),
    )
    result = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo)

    assert result.dwell_days == 44
    assert result.dwell_status == FtzDwellStatus.OVERSTAY
    assert result.statutory_clearance_granted is False
    assert "Quá hạn lưu bãi" in result.action_required


def test_ftz_cargo_extended_dwell_up_to_60_days():
    """Verify cargo with approved extension allows up to 60 days dwell."""
    cargo = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC99002",
        container_no="TEMU8888888",
        discharge_date="2026-08-25",
        current_date="2026-10-08",  # 44 days dwell
        extension_approved=True,     # Up to 60 days allowed
        current_coordinate=GeoCoordinate(10.6420, 106.8427),
    )
    result = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo)

    assert result.dwell_days == 44
    assert result.dwell_status == FtzDwellStatus.EXTENDED
    assert result.statutory_clearance_granted is True


def test_ftz_eseal_corridor_deviation():
    """Verify corridor deviation exceeding 500m flags deviation status."""
    cargo = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC99003",
        container_no="TEMU7777777",
        discharge_date="2026-10-01",
        current_date="2026-10-08",
        # Route is 10.5218, 107.0253 -> 10.7626, 106.6601
        # Test coordinate deviated far inland:
        current_coordinate=GeoCoordinate(11.1000, 106.5000),
    )
    result = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo)

    assert result.corridor_deviation_meters > 500.0
    assert result.e_seal_status == ESealSecurityState.CORRIDOR_DEVIATION
    assert result.statutory_clearance_granted is False


def test_ftz_eseal_physical_tamper_and_cable_cut():
    """Verify physical cable cut and tamper switch triggers TAMPERED status."""
    # Cable cut
    cargo_cut = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC99004",
        container_no="TEMU6666666",
        discharge_date="2026-10-01",
        current_date="2026-10-08",
        e_seal_cable_intact=False,
    )
    res_cut = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo_cut)
    assert res_cut.e_seal_status == ESealSecurityState.TAMPERED_CUT
    assert res_cut.statutory_clearance_granted is False

    # Tamper switch
    cargo_switch = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC99005",
        container_no="TEMU5555555",
        discharge_date="2026-10-01",
        current_date="2026-10-08",
        e_seal_tamper_switch=True,
    )
    res_switch = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo_switch)
    assert res_switch.e_seal_status == ESealSecurityState.TAMPERED_CUT
    assert res_switch.statutory_clearance_granted is False


def test_ftz_eseal_low_battery():
    """Verify battery level < 15% triggers BATTERY_CRITICAL status."""
    cargo = TransshipmentCargoInput(
        declaration_no="OTL-2026-TC99006",
        container_no="TEMU4444444",
        discharge_date="2026-10-01",
        current_date="2026-10-08",
        current_coordinate=GeoCoordinate(10.6420, 106.8427),
        battery_level_pct=10.0,
    )
    result = SeaportFtzTransshipmentEngine.supervise_transshipment(cargo)
    assert result.e_seal_status == ESealSecurityState.BATTERY_CRITICAL


# ==============================================================================
# CLI Command Integration Tests
# ==============================================================================

def test_cli_bwms_command():
    """Test Typer bwms evaluate command."""
    res = runner.invoke(app, [
        "bwms",
        "evaluate",
        "--vessel", "MV TEST BWMS",
        "--imo", "1234567",
        "--org-50", "1.5",
        "--org-10", "3.0",
        "--raw-tro", "2.8",
        "--neutral-tro", "0.03",
    ])
    assert res.exit_code == 0
    assert "ĐÁNH GIÁ XẢ NƯỚC DẰN TÀU" in res.output
    assert "MV TEST BWMS" in res.output
    assert "D2_COMPLIANT" in res.output


def test_cli_mortgage_command():
    """Test Typer mortgage enforce command."""
    res = runner.invoke(app, [
        "mortgage",
        "enforce",
        "--vessel", "MV TEST MORTGAGE",
        "--reg", "VN-9999-HP",
        "--proceeds", "50000000000",
        "--notice", "21",
    ])
    assert res.exit_code == 0
    assert "XỬ LÝ THẾ CHẤP TÀU BIỂN" in res.output
    assert "VN-9999-HP" in res.output
    assert "HỢP LỆ" in res.output


def test_cli_pilotage_command():
    """Test Typer pilotage dues command."""
    res = runner.invoke(app, [
        "pilotage",
        "dues",
        "--vessel", "MV TEST PILOT",
        "--gt", "25000",
        "--dist", "30",
        "--zone", "ZONE_I",
        "--freeboard", "10.5",
        "--climb", "6.0",
        "--night",
    ])
    assert res.exit_code == 0
    assert "ĐIỀU ĐỘ HOA TIÊU HÀNG HẢI" in res.output
    assert "MV TEST PILOT" in res.output
    assert "TỔNG CƯỚC HOA TIÊU" in res.output


def test_cli_ftz_command():
    """Test Typer ftz supervise command."""
    res = runner.invoke(app, [
        "seaportftz",
        "supervise",
        "--dec", "OTL-2026-TEST01",
        "--cont", "CONT1234567",
        "--discharge", "2026-09-20",
        "--current", "2026-10-08",
        "--lat", "10.6420",
        "--lon", "106.8427",
    ])
    assert res.exit_code == 0
    assert "GIÁM SÁT HÀNG TRUNG CHUYỂN QUỐC TẾ" in res.output
    assert "CONT1234567" in res.output
    assert "SECURE" in res.output


# ==============================================================================
# FastMCP Handlers Tests
# ==============================================================================

def test_mcp_handler_bwms_roundtrip():
    """Test MCP handler for mekong_bwms_d2_compliance_calculate."""
    payload = {
        "vessel_name": "MV MCP BWMS",
        "imo_number": "9988776",
        "viable_organisms_ge_50um_per_m3": 1.2,
        "viable_organisms_10_to_50um_per_ml": 2.5,
        "raw_tro_mg_l": 2.5,
        "neutralized_tro_mg_l": 0.05,
    }
    raw_res = handle_bwms_d2_compliance_calculate(payload)
    parsed = json.loads(raw_res)
    assert parsed["ok"] is True
    assert parsed["bwms_evaluation"]["compliance_status"] == "D2_COMPLIANT"


def test_mcp_handler_ship_mortgage_roundtrip():
    """Test MCP handler for mekong_ship_mortgage_enforcement_distribute."""
    payload = {
        "vessel_name": "MV MCP MORTGAGE",
        "vessel_registry_no": "VN-MCP-01",
        "gross_proceeds_vnd": 60000000000.0,
        "notice_period_days": 18,
    }
    raw_res = handle_ship_mortgage_enforcement_distribute(payload)
    parsed = json.loads(raw_res)
    assert parsed["ok"] is True
    assert parsed["mortgage_enforcement"]["statutory_notice_valid"] is True


def test_mcp_handler_pilotage_dues_roundtrip():
    """Test MCP handler for mekong_maritime_pilotage_dues_calculate."""
    payload = {
        "vessel_name": "MV MCP PILOT",
        "gross_tonnage": 15000.0,
        "distance_nm": 20.0,
        "zone": "ZONE_II",
        "freeboard_m": 8.0,
        "climbing_height_m": 5.0,
    }
    raw_res = handle_maritime_pilotage_dues_calculate(payload)
    parsed = json.loads(raw_res)
    assert parsed["ok"] is True
    assert parsed["pilotage_dues"]["total_dues_usd"] > 0


def test_mcp_handler_ftz_transshipment_roundtrip():
    """Test MCP handler for mekong_seaport_ftz_transshipment_verify."""
    payload = {
        "declaration_no": "OTL-MCP-88",
        "container_no": "CONT8888888",
        "discharge_date": "2026-09-28",
        "current_date": "2026-10-08",
        "current_lat": 10.6420,
        "current_lon": 106.8427,
    }
    raw_res = handle_seaport_ftz_transshipment_verify(payload)
    parsed = json.loads(raw_res)
    assert parsed["ok"] is True
    assert parsed["transshipment_supervision"]["statutory_clearance_granted"] is True
