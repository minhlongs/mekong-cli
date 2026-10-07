"""Comprehensive test suite for Phases 191-194:
- Phase 191: Vietnam National Maritime Single Window (VNSW) & Port Clearance (Decree 58/2017/NĐ-CP & Decree 76/2021/NĐ-CP)
- Phase 192: Seafarer Safe Manning, STCW Rest Hours & Border Immigration Shore Pass (Decree 77/2017/NĐ-CP & Circular 20/2023/TT-BGTVT)
- Phase 193: Maritime International Health Quarantine, SSCEC & Free Pratique (IHR 2005 & Decree 89/2018/NĐ-CP)
- Phase 194: Marine Environmental Protection, MARPOL 73/78 & PRF Waste Reception (Decree 08/2022/NĐ-CP & MARPOL Annex I/VI)

Verifies:
1. Pure Python standard library AST zero-external-dependency invariants.
2. VNSW statutory notification timeliness, FAL 1-7 document checklist validation, SHA-256 PKI digital permits and statutory dues.
3. Seafarer Minimum Safe Manning levels, STCW mandatory rest intervals, and Shore Pass granting.
4. Ship Sanitation Control Exemption Certificate (SSCEC) audit, Epidemiological Risk Scoring, and Free Pratique vs Yellow Flag quarantine.
5. MARPOL Annex I 15 ppm OWS, Annex VI 0.50% sulfur fuel, and PRF reception fee auditing.
6. Typer CLI command group execution and --json outputs.
7. FastMCP tool handlers execution and json response contracts.
"""

import ast
import json
import pytest
from typer.testing import CliRunner

from src.core.maritime_vnsw_quarantine_marpol_engine import (
    VNSWNotificationType,
    VesselVoyageType,
    ClearanceStatus,
    SeafarerRank,
    SeafarerCrewMember,
    ImmigrationPassType,
    HealthQuarantineStatus,
    MaritimeSingleWindowEngine,
    SeafarerImmigrationEngine,
    MaritimeHealthQuarantineEngine,
    MARPOLPortReceptionEngine,
)
from src.cli.commands.maritime_vnsw_quarantine_marpol_command import (
    vnsw_app,
    seafarer_app,
    quarantine_app,
    marpol_app,
)
from scripts.mcp_server import (
    handle_vnsw_clearance,
    handle_seafarer_manning,
    handle_quarantine_eval,
    handle_marpol_audit,
)

runner = CliRunner()


# ===========================================================================
# 1. Zero External Dependency & AST Invariant Tests
# ===========================================================================


