"""Comprehensive test suite for Ship Technical, Registration, Dredging & Seaport Masterplan Suite (Phases 195-198).

Validates:
- AST zero-dependency invariant (Pure Python Standard Library only).
- Phase 195: Ship Classification, HSSC survey intervals & Condition of Class (Circular 17/2023/TT-BGTVT).
- Phase 196: Ship Registration, bareboat flag suspension & maritime mortgages (Decree 171/2016/NĐ-CP).
- Phase 197: Maritime Channel Dredging & Dynamic UKC Squat (Decree 58/2017/NĐ-CP & PIANC).
- Phase 198: Seaport Masterplan Capacity & Queuing Dynamics (Decision 1579/QĐ-TTg).
- CLI commands and aliases via Typer CliRunner.
- FastMCP tool handler invocations.
"""

import ast
import json
from typer.testing import CliRunner

from src.core.ship_tech_masterplan_engine import (
    ClassStatus,
    ConditionOfClass,
    ShipClassificationEngine,
    RegistryType,
    MortgagePriority,
    MaritimeMortgage,
    ShipRegistrationEngine,
    ChannelType,
    MaritimeDredgingUKCEngine,
    SeaportCategory,
    SeaportMasterplanEngine,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_shipclass_audit,
    handle_shipreg_evaluate,
    handle_dredging_ukc,
    handle_masterplan_capacity,
)


# ===========================================================================
# 1. AST Zero-Dependency Invariant Test
# ===========================================================================

