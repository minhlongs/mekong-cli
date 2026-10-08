"""Comprehensive Test Suite for Maritime ISM SMS, Green Ship Recycling IHM, Port Waste PRF & ISPS Security Suite (Phases 243-246).

Statutory & Standard References:
- Phase 243: SOLAS Chapter IX, IMO Res. A.741(18), Vietnam Maritime Code 2015 Arts. 65-72 & Decree 58/2017/NĐ-CP Arts. 11-15 (ISM Code, DOC/SMC, Audit Windows, Major NC Downgrades).
- Phase 244: Hong Kong Convention 2009 (SR/CONF/45), EU Ship Recycling Regulation (EU) No 1257/2013, Law on Environmental Protection 2020 Art. 75, Decree 08/2022/NĐ-CP & Decree 82/2019/NĐ-CP (IHM Tables A/B, Scrap Recovery, Salvage Valuation).
- Phase 245: MARPOL Annexes I-VI, Circular 39/2023/TT-BGTVT, Circular 41/2020/TT-BGTVT, Directive (EU) 2019/883 (AWN Waste Notification, Mandatory PRF Discharge, Indirect Tariff).
- Phase 246: ISPS Code Parts A & B, SOLAS Chapter XI-2, Vietnam Maritime Code 2015 Arts. 102-105, Decree 58/2017/NĐ-CP Arts. 82-94 & Decision 22/2017/QĐ-TTg (Security Levels 1-3, DoS Mandates, TVC Risk Matrix).
"""

import ast
import json
from pathlib import Path

from typer.testing import CliRunner

from scripts.mcp_server import CORE_HANDLERS
from src.cli.commands.maritime_ism_recycling_waste_isps_command import (
    ispssecurity_app,
    ismsafety_app,
    portwaste_app,
    shiprecycling_app,
)
from src.core.maritime_ism_recycling_waste_isps_engine import (
    AdvanceWasteNotificationStatus,
    DeclarationOfSecurityResult,
    GreenShipRecyclingIhmEngine,
    IhmMaterialCategory,
    IhmMaterialFinding,
    IsmAuditEvaluation,
    IsmCertificateStatus,
    IsmCertificateType,
    IsmSafetyManagementEngine,
    IspsPortSecurityEngine,
    NonConformitySeverity,
    PortReceptionWasteEngine,
    PortWasteFeeReceipt,
    SecurityRiskTier,
    ShipRecyclingValuation,
    ThreatVulnerabilityAssessment,
)

runner = CliRunner()