def test_core_engine_zero_external_dependencies():
    """Verify that src/core/maritime_vnsw_quarantine_marpol_engine.py only imports from Python standard library."""
    with open("src/core/maritime_vnsw_quarantine_marpol_engine.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    allowed_stdlib = {"dataclasses", "datetime", "enum", "math", "typing", "json", "hashlib", "re"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_pkg = alias.name.split(".")[0]
                assert root_pkg in allowed_stdlib, f"Unauthorized external import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_stdlib, f"Unauthorized external from-import: {node.module}"


# ===========================================================================
# 2. Phase 191: Maritime Single Window Engine Tests
# ===========================================================================


def test_vnsw_port_clearance_international_granted():
    """Test standard international vessel port clearance with full FAL documents and timely notice."""
    forms = ["FAL_1", "FAL_2", "FAL_3", "FAL_4", "FAL_5", "FAL_6", "FAL_7"]
    res = MaritimeSingleWindowEngine.evaluate_port_clearance(
        imo_number="9382710",
        vessel_name="MV MEKONG STAR",
        call_sign="3WKT",
        voyage_type=VesselVoyageType.INTERNATIONAL,
        gross_tonnage=15000.0,
        notification_type=VNSWNotificationType.ARRIVAL_NOTICE_24H,
        hours_before_event=25.0,
        submitted_forms=forms,
    )
    assert res.status == ClearanceStatus.CLEARED
    assert res.is_notification_timely is True
    assert res.is_dossier_complete is True
    assert len(res.missing_declarations) == 0
    assert res.clearance_permit_no.startswith("VN-VNSW-")
    assert "https://vnsw.gov.vn/verify?permit=" in res.qr_verification_payload
    # Statutory math check:
    # Tonnage: 15000 * 0.034 * 25000 = 12,750,000 VND
    # Safety: 15000 * 0.045 * 25000 = 16,875,000 VND
    # Permit fee: 100,000 VND
    # Total: 29,725,000 VND
    assert res.tonnage_dues_vnd == 12750000.0
    assert res.maritime_safety_fee_vnd == 16875000.0
    assert res.port_clearance_fee_vnd == 100000.0
    assert res.total_statutory_dues_vnd == 29725000.0


def test_vnsw_port_clearance_domestic_missing_docs():
    """Test domestic vessel port clearance with missing FAL forms resulting in documentation rejection."""
    forms = ["FAL_1", "FAL_3"]  # Missing FAL_4, FAL_5, etc.
    res = MaritimeSingleWindowEngine.evaluate_port_clearance(
        imo_number="9123456",
        vessel_name="MV SONG HAU",
        call_sign="3WSH",
        voyage_type=VesselVoyageType.DOMESTIC,
        gross_tonnage=3000.0,
        notification_type=VNSWNotificationType.ARRIVAL_CONFIRMATION_2H,
        hours_before_event=3.0,
        submitted_forms=forms,
    )
    assert res.status == ClearanceStatus.DETAINED_OR_REJECTED
    assert res.is_notification_timely is True
    assert res.is_dossier_complete is False
    assert "FAL_2" in res.missing_declarations
    assert "FAL_4" in res.missing_declarations
    assert "FAL_5" in res.missing_declarations
    # Domestic dues:
    # Tonnage: 3000 * 400 = 1,200,000 VND
    # Safety: 3000 * 600 = 1,800,000 VND
    # Permit fee: 50,000 VND
    # Total: 3,050,000 VND
    assert res.tonnage_dues_vnd == 1200000.0
    assert res.maritime_safety_fee_vnd == 1800000.0
    assert res.port_clearance_fee_vnd == 50000.0
    assert res.total_statutory_dues_vnd == 3050000.0


def test_vnsw_port_clearance_delayed_notice():
    """Test vessel notification submitted too late breaching statutory timeframe."""
    forms = ["FAL_1", "FAL_2", "FAL_3", "FAL_4", "FAL_5", "FAL_6", "FAL_7"]
    res = MaritimeSingleWindowEngine.evaluate_port_clearance(
        imo_number="9382710",
        vessel_name="MV MEKONG STAR",
        call_sign="3WKT",
        voyage_type=VesselVoyageType.INTERNATIONAL,
        gross_tonnage=10000.0,
        notification_type=VNSWNotificationType.ARRIVAL_NOTICE_24H,
        hours_before_event=12.0,  # Below 24h statutory deadline
        submitted_forms=forms,
    )
    assert res.is_notification_timely is False
    assert res.status == ClearanceStatus.CONDITIONAL_CLEARANCE
    assert any("Arrival notice sent 12.0h before arrival" in note for note in res.action_notes)


# ===========================================================================
# 3. Phase 192: Seafarer Manning & Border Immigration Tests
# ===========================================================================


def test_seafarer_manning_full_compliance():
    """Test crew meeting MSMD mandatory ranks and STCW rest hours obtaining shore passes."""
    crew = [
        SeafarerCrewMember("Nguyen Van A", "VNM", "B1234567", "VN-0988", SeafarerRank.MASTER, "2028-12-31", "2028-12-31", 11.0, 84.0),
        SeafarerCrewMember("Tran Van B", "VNM", "B2345678", "VN-0989", SeafarerRank.CHIEF_MATE, "2028-12-31", "2028-12-31", 10.5, 80.0),
        SeafarerCrewMember("Le Van C", "VNM", "B3456789", "VN-0990", SeafarerRank.CHIEF_ENGINEER, "2028-12-31", "2028-12-31", 12.0, 88.0),
        SeafarerCrewMember("Pham Van D", "VNM", "B4567890", "VN-0991", SeafarerRank.SECOND_ENGINEER, "2028-12-31", "2028-12-31", 10.0, 78.0),
        SeafarerCrewMember("Do Van E", "VNM", "B5678901", "VN-0992", SeafarerRank.RATING_ABLE_SEAMAN, "2028-12-31", "2028-12-31", 10.0, 77.0),
    ]
    res = SeafarerImmigrationEngine.audit_crew_and_immigration("MV PACIFIC OCEAN", crew, assessment_date_iso="2026-10-01")
    assert res.is_safe_manning_compliant is True
    assert res.is_stcw_rest_compliant is True
    assert len(res.deficiencies) == 0
    assert res.shore_pass_granted_count == 5
    assert res.shore_pass_denied_count == 0
    assert res.immigration_status == ImmigrationPassType.SHORE_PASS_PERMITTED


def test_seafarer_manning_breach_and_rest_violation():
    """Test crew missing Chief Engineer and with fatigue rest violation."""
    crew = [
        SeafarerCrewMember("Nguyen Van A", "VNM", "B1234567", "VN-0988", SeafarerRank.MASTER, "2028-12-31", "2028-12-31", 11.0, 84.0),
        SeafarerCrewMember("Tran Van B", "VNM", "B2345678", "VN-0989", SeafarerRank.CHIEF_MATE, "2028-12-31", "2028-12-31", 8.0, 60.0),  # STCW breach (<10h / <77h)
        SeafarerCrewMember("Pham Van D", "VNM", "B4567890", "VN-0991", SeafarerRank.SECOND_ENGINEER, "2028-12-31", "2028-12-31", 10.0, 78.0),
    ]
    res = SeafarerImmigrationEngine.audit_crew_and_immigration("MV SHORT CREW", crew, assessment_date_iso="2026-10-01")
    assert res.is_safe_manning_compliant is False
    assert res.is_stcw_rest_compliant is False
    assert any("CHIEF_ENGINEER" in d for d in res.deficiencies)
    assert res.shore_pass_granted_count == 3
    assert res.shore_pass_denied_count == 0
    assert res.immigration_status == ImmigrationPassType.TRANSIT_VISA_REQUIRED


# ===========================================================================
# 4. Phase 193: Maritime Health Quarantine Tests
# ===========================================================================


def test_quarantine_free_pratique_granted():
    """Test health quarantine evaluation with valid SSCEC and zero cases granting Free Pratique."""
    res = MaritimeHealthQuarantineEngine.evaluate_health_quarantine(
        vessel_name="MV OCEAN PEARL",
        sscec_valid_until_iso="2026-12-31",
        communicable_cases_detected=0,
        has_visited_endemic_yellow_fever_port=False,
        assessment_date_iso="2026-10-01",
    )
    assert res.is_sscec_valid is True
    assert res.epidemiological_risk_score == 0.0
    assert res.quarantine_status == HealthQuarantineStatus.FREE_PRATIQUE_GRANTED
    assert res.yellow_flag_required is False
    assert res.free_pratique_certificate_no.startswith("VN-MDH-FP-")


def test_quarantine_yellow_flag_anchorage_required():
    """Test quarantine with expired SSCEC and endemic yellow fever port causing quarantine anchorage."""
    res = MaritimeHealthQuarantineEngine.evaluate_health_quarantine(
        vessel_name="MV RISK VOYAGER",
        sscec_valid_until_iso="2026-05-01",  # Expired
        communicable_cases_detected=0,
        has_visited_endemic_yellow_fever_port=True,
        assessment_date_iso="2026-10-01",
    )
    assert res.is_sscec_valid is False
    # Score = 0.0 + 2.5 (expired) + 2.0 (endemic) = 4.5
    assert res.epidemiological_risk_score == 4.5
    assert res.quarantine_status == HealthQuarantineStatus.QUARANTINE_ANCHORAGE_REQUIRED
    assert res.yellow_flag_required is True
    assert res.free_pratique_certificate_no is None


def test_quarantine_isolation_and_disinfection():
    """Test quarantine with infected cases detected requiring immediate isolation."""
    res = MaritimeHealthQuarantineEngine.evaluate_health_quarantine(
        vessel_name="MV INFECTED STAR",
        sscec_valid_until_iso="2026-12-31",
        communicable_cases_detected=3,
        has_visited_endemic_yellow_fever_port=False,
        assessment_date_iso="2026-10-01",
    )
    # Score = 3 * 3.0 = 9.0 (>= 6.0)
    assert res.epidemiological_risk_score == 9.0
    assert res.quarantine_status == HealthQuarantineStatus.ISOLATION_AND_DISINFECTION
    assert res.yellow_flag_required is True
    assert any("Isolate 3 infected personnel" in m for m in res.mandatory_health_measures)


# ===========================================================================
# 5. Phase 194: MARPOL & PRF Waste Reception Tests
# ===========================================================================


def test_marpol_environmental_full_compliance():
    """Test vessel compliant with 15 ppm OWS and 0.50% sulfur with PRF waste receipt."""
    res = MARPOLPortReceptionEngine.evaluate_environmental_compliance(
        vessel_name="MV GREEN VOYAGER",
        ows_bilge_oil_content_ppm=12.5,
        fuel_sulfur_content_pct=0.45,
        sludge_delivered_m3=5.0,
        garbage_delivered_m3=2.0,
    )
    assert res.is_ows_compliant is True
    assert res.is_fuel_sulfur_compliant is True
    assert res.is_marpol_fully_compliant is True
    assert res.prf_waste_delivery_receipt_no.startswith("VN-PRF-WDR-")
    # Tariff check: 5.0 * 1,500,000 + 2.0 * 400,000 = 7,500,000 + 800,000 = 8,300,000 VND
    assert res.environmental_levy_vnd == 8300000.0


def test_marpol_environmental_breach():
    """Test vessel with oily water separator > 15 ppm and high sulfur fuel."""
    res = MARPOLPortReceptionEngine.evaluate_environmental_compliance(
        vessel_name="MV POLLUTING SHIP",
        ows_bilge_oil_content_ppm=28.0,
        fuel_sulfur_content_pct=0.75,
        sludge_delivered_m3=0.0,
        garbage_delivered_m3=0.0,
    )
    assert res.is_ows_compliant is False
    assert res.is_fuel_sulfur_compliant is False
    assert res.is_marpol_fully_compliant is False
    assert res.prf_waste_delivery_receipt_no is None
    assert any("MARPOL Annex I Breach" in v for v in res.violations)
    assert any("MARPOL Annex VI Breach" in v for v in res.violations)


# ===========================================================================
# 6. Typer CLI Command Execution Tests
# ===========================================================================


def test_cli_vnsw_command():
    """Test vnsw clearance CLI command execution and JSON mode."""
    from src.cli.app_setup import build_app
    app = build_app()
    res = runner.invoke(app, ["vnsw", "clearance", "9382710", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["imo_number"] == "9382710"
    assert data["status"] == "CLEARED"


def test_cli_seafarer_command():
    """Test seafarer audit CLI command execution and JSON mode."""
    from src.cli.app_setup import build_app
    app = build_app()
    res = runner.invoke(app, ["seafarer", "audit", "MV_MYSHIP", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["vessel_name"] == "MV_MYSHIP"
    assert data["is_safe_manning_compliant"] is True


def test_cli_quarantine_command():
    """Test quarantine evaluate CLI command execution and JSON mode."""
    from src.cli.app_setup import build_app
    app = build_app()
    res = runner.invoke(app, ["quarantine", "evaluate", "MV_MYSHIP", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["vessel_name"] == "MV_MYSHIP"
    assert data["quarantine_status"] == "FREE_PRATIQUE_GRANTED"


def test_cli_marpol_command():
    """Test marpol audit CLI command execution and JSON mode."""
    from src.cli.app_setup import build_app
    app = build_app()
    res = runner.invoke(app, ["marpol", "audit", "MV_MYSHIP", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["vessel_name"] == "MV_MYSHIP"
    assert data["is_marpol_fully_compliant"] is True


# ===========================================================================
# 7. FastMCP Tool Handler Execution Tests
# ===========================================================================


def test_mcp_vnsw_clearance_handler():
    """Test FastMCP handle_vnsw_clearance response contract."""
    raw = handle_vnsw_clearance({
        "imo_number": "9382710",
        "vessel_name": "MV MEKONG STAR",
        "gross_tonnage": 15000.0,
    })
    resp = json.loads(raw)
    assert resp["ok"] is True
    assert resp["imo_number"] == "9382710"
    assert resp["status"] == "CLEARED"


def test_mcp_seafarer_manning_handler():
    """Test FastMCP handle_seafarer_manning response contract."""
    raw = handle_seafarer_manning({
        "vessel_name": "MV PACIFIC OCEAN",
    })
    resp = json.loads(raw)
    assert resp["ok"] is True
    assert resp["vessel_name"] == "MV PACIFIC OCEAN"
    assert resp["is_safe_manning_compliant"] is True


def test_mcp_quarantine_eval_handler():
    """Test FastMCP handle_quarantine_eval response contract."""
    raw = handle_quarantine_eval({
        "vessel_name": "MV OCEAN PEARL",
        "sscec_valid_until_iso": "2026-12-31",
    })
    resp = json.loads(raw)
    assert resp["ok"] is True
    assert resp["vessel_name"] == "MV OCEAN PEARL"
    assert resp["quarantine_status"] == "FREE_PRATIQUE_GRANTED"


def test_mcp_marpol_audit_handler():
    """Test FastMCP handle_marpol_audit response contract."""
    raw = handle_marpol_audit({
        "vessel_name": "MV GREEN VOYAGER",
        "ows_bilge_oil_content_ppm": 12.5,
        "fuel_sulfur_content_pct": 0.45,
    })
    resp = json.loads(raw)
    assert resp["ok"] is True
    assert resp["vessel_name"] == "MV GREEN VOYAGER"
    assert resp["is_marpol_fully_compliant"] is True