def test_ast_zero_external_dependencies():
    """Ensure engine module strictly uses Python standard library only."""
    with open("src/core/ship_tech_masterplan_engine.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    allowed_modules = {
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
                assert root_pkg in allowed_modules, f"Disallowed external import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_pkg = node.module.split(".")[0]
                assert root_pkg in allowed_modules, f"Disallowed external import from: {node.module}"


# ===========================================================================
# 2. Phase 195: Ship Classification & HSSC Engine Tests
# ===========================================================================

def test_ship_classification_in_class():
    """Verify compliant vessel with active class and no overdue surveys."""
    audit = ShipClassificationEngine.audit_classification(
        imo_number="9481234",
        vessel_name="MV MEKONG PRIDE",
        class_society="VIETNAM_REGISTER",
        certificate_issued_iso="2023-01-15",
        last_renewal_survey_iso="2023-01-15",
        last_drydock_survey_iso="2024-06-01",
        assessment_date_iso="2024-12-15",
        cocs=[],
    )

    assert audit.is_in_class is True
    assert audit.class_status in [ClassStatus.IN_CLASS, ClassStatus.SURVEY_DUE]
    assert audit.drydock_interval_months <= 36.0
    assert len(audit.overdue_surveys) == 0


def test_ship_classification_overdue_drydock_and_coc():
    """Verify vessel status suspended when bottom drydock exceeds 36 months and CoC overdue."""
    coc = ConditionOfClass(
        coc_id="COC-01",
        description="Cracked ballast tank frame #42",
        due_date_iso="2025-01-01",
        is_rectified=False,
    )
    audit = ShipClassificationEngine.audit_classification(
        imo_number="9112233",
        vessel_name="MV OLD CARRIER",
        class_society="VIETNAM_REGISTER",
        certificate_issued_iso="2020-01-15",
        last_renewal_survey_iso="2020-01-15",
        last_drydock_survey_iso="2020-02-01",  # > 36 months by 2026
        assessment_date_iso="2026-10-01",
        cocs=[coc],
    )

    assert audit.is_in_class is False
    assert audit.class_status == ClassStatus.SUSPENDED
    assert any("BOTTOM_DRYDOCK_OVERDUE" in s for s in audit.overdue_surveys)
    assert any("COC_OVERDUE" in s for s in audit.overdue_surveys)


# ===========================================================================
# 3. Phase 196: Ship Registration & Mortgage Engine Tests
# ===========================================================================

def test_ship_registration_valid_official():
    """Verify official registration with full statutory dossier."""
    m1 = MaritimeMortgage(
        mortgage_id="M-01",
        mortgagee_name="Vietcombank HCM",
        secured_amount_vnd=250_000_000_000.0,
        registration_date_iso="2024-01-10",
        priority=MortgagePriority.FIRST_RANK,
    )
    res = ShipRegistrationEngine.evaluate_registration(
        registration_no="VN-HP-8899",
        vessel_name="MV MEKONG PIONEER",
        registry_type=RegistryType.OFFICIAL,
        submitted_documents=["BILL_OF_SALE", "BUILDER_CERTIFICATE", "CLASS_CERTIFICATE", "TONNAGE_CERTIFICATE", "DELETION_CERTIFICATE"],
        mortgages=[m1],
        is_arrested=False,
    )

    assert res.is_valid_vietnamese_flag is True
    assert res.flag_state == "VIETNAM"
    assert res.required_dossier_complete is True
    assert res.total_encumbrance_vnd == 250_000_000_000.0
    assert res.is_free_from_arrest is True


def test_ship_registration_bareboat_out_suspends_flag():
    """Verify bareboat charter out temporarily suspends Vietnamese flag."""
    res = ShipRegistrationEngine.evaluate_registration(
        registration_no="VN-SG-1002",
        vessel_name="MV LEASED OVERSEAS",
        registry_type=RegistryType.BAREBOAT_OUT,
        submitted_documents=["BAREBOAT_CHARTER_CONTRACT", "VN_FLAG_SUSPENSION_APPLICATION", "MORTGAGEE_CONSENT"],
        mortgages=[],
        is_arrested=False,
    )

    assert res.is_valid_vietnamese_flag is False
    assert res.flag_state == "SUSPENDED/FOREIGN"
    assert res.required_dossier_complete is True


def test_ship_registration_incomplete_dossier():
    """Verify incomplete statutory dossier flags missing documents."""
    res = ShipRegistrationEngine.evaluate_registration(
        registration_no="VN-HP-5555",
        vessel_name="MV MISSING PAPERS",
        registry_type=RegistryType.OFFICIAL,
        submitted_documents=["BILL_OF_SALE"],
        mortgages=[],
        is_arrested=False,
    )

    assert res.is_valid_vietnamese_flag is False
    assert res.required_dossier_complete is False
    assert len(res.missing_documents) == 4
    assert "INCOMPLETE DOSSIER" in res.status_summary


def test_ship_registration_judicial_arrest():
    """Verify judicial arrest immediately invalidates flight and flags vessel."""
    res = ShipRegistrationEngine.evaluate_registration(
        registration_no="VN-HP-7711",
        vessel_name="MV ARRESTED TANKER",
        registry_type=RegistryType.OFFICIAL,
        submitted_documents=["BILL_OF_SALE", "BUILDER_CERTIFICATE", "CLASS_CERTIFICATE", "TONNAGE_CERTIFICATE", "DELETION_CERTIFICATE"],
        mortgages=[],
        is_arrested=True,
    )

    assert res.is_valid_vietnamese_flag is False
    assert res.is_free_from_arrest is False
    assert "JUDICIAL ARREST" in res.status_summary


# ===========================================================================
# 4. Phase 197: Maritime Dredging & UKC Squat Engine Tests
# ===========================================================================

def test_dredging_ukc_safe_passage():
    """Verify safe passage in confined channel when net UKC exceeds margin."""
    res = MaritimeDredgingUKCEngine.calculate_ukc(
        channel_name="Soai Rap Channel",
        channel_type=ChannelType.CONFINED,
        designed_depth_m=9.5,
        tide_height_m=2.8,
        vessel_draft_m=9.8,
        speed_knots=8.0,
        block_coefficient=0.80,
        wave_swell_allowance_m=0.20,
        sediment_allowance_m=0.15,
        safety_margin_m=0.30,
    )

    # Gross = 9.5 + 2.8 - 9.8 = 2.5m
    # Squat = (0.80 * 64 / 100) * 2.0 = 1.024m
    # Net = 2.5 - (1.024 + 0.20 + 0.15) = 1.126m >= 0.30m
    assert res.gross_ukc_m == 2.5
    assert res.is_passage_safe is True
    assert "SAFE NAVIGATION" in res.clearance_verdict


def test_dredging_ukc_grounding_risk():
    """Verify grounding risk triggered when speed/draft induces excessive squat."""
    res = MaritimeDredgingUKCEngine.calculate_ukc(
        channel_name="Dinh An Channel",
        channel_type=ChannelType.CONFINED,
        designed_depth_m=4.5,
        tide_height_m=1.0,
        vessel_draft_m=5.0,
        speed_knots=12.0,
        block_coefficient=0.85,
        wave_swell_allowance_m=0.20,
        sediment_allowance_m=0.20,
        safety_margin_m=0.30,
    )

    assert res.is_passage_safe is False
    assert "GROUNDING RISK" in res.clearance_verdict


# ===========================================================================
# 5. Phase 198: Seaport Masterplan Capacity Engine Tests
# ===========================================================================

def test_seaport_masterplan_optimal_capacity():
    """Verify port within Decision 1579 utilization limit (<= 70%)."""
    res_optimal = SeaportMasterplanEngine.evaluate_port_capacity(
        port_name="Cai Mep Deepwater Hub",
        category=SeaportCategory.SPECIAL,
        total_berths=20,
        annual_actual_throughput_teu=2_500_000.0,
        crane_productivity_teu_per_hour=30.0,
        operating_days_per_year=350,
        working_hours_per_day=20.0,
        utilization_limit_pct=70.0,
    )

    # Capacity = 20 * 350 * 20 * 30 = 4,200,000 TEU
    # Occupancy = 2.5M / 4.2M = ~59.5%
    assert res_optimal.is_within_masterplan_limit is True
    assert res_optimal.occupancy_rate_pct < 70.0
    assert res_optimal.expected_queue_delay_hours >= 0.0
    assert "CAPACITY OPTIMAL" in res_optimal.recommendation


def test_seaport_masterplan_congestion_warning():
    """Verify congestion warning when throughput exceeds 70% utilization threshold."""
    res_congested = SeaportMasterplanEngine.evaluate_port_capacity(
        port_name="Congested River Port",
        category=SeaportCategory.CLASS_II,
        total_berths=2,
        annual_actual_throughput_teu=400_000.0,
        crane_productivity_teu_per_hour=25.0,
        operating_days_per_year=350,
        working_hours_per_day=20.0,
        utilization_limit_pct=70.0,
    )

    # Capacity = 2 * 350 * 20 * 25 = 350,000 TEU
    # Occupancy = 400,000 / 350,000 = 114.3%
    assert res_congested.is_within_masterplan_limit is False
    assert "CONGESTION WARNING" in res_congested.recommendation


# ===========================================================================
# 6. CLI Runner Invocation Tests
# ===========================================================================

def test_cli_shipclass_commands():
    """Verify shipclass and dangkiem CLI commands, including complex CoC descriptions."""
    runner = CliRunner()
    app = build_app()

    res1 = runner.invoke(app, [
        "shipclass", "audit",
        "--coc", "COC-101:Weld inspection: Frame #4:2025-11-01",
        "--json",
    ])
    assert res1.exit_code == 0
    data1 = json.loads(res1.stdout)
    assert data1["class_society"] == "VIETNAM_REGISTER"
    assert len(data1["outstanding_cocs"]) == 1
    assert data1["outstanding_cocs"][0]["description"] == "Weld inspection: Frame #4"

    res2 = runner.invoke(app, ["dangkiem", "audit", "--json"])
    assert res2.exit_code == 0


def test_cli_shipreg_commands():
    """Verify shipreg and dangky CLI commands."""
    runner = CliRunner()
    app = build_app()

    res1 = runner.invoke(app, ["shipreg", "evaluate", "--json"])
    assert res1.exit_code == 0
    data1 = json.loads(res1.stdout)
    assert data1["is_valid_vietnamese_flag"] is True

    res2 = runner.invoke(app, ["dangky", "evaluate", "--json"])
    assert res2.exit_code == 0


def test_cli_dredging_commands():
    """Verify dredging and naovet CLI commands."""
    runner = CliRunner()
    app = build_app()

    res1 = runner.invoke(app, ["dredging", "ukc-calc", "--json"])
    assert res1.exit_code == 0
    data1 = json.loads(res1.stdout)
    assert "net_ukc_m" in data1

    res2 = runner.invoke(app, ["naovet", "ukc-calc", "--json"])
    assert res2.exit_code == 0


def test_cli_masterplan_commands():
    """Verify masterplan and quyhoach CLI commands."""
    runner = CliRunner()
    app = build_app()

    res1 = runner.invoke(app, ["masterplan", "port-capacity", "--json"])
    assert res1.exit_code == 0
    data1 = json.loads(res1.stdout)
    assert "annual_capacity_teu" in data1

    res2 = runner.invoke(app, ["quyhoach", "port-capacity", "--json"])
    assert res2.exit_code == 0


# ===========================================================================
# 7. FastMCP Handler Tests
# ===========================================================================

def test_mcp_shipclass_audit_handler():
    """Test handle_shipclass_audit FastMCP endpoint."""
    raw = handle_shipclass_audit({
        "imo_number": "9481234",
        "vessel_name": "MV MEKONG PRIDE",
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["class_status"] == "IN_CLASS"


def test_mcp_shipreg_evaluate_handler():
    """Test handle_shipreg_evaluate FastMCP endpoint."""
    raw = handle_shipreg_evaluate({
        "registration_no": "VN-HP-8899",
        "registry_type": "OFFICIAL",
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["is_valid_vietnamese_flag"] is True


def test_mcp_dredging_ukc_handler():
    """Test handle_dredging_ukc FastMCP endpoint."""
    raw = handle_dredging_ukc({
        "channel_name": "Soai Rap",
        "channel_type": "CONFINED",
        "speed_knots": 8.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["is_passage_safe"] is True


def test_mcp_masterplan_capacity_handler():
    """Test handle_masterplan_capacity FastMCP endpoint."""
    raw = handle_masterplan_capacity({
        "port_name": "Cai Mep",
        "total_berths": 15,
        "annual_actual_throughput_teu": 3000000.0,
    })
    res = json.loads(raw)
    assert res["ok"] is True
    assert "occupancy_rate_pct" in res
