"""Automated Test Suite for Port Terminal Stevedoring, Marine Labor Safety, Ship Waste Reception & Remediation Escrow (Phases 227-230).

Covers:
- Phase 227: Port Terminal Stevedoring & Terminal Operator Liability Suite (VMC 2015 Arts. 214-224, Hague-Visby Caps)
- Phase 228: Marine Labor Occupational Safety & Seafarer Health Protection Suite (MLC 2006, IMO Res. A.1050(27), Law on OSH 2015)
- Phase 229: Seaport Reception Facilities & Ship Waste Delivery Compliance Suite (MARPOL 73/78, Circular 41/2020/TT-BGTVT)
- Phase 230: Maritime Environmental Remediation Escrow & Spill Cleanup Bond Guarantee Suite (LEP 2020 Art. 136, Decree 08/2022/ND-CP)
- AST Zero-External-Dependency verification
- CLI Typer command execution
- FastMCP tool handler tests
"""

import ast
import json
from typer.testing import CliRunner

from src.core.maritime_portops_labor_waste_remediation_engine import (
    StevedoreTerminalLiabilityEngine,
    MarineLaborSafetyEngine,
    EnclosedSpaceAtmosphereTest,
    PortWasteReceptionEngine,
    MarpolWasteCategory,
    MaritimeRemediationEscrowEngine,
    OilPersistenceClass,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_stevedore_terminal_liability,
    handle_marine_labor_safety_audit,
    handle_port_waste_reception_verify,
    handle_maritime_remediation_escrow,
)


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================
def test_ast_zero_external_dependency_invariant():
    """Verify engine relies purely on Python standard library modules."""
    engine_path = "src/core/maritime_portops_labor_waste_remediation_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_path)

    allowed_stdlib = {"dataclasses", "enum", "math", "typing", "json", "re", "hashlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_pkg = alias.name.split(".")[0]
                assert base_pkg in allowed_stdlib, f"Unauthorized external import: {base_pkg}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_pkg = node.module.split(".")[0]
                assert base_pkg in allowed_stdlib, f"Unauthorized external importFrom: {base_pkg}"


# ===========================================================================
# 2. Phase 227: Stevedore Terminal Liability Tests
# ===========================================================================
def test_phase227_stevedore_statutory_package_vs_weight_limit():
    """Verify max(500 SDR/pkg, 2 SDR/kg) calculation."""
    # 50 packages, 20,000 kg:
    # 50 * 500 = 25,000 SDR. 20,000 * 2 = 40,000 SDR. Statutory cap = 40,000 SDR (weight governs)
    res = StevedoreTerminalLiabilityEngine.assess_liability(
        vessel_name="MV CAI MEP EXPRESS",
        terminal_operator="TCIT",
        package_count=50,
        gross_weight_kg=20000.0,
        claimed_loss_sdr=50000.0,
        days_since_delivery=15,
        notice_given_days_after_delivery=0,
        is_apparent_damage=True,
    )
    assert res.per_package_limit_sdr == 25000.0
    assert res.per_kg_limit_sdr == 40000.0
    assert res.applicable_statutory_limit_sdr == 40000.0
    assert res.terminal_payable_sdr == 40000.0
    assert res.uncompensated_cargo_loss_sdr == 10000.0
    assert res.is_timebarred is False
    assert res.notice_of_damage_valid is True

    # 100 packages, 10,000 kg:
    # 100 * 500 = 50,000 SDR. 10,000 * 2 = 20,000 SDR. Statutory cap = 50,000 SDR (package governs)
    res2 = StevedoreTerminalLiabilityEngine.assess_liability(
        vessel_name="MV CAI MEP EXPRESS",
        terminal_operator="TCIT",
        package_count=100,
        gross_weight_kg=10000.0,
        claimed_loss_sdr=45000.0,
        days_since_delivery=10,
        notice_given_days_after_delivery=1,
        is_apparent_damage=False,
    )
    assert res2.per_package_limit_sdr == 50000.0
    assert res2.per_kg_limit_sdr == 20000.0
    assert res2.applicable_statutory_limit_sdr == 50000.0
    assert res2.terminal_payable_sdr == 45000.0  # Claimed is less than cap
    assert res2.notice_of_damage_valid is True


def test_phase227_stevedore_declared_value_and_gross_recklessness():
    """Verify declared value override and forfeiture of limitation for gross recklessness."""
    # Declared cargo value
    res = StevedoreTerminalLiabilityEngine.assess_liability(
        vessel_name="MV GEMALINK CARRIER",
        terminal_operator="GEMALINK",
        package_count=10,
        gross_weight_kg=5000.0,
        claimed_loss_sdr=80000.0,
        declared_cargo_value_sdr=100000.0,
        notice_given_days_after_delivery=0,
    )
    assert res.declared_cargo_value_sdr == 100000.0
    assert res.terminal_payable_sdr == 80000.0

    # Gross recklessness breaks the limit
    res_reckless = StevedoreTerminalLiabilityEngine.assess_liability(
        vessel_name="MV GEMALINK CARRIER",
        terminal_operator="GEMALINK",
        package_count=10,
        gross_weight_kg=5000.0,
        claimed_loss_sdr=80000.0,
        is_gross_recklessness=True,
        notice_given_days_after_delivery=0,
    )
    assert res_reckless.is_limitation_lost_recklessness is True
    assert res_reckless.terminal_payable_sdr == 80000.0


def test_phase227_stevedore_damage_notice_and_timebar():
    """Verify apparent vs concealed damage notice rules and 1-year timebar under Art. 224."""
    # Apparent damage given 2 days late (requires 0 days)
    res_late_notice = StevedoreTerminalLiabilityEngine.assess_liability(
        vessel_name="MV VICT CARRIER",
        terminal_operator="VICT",
        package_count=20,
        gross_weight_kg=10000.0,
        claimed_loss_sdr=10000.0,
        days_since_delivery=20,
        notice_given_days_after_delivery=2,
        is_apparent_damage=True,
    )
    assert res_late_notice.notice_of_damage_valid is False

    # Concealed damage given 3 days after (within 3-day limit)
    res_concealed_ok = StevedoreTerminalLiabilityEngine.assess_liability(
        vessel_name="MV VICT CARRIER",
        terminal_operator="VICT",
        package_count=20,
        gross_weight_kg=10000.0,
        claimed_loss_sdr=10000.0,
        days_since_delivery=20,
        notice_given_days_after_delivery=3,
        is_apparent_damage=False,
    )
    assert res_concealed_ok.notice_of_damage_valid is True

    # Claim after 366 days is timebarred
    res_timebarred = StevedoreTerminalLiabilityEngine.assess_liability(
        vessel_name="MV VICT CARRIER",
        terminal_operator="VICT",
        package_count=20,
        gross_weight_kg=10000.0,
        claimed_loss_sdr=10000.0,
        days_since_delivery=366,
    )
    assert res_timebarred.is_timebarred is True
    assert res_timebarred.terminal_payable_sdr == 0.0


# ===========================================================================
# 3. Phase 228: Marine Labor Occupational Safety Tests
# ===========================================================================
def test_phase228_enclosed_space_entry_passed():
    """Verify enclosed space atmospheric testing and entry permit approval."""
    test_params = EnclosedSpaceAtmosphereTest(
        oxygen_pct=20.9,
        lel_combustible_pct=0.5,
        h2s_ppm=2.0,
        co_ppm=10.0,
        ventilation_duration_minutes=45.0,
        calibrated_gas_detector_used=True,
        standby_crew_positioned=True,
        rescue_harness_ready=True,
    )
    audit = MarineLaborSafetyEngine.audit_enclosed_space_entry(
        vessel_name="MV MEKONG SKY",
        space_name="BALLAST_TANK",
        test=test_params,
    )
    assert audit.is_entry_permitted is True
    assert audit.atmospheric_safe is True
    assert audit.safety_gear_ready is True
    assert audit.oxygen_pass is True
    assert audit.lel_pass is True
    assert audit.h2s_pass is True
    assert audit.co_pass is True
    assert len(audit.deficiencies) == 0


def test_phase228_enclosed_space_entry_denied_violations():
    """Verify permit refusal when oxygen low, toxic gases high, or safety gear missing."""
    test_params = EnclosedSpaceAtmosphereTest(
        oxygen_pct=19.5,  # Too low
        lel_combustible_pct=2.5,  # Exceeds 1.0%
        h2s_ppm=8.0,  # Exceeds 5.0 ppm
        co_ppm=35.0,  # Exceeds 25.0 ppm
        ventilation_duration_minutes=15.0,  # Less than 30 min
        calibrated_gas_detector_used=False,
        standby_crew_positioned=False,
        rescue_harness_ready=False,
    )
    audit = MarineLaborSafetyEngine.audit_enclosed_space_entry(
        vessel_name="MV MEKONG SKY",
        space_name="CARGO_HOLD",
        test=test_params,
    )
    assert audit.is_entry_permitted is False
    assert audit.atmospheric_safe is False
    assert audit.safety_gear_ready is False
    assert len(audit.deficiencies) >= 5
    assert "Nồng độ Oxy (19.5%)" in audit.deficiencies[0]


def test_phase228_disability_compensation_statutory_scale():
    """Verify compensation scale under Vietnam Law on OSH 2015 Art. 38 and MLC 2006."""
    # Under 5% -> 0 months
    res_under = MarineLaborSafetyEngine.calculate_occupational_injury_compensation(
        seafarer_name="Nguyen Van A",
        monthly_base_salary_vnd=20000000.0,
        disability_percentage=4.0,
    )
    assert res_under["statutory_salary_months"] == 0.0
    assert res_under["indemnity_amount_vnd"] == 0.0

    # 10% disability -> 1.5 months
    res_10 = MarineLaborSafetyEngine.calculate_occupational_injury_compensation(
        seafarer_name="Nguyen Van A",
        monthly_base_salary_vnd=20000000.0,
        disability_percentage=10.0,
    )
    assert res_10["statutory_salary_months"] == 1.5
    assert res_10["indemnity_amount_vnd"] == 30000000.0

    # 35% disability -> 1.5 + (35 - 10) * 0.4 = 1.5 + 10.0 = 11.5 months
    res_35 = MarineLaborSafetyEngine.calculate_occupational_injury_compensation(
        seafarer_name="Tran Van B",
        monthly_base_salary_vnd=30000000.0,
        disability_percentage=35.0,
    )
    assert res_35["statutory_salary_months"] == 11.5
    assert res_35["indemnity_amount_vnd"] == 345000000.0

    # 85% disability -> >= 81% caps at 30.0 months
    res_85 = MarineLaborSafetyEngine.calculate_occupational_injury_compensation(
        seafarer_name="Le Van C",
        monthly_base_salary_vnd=25000000.0,
        disability_percentage=85.0,
    )
    assert res_85["statutory_salary_months"] == 30.0
    assert res_85["indemnity_amount_vnd"] == 750000000.0

    # 50% employer fault reduces employer share by 50%
    res_fault = MarineLaborSafetyEngine.calculate_occupational_injury_compensation(
        seafarer_name="Le Van C",
        monthly_base_salary_vnd=25000000.0,
        disability_percentage=85.0,
        employer_fault_percentage=50.0,
    )
    assert res_fault["statutory_salary_months"] == 30.0
    assert res_fault["indemnity_amount_vnd"] == 375000000.0


# ===========================================================================
# 4. Phase 229: Port Waste Reception Facilities Tests
# ===========================================================================
def test_phase229_port_waste_advance_notification_and_fee():
    """Verify AWN compliance (>=24h), fee computation, and Waste Transfer Note receipt."""
    res = PortWasteReceptionEngine.verify_waste_delivery(
        vessel_name="MV DA NANG PEARL",
        port_name="TIEN SA PORT",
        advance_notice_hours=28.0,
        waste_category=MarpolWasteCategory.ANNEX_I_OILY_BILGE_SLUDGE,
        volume_to_deliver_m3=10.0,
        onboard_retention_capacity_m3=30.0,
        estimated_generation_to_next_port_m3=10.0,
    )
    assert res.advance_notice_compliant is True
    assert res.mandatory_delivery_enforced is True
    assert res.exemption_granted_for_next_port is False
    # Annex I rate is 450,000 VND/m3 * 10 = 4,500,000 + 1,200,000 base = 5,700,000 VND
    assert res.statutory_port_waste_fee_vnd == 5700000.0
    assert res.reception_facility_transfer_note_issued is True


def test_phase229_port_waste_retention_exemption():
    """Verify retention exemption when capacity >= 1.2 * generation, and denial when insufficient."""
    # Sufficient capacity: 25 m3 onboard vs 10 m3 estimated gen -> 10 * 1.2 = 12 m3 <= 25 m3 -> Exemption OK
    res_ok = PortWasteReceptionEngine.verify_waste_delivery(
        vessel_name="MV DA NANG PEARL",
        port_name="TIEN SA PORT",
        advance_notice_hours=24.0,
        waste_category=MarpolWasteCategory.ANNEX_V_GARBAGE_PLASTICS,
        volume_to_deliver_m3=0.0,
        onboard_retention_capacity_m3=25.0,
        estimated_generation_to_next_port_m3=10.0,
        request_exemption_retention=True,
    )
    assert res_ok.exemption_granted_for_next_port is True
    assert res_ok.mandatory_delivery_enforced is False
    assert res_ok.statutory_port_waste_fee_vnd == 1200000.0  # Base administrative dockage fee

    # Insufficient capacity: 10 m3 onboard vs 10 m3 estimated gen -> 10 * 1.2 = 12 m3 > 10 m3 -> Exemption DENIED
    res_denied = PortWasteReceptionEngine.verify_waste_delivery(
        vessel_name="MV DA NANG PEARL",
        port_name="TIEN SA PORT",
        advance_notice_hours=12.0,  # Also < 24h
        waste_category=MarpolWasteCategory.ANNEX_V_GARBAGE_PLASTICS,
        volume_to_deliver_m3=5.0,
        onboard_retention_capacity_m3=10.0,
        estimated_generation_to_next_port_m3=10.0,
        request_exemption_retention=True,
    )
    assert res_denied.advance_notice_compliant is False
    assert res_denied.exemption_granted_for_next_port is False
    assert res_denied.mandatory_delivery_enforced is True


# ===========================================================================
# 5. Phase 230: Maritime Remediation Escrow & Spill Cleanup Bond Tests
# ===========================================================================
def test_phase230_remediation_escrow_calculation():
    """Verify cleanup base cost, persistence tier, ESI sensitivity, and 20% restoration contingency."""
    # 20 m3, Heavy persistent oil (1.8x), ESI 5 (1.3x moderate):
    # Base = 20 * 18,000,000 = 360,000,000 VND
    # Subtotal = 360,000,000 * 1.8 * 1.3 = 842,400,000 VND
    # Restoration contingency (20%) = 168,480,000 VND
    # Total Escrow = 1,010,880,000 VND
    res = MaritimeRemediationEscrowEngine.calculate_escrow(
        incident_id="INC-2026-SPILL-01",
        vessel_name="MT DONG NAI",
        spill_volume_m3=20.0,
        oil_persistence=OilPersistenceClass.PERSISTENT_CRUDE_HEAVY_FUEL,
        esi_sensitivity_index=5,
    )
    assert res.base_cleanup_cost_per_m3_vnd == 18000000.0
    assert res.persistence_factor == 1.8
    assert res.esi_factor == 1.3
    assert res.subtotal_remediation_cost_vnd == 842400000.0
    assert res.ecological_restoration_contingency_vnd == 168480000.0
    assert res.total_statutory_escrow_deposit_vnd == 1010880000.0
    assert res.irrevocable_bank_guarantee_required is True
    assert "Quỹ Bảo vệ Môi trường Việt Nam" in res.escrow_account_beneficiary


def test_phase230_remediation_escrow_high_sensitivity():
    """Verify ESI >= 8 applies 2.0x multiplier and light oil applies 1.0x."""
    # 5 m3, Light refined oil (1.0x), ESI 9 (2.0x high sensitivity mangrove/coral):
    # Base = 5 * 18,000,000 = 90,000,000 VND
    # Subtotal = 90,000,000 * 1.0 * 2.0 = 180,000,000 VND
    # Restoration = 36,000,000 VND
    # Total = 216,000,000 VND
    res = MaritimeRemediationEscrowEngine.calculate_escrow(
        incident_id="INC-2026-SPILL-02",
        vessel_name="MT CAN THO",
        spill_volume_m3=5.0,
        oil_persistence=OilPersistenceClass.NON_PERSISTENT_GASOLINE_MGO,
        esi_sensitivity_index=9,
    )
    assert res.persistence_factor == 1.0
    assert res.esi_factor == 2.0
    assert res.subtotal_remediation_cost_vnd == 180000000.0
    assert res.ecological_restoration_contingency_vnd == 36000000.0
    assert res.total_statutory_escrow_deposit_vnd == 216000000.0


# ===========================================================================
# 6. Typer CLI Command Execution Tests
# ===========================================================================
def test_cli_stevedore_command():
    """Verify stevedore CLI group command execution."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "stevedore", "assess",
        "--vessel", "MV PACIFIC VOYAGER",
        "--terminal", "SP-PSA TERMINAL",
        "--packages", "80",
        "--weight", "30000.0",
        "--claimed-loss", "60000.0",
    ])
    assert result.exit_code == 0
    assert "ĐÁNH GIÁ TRÁCH NHIỆM BỐC DỠ CẢNG BIỂN" in result.output
    assert "MV PACIFIC VOYAGER" in result.output


def test_cli_maritimesafety_command():
    """Verify maritimesafety CLI group commands execution."""
    app = build_app()
    runner = CliRunner()

    # audit-entry command
    res1 = runner.invoke(app, [
        "maritimesafety", "audit-entry",
        "--vessel", "MV HAI PHONG EXPRESS",
        "--space", "FUEL_OIL_TANK_3P",
        "--o2", "20.9",
        "--lel", "0.2",
        "--h2s", "1.0",
        "--co", "5.0",
        "--ventilation", "40.0",
    ])
    assert res1.exit_code == 0
    assert "KIỂM TOÁN AN TOÀN VÀO BUỒNG KÍN" in res1.output

    # calc-injury command
    res2 = runner.invoke(app, [
        "maritimesafety", "calc-injury",
        "--seafarer", "Doan Van D",
        "--salary", "25000000.0",
        "--disability", "25.0",
    ])
    assert res2.exit_code == 0
    assert "BỒI THƯỜNG TAI NẠN LAO ĐỘNG HÀNG HẢI" in res2.output


def test_cli_portwaste_command():
    """Verify portwaste CLI group command execution."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "portwaste-reception", "verify",
        "--vessel", "MV QUY NHON PRIDE",
        "--port", "QUY NHON PORT",
        "--notice-hours", "25.0",
        "--category", "ANNEX_I_OILY_BILGE_SLUDGE",
        "--volume", "6.5",
    ])
    assert result.exit_code == 0
    assert "THẨM ĐỊNH THỦ TỤC CHẤT THẢI CẢNG BIỂN" in result.output