def test_ast_zero_external_dependency_invariant() -> None:
    """Verify that the core maritime engine module maintains zero external dependencies."""
    engine_path = Path("src/core/maritime_ism_recycling_waste_isps_engine.py")
    assert engine_path.exists(), "Engine file must exist"

    tree = ast.parse(engine_path.read_text(encoding="utf-8"))
    allowed_standard_modules = {
        "__future__",
        "dataclasses",
        "enum",
        "math",
        "typing",
        "hashlib",
        "datetime",
        "json",
        "re",
        "sys",
        "os",
        "pathlib",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                assert root_pkg in allowed_standard_modules, f"Disallowed import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_standard_modules, f"Disallowed from-import: {node.module}"


# ---------------------------------------------------------------------------
# Phase 243: Maritime ISM Code Safety Management System (SMS) & DPA Oversight
# ---------------------------------------------------------------------------


def test_ism_certificate_validity_evaluation() -> None:
    """Verify DOC and SMC certificate validity, expiry, and annual/intermediate audit windows."""
    # Active valid DOC
    doc_valid: IsmCertificateStatus = IsmSafetyManagementEngine.evaluate_certificate_validity(
        cert_type=IsmCertificateType.DOC,
        cert_number="DOC-VN-2024-001",
        issue_date_str="2024-01-01",
        expiry_date_str="2029-01-01",
        current_date_str="2025-01-01",
        last_audit_date_str="2024-01-01",
    )
    assert doc_valid.is_valid is True
    assert doc_valid.days_to_expiry > 0

    # Expired SMC certificate
    smc_expired: IsmCertificateStatus = IsmSafetyManagementEngine.evaluate_certificate_validity(
        cert_type=IsmCertificateType.SMC,
        cert_number="SMC-VN-2018-099",
        issue_date_str="2018-01-01",
        expiry_date_str="2023-01-01",
        current_date_str="2025-01-01",
    )
    assert smc_expired.is_valid is False
    assert smc_expired.days_to_expiry <= 0
    assert "hết hiệu lực" in smc_expired.remarks.lower() or "expired" in smc_expired.remarks.lower()


def test_ism_audit_findings_major_nc_downgrade() -> None:
    """Verify ISM audit evaluation, Major NC suspension rule, and temporary downgrade conditions."""
    findings_major = [
        {
            "finding_id": "NC-001",
            "category": "emergency_preparedness",
            "severity": "major_nc",
            "description": "Oily water separator bypass valve inoperable",
            "downgraded_to_minor": False,
        },
        {
            "finding_id": "NC-002",
            "category": "documentation",
            "severity": "minor_nc",
            "description": "Bridge logbook missing chief mate signature",
            "downgraded_to_minor": False,
        },
    ]

    # Without downgrade -> Major NC triggers suspension and detention risk
    eval_fail: IsmAuditEvaluation = IsmSafetyManagementEngine.evaluate_audit_findings(
        ship_name="MV MEKONG STAR",
        imo_number="9876543",
        findings=findings_major,
        drills_conducted=12,
        drills_required=12,
    )
    assert eval_fail.smc_suspended is True
    assert eval_fail.detention_risk is True
    assert eval_fail.major_nc_count == 1
    assert eval_fail.cap_deadline_days == 0

    # With authorized temporary downgrade -> Conditional pass, 90-day CAP deadline
    findings_downgraded = [
        {
            "finding_id": "NC-001",
            "category": "emergency_preparedness",
            "severity": "major_nc",
            "description": "Oily water separator bypass valve inoperable",
            "downgraded_to_minor": True,
        },
        {
            "finding_id": "NC-002",
            "category": "documentation",
            "severity": "minor_nc",
            "description": "Bridge logbook missing chief mate signature",
            "downgraded_to_minor": False,
        },
    ]
    eval_pass: IsmAuditEvaluation = IsmSafetyManagementEngine.evaluate_audit_findings(
        ship_name="MV MEKONG STAR",
        imo_number="9876543",
        findings=findings_downgraded,
        drills_conducted=12,
        drills_required=12,
    )
    assert eval_pass.smc_suspended is False
    assert eval_pass.detention_risk is False
    assert eval_pass.major_nc_count == 0
    assert eval_pass.minor_nc_count == 2
    assert eval_pass.cap_deadline_days == 90


# ---------------------------------------------------------------------------
# Phase 244: Green Ship Recycling & Inventory of Hazardous Materials (IHM)
# ---------------------------------------------------------------------------


def test_ihm_material_threshold_auditing() -> None:
    """Verify Hong Kong Convention 2009 & EU SRR Table A/B threshold compliance auditing."""
    samples = [
        {
            "category": "asbestos",
            "location": "Engine Room Exhaust Casing",
            "concentration_mg_kg": 800.0,  # <= 1000 mg/kg limit
            "estimated_mass_kg": 150.0,
        },
        {
            "category": "pcb",
            "location": "Main Switchboard Capacitors",
            "concentration_mg_kg": 40.0,  # <= 50 mg/kg limit
            "estimated_mass_kg": 50.0,
        },
    ]

    compliant, findings = GreenShipRecyclingIhmEngine.audit_ihm_materials(samples)
    assert compliant is True
    assert len(findings) == 2
    assert all(f.is_exceeded is False for f in findings)

    # Samples exceeding statutory threshold
    samples_violation = [
        {
            "category": "asbestos",
            "location": "Galley Bulkhead Insulation",
            "concentration_mg_kg": 1500.0,  # > 1000 mg/kg
            "estimated_mass_kg": 350.0,
        },
        {
            "category": "ods",
            "location": "Reefer Compressor Unit",
            "concentration_mg_kg": 10.0,  # ODS threshold is 0.0 mg/kg
            "estimated_mass_kg": 20.0,
        },
    ]
    comp_viol, findings_viol = GreenShipRecyclingIhmEngine.audit_ihm_materials(samples_violation)
    assert comp_viol is False
    assert len(findings_viol) == 2
    assert findings_viol[0].is_exceeded is True
    assert findings_viol[1].is_exceeded is True


def test_ship_recycling_salvage_valuation() -> None:
    """Verify structural LDT scrap steel recovery, decontamination cost deductions, and net salvage valuation."""
    ihm_findings = [
        IhmMaterialFinding(
            material=IhmMaterialCategory.ASBESTOS,
            location="Accommodation",
            measured_concentration_mg_kg=1200.0,
            statutory_threshold_mg_kg=1000.0,
            is_table_a_prohibited=True,
            is_exceeded=True,
            estimated_mass_kg=2500.0,
        )
    ]

    val: ShipRecyclingValuation = GreenShipRecyclingIhmEngine.calculate_recycling_valuation(
        ldt_tonnes=10000.0,
        ihm_findings=ihm_findings,
        steel_scrap_price_usd_tonne=480.0,
        nonferrous_price_usd_tonne=1800.0,
        hazardous_treatment_tariff_usd_tonne=650.0,
        demolition_labor_usd_ldt=95.0,
    )
    # Recoverable steel: 10,000 * 0.88 = 8,800 tons
    assert val.recovered_steel_tonnes == 8800.0
    # Recoverable non-ferrous: 10,000 * 0.035 = 350 tons
    assert val.recovered_nonferrous_tonnes == 350.0
    assert val.gross_scrap_revenue_usd > 0.0
    assert val.labor_demolition_cost_usd == 10000.0 * 95.0
    assert val.net_salvage_value_usd == (
        val.gross_scrap_revenue_usd - val.hazardous_disposal_cost_usd - val.labor_demolition_cost_usd
    )
    assert val.net_salvage_value_vnd > 0.0


# ---------------------------------------------------------------------------
# Phase 245: Port Reception Facilities (PRF Waste Delivery & Circular 39 Tariffs)
# ---------------------------------------------------------------------------


def test_awn_mandatory_delivery_evaluation() -> None:
    """Verify Advance Waste Notification (AWN) mandatory PRF discharge criteria under Circular 41/2020."""
    # Sufficient capacity on board -> Voluntary delivery
    awn_ok: AdvanceWasteNotificationStatus = PortReceptionWasteEngine.evaluate_awn_delivery_mandate(
        hours_before_arrival=24.0,
        remaining_storage_m3=60.0,
        total_tank_capacity_m3=100.0,
        predicted_generation_next_leg_m3=20.0,
    )
    assert awn_ok.is_filed_on_time is True
    assert awn_ok.mandatory_discharge_required is False

    # High tank fullness (>= 75%) -> Mandatory discharge required
    awn_mand: AdvanceWasteNotificationStatus = PortReceptionWasteEngine.evaluate_awn_delivery_mandate(
        hours_before_arrival=24.0,
        remaining_storage_m3=20.0,
        total_tank_capacity_m3=100.0,
        predicted_generation_next_leg_m3=10.0,
    )
    assert awn_mand.mandatory_discharge_required is True

    # Late notification (< 24 hours)
    awn_late: AdvanceWasteNotificationStatus = PortReceptionWasteEngine.evaluate_awn_delivery_mandate(
        hours_before_arrival=12.0,
        remaining_storage_m3=70.0,
        total_tank_capacity_m3=100.0,
        predicted_generation_next_leg_m3=10.0,
    )
    assert awn_late.is_filed_on_time is False


def test_circular_39_port_waste_tariffs() -> None:
    """Verify Circular 39/2023/TT-BGTVT indirect No-Special-Fee system and excess volume tariffs."""
    # Vessel 25,000 GT berthed for 3 days, delivers 18 m3 garbage and 5 m3 sludge
    receipt: PortWasteFeeReceipt = PortReceptionWasteEngine.calculate_port_waste_tariffs(
        gross_tonnage=25000.0,
        days_at_berth=3.0,
        delivered_garbage_m3=18.0,
        annex_i_sludge_m3=5.0,
    )
    # Indirect fee: 25,000 * 120 = 3,000,000 VND (within 1.5M - 18M clamp)
    assert receipt.indirect_waste_fee_vnd == 3000000.0
    # Allowance: 25,000 * 0.00015 * 3 = 11.25 m3
    assert receipt.included_garbage_allowance_m3 == 11.25
    # Excess: 18 - 11.25 = 6.75 m3 * 350,000 VND = 2,362,500 VND
    assert receipt.excess_garbage_m3 == 6.75
    assert receipt.excess_garbage_fee_vnd == 2362500.0
    # Sludge: 5.0 * 950,000 = 4,750,000 VND
    assert receipt.hazardous_waste_fee_vnd == 4750000.0
    assert receipt.total_waste_fee_vnd == 3000000.0 + 2362500.0 + 4750000.0


# ---------------------------------------------------------------------------
# Phase 246: Seaport ISPS Maritime Security Levels, DoS & TVC Risk Matrix
# ---------------------------------------------------------------------------


def test_isps_security_level_and_dos_mandate() -> None:
    """Verify ISPS Security Levels 1-3 and mandatory Declaration of Security (DoS) conditions."""
    # Ship at Level 1, Port at Level 1, normal ops -> No DoS required
    res_normal: DeclarationOfSecurityResult = IspsPortSecurityEngine.evaluate_dos_requirement(
        ship_level=1,
        port_level=1,
        has_dangerous_cargo=False,
        is_sts_operation=False,
    )
    assert res_normal.dos_mandatory is False

    # Level mismatch: Ship Level 2, Port Level 1 -> Mandatory DoS
    res_mismatch: DeclarationOfSecurityResult = IspsPortSecurityEngine.evaluate_dos_requirement(
        ship_level=2,
        port_level=1,
        has_dangerous_cargo=False,
        is_sts_operation=False,
    )
    assert res_mismatch.dos_mandatory is True

    # Security Level 3 -> Mandatory DoS
    res_lvl3: DeclarationOfSecurityResult = IspsPortSecurityEngine.evaluate_dos_requirement(
        ship_level=1,
        port_level=3,
        has_dangerous_cargo=False,
        is_sts_operation=False,
    )
    assert res_lvl3.dos_mandatory is True

    # STS transfer -> Mandatory DoS
    res_sts: DeclarationOfSecurityResult = IspsPortSecurityEngine.evaluate_dos_requirement(
        ship_level=1,
        port_level=1,
        has_dangerous_cargo=False,
        is_sts_operation=True,
    )
    assert res_sts.dos_mandatory is True


def test_isps_tvc_risk_score_calculation() -> None:
    """Verify Threat x Vulnerability x Consequence (TVC) risk score calculation and classification."""
    # Low risk (2 x 2 x 3 = 12)
    tvc_low: ThreatVulnerabilityAssessment = IspsPortSecurityEngine.calculate_tvc_risk_score(
        facility_name="General Berth 3",
        threat=2,
        vulnerability=2,
        consequence=3,
    )
    assert tvc_low.risk_score == 12
    assert tvc_low.risk_tier == SecurityRiskTier.LOW

    # High risk (4 x 4 x 4 = 64)
    tvc_high: ThreatVulnerabilityAssessment = IspsPortSecurityEngine.calculate_tvc_risk_score(
        facility_name="LNG Terminal Jetty",
        threat=4,
        vulnerability=4,
        consequence=4,
    )
    assert tvc_high.risk_score == 64
    assert tvc_high.risk_tier == SecurityRiskTier.HIGH

    # Critical risk (5 x 5 x 4 = 100)
    tvc_crit: ThreatVulnerabilityAssessment = IspsPortSecurityEngine.calculate_tvc_risk_score(
        facility_name="Chemical Bulk Hub",
        threat=5,
        vulnerability=5,
        consequence=4,
    )
    assert tvc_crit.risk_score == 100
    assert tvc_crit.risk_tier == SecurityRiskTier.CRITICAL


# ---------------------------------------------------------------------------
# Typer CLI Command Integration Tests
# ---------------------------------------------------------------------------


def test_cli_ismsafety_commands() -> None:
    """Verify CLI commands for ISM certificate check and audit evaluation."""
    res_chk = runner.invoke(ismsafety_app, ["check", "--type", "smc", "--issue", "2024-01-01", "--expiry", "2029-01-01", "--json"])
    assert res_chk.exit_code == 0
    assert "is_valid" in res_chk.stdout

    res_aud = runner.invoke(ismsafety_app, ["audit", "--ship", "MV MEKONG", "--imo", "9876543", "--json"])
    assert res_aud.exit_code == 0
    assert "audit_summary" in res_aud.stdout


def test_cli_shiprecycling_commands() -> None:
    """Verify CLI commands for IHM audit and ship recycling salvage valuation."""
    res_ihm = runner.invoke(shiprecycling_app, ["ihm", "--json"])
    assert res_ihm.exit_code == 0
    assert "compliant" in res_ihm.stdout

    res_sal = runner.invoke(shiprecycling_app, ["salvage", "--ldt", "12000.0", "--steel-price", "460.0", "--json"])
    assert res_sal.exit_code == 0
    assert "recovered_steel_tonnes" in res_sal.stdout
    assert "net_salvage_value_usd" in res_sal.stdout


def test_cli_portwaste_commands() -> None:
    """Verify CLI commands for AWN waste delivery check and Circular 39 tariff receipt."""
    res_awn = runner.invoke(portwaste_app, ["awn", "--hours", "24.0", "--remaining", "60.0", "--capacity", "100.0", "--next-gen", "20.0", "--json"])
    assert res_awn.exit_code == 0
    assert "is_filed_on_time" in res_awn.stdout

    res_tar = runner.invoke(portwaste_app, ["tariff", "--gt", "30000.0", "--days", "2.0", "--garbage", "12.0", "--json"])
    assert res_tar.exit_code == 0
    assert "indirect_waste_fee_vnd" in res_tar.stdout
    assert "total_waste_fee_vnd" in res_tar.stdout


def test_cli_ispssecurity_commands() -> None:
    """Verify CLI commands for ISPS Declaration of Security and TVC risk calculation."""
    res_dos = runner.invoke(ispssecurity_app, ["dos", "--ship-level", "2", "--port-level", "1", "--json"])
    assert res_dos.exit_code == 0
    assert "dos_mandatory" in res_dos.stdout

    res_risk = runner.invoke(ispssecurity_app, ["threat", "--facility", "LNG Jetty", "--threat", "4", "--vulnerability", "4", "--consequence", "4", "--json"])
    assert res_risk.exit_code == 0
    assert "risk_score" in res_risk.stdout
    assert "risk_tier" in res_risk.stdout


# ---------------------------------------------------------------------------
# FastMCP Tool Integration Tests
# ---------------------------------------------------------------------------


def test_mcp_ism_safety_management_handler() -> None:
    """Verify FastMCP handler for mekong_ism_safety_management_evaluate."""
    handler = CORE_HANDLERS["mekong_ism_safety_management_evaluate"]
    raw_res = handler({"cert_type": "smc", "cert_number": "SMC-001", "issue_date": "2024-01-01", "expiry_date": "2029-01-01"})
    payload = json.loads(raw_res)
    assert payload["ok"] is True
    assert "certificate_status" in payload
    assert payload["certificate_status"]["is_valid"] is True


def test_mcp_ship_recycling_ihm_handler() -> None:
    """Verify FastMCP handler for mekong_ship_recycling_ihm_evaluate."""
    handler = CORE_HANDLERS["mekong_ship_recycling_ihm_evaluate"]
    raw_res = handler({"ldt_tonnes": 15000.0, "steel_scrap_price_usd_tonne": 450.0})
    payload = json.loads(raw_res)
    assert payload["ok"] is True
    assert "recycling_valuation" in payload
    assert payload["recycling_valuation"]["recovered_steel_tonnes"] == 15000.0 * 0.88


def test_mcp_port_reception_waste_handler() -> None:
    """Verify FastMCP handler for mekong_port_reception_waste_evaluate."""
    handler = CORE_HANDLERS["mekong_port_reception_waste_evaluate"]
    raw_res = handler({"gross_tonnage": 20000.0, "days_at_berth": 2.0, "delivered_garbage_m3": 10.0})
    payload = json.loads(raw_res)
    assert payload["ok"] is True
    assert "port_waste_receipt" in payload
    assert payload["port_waste_receipt"]["indirect_waste_fee_vnd"] > 0


def test_mcp_isps_port_security_handler() -> None:
    """Verify FastMCP handler for mekong_isps_port_security_evaluate."""
    handler = CORE_HANDLERS["mekong_isps_port_security_evaluate"]
    raw_res = handler({
        "ship_security_level": 2,
        "port_security_level": 1,
        "threat_likelihood": 3,
        "vulnerability_level": 3,
        "consequence_severity": 4,
    })
    payload = json.loads(raw_res)
    assert payload["ok"] is True
    assert payload["declaration_of_security"]["dos_mandatory"] is True
    assert payload["threat_vulnerability_assessment"]["risk_score"] == 36
