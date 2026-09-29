# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Pharmaceutical Logistics, National Drug Bank & GXP QA Engine (Phase 63)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.pharma_engine import (
    DRUG_CLASSIFICATIONS,
    GSP_STORAGE_CONDITIONS,
    RECALL_LEVELS,
    PharmaEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestPharmaCoreBoundary:
    """Ensure PharmaEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/pharma_engine.py")
        assert source_path.exists(), "pharma_engine.py must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import: {pkg}"


# ---------------------------------------------------------------------------
# Engine Unit Tests
# ---------------------------------------------------------------------------


class TestPharmaEngine:
    """Test PharmaEngine marketing authorizations, GSP storage audits, GS1 batch tracking, and pricing."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> PharmaEngine:
        db_file = tmp_path / "test_pharma.db"
        return PharmaEngine(db_path=db_file)

    def test_constants_and_classifications(self) -> None:
        assert "RX_PRESCRIPTION" in DRUG_CLASSIFICATIONS
        assert "OTC_NON_PRESCRIPTION" in DRUG_CLASSIFICATIONS
        assert "SPECIAL_CONTROL_NARCOTIC" in DRUG_CLASSIFICATIONS
        assert "VACCINE_BIOLOGICAL" in DRUG_CLASSIFICATIONS

        assert DRUG_CLASSIFICATIONS["RX_PRESCRIPTION"]["requires_prescription"] is True
        assert DRUG_CLASSIFICATIONS["OTC_NON_PRESCRIPTION"]["requires_prescription"] is False
        assert DRUG_CLASSIFICATIONS["SPECIAL_CONTROL_NARCOTIC"]["special_control"] is True

        assert "STANDARD_ROOM" in GSP_STORAGE_CONDITIONS
        assert "COOL_STORAGE" in GSP_STORAGE_CONDITIONS
        assert "COLD_CHAIN" in GSP_STORAGE_CONDITIONS
        assert "DEEP_FREEZE" in GSP_STORAGE_CONDITIONS

        assert GSP_STORAGE_CONDITIONS["COLD_CHAIN"]["min_temp_c"] == 2.0
        assert GSP_STORAGE_CONDITIONS["COLD_CHAIN"]["max_temp_c"] == 8.0

        assert "LEVEL_1" in RECALL_LEVELS
        assert RECALL_LEVELS["LEVEL_1"]["timeframe_hours"] == 24
        assert RECALL_LEVELS["LEVEL_2"]["timeframe_hours"] == 48
        assert RECALL_LEVELS["LEVEL_3"]["timeframe_hours"] == 72

    def test_register_drug_marketing_authorization(self, engine: PharmaEngine) -> None:
        # Imported drug registration
        res_import = engine.register_drug_marketing_authorization(
            visa_number="VN-22019-19",
            drug_name="Augmentin 1g",
            active_ingredient="Amoxicillin + Clavulanic Acid",
            strength="1000mg",
            dosage_form="Viên nén bao phim",
            classification="RX_PRESCRIPTION",
            manufacturer_name="Glaxo Wellcome Production",
            country_of_origin="France",
            tenure_years=5,
        )
        assert res_import["ok"] is True
        assert res_import["registration_id"].startswith("MA-")
        assert res_import["marketing_authorization"]["visa_number"] == "VN-22019-19"
        assert res_import["marketing_authorization"]["is_imported_drug"] is True
        assert res_import["marketing_authorization"]["is_domestic_drug"] is False
        assert res_import["regulatory_classification"]["requires_prescription"] is True
        assert res_import["manufacturing_profile"]["valid_tenure_years"] == 5

        # Domestic drug registration
        res_domestic = engine.register_drug_marketing_authorization(
            visa_number="VD-35124-21",
            drug_name="Hapacol 650",
            active_ingredient="Paracetamol",
            strength="650mg",
            dosage_form="Viên nén",
            classification="OTC_NON_PRESCRIPTION",
            manufacturer_name="DHG Pharma",
            country_of_origin="Vietnam",
        )
        assert res_domestic["marketing_authorization"]["is_domestic_drug"] is True
        assert res_domestic["marketing_authorization"]["is_imported_drug"] is False
        assert res_domestic["regulatory_classification"]["requires_prescription"] is False

    def test_audit_gsp_storage_condition_compliant(self, engine: PharmaEngine) -> None:
        # Vaccine cold chain: 4.5°C, 55% humidity -> fully compliant
        res = engine.audit_gsp_storage_condition(
            warehouse_id="WH-COLD-01",
            warehouse_name="Kho Vắc xin Trung tâm",
            storage_condition="COLD_CHAIN",
            recorded_temp_c=4.5,
            recorded_humidity_pct=55.0,
            sensor_id="LOG-TMP-01",
        )
        assert res["ok"] is True
        assert res["log_id"].startswith("GSP-")
        assert res["warehouse_facility"]["warehouse_id"] == "WH-COLD-01"
        assert res["environmental_telemetry"]["temperature_compliant"] is True
        assert res["environmental_telemetry"]["humidity_compliant"] is True
        assert res["gsp_compliance_verdict"]["is_fully_compliant"] is True
        assert res["gsp_compliance_verdict"]["audit_status"] == "GSP_COMPLIANT_SAFE"

    def test_audit_gsp_storage_condition_excursion_alert(self, engine: PharmaEngine) -> None:
        # Cold chain failure: 12.0°C (exceeds max 8.0°C)
        res = engine.audit_gsp_storage_condition(
            warehouse_id="WH-COLD-02",
            warehouse_name="Kho Lạnh Trạm Y Tế",
            storage_condition="COLD_CHAIN",
            recorded_temp_c=12.0,
            recorded_humidity_pct=60.0,
        )
        assert res["ok"] is True
        assert res["environmental_telemetry"]["temperature_compliant"] is False
        assert res["environmental_telemetry"]["temperature_deviation_c"] == 4.0
        assert res["gsp_compliance_verdict"]["is_fully_compliant"] is False
        assert res["gsp_compliance_verdict"]["audit_status"] == "GSP_TEMPERATURE_EXCURSION_ALERT"

    def test_track_batch_traceability_gs1_and_recall(self, engine: PharmaEngine) -> None:
        # Standard clear batch
        res_clear = engine.track_batch_traceability(
            batch_number="B2609-01",
            visa_number="VD-35124-21",
            drug_name="Hapacol 650",
            gtin_14="08935000000018",
            serial_number="SN9988776655",
            manufacturing_date="2026-01-15",
            expiry_date="2028-01-15",
            quantity_units=20000,
            recall_action="NONE",
        )
        assert res_clear["ok"] is True
        assert res_clear["batch_id"].startswith("BAT-")
        assert res_clear["gs1_healthcare_matrix"]["symbology"] == "GS1_2D_DATAMATRIX"
        assert "(01)08935000000018" in res_clear["gs1_healthcare_matrix"]["gs1_composite_string"]
        assert "(10)B2609-01" in res_clear["gs1_healthcare_matrix"]["gs1_composite_string"]
        assert "(21)SN9988776655" in res_clear["gs1_healthcare_matrix"]["gs1_composite_string"]
        assert res_clear["recall_governance"]["is_recalled"] is False

        # Recalled batch Level 1
        res_recall = engine.track_batch_traceability(
            batch_number="B2508-BAD",
            visa_number="VN-99999-20",
            drug_name="Thuốc Kém Chất Lượng",
            recall_action="LEVEL_1",
        )
        assert res_recall["recall_governance"]["is_recalled"] is True
        assert res_recall["recall_governance"]["recall_level"] == "LEVEL_1"
        assert res_recall["recall_governance"]["statutory_timeline_hours"] == 24
        assert res_recall["recall_governance"]["severity_level"] == "CRITICAL_FATAL_RISK"

    def test_declare_drug_pricing_margins(self, engine: PharmaEngine) -> None:
        # Bracket: 5,000 to 100,000 VND -> max margin 7.0%
        # Wholesale 50,000 VND, Retail 53,000 VND -> margin = (53000-50000)/50000 = 6.0% <= 7.0% (Compliant)
        res_ok = engine.declare_drug_pricing(
            visa_number="VN-22019-19",
            drug_name="Augmentin 1g",
            wholesale_price_vnd=50000.0,
            hospital_retail_price_vnd=53000.0,
            declared_by="GlaxoSmithKline",
        )
        assert res_ok["ok"] is True
        assert res_ok["declaration_id"].startswith("PRC-")
        assert res_ok["pricing_evaluation_vnd"]["actual_retail_margin_pct"] == 6.0
        assert res_ok["pricing_evaluation_vnd"]["statutory_max_margin_pct"] == 7.0
        assert res_ok["pricing_evaluation_vnd"]["is_margin_compliant"] is True
        assert res_ok["statutory_governance"]["status"] == "PRICING_APPROVED"

        # Excessive margin test: Wholesale 50,000 VND, Retail 60,000 VND -> margin = 20.0% > 7.0% (Rejected)
        res_excess = engine.declare_drug_pricing(
            visa_number="VN-22019-19",
            drug_name="Augmentin 1g",
            wholesale_price_vnd=50000.0,
            hospital_retail_price_vnd=60000.0,
        )
        assert res_excess["pricing_evaluation_vnd"]["is_margin_compliant"] is False
        assert res_excess["statutory_governance"]["status"] == "EXCEEDS_STATUTORY_RETAIL_MARGIN"

    def test_pharma_lists_and_status(self, engine: PharmaEngine) -> None:
        engine.register_drug_marketing_authorization(
            visa_number="VN-11111-20",
            drug_name="TestDrug",
            active_ingredient="API",
            strength="10mg",
            dosage_form="Tablet",
        )
        engine.audit_gsp_storage_condition(warehouse_id="WH-01", warehouse_name="Wh1")
        engine.track_batch_traceability(batch_number="B01", visa_number="VN-11111-20", drug_name="TestDrug")
        engine.declare_drug_pricing(visa_number="VN-11111-20", drug_name="TestDrug", wholesale_price_vnd=10000, hospital_retail_price_vnd=10500)

        drugs = engine.list_drug_registrations()
        assert len(drugs) == 1
        assert drugs[0]["visa_number"] == "VN-11111-20"

        logs = engine.list_gsp_logs()
        assert len(logs) == 1
        assert logs[0]["warehouse_id"] == "WH-01"

        batches = engine.list_batch_traceability()
        assert len(batches) == 1
        assert batches[0]["batch_number"] == "B01"

        prices = engine.list_price_declarations()
        assert len(prices) == 1
        assert prices[0]["visa_number"] == "VN-11111-20"

        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "PharmaEngine"
        assert status["metrics"]["drugs_registered"] == 1
        assert status["metrics"]["gsp_audits_logged"] == 1
        assert status["metrics"]["batches_tracked"] == 1
        assert status["metrics"]["price_declarations_filed"] == 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestPharmaCLI:
    """Test Typer CLI surface for mekong pharma commands."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_pharma_root_callback_console_and_json(self, app) -> None:
        # Console mode
        res = runner.invoke(app, ["pharma"])
        assert res.exit_code == 0
        assert "QUẢN TRỊ DƯỢC PHẨM QUỐC GIA" in res.output or "Vietnam National Drug Bank" in res.output

        # JSON mode
        res_json = runner.invoke(app, ["pharma", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["engine"] == "PharmaEngine"
        assert "metrics" in data

    def test_pharma_drug_cmd(self, app) -> None:
        # Console mode
        res = runner.invoke(
            app,
            [
                "pharma",
                "drug",
                "VN-22019-19",
                "Augmentin 1g",
                "Amoxicillin + Clavulanic Acid",
                "1000mg",
                "Viên nén bao phim",
                "--class",
                "RX_PRESCRIPTION",
                "--mfg",
                "Glaxo Wellcome Production",
                "--country",
                "France",
                "--tenure",
                "5",
            ],
        )
        assert res.exit_code == 0
        assert "GIẤY ĐĂNG KÝ LƯU HÀNH THUỐC QUỐC GIA" in res.output

        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "pharma",
                "drug",
                "VD-35124-21",
                "Hapacol 650",
                "Paracetamol",
                "650mg",
                "Viên nén",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["marketing_authorization"]["visa_number"] == "VD-35124-21"

    def test_pharma_gsp_cmd(self, app) -> None:
        # Console mode
        res = runner.invoke(
            app,
            [
                "pharma",
                "gsp",
                "WH-COLD-01",
                "Kho Lạnh Vắc Xin Trung Tâm",
                "--condition",
                "COLD_CHAIN",
                "--temp",
                "4.5",
                "--humidity",
                "55.0",
                "--sensor",
                "SENSOR-LOG-01",
            ],
        )
        assert res.exit_code == 0
        assert "KHO BẢO QUẢN THUỐC GSP" in res.output

        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "pharma",
                "gsp",
                "WH-ROOM-02",
                "Kho Thường",
                "--condition",
                "STANDARD_ROOM",
                "--temp",
                "22.0",
                "--humidity",
                "60.0",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["warehouse_facility"]["warehouse_id"] == "WH-ROOM-02"

    def test_pharma_batch_cmd(self, app) -> None:
        # Console mode
        res = runner.invoke(
            app,
            [
                "pharma",
                "batch",
                "B2609-01",
                "VD-35124-21",
                "Hapacol 650",
                "--gtin",
                "08935000000018",
                "--serial",
                "SN1234567890",
                "--qty",
                "50000",
            ],
        )
        assert res.exit_code == 0
        assert "TRUY XUẤT NGUỒN GỐC LÔ THUỐC" in res.output

        # JSON mode with recall
        res_json = runner.invoke(
            app,
            [
                "pharma",
                "batch",
                "B2508-BAD",
                "VN-99999-20",
                "Thuốc Thu Hồi",
                "--recall",
                "LEVEL_1",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["recall_governance"]["is_recalled"] is True
        assert data["recall_governance"]["recall_level"] == "LEVEL_1"

    def test_pharma_price_cmd(self, app) -> None:
        # Console mode
        res = runner.invoke(
            app,
            [
                "pharma",
                "price",
                "VN-22019-19",
                "Augmentin 1g",
                "50000",
                "53000",
                "--declared-by",
                "GSK",
            ],
        )
        assert res.exit_code == 0
        assert "KÊ KHAI GIÁ THUỐC & THẶNG SỐ BÁN LẺ" in res.output

        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "pharma",
                "price",
                "VD-35124-21",
                "Hapacol 650",
                "1200",
                "1300",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["pricing_evaluation_vnd"]["is_margin_compliant"] is True

    def test_pharma_list_cmd(self, app) -> None:
        res = runner.invoke(app, ["pharma", "list", "drugs"])
        assert res.exit_code == 0
        assert "Giấy phép Lưu hành Thuốc" in res.output

        res_gsp = runner.invoke(app, ["pharma", "list", "gsp", "--json"])
        assert res_gsp.exit_code == 0
        data_gsp = json.loads(res_gsp.output)
        assert data_gsp["ok"] is True
        assert "gsp_logs" in data_gsp

        res_bat = runner.invoke(app, ["pharma", "list", "batches", "--json"])
        assert res_bat.exit_code == 0
        data_bat = json.loads(res_bat.output)
        assert data_bat["ok"] is True
        assert "batches" in data_bat

        res_prc = runner.invoke(app, ["pharma", "list", "prices", "--json"])
        assert res_prc.exit_code == 0
        data_prc = json.loads(res_prc.output)
        assert data_prc["ok"] is True
        assert "prices" in data_prc

    def test_pharma_status_cmd(self, app) -> None:
        res = runner.invoke(app, ["pharma", "status"])
        assert res.exit_code == 0
        assert "CHỈ SỐ ĐIỀU HÀNH DƯỢC PHẨM" in res.output

        res_json = runner.invoke(app, ["pharma", "status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Tool & Server Parity Tests
# ---------------------------------------------------------------------------


class TestPharmaMCPIntegration:
    """Test MCP tool registration and JSON-RPC dispatch for pharma tools."""

    def test_src_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Drug
        res_drug = json.loads(server._handle_pharma_drug(
            visa_number="VN-22019-19",
            drug_name="Augmentin",
            active_ingredient="Amoxicillin",
            strength="1g",
            dosage_form="Tablet",
        ))
        assert res_drug["ok"] is True
        assert res_drug["marketing_authorization"]["visa_number"] == "VN-22019-19"

        # GSP
        res_gsp = json.loads(server._handle_pharma_gsp(
            warehouse_id="WH-COLD-MCP",
            warehouse_name="Cold Storage",
        ))
        assert res_gsp["ok"] is True
        assert res_gsp["warehouse_facility"]["warehouse_id"] == "WH-COLD-MCP"

        # Batch
        res_bat = json.loads(server._handle_pharma_batch(
            batch_number="BAT-MCP-01",
            visa_number="VN-22019-19",
            drug_name="Augmentin",
        ))
        assert res_bat["ok"] is True
        assert res_bat["batch_profile"]["batch_number"] == "BAT-MCP-01"

        # Price
        res_prc = json.loads(server._handle_pharma_price(
            visa_number="VN-22019-19",
            drug_name="Augmentin",
            wholesale_price_vnd=50000,
            hospital_retail_price_vnd=53000,
        ))
        assert res_prc["ok"] is True
        assert res_prc["pricing_evaluation_vnd"]["actual_retail_margin_pct"] == 6.0

        # List & Status
        res_list = json.loads(server._handle_pharma_list(item_type="drugs"))
        assert isinstance(res_list, list)

        res_stat = json.loads(server._handle_pharma_status())
        assert res_stat["ok"] is True
        assert "metrics" in res_stat

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as script_mcp

        # Drug
        res_drug = json.loads(script_mcp.handle_pharma_drug({
            "visa_number": "VD-99999-22",
            "drug_name": "Paracetamol DHG",
            "active_ingredient": "Paracetamol",
            "strength": "500mg",
            "dosage_form": "Tablet",
        }))
        assert res_drug["ok"] is True

        # GSP
        res_gsp = json.loads(script_mcp.handle_pharma_gsp({
            "warehouse_id": "WH-SCRIPT",
            "warehouse_name": "Script Warehouse",
        }))
        assert res_gsp["ok"] is True

        # Batch
        res_bat = json.loads(script_mcp.handle_pharma_batch({
            "batch_number": "B-SCRIPT",
            "visa_number": "VD-99999-22",
            "drug_name": "Paracetamol",
        }))
        assert res_bat["ok"] is True

        # Price
        res_prc = json.loads(script_mcp.handle_pharma_price({
            "visa_number": "VD-99999-22",
            "drug_name": "Paracetamol",
            "wholesale_price_vnd": 1000,
            "hospital_retail_price_vnd": 1100,
        }))
        assert res_prc["ok"] is True

        # List & Status
        res_list = json.loads(script_mcp.handle_pharma_list({"item_type": "gsp"}))
        assert isinstance(res_list, list)

        res_stat = json.loads(script_mcp.handle_pharma_status({}))
        assert res_stat["ok"] is True

        # Check CORE_TOOLS_SPEC and CORE_HANDLERS
        spec_names = {t["name"] for t in script_mcp.CORE_TOOLS_SPEC}
        assert "mekong_pharma_drug" in spec_names
        assert "mekong_pharma_gsp" in spec_names
        assert "mekong_pharma_batch" in spec_names
        assert "mekong_pharma_price" in spec_names
        assert "mekong_pharma_list" in spec_names
        assert "mekong_pharma_status" in spec_names

        assert "mekong_pharma_drug" in script_mcp.CORE_HANDLERS
        assert "mekong_pharma_gsp" in script_mcp.CORE_HANDLERS
        assert "mekong_pharma_batch" in script_mcp.CORE_HANDLERS
        assert "mekong_pharma_price" in script_mcp.CORE_HANDLERS
        assert "mekong_pharma_list" in script_mcp.CORE_HANDLERS
        assert "mekong_pharma_status" in script_mcp.CORE_HANDLERS