def test_cli_remediationescrow_command():
    """Verify remediationescrow CLI group command execution."""
    app = build_app()
    runner = CliRunner()
    result = runner.invoke(app, [
        "remediationescrow", "calculate",
        "--incident", "INC-TEST-001",
        "--vessel", "MT CAM RANH",
        "--volume", "12.0",
        "--persistence", "PERSISTENT_CRUDE_HEAVY_FUEL",
        "--esi", "7",
    ])
    assert result.exit_code == 0
    assert "KÝ QUỸ PHỤC HỒI MÔI TRƯỜNG BIỂN" in result.output


# ===========================================================================
# 7. FastMCP Tool Handler Tests
# ===========================================================================
def test_mcp_stevedore_terminal_liability_handler():
    """Verify FastMCP handler for stevedore terminal liability."""
    output = handle_stevedore_terminal_liability({
        "vessel_name": "MV PHU MY EXPRESS",
        "terminal_operator": "PHU MY PORT",
        "package_count": 60,
        "gross_weight_kg": 24000.0,
        "claimed_loss_sdr": 45000.0,
        "notice_given_days_after_delivery": 0,
    })
    data = json.loads(output)
    assert data["ok"] is True
    assert data["vessel_name"] == "MV PHU MY EXPRESS"
    assert data["per_package_limit_sdr"] == 30000.0
    assert data["per_kg_limit_sdr"] == 48000.0
    assert data["terminal_payable_sdr"] == 45000.0


