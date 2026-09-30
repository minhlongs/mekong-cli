"""
Test Suite for Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Suite (Phase 93).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- ChemicalEngine domain logic (Luật Hóa chất, Nghị định 113/2017, Nghị định 82/2022, Nghị định 34/2024, Nghị định 71/2019).
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
from src.core.chemical_engine import ChemicalEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestChemicalBoundary:
    """Verifies that chemical_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "chemical_engine.py")
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


class TestChemicalEngine:
    """Tests core domain and regulatory business logic of ChemicalEngine."""

    def test_classify_chemical_cas_sulfuric(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.classify_chemical("7664-93-9")
        assert res["cas_number"] == "7664-93-9"
        assert res["chemical_name"] == "Axit sulfuric"
        assert res["category"] == "CONDITIONAL"
        assert res["un_number"] == "UN 1830"
        assert res["requires_incident_plan"] is True
        assert res["requires_nsw_declaration"] is True

    def test_classify_chemical_name_nitric(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.classify_chemical("Axit nitric")
        assert res["cas_number"] == "7697-37-2"
        assert res["category"] == "RESTRICTED"
        assert res["requires_incident_plan"] is True

    def test_classify_chemical_formula_ammonium_nitrate(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.classify_chemical("nh4no3")
        assert res["cas_number"] == "6484-52-2"
        assert res["category"] == "EXPLOSIVE_PRECURSOR"
        assert "UN 1942" in res["un_number"]

    def test_classify_chemical_unknown_generic(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.classify_chemical("Compound-XYZ-999")
        assert res["cas_number"] == "UNKNOWN"
        assert res["category"] == "GENERAL_INDUSTRIAL"
        assert res["requires_incident_plan"] is False

    def test_audit_chemical_storage_compliant(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.audit_chemical_storage(
            facility_name="Kho Hóa chất Mekong Đình Vũ",
            chemical_name="Axit sulfuric",
            volume_liters=60000.0,
            bund_capacity_pct=115.0,  # >= 110%
            shower_distance_m=8.0,    # <= 10m
            has_explosion_proof_ventilation=True,
            has_grounding_system=True,
        )
        assert res["is_compliant"] is True
        assert len(res["deficiencies"]) == 0
        assert res["potential_penalty_vnd"] == 0

    def test_audit_chemical_storage_low_bund_penalty(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        # Bund capacity only 90% (< 110%)
        res = engine.audit_chemical_storage(
            facility_name="Kho Hóa chất Thường Tín",
            chemical_name="Axit sulfuric",
            volume_liters=40000.0,
            bund_capacity_pct=90.0,
            shower_distance_m=7.0,
            has_explosion_proof_ventilation=True,
            has_grounding_system=True,
        )
        assert res["is_compliant"] is False
        assert any("đê bao chống tràn" in d for d in res["deficiencies"])
        assert res["potential_penalty_vnd"] >= 40_000_000

    def test_audit_chemical_storage_far_shower_penalty(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        # Shower distance 15m (> 10m)
        res = engine.audit_chemical_storage(
            facility_name="Kho Xăng dầu Dung Quất",
            chemical_name="Axeton",
            volume_liters=20000.0,
            bund_capacity_pct=120.0,
            shower_distance_m=15.0,
            has_explosion_proof_ventilation=True,
            has_grounding_system=True,
        )
        assert res["is_compliant"] is False
        assert any("tắm khẩn cấp" in d for d in res["deficiencies"])
        assert res["potential_penalty_vnd"] >= 15_000_000

    def test_audit_chemical_storage_no_vent_or_ground(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.audit_chemical_storage(
            facility_name="Kho Tạp chất Không đạt chuẩn",
            chemical_name="Axeton",
            volume_liters=10000.0,
            bund_capacity_pct=80.0,
            shower_distance_m=18.0,
            has_explosion_proof_ventilation=False,
            has_grounding_system=False,
        )
        assert res["is_compliant"] is False
        assert len(res["deficiencies"]) == 4
        assert res["potential_penalty_vnd"] == 40_000_000 + 15_000_000 + 25_000_000 + 20_000_000

    def test_declare_chemical_import_automatic(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.declare_chemical_import(
            importer_name="Công ty Hóa chất Mekong",
            cas_number="7664-93-9",
            quantity_kg=12000.0,
            country_of_origin="Japan",
            border_gate="Cảng Hải Phòng",
        )
        assert res["status"] == "APPROVED_AUTOMATIC"
        assert res["nsw_reference_no"].startswith("NSW-BCT-")
        assert res["duty_free_declaration"] is True
        assert res["quantity_kg"] == 12000.0

    def test_audit_dangerous_goods_transport_approved(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.audit_dangerous_goods_transport(
            carrier_name="Công ty Vận tải Mekong Logistics",
            un_number="UN 1830",
            hazard_class_key="8",
            gross_weight_kg=15000.0,
            has_dangerous_goods_license=True,
            has_fire_extinguishers=True,
            driver_hazmat_certified=True,
        )
        assert res["is_approved"] is True
        assert len(res["violations"]) == 0
        assert res["potential_penalty_vnd"] == 0
        assert "Class 8" in res["hazard_class"]

    def test_audit_dangerous_goods_transport_unlicensed_violations(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.audit_dangerous_goods_transport(
            carrier_name="Xe chui không phép",
            un_number="UN 1203",
            hazard_class_key="3",
            gross_weight_kg=8000.0,
            has_dangerous_goods_license=False,  # Violation!
            has_fire_extinguishers=False,      # Violation!
            driver_hazmat_certified=True,
        )
        assert res["is_approved"] is False
        assert any("Giấy phép vận chuyển" in v for v in res["violations"])
        assert any("bình chữa cháy" in v for v in res["violations"])
        assert res["potential_penalty_vnd"] >= 40_000_000

    def test_audit_dangerous_goods_transport_uncertified_driver(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        res = engine.audit_dangerous_goods_transport(
            carrier_name="Đội xe Hợp tác xã",
            un_number="UN 1942",
            hazard_class_key="5",
            gross_weight_kg=5000.0,
            has_dangerous_goods_license=True,
            has_fire_extinguishers=True,
            driver_hazmat_certified=False,  # Violation!
        )
        assert res["is_approved"] is False
        assert any("Chứng chỉ huấn luyện" in v for v in res["violations"])
        assert res["potential_penalty_vnd"] >= 15_000_000

    def test_list_records_and_status(self, temp_db):
        engine = ChemicalEngine(db_path=temp_db)
        engine.classify_chemical("7664-93-9")
        engine.audit_chemical_storage("Kho Test", "Axit sulfuric", 50000.0, 115.0, 8.0)
        engine.declare_chemical_import("DN Test", "7664-93-9", 3000.0)
        engine.audit_dangerous_goods_transport("Xe Test", "UN 1830", "8", 10000.0, True, True, True)

        all_records = engine.list_records(category="all")
        assert len(all_records) == 4

        cls_records = engine.list_records(category="classifications")
        assert len(cls_records) == 1

        aud_records = engine.list_records(category="audits")
        assert len(aud_records) == 1

        dec_records = engine.list_records(category="declarations")
        assert len(dec_records) == 1

        trn_records = engine.list_records(category="transports")
        assert len(trn_records) == 1

        status = engine.get_status()
        assert status["total_classifications"] == 1
        assert status["total_storage_audits"] == 1
        assert status["total_import_declarations"] == 1
        assert status["total_transport_audits"] == 1
        assert status["total_imported_quantity_kg"] == 3000.0
        assert status["storage_compliance_rate_pct"] == 100.0


class TestChemicalCLI:
    """Verifies chemical Typer CLI commands in normal and JSON mode."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        self.app = build_app()
        self.runner = CliRunner()

    def test_cli_main_and_status(self):
        res = self.runner.invoke(self.app, ["chemical", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "regulatory_framework" in data
        assert "statutory_catalog_count" in data

    def test_cli_classify_cmd(self):
        res = self.runner.invoke(self.app, ["chemical", "classify", "7664-93-9", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["cas_number"] == "7664-93-9"
        assert data["chemical_name"] == "Axit sulfuric"

    def test_cli_storage_cmd(self):
        res = self.runner.invoke(
            self.app,
            [
                "chemical",
                "storage",
                "Kho Hóa chất Mekong",
                "--chemical",
                "Axit sulfuric",
                "--volume",
                "50000",
                "--bund",
                "115.0",
                "--shower",
                "8.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["facility_name"] == "Kho Hóa chất Mekong"
        assert data["is_compliant"] is True

    def test_cli_declare_cmd(self):
        res = self.runner.invoke(
            self.app,
            [
                "chemical",
                "declare",
                "Công ty Nhập khẩu Mekong",
                "--cas",
                "7664-93-9",
                "--qty",
                "8000",
                "--origin",
                "Japan",
                "--gate",
                "Cảng Hải Phòng",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["importer_name"] == "Công ty Nhập khẩu Mekong"
        assert data["status"] == "APPROVED_AUTOMATIC"

    def test_cli_transport_cmd(self):
        res = self.runner.invoke(
            self.app,
            [
                "chemical",
                "transport",
                "Đoàn xe Bồn Mekong Logistics",
                "--un",
                "UN 1830",
                "--class",
                "8",
                "--weight",
                "12000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["carrier_name"] == "Đoàn xe Bồn Mekong Logistics"
        assert data["is_approved"] is True

    def test_cli_list_cmd(self):
        res = self.runner.invoke(self.app, ["chemical", "list", "all", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestChemicalMCP:
    """Verifies dual MCP servers handle chemical tools properly."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-chemical-core")

        # 1. Classify
        res_cls = json.loads(server._handle_chemical_classify(query="7664-93-9"))
        assert res_cls["cas_number"] == "7664-93-9"

        # 2. Storage
        res_str = json.loads(
            server._handle_chemical_storage(
                facility_name="Kho Core Test",
                chemical_name="Axit sulfuric",
                volume_liters=40000.0,
                bund_capacity_pct=115.0,
                shower_distance_m=7.0,
            )
        )
        assert res_str["is_compliant"] is True

        # 3. Declare
        res_dec = json.loads(
            server._handle_chemical_declare(
                importer_name="DN Core Test",
                cas_number="7664-93-9",
                quantity_kg=5000.0,
            )
        )
        assert res_dec["status"] == "APPROVED_AUTOMATIC"

        # 4. Transport
        res_trn = json.loads(
            server._handle_chemical_transport(
                carrier_name="Xe Core Test",
                un_number="UN 1830",
                hazard_class_key="8",
                gross_weight_kg=10000.0,
            )
        )
        assert res_trn["is_approved"] is True

        # 5. List
        res_lst = json.loads(server._handle_chemical_list(category="all", limit=10))
        assert isinstance(res_lst, list)

        # 6. Status
        res_stat = json.loads(server._handle_chemical_status())
        assert res_stat["status"] == "operational"

    def test_scripts_mcp_server_handlers(self):
        import scripts.mcp_server as s_mcp

        # 1. Classify
        res_cls = json.loads(s_mcp.handle_chemical_classify({"query": "7697-37-2"}))
        assert res_cls["cas_number"] == "7697-37-2"

        # 2. Storage
        res_str = json.loads(
            s_mcp.handle_chemical_storage({
                "facility_name": "Kho Scripts Test",
                "chemical_name": "Axit nitric",
                "volume_liters": 25000.0,
                "bund_capacity_pct": 120.0,
                "shower_distance_m": 6.0,
            })
        )
        assert res_str["is_compliant"] is True

        # 3. Declare
        res_dec = json.loads(
            s_mcp.handle_chemical_declare({
                "importer_name": "DN Scripts Test",
                "cas_number": "7697-37-2",
                "quantity_kg": 4000.0,
            })
        )
        assert res_dec["status"] == "APPROVED_AUTOMATIC"

        # 4. Transport
        res_trn = json.loads(
            s_mcp.handle_dangerous_goods_transport({
                "carrier_name": "Xe Scripts Test",
                "un_number": "UN 2031",
                "hazard_class_key": "8",
                "gross_weight_kg": 9000.0,
            }) if hasattr(s_mcp, "handle_dangerous_goods_transport") else s_mcp.handle_chemical_transport({
                "carrier_name": "Xe Scripts Test",
                "un_number": "UN 2031",
                "hazard_class_key": "8",
                "gross_weight_kg": 9000.0,
            })
        )
        assert res_trn["is_approved"] is True

        # 5. List
        res_lst = json.loads(s_mcp.handle_chemical_list({"category": "all", "limit": 10}))
        assert isinstance(res_lst, list)

        # 6. Status
        res_stat = json.loads(s_mcp.handle_chemical_status({}))
        assert res_stat["status"] == "operational"
