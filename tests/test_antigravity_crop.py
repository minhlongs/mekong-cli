"""
Test Suite for Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Suite (Phase 98).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- CropEngine domain logic (Luật Trồng trọt 2018, Luật Bảo vệ và KDTV 2013, Thông tư 09/2023/TT-BNNPTNT, TCCS 774:2020/BVTV).
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
from src.core.crop_engine import (
    CropEngine,
    BANNED_PESTICIDE_ACTIVE_INGREDIENTS,
    STATUTORY_ALLOWED_INGREDIENTS,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestCropBoundary:
    """Verifies that crop_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "crop_engine.py")
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


class TestCropEngine:
    """Tests core domain and regulatory business logic of CropEngine."""

    def test_audit_planting_area_code_eligible(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        res = engine.audit_planting_area_code(
            area_name="HTX Sầu riêng Krông Pắc",
            crop_type="DURIAN_EXPORT",
            province="Đắk Lắk",
            cultivated_hectares=15.0,
            household_count=20,
            has_digital_farming_log=True,
            uses_allowed_pesticides_only=True,
            has_pest_monitoring_system=True,
            target_market="CHINA_GACC",
        )

        assert res["is_eligible"] is True
        assert len(res["deficiencies"]) == 0
        assert res["puc_code"] is not None
        assert res["puc_code"].startswith("VN-")
        assert res["audit_id"].startswith("PUC-AUD-")

    def test_audit_planting_area_code_ineligible(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        res = engine.audit_planting_area_code(
            area_name="Vườn Manh Mún Tự Phát",
            crop_type="DURIAN_EXPORT",
            province="Lâm Đồng",
            cultivated_hectares=3.5,  # < 10.0 ha min
            household_count=4,
            has_digital_farming_log=False,
            uses_allowed_pesticides_only=False,
            has_pest_monitoring_system=False,
            target_market="CHINA_GACC",
        )

        assert res["is_eligible"] is False
        assert res["puc_code"] is None
        assert len(res["deficiencies"]) >= 4
        assert any("Diện tích vùng trồng" in d for d in res["deficiencies"])
        assert any("Nhật ký canh tác" in d for d in res["deficiencies"])

    def test_audit_pesticide_compliance_banned(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        res = engine.audit_pesticide_compliance(
            crop_type="Sầu riêng",
            active_ingredient="PARAQUAT",
            dosage_liters_per_ha=1.0,
            days_since_application=10,
            intended_harvest_days=5,
        )

        assert res["is_banned"] is True
        assert "CRITICAL_BANNED_SUBSTANCE" in res["safety_status"]
        assert any("HOẠT CHẤT CẤM" in v for v in res["violations"])

    def test_audit_pesticide_compliance_phi_breach(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        # Azoxystrobin requires 7 days PHI. 2 + 1 = 3 days < 7
        res = engine.audit_pesticide_compliance(
            crop_type="Thanh long",
            active_ingredient="AZOXYSTROBIN",
            dosage_liters_per_ha=0.6,
            days_since_application=2,
            intended_harvest_days=1,
        )

        assert res["is_banned"] is False
        assert res["is_phi_breached"] is True
        assert "WARNING_PHI_BREACH" in res["safety_status"]
        assert any("VI PHẠM THỜI GIAN CÁCH LY" in v for v in res["violations"])

    def test_audit_pesticide_compliance_safe(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        # Bacillus thuringiensis has 1 day PHI
        res = engine.audit_pesticide_compliance(
            crop_type="Rau muống hữu cơ",
            active_ingredient="BACILLUS_THURINGIENSIS",
            dosage_liters_per_ha=1.0,
            days_since_application=3,
            intended_harvest_days=2,
        )

        assert res["is_banned"] is False
        assert res["is_phi_breached"] is False
        assert "SAFE_COMPLIANT" in res["safety_status"]
        assert len(res["violations"]) == 0

    def test_issue_phytosanitary_certificate_approved(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        res = engine.issue_phytosanitary_certificate(
            consignment_id="EXP-DUR-001",
            commodity_name="Sầu riêng Dona cấp đông",
            weight_metric_tons=28.0,
            origin_province="Đắk Lắk",
            destination_country="CHINA",
            treatment_method="VAPOR_HEAT_TREATMENT",
            puc_verified=True,
            quarantine_pests_detected=[],
        )

        assert res["is_approved"] is True
        assert "ĐẠT YÊU CẦU" in res["inspection_result"]
        assert res["certificate_id"].startswith("PHYTO-CERT-")

    def test_issue_phytosanitary_certificate_rejected(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        res = engine.issue_phytosanitary_certificate(
            consignment_id="EXP-DUR-002",
            commodity_name="Xoài cát Chu tươi",
            weight_metric_tons=15.0,
            origin_province="Đồng Tháp",
            destination_country="USA",
            treatment_method="HOT_WATER_TREATMENT",
            puc_verified=False,
            quarantine_pests_detected=["Bactrocera dorsalis"],
        )

        assert res["is_approved"] is False
        assert "KHÔNG ĐẠT" in res["inspection_result"]
        assert any("PHÁT HIỆN SINH VẬT GÂY HẠI" in a for a in res["quarantine_actions"])

    def test_audit_pesticide_store_license_eligible(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        res = engine.audit_pesticide_store_license(
            store_name="Đại lý VTNN Mekong Xanh",
            owner_name="Trần Văn Nông",
            province="An Giang",
            owner_has_practice_cert=True,
            distance_to_water_source_m=75.0,
            has_ventilation_and_leak_basin=True,
            has_pccc_equipment=True,
            has_expired_or_counterfeit=False,
        )

        assert res["is_eligible"] is True
        assert res["validity_years"] == 5
        assert len(res["deficiencies"]) == 0
        assert res["audit_id"].startswith("PEST-STR-")

    def test_audit_pesticide_store_license_ineligible(self, temp_db):
        engine = CropEngine(db_path=temp_db)
        res = engine.audit_pesticide_store_license(
            store_name="Tiệm Tạp Hóa Trộn Thuốc",
            owner_name="Lê Vi Phạm",
            province="Cần Thơ",
            owner_has_practice_cert=False,
            distance_to_water_source_m=20.0,  # < 50m
            has_ventilation_and_leak_basin=False,
            has_pccc_equipment=False,
            has_expired_or_counterfeit=True,
        )

        assert res["is_eligible"] is False
        assert res["validity_years"] == 0
        assert len(res["deficiencies"]) >= 4

    def test_list_records_and_status(self, temp_db):
        engine = CropEngine(db_path=temp_db)

        # Populate
        engine.audit_planting_area_code(area_name="Vùng 1")
        engine.audit_pesticide_compliance(crop_type="Lúa", active_ingredient="AZOXYSTROBIN")
        engine.issue_phytosanitary_certificate(consignment_id="LOT-1", commodity_name="Lúa ST25")
        engine.audit_pesticide_store_license(store_name="Cửa hàng 1")

        # List all
        all_rec = engine.list_records(category="all", limit=10)
        assert len(all_rec) == 4

        # List categories
        assert len(engine.list_records(category="puc")) == 1
        assert len(engine.list_records(category="pesticides")) == 1
        assert len(engine.list_records(category="phyto")) == 1
        assert len(engine.list_records(category="stores")) == 1

        # Status
        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_puc_audits"] == 1
        assert status["total_pesticide_checks"] == 1
        assert status["total_phytosanitary_certificates"] == 1
        assert status["total_pesticide_stores_audited"] == 1


class TestCropCLI:
    """Tests Typer CLI interface for crop commands in --json mode."""

    def test_crop_puc_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "crop",
                "puc",
                "HTX Sầu riêng Cai Lậy",
                "--crop", "DURIAN_EXPORT",
                "--province", "Tiền Giang",
                "--hectares", "16.0",
                "--households", "22",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_eligible"] is True
        assert data["area_name"] == "HTX Sầu riêng Cai Lậy"

    def test_crop_pesticide_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "crop",
                "pesticide",
                "Sầu riêng",
                "--ingredient", "AZOXYSTROBIN",
                "--dosage", "0.5",
                "--days-applied", "10",
                "--harvest-in", "2",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "SAFE_COMPLIANT" in data["safety_status"]

    def test_crop_phyto_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "crop",
                "phyto",
                "EXP-LOT-2026",
                "--commodity", "Thanh long ruột đỏ",
                "--weight", "20.0",
                "--province", "Bình Thuận",
                "--dest", "CHINA",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_approved"] is True
        assert data["consignment_id"] == "EXP-LOT-2026"

    def test_crop_store_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "crop",
                "store",
                "Cửa hàng Nông Nghiệp Xanh",
                "--owner", "Nguyễn Văn Lúa",
                "--province", "An Giang",
                "--water-dist", "80.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_eligible"] is True

    def test_crop_list_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["crop", "list", "all", "--limit", "10", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_crop_status_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["crop", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"
        assert "total_puc_audits" in data


class TestCropMCP:
    """Tests dual MCP handlers for crop cultivation and plant protection tools."""

    def test_core_mcp_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-crop-core")

        # PUC
        res1 = json.loads(server._handle_crop_puc(area_name="MCP Test Area", cultivated_hectares=14.0))
        assert res1["area_name"] == "MCP Test Area"
        assert res1["is_eligible"] is True

        # Pesticide
        res2 = json.loads(server._handle_crop_pesticide(crop_type="Sầu riêng", active_ingredient="PARAQUAT"))
        assert res2["is_banned"] is True

        # Phyto
        res3 = json.loads(server._handle_crop_phyto(consignment_id="MCP-PHYTO-01"))
        assert res3["is_approved"] is True

        # Store
        res4 = json.loads(server._handle_crop_store(store_name="MCP Pesticide Store"))
        assert res4["is_eligible"] is True

        # List
        res5 = json.loads(server._handle_crop_list(category="all", limit=5))
        assert isinstance(res5, list)

        # Status
        res6 = json.loads(server._handle_crop_status())
        assert res6["status"] == "operational"

    def test_scripts_mcp_handlers(self):
        from scripts.mcp_server import (
            handle_crop_puc,
            handle_crop_pesticide,
            handle_crop_phyto,
            handle_crop_store,
            handle_crop_list,
            handle_crop_status,
        )

        res1 = json.loads(handle_crop_puc({"area_name": "Fallback Crop Area"}))
        assert res1["area_name"] == "Fallback Crop Area"

        res2 = json.loads(handle_crop_pesticide({"crop_type": "Thanh long", "active_ingredient": "ABAMECTIN"}))
        assert "safety_status" in res2

        res3 = json.loads(handle_crop_phyto({"consignment_id": "Fallback Phyto Lot"}))
        assert "is_approved" in res3

        res4 = json.loads(handle_crop_store({"store_name": "Fallback Store"}))
        assert "is_eligible" in res4

        res5 = json.loads(handle_crop_list({"category": "all", "limit": 5}))
        assert isinstance(res5, list)

        res6 = json.loads(handle_crop_status({}))
        assert res6["status"] == "operational"