def test_mcp_marine_labor_safety_audit_handler():
    """Verify FastMCP handler for marine labor safety audit."""
    output = handle_marine_labor_safety_audit({
        "vessel_name": "MV MEKONG SEAS",
        "space_name": "SEWAGE_HOLDING_TANK",
        "oxygen_pct": 20.9,
        "lel_combustible_pct": 0.0,
        "h2s_ppm": 0.0,
        "co_ppm": 0.0,
        "ventilation_duration_minutes": 35.0,
    })
    data = json.loads(output)
    assert data["ok"] is True
    assert data["is_entry_permitted"] is True
    assert data["atmospheric_safe"] is True
    assert data["vessel_name"] == "MV MEKONG SEAS"


def test_mcp_port_waste_reception_verify_handler():
    """Verify FastMCP handler for port waste reception verify."""
    output = handle_port_waste_reception_verify({
        "vessel_name": "MV NHA TRANG STAR",
        "port_name": "NHA TRANG PORT",
        "advance_notice_hours": 30.0,
        "waste_category": "ANNEX_IV_SEWAGE_BLACKWATER",
        "volume_to_deliver_m3": 15.0,
    })
    data = json.loads(output)
    assert data["ok"] is True
    assert data["advance_notice_compliant"] is True
    assert data["mandatory_delivery_enforced"] is True
    assert data["statutory_port_waste_fee_vnd"] > 0.0


def test_mcp_maritime_remediation_escrow_handler():
    """Verify FastMCP handler for maritime remediation escrow."""
    output = handle_maritime_remediation_escrow({
        "incident_id": "SPILL-2026-NT-01",
        "vessel_name": "MT NHA TRANG PRIDE",
        "spill_volume_m3": 10.0,
        "oil_persistence": "MEDIUM_DISTILLATE_DIESEL",
        "esi_sensitivity_index": 4,
    })
    data = json.loads(output)
    assert data["ok"] is True
    assert data["incident_id"] == "SPILL-2026-NT-01"
    assert data["irrevocable_bank_guarantee_required"] is True
    assert data["total_statutory_escrow_deposit_vnd"] > 0.0
