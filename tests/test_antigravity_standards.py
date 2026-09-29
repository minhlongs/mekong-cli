"""
Test Suite for Vietnamese Technical Standards, Metrology & Product Quality Suite (Phase 87).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- StandardsEngine domain logic (TCVN/QCVN lookup, conformity declarations, CR mark audit, measuring instruments, quality inspections).
- CLI commands with Rich tables and headless --json mode.
- Dual MCP server handlers (FastMCP and fallback JSON-RPC 2.0).
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.standards_engine import StandardsEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestStandardsBoundary:
    """Verifies that standards_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "standards_engine.py")
        with open(engine_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=engine_path)

        forbidden_prefixes = ("requests", "httpx", "aiohttp", "boto3", "openai", "anthropic", "google")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith(forbidden_prefixes), f"Forbidden from-import: {node.module}"


class TestStandardsEngine:
    """Tests core business logic of StandardsEngine."""

    def test_lookup_standards(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        all_std = engine.lookup_standard("")
        assert len(all_std) >= 5

        qcvn_list = engine.lookup_standard("an toàn", standard_type="QCVN")
        assert len(qcvn_list) >= 1
        for s in qcvn_list:
            assert s["type"] == "QCVN"
            assert s["is_mandatory"] == 1

        tcvn_list = engine.lookup_standard("ISO", standard_type="TCVN")
        assert len(tcvn_list) >= 1
        for s in tcvn_list:
            assert s["type"] == "TCVN"

    def test_register_conformity_declaration_compliant(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        res = engine.register_conformity_declaration(
            product_name="Quạt điện gia dụng",
            manufacturer="Công ty TNHH Cơ điện Mekong",
            standard_code="QCVN 04:2009/BKHCN",
            conformity_type="HOP_QUY",
            test_report_no="TR-2026-MEK-01",
            cert_body="QUATEST 3",
            is_group_2=True,
        )
        assert res["status"] == "REGISTERED_COMPLIANT"
        assert res["is_approved"] is True
        assert res["declaration_code"].startswith("DKHQ-")
        assert len(res["deficiencies"]) == 0

    def test_register_conformity_declaration_group2_tcvn_deficient(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        # Group 2 product claiming voluntary HOP_CHUAN instead of mandatory HOP_QUY
        res = engine.register_conformity_declaration(
            product_name="Mũ bảo hiểm xe máy",
            manufacturer="Xưởng Sản xuất Việt Phát",
            standard_code="TCVN ISO 9001:2015",
            conformity_type="HOP_CHUAN",
            test_report_no="TR-2026-FAIL",
            cert_body="QUACERT",
            is_group_2=True,
        )
        assert res["status"] == "DEFICIENT_REJECTED"
        assert res["is_approved"] is False
        assert len(res["deficiencies"]) >= 1

    def test_verify_cr_marking_compliant(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        res = engine.verify_cr_marking(
            product_name="Bàn là điện hơi nước",
            has_cr_mark=True,
            cr_height_mm=6.5,  # >= 5.0mm
            cert_body_code="VN01",
            declaration_code="DKHQ-2026-088",
            is_group_2=True,
        )
        assert res["status"] == "COMPLIANT_CR_MARK"
        assert res["is_compliant"] is True
        assert res["estimated_fine_vnd"] == 0.0

    def test_verify_cr_marking_missing_or_small(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        # Missing CR mark on Group 2 product
        res1 = engine.verify_cr_marking(
            product_name="Đồ chơi xếp hình trẻ em",
            has_cr_mark=False,
            is_group_2=True,
        )
        assert res1["status"] == "VIOLATION_CR_MARK"
        assert res1["is_compliant"] is False
        assert res1["estimated_fine_vnd"] >= 20_000_000.0

        # Sub-standard height (< 5mm)
        res2 = engine.verify_cr_marking(
            product_name="Máy sấy tóc",
            has_cr_mark=True,
            cr_height_mm=3.5,  # < 5mm
            cert_body_code="VN01",
            declaration_code="DKHQ-01",
            is_group_2=True,
        )
        assert res2["status"] == "VIOLATION_CR_MARK"
        assert res2["is_compliant"] is False
        assert res2["estimated_fine_vnd"] >= 15_000_000.0

    def test_audit_measuring_instrument_valid(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        res = engine.audit_measuring_instrument(
            instrument_name="Cột đo xăng dầu Tokico",
            instrument_type="FUEL_DISPENSER",
            serial_number="TK-9921",
            last_verification_date="2026-01-15",
            validity_period_months=12,
            seal_intact=True,
            check_date="2026-06-01",
        )
        assert res["status"] == "VERIFIED_VALID"
        assert res["is_valid"] is True
        assert res["estimated_fine_vnd"] == 0.0

    def test_audit_measuring_instrument_expired(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        res = engine.audit_measuring_instrument(
            instrument_name="Cân đồng hồ thương mại 30kg",
            instrument_type="SCALE",
            serial_number="SC-0044",
            last_verification_date="2024-01-01",
            validity_period_months=12,
            seal_intact=True,
            check_date="2026-01-01",
        )
        assert res["status"] == "EXPIRED_VERIFICATION"
        assert res["is_valid"] is False
        assert res["estimated_fine_vnd"] >= 15_000_000.0

    def test_audit_measuring_instrument_broken_seal(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        res = engine.audit_measuring_instrument(
            instrument_name="Công tơ điện 3 pha",
            instrument_type="ELECTRIC_METER",
            serial_number="EM-7711",
            last_verification_date="2026-01-01",
            validity_period_months=24,
            seal_intact=False,  # Broken seal
            check_date="2026-05-01",
        )
        assert res["status"] == "BROKEN_SEAL_VIOLATION"
        assert res["is_valid"] is False
        assert res["estimated_fine_vnd"] >= 20_000_000.0

    def test_record_quality_inspection_pass_and_fail(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        # Passed batch
        res_pass = engine.record_quality_inspection(
            batch_no="LOT-2026-ST-01",
            product_name="Dây cáp điện chống cháy",
            sample_size=200,
            defective_units=0,
        )
        assert res_pass["status"] == "PASSED_INSPECTION"
        assert res_pass["is_passed"] is True

        # Failed batch
        res_fail = engine.record_quality_inspection(
            batch_no="LOT-2026-ST-02",
            product_name="Gạch men ceramic",
            sample_size=200,
            defective_units=15,  # 7.5% defect rate > 1%
        )
        assert res_fail["status"] == "FAILED_INSPECTION"
        assert res_fail["is_passed"] is False

    def test_list_records_and_status(self, temp_db):
        engine = StandardsEngine(db_path=temp_db)
        engine.register_conformity_declaration("Ấm đun nước", "NXB MK", "QCVN 04:2009/BKHCN")
        engine.verify_cr_marking("Ấm đun nước", has_cr_mark=True, cr_height_mm=6.0)
        engine.audit_measuring_instrument("Đồng hồ nước", "WATER_METER", "SN-01", "2026-01-01")
        engine.record_quality_inspection("BATCH-01", "Sơn tường")

        decs = engine.list_records("declarations")
        assert len(decs) >= 1
        cr_records = engine.list_records("cr_marks")
        assert len(cr_records) >= 1
        insts = engine.list_records("instruments")
        assert len(insts) >= 1
        insps = engine.list_records("inspections")
        assert len(insps) >= 1

        dash = engine.get_status()
        assert dash["total_standards_cataloged"] >= 5
        assert dash["total_conformity_declarations"] >= 1
        assert dash["total_cr_mark_verifications"] >= 1


class TestStandardsCLI:
    """Tests CLI command execution for mekong standards."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_help(self, runner, app):
        result = runner.invoke(app, ["standards", "--help"])
        assert result.exit_code == 0
        assert "standards" in result.stdout.lower()

    def test_cli_status_json(self, runner, app):
        result = runner.invoke(app, ["standards", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_standards_cataloged" in data

    def test_cli_lookup_json(self, runner, app):
        result = runner.invoke(app, ["standards", "lookup", "an toàn", "--type", "QCVN", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_cli_declare_json(self, runner, app):
        result = runner.invoke(
            app,
            [
                "standards",
                "declare",
                "Máy sấy quần áo",
                "QCVN 04:2009/BKHCN",
                "--manufacturer",
                "Mekong Electronics",
                "--type",
                "HOP_QUY",
                "--report-no",
                "TR-2026-CLI-01",
                "--cert-body",
                "QUATEST 1",
                "--group-2",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "REGISTERED_COMPLIANT"

    def test_cli_cr_json(self, runner, app):
        result = runner.invoke(
            app,
            [
                "standards",
                "cr",
                "Lò vi sóng",
                "--has-cr",
                "--height",
                "6.0",
                "--cert-code",
                "VN01",
                "--dec-code",
                "DKHQ-2026-CLI",
                "--group-2",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "COMPLIANT_CR_MARK"

    def test_cli_instrument_json(self, runner, app):
        result = runner.invoke(
            app,
            [
                "standards",
                "instrument",
                "Cột đo xăng dầu số 2",
                "SN-PETROL-002",
                "--type",
                "FUEL_DISPENSER",
                "--last-date",
                "2026-01-01",
                "--validity-months",
                "12",
                "--seal",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "VERIFIED_VALID"

    def test_cli_inspect_json(self, runner, app):
        result = runner.invoke(
            app,
            [
                "standards",
                "inspect",
                "LOT-CLI-01",
                "Thép kết cấu",
                "--origin",
                "Nhật Bản",
                "--sample",
                "150",
                "--defective",
                "0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "PASSED_INSPECTION"

    def test_cli_list_json(self, runner, app):
        result = runner.invoke(app, ["standards", "list", "standards", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestStandardsMCP:
    """Tests dual FastMCP and fallback JSON-RPC handlers."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_lookup = server._handle_standards_lookup(query="ISO", standard_type="TCVN")
        data_lookup = json.loads(res_lookup)
        assert isinstance(data_lookup, list)

        res_dec = server._handle_standards_declare(
            product_name="Đèn LED chiếu sáng",
            standard_code="QCVN 09:2012/BKHCN",
            conformity_type="HOP_QUY",
        )
        data_dec = json.loads(res_dec)
        assert data_dec["status"] == "REGISTERED_COMPLIANT"

        res_cr = server._handle_standards_cr(
            product_name="Đèn LED chiếu sáng",
            has_cr_mark=True,
            cr_height_mm=5.5,
        )
        data_cr = json.loads(res_cr)
        assert data_cr["status"] == "COMPLIANT_CR_MARK"

        res_status = server._handle_standards_status()
        data_status = json.loads(res_status)
        assert "total_standards_cataloged" in data_status

    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_standards_lookup,
            handle_standards_declare,
            handle_standards_cr,
            handle_standards_instrument,
            handle_standards_inspect,
            handle_standards_list,
            handle_standards_status,
        )

        res_lookup = handle_standards_lookup({"query": "QCVN 04"})
        data_lookup = json.loads(res_lookup)
        assert isinstance(data_lookup, list)

        res_inst = handle_standards_instrument({
            "instrument_name": "Cân phân tích phòng thí nghiệm",
            "serial_number": "SN-LAB-99",
            "instrument_type": "SCALE",
            "last_verification_date": "2026-02-01",
            "validity_period_months": 12,
            "seal_intact": True,
        })
        data_inst = json.loads(res_inst)
        assert data_inst["status"] == "VERIFIED_VALID"

        res_status = handle_standards_status({})
        data_status = json.loads(res_status)
        assert "total_standards_cataloged" in data_status
