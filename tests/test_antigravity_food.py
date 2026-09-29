# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Food Safety, Dietary Supplements & Hygiene Certification Suite (Phase 78)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.food_engine import (
    CERTIFICATE_EXEMPTIONS,
    FOOD_FACILITY_TYPES,
    FOOD_PRODUCT_CATEGORIES,
    FOOD_RECALL_CLASSES,
    HACCP_7_PRINCIPLES,
    IMPORT_INSPECTION_MODES,
    FoodEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestFoodCoreBoundary:
    """Ensure FoodEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/food_engine.py")
        assert source_path.exists(), "food_engine.py must exist"

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


class TestFoodEngine:
    """Test FoodEngine declarations, facilities, inspections, recalls, and HACCP audits."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> FoodEngine:
        db_file = tmp_path / "test_food.db"
        return FoodEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Product Categories
        assert "DIETARY_SUPPLEMENT" in FOOD_PRODUCT_CATEGORIES
        assert FOOD_PRODUCT_CATEGORIES["DIETARY_SUPPLEMENT"]["declaration_path"] == "REGISTRATION"
        assert FOOD_PRODUCT_CATEGORIES["DIETARY_SUPPLEMENT"]["gmp_required"] is True

        assert "MEDICAL_FOOD" in FOOD_PRODUCT_CATEGORIES
        assert "INFANT_NUTRITION" in FOOD_PRODUCT_CATEGORIES
        assert "PROCESSED_PACKAGED_FOOD" in FOOD_PRODUCT_CATEGORIES
        assert FOOD_PRODUCT_CATEGORIES["PROCESSED_PACKAGED_FOOD"]["declaration_path"] == "SELF_DECLARATION"
        assert "FOOD_ADDITIVE" in FOOD_PRODUCT_CATEGORIES
        assert "PACKAGING_MATERIAL" in FOOD_PRODUCT_CATEGORIES

        # Facilities
        assert "MANUFACTURING" in FOOD_FACILITY_TYPES
        assert "PROCESSING" in FOOD_FACILITY_TYPES
        assert "PACKAGING" in FOOD_FACILITY_TYPES
        assert "CATERING" in FOOD_FACILITY_TYPES
        assert "TRADING" in FOOD_FACILITY_TYPES

        # Exemptions
        assert "GMP" in CERTIFICATE_EXEMPTIONS
        assert CERTIFICATE_EXEMPTIONS["GMP"]["exemption_status"] == "EXEMPT"
        assert "HACCP" in CERTIFICATE_EXEMPTIONS
        assert "ISO_22000" in CERTIFICATE_EXEMPTIONS
        assert "FSSC_22000" in CERTIFICATE_EXEMPTIONS
        assert "NONE" in CERTIFICATE_EXEMPTIONS
        assert CERTIFICATE_EXEMPTIONS["NONE"]["exemption_status"] == "REQUIRED"

        # Import inspection modes
        assert "REDUCED" in IMPORT_INSPECTION_MODES
        assert IMPORT_INSPECTION_MODES["REDUCED"]["sampling_rate_pct"] == 5.0
        assert "NORMAL" in IMPORT_INSPECTION_MODES
        assert "TIGHTENED" in IMPORT_INSPECTION_MODES
        assert IMPORT_INSPECTION_MODES["TIGHTENED"]["sampling_mandatory"] is True

        # Recall classes
        assert "CLASS_1" in FOOD_RECALL_CLASSES
        assert FOOD_RECALL_CLASSES["CLASS_1"]["notice_deadline_hours"] == 24
        assert FOOD_RECALL_CLASSES["CLASS_1"]["recall_completion_days"] == 3
        assert "CLASS_2" in FOOD_RECALL_CLASSES
        assert "CLASS_3" in FOOD_RECALL_CLASSES

        # HACCP 7 Principles
        assert len(HACCP_7_PRINCIPLES) == 7

    def test_declare_product_self_declaration_success(self, engine: FoodEngine) -> None:
        res = engine.declare_product(
            product_name="Bánh quy Bơ Sữa Mekong",
            product_category="PROCESSED_PACKAGED_FOOD",
            enterprise_name="Công ty CP Bánh Kẹo Mekong",
            tax_id="0108899112",
            manufacturer_name="Nhà máy Bánh Kẹo Mekong",
            origin_country="Việt Nam",
            ingredients=["Bột mì", "Bơ thực vật", "Sữa đặc", "Đường"],
            shelf_life_months=12,
            lab_test_cert="TEST-LAB-2026/0111",
        )
        assert res["status"] == "PUBLISHED"
        assert res["declaration_path"] == "SELF_DECLARATION"
        assert res["declaration_number"].endswith("/TCB-MK")
        assert res["product_name"] == "Bánh quy Bơ Sữa Mekong"

    def test_declare_product_registration_success(self, engine: FoodEngine) -> None:
        res = engine.declare_product(
            product_name="Viên nang Đông trùng Hạ thảo Gold",
            product_category="DIETARY_SUPPLEMENT",
            enterprise_name="Công ty Dược phẩm Mekong",
            tax_id="0109988776",
            manufacturer_name="Nhà máy Dược phẩm GMP Mekong",
            origin_country="Việt Nam",
            ingredients=["Đông trùng hạ thảo", "Linh chi", "Vitamin B1"],
            shelf_life_months=36,
            lab_test_cert="TEST-VFA-2026/0892",
            gmp_cert_number="GMP-MOH-2026-0045",
        )
        assert res["status"] == "APPROVED"
        assert res["declaration_path"] == "REGISTRATION"
        assert res["declaration_number"].endswith("/ĐKSP")
        assert "Bộ Y tế" in res["authority"]

    def test_declare_product_missing_gmp_error(self, engine: FoodEngine) -> None:
        with pytest.raises(ValueError, match="bắt buộc phải có Giấy chứng nhận GMP"):
            engine.declare_product(
                product_name="Sữa công thức dinh dưỡng Y học",
                product_category="MEDICAL_FOOD",
                enterprise_name="Công ty Dược phẩm Mekong",
                tax_id="0109988776",
                manufacturer_name="Nhà máy Mekong",
                origin_country="Việt Nam",
                ingredients=["Protein", "Maltodextrin"],
                shelf_life_months=24,
                lab_test_cert="TEST-001",
                gmp_cert_number=None,
            )

    def test_declare_product_invalid_category_error(self, engine: FoodEngine) -> None:
        with pytest.raises(ValueError, match="Danh mục thực phẩm không hợp lệ"):
            engine.declare_product(
                product_name="SP Test",
                product_category="INVALID_CAT",
                enterprise_name="CTY A",
                tax_id="010101",
                manufacturer_name="Xưởng A",
                origin_country="VN",
                ingredients=["A"],
                shelf_life_months=12,
                lab_test_cert="TEST-1",
            )

    def test_register_facility_with_gcn(self, engine: FoodEngine) -> None:
        res = engine.register_facility(
            facility_name="Cơ sở Bánh ngọt Mekong",
            enterprise_name="Hộ kinh doanh Mekong Bakery",
            tax_id="0108877665",
            address="123 Đường 3/2, Q. Ninh Kiều",
            province="Cần Thơ",
            activity_type="PROCESSING",
            exemption_type="NONE",
            inspection_rating="GOOD",
        )
        assert res["status"] == "ACTIVE"
        assert res["is_exempt_from_gcn"] is False
        assert "ATTP-GCN" in res["cert_number"]
        assert res["expiry_date"] is not None

    def test_register_facility_with_haccp_exemption(self, engine: FoodEngine) -> None:
        res = engine.register_facility(
            facility_name="Nhà máy Chế biến Thực phẩm Đạt chuẩn HACCP",
            enterprise_name="Công ty CP Thực phẩm Mekong",
            tax_id="0108877665",
            address="KCN Trà Nóc, TP. Cần Thơ",
            province="Cần Thơ",
            activity_type="MANUFACTURING",
            exemption_type="HACCP",
            cert_number="HACCP-CERT-2026-99",
            inspection_rating="EXCELLENT",
        )
        assert res["status"] == "ACTIVE"
        assert res["is_exempt_from_gcn"] is True
        assert "Nghị định 15/2018" in res["statutory_ref"]

    def test_register_facility_invalid_inputs(self, engine: FoodEngine) -> None:
        with pytest.raises(ValueError, match="Loại hình cơ sở không hợp lệ"):
            engine.register_facility(
                facility_name="Test",
                enterprise_name="CTY",
                tax_id="01",
                address="Addr",
                province="HN",
                activity_type="UNKNOWN_ACT",
            )

        with pytest.raises(ValueError, match="Loại hình miễn trừ không hợp lệ"):
            engine.register_facility(
                facility_name="Test",
                enterprise_name="CTY",
                tax_id="01",
                address="Addr",
                province="HN",
                activity_type="MANUFACTURING",
                exemption_type="UNKNOWN_EXEMPT",
            )

    def test_inspect_imported_food_normal_pass(self, engine: FoodEngine) -> None:
        res = engine.inspect_imported_food(
            shipment_id="SHP-AUS-2026-001",
            importer_name="Công ty TNHH Nhập khẩu Mekong",
            product_name="Thịt bò đông lạnh Úc",
            origin_country="Úc",
            quantity_kg=10000.0,
            inspection_mode="NORMAL",
        )
        assert res["result_status"] == "PASS"
        assert res["clearance_status"] == "CLEARED"
        assert res["sampling_performed"] is False

    def test_inspect_imported_food_reduced_mode(self, engine: FoodEngine) -> None:
        res = engine.inspect_imported_food(
            shipment_id="SHP-NZ-2026-002",
            importer_name="Công ty Sữa Mekong",
            product_name="Bột sữa nguyên kem New Zealand",
            origin_country="New Zealand",
            quantity_kg=25000.0,
            inspection_mode="REDUCED",
        )
        assert res["result_status"] == "PASS"
        assert res["clearance_status"] == "CLEARED"

    def test_inspect_imported_food_tightened_fail(self, engine: FoodEngine) -> None:
        res = engine.inspect_imported_food(
            shipment_id="SHP-IMP-2026-999",
            importer_name="Công ty Hải sản Mekong",
            product_name="Tôm sú đông lạnh nhập khẩu",
            origin_country="Ấn Độ",
            quantity_kg=5000.0,
            inspection_mode="TIGHTENED",
            lab_test_results={"heavy_metal": "PASS", "chloramphenicol": "FAIL"},
        )
        assert res["result_status"] == "FAIL"
        assert res["clearance_status"] == "DETAINED"
        assert res["sampling_performed"] is True

    def test_initiate_recall_class_1_and_recovery(self, engine: FoodEngine) -> None:
        recall = engine.initiate_recall(
            product_name="Pate Gan Heo Đóng Hộp",
            batch_number="LOT-2026-P01",
            recall_class="CLASS_1",
            reason="Phát hiện độc tố Clostridium botulinum",
            hazard_description="Ngộ độc cấp tính, nguy cơ suy hô hấp tử vong",
            affected_quantity=2000.0,
            recovered_quantity=500.0,
            recall_scope="NATIONWIDE",
            disposal_method="DESTROY",
        )
        assert recall["status"] == "ACTIVE"
        assert recall["notice_deadline_hours"] == 24
        assert recall["recall_completion_days"] == 3
        assert recall["recovery_rate_pct"] == 25.0

        # Update recovery to completion
        update_res = engine.update_recall_recovery(recall["recall_id"], additional_recovered_qty=1500.0)
        assert update_res["status"] == "COMPLETED"
        assert update_res["recovery_rate_pct"] == 100.0
        assert update_res["is_complete"] is True

    def test_initiate_recall_class_2_and_3(self, engine: FoodEngine) -> None:
        r2 = engine.initiate_recall(
            product_name="Bánh xốp dâu",
            batch_number="LOT-B02",
            recall_class="CLASS_2",
            reason="Hàm lượng chất bảo quản vượt ngưỡng nhẹ",
            hazard_description="Rối loạn tiêu hóa tạm thời",
            affected_quantity=1000.0,
        )
        assert r2["notice_deadline_hours"] == 72
        assert r2["recall_completion_days"] == 7

        r3 = engine.initiate_recall(
            product_name="Nước khoáng đóng chai",
            batch_number="LOT-W03",
            recall_class="CLASS_3",
            reason="In sai lỗi chính tả bảng thành phần",
            hazard_description="Không ảnh hưởng trực tiếp sức khỏe",
            affected_quantity=5000.0,
        )
        assert r3["notice_deadline_hours"] == 120
        assert r3["recall_completion_days"] == 15

    def test_initiate_recall_invalid_class(self, engine: FoodEngine) -> None:
        with pytest.raises(ValueError, match="Cấp độ thu hồi không hợp lệ"):
            engine.initiate_recall(
                product_name="SP",
                batch_number="LOT-1",
                recall_class="CLASS_INVALID",
                reason="Lý do",
                hazard_description="Mô tả",
                affected_quantity=100.0,
            )

    def test_audit_haccp_system_certified(self, engine: FoodEngine) -> None:
        res = engine.audit_haccp_system(
            facility_id_or_name="Nhà máy Chế biến Thực phẩm Sạch Mekong",
            auditor_name="Trần Quốc Tuấn (HACCP Lead Auditor)",
            principles_scores={"P1_HAZARD_ANALYSIS": 100.0, "P2_DETERMINE_CCPS": 95.0},
            total_ccps=4,
            critical_non_conformities=0,
            major_non_conformities=0,
            minor_non_conformities=1,
        )
        assert res["audit_verdict"] == "CERTIFIED"
        assert res["compliance_score"] >= 85.0

    def test_audit_haccp_system_conditional_and_failed(self, engine: FoodEngine) -> None:
        # Conditional
        res_cond = engine.audit_haccp_system(
            facility_id_or_name="Xưởng Gia Công A",
            auditor_name="Auditor 1",
            principles_scores={"P1_HAZARD_ANALYSIS": 80.0, "P2_DETERMINE_CCPS": 75.0},
            total_ccps=3,
            critical_non_conformities=0,
            major_non_conformities=3,
        )
        assert res_cond["audit_verdict"] == "CONDITIONAL"

        # Failed due to critical non-conformity
        res_fail = engine.audit_haccp_system(
            facility_id_or_name="Xưởng Vi Phạm",
            auditor_name="Auditor 2",
            principles_scores={},
            total_ccps=2,
            critical_non_conformities=1,
        )
        assert res_fail["audit_verdict"] == "FAILED"

    def test_list_and_status_telemetry(self, engine: FoodEngine) -> None:
        # Seed records
        engine.declare_product(
            product_name="Trà thảo mộc Mekong",
            product_category="PROCESSED_PACKAGED_FOOD",
            enterprise_name="Công ty Mekong",
            tax_id="010101",
            manufacturer_name="Xưởng Mekong",
            origin_country="Việt Nam",
            ingredients=["Trà", "Hoa cúc"],
            shelf_life_months=24,
            lab_test_cert="TEST-002",
        )
        engine.register_facility(
            facility_name="Cơ sở Mekong Trà",
            enterprise_name="Công ty Mekong",
            tax_id="010101",
            address="Đồng Tháp",
            province="Đồng Tháp",
            activity_type="PROCESSING",
        )
        engine.inspect_imported_food(
            shipment_id="SHP-001",
            importer_name="Mekong Import",
            product_name="Nho khô",
            origin_country="Mỹ",
            quantity_kg=2000.0,
        )
        engine.initiate_recall(
            product_name="Trà thảo mộc Mekong",
            batch_number="LOT-001",
            recall_class="CLASS_3",
            reason="Lỗi nhãn",
            hazard_description="Không độc",
            affected_quantity=500.0,
        )
        engine.audit_haccp_system(
            facility_id_or_name="Cơ sở Mekong Trà",
            auditor_name="Lead Auditor",
            principles_scores={},
            total_ccps=2,
        )

        assert len(engine.list_declarations()) >= 1
        assert len(engine.list_facilities()) >= 1
        assert len(engine.list_inspections()) >= 1
        assert len(engine.list_recalls()) >= 1
        assert len(engine.list_haccp_audits()) >= 1

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["declarations"]["total"] >= 1
        assert status["facilities"]["total"] >= 1
        assert status["imported_food_inspections"]["cleared"] >= 1
        assert status["food_recalls"]["active_monitoring"] >= 1


# ---------------------------------------------------------------------------
# CLI Commands Tests
# ---------------------------------------------------------------------------


class TestFoodCli:
    """Test Typer CLI commands for mekong food."""

    def test_food_cli_main_panel(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["food"])
        assert result.exit_code == 0
        assert "HỆ THỐNG AN TOÀN THỰC PHẨM" in result.output

    def test_food_cli_main_json(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["food", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"
        assert "declarations" in data

    def test_food_cli_declare(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "declare", "Sữa Hạt Sen Mekong", "PROCESSED_PACKAGED_FOOD",
                "--enterprise", "Công ty CP Thực phẩm Sen Mekong",
                "--tax-id", "0109988111",
                "--manufacturer", "Nhà máy Sen Tháp Mười",
                "--origin", "Việt Nam",
                "--ingredients", "Hạt sen, Đậu nành, Đường phèn",
                "--shelf-life", "12",
                "--test-cert", "TEST-SEN-2026/01",
            ],
        )
        assert result.exit_code == 0
        assert "Bản Công Bố Thực Phẩm" in result.output

    def test_food_cli_declare_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "declare", "Viên Uống Nghệ Curcumin", "DIETARY_SUPPLEMENT",
                "--enterprise", "Công ty Dược Mekong",
                "--tax-id", "0109988111",
                "--manufacturer", "Nhà máy GMP",
                "--gmp-cert", "GMP-2026-99",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["declaration_path"] == "REGISTRATION"

    def test_food_cli_facility(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "facility", "Bếp Ăn Công Nghiệp Mekong", "Công ty Mekong Catering", "0109988222",
                "--activity", "CATERING",
                "--province", "TP. Hồ Chí Minh",
                "--rating", "GOOD",
            ],
        )
        assert result.exit_code == 0
        assert "Chứng Nhận An Toàn Thực Phẩm" in result.output

    def test_food_cli_facility_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "facility", "Nhà máy ISO Mekong", "Công ty Mekong Foods", "0109988333",
                "--activity", "MANUFACTURING",
                "--exemption", "ISO_22000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_exempt_from_gcn"] is True

    def test_food_cli_inspect(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "inspect", "SHP-JP-2026-777", "Bột Trà Xanh Matcha Nhật Bản",
                "--importer", "Công ty TNHH Nhập khẩu Mekong",
                "--origin", "Nhật Bản",
                "--qty", "1500",
                "--mode", "REDUCED",
            ],
        )
        assert result.exit_code == 0
        assert "Kiểm Tra ATTP Hàng Nhập Khẩu" in result.output

    def test_food_cli_inspect_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "inspect", "SHP-NZ-2026-888", "Bơ Sữa New Zealand",
                "--origin", "New Zealand",
                "--qty", "20000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["clearance_status"] == "CLEARED"

    def test_food_cli_recall(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "recall", "Pate Cột Đèn", "LOT-RECALL-01",
                "--class", "CLASS_1",
                "--reason", "Nhiễm khuẩn Clostridium botulinum",
                "--affected", "1500",
            ],
        )
        assert result.exit_code == 0
        assert "Lệnh Thu Hồi Thực Phẩm Khẩn Cấp" in result.output

    def test_food_cli_recall_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "recall", "Nước ép cam", "LOT-ORANGE-02",
                "--class", "CLASS_3",
                "--reason", "Lỗi in hạn dùng",
                "--affected", "500",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["notice_deadline_hours"] == 120

    def test_food_cli_haccp(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "haccp", "Nhà máy Thực phẩm Sạch Mekong",
                "--auditor", "Trần Quốc Tuấn",
                "--ccps", "4",
                "--critical-nc", "0",
            ],
        )
        assert result.exit_code == 0
        assert "Đánh Giá Thẩm Định Hệ Thống HACCP" in result.output

    def test_food_cli_haccp_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            [
                "food", "haccp", "Nhà máy Thực phẩm Sạch Mekong",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["audit_verdict"] == "CERTIFIED"

    def test_food_cli_list(self) -> None:
        app = build_app()
        for l_type in ["declarations", "facilities", "inspections", "recalls", "haccp"]:
            result = runner.invoke(app, ["food", "list", "--type", l_type])
            assert result.exit_code == 0
            assert "Danh Sách Dữ Liệu An Toàn Thực Phẩm" in result.output

    def test_food_cli_status(self) -> None:
        app = build_app()
        result = runner.invoke(app, ["food", "status"])
        assert result.exit_code == 0
        assert "TRẠNG THÁI TỔNG THỂ" in result.output

        res_json = runner.invoke(app, ["food", "status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "HEALTHY"


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestFoodMcpServer:
    """Test pure-Python and FastMCP server tools parity for food safety."""

    def test_pure_rpc_handlers(self) -> None:
        import scripts.mcp_server as rpc_server

        # 1. handle_food_declare
        res1 = rpc_server.handle_food_declare({
            "product_name": "Trà Atiso Đà Lạt",
            "product_category": "PROCESSED_PACKAGED_FOOD",
            "enterprise_name": "Công ty Atiso Mekong",
            "tax_id": "0109988444",
            "manufacturer_name": "Nhà máy Atiso",
            "origin_country": "Việt Nam",
            "ingredients": ["Hoa Atiso"],
            "shelf_life_months": 24,
            "lab_test_cert": "TEST-ATISO-01",
        })
        d1 = json.loads(res1)
        assert d1["status"] == "PUBLISHED"

        # 2. handle_food_facility
        res2 = rpc_server.handle_food_facility({
            "facility_name": "Cơ sở Đóng gói Atiso",
            "enterprise_name": "Công ty Atiso Mekong",
            "tax_id": "0109988444",
            "activity_type": "PACKAGING",
            "exemption_type": "GMP",
        })
        d2 = json.loads(res2)
        assert d2["is_exempt_from_gcn"] is True

        # 3. handle_food_inspect
        res3 = rpc_server.handle_food_inspect({
            "shipment_id": "SHP-MCP-001",
            "product_name": "Táo Envy Mỹ",
            "origin_country": "Mỹ",
            "quantity_kg": 8000.0,
            "inspection_mode": "NORMAL",
        })
        d3 = json.loads(res3)
        assert d3["clearance_status"] == "CLEARED"

        # 4. handle_food_recall
        res4 = rpc_server.handle_food_recall({
            "product_name": "Mứt Dâu Tây",
            "batch_number": "LOT-MCP-02",
            "recall_class": "CLASS_2",
            "reason": "Phụ gia quá liều",
            "hazard_description": "Kích ứng nhẹ",
            "affected_quantity": 500.0,
        })
        d4 = json.loads(res4)
        assert d4["notice_deadline_hours"] == 72

        # 5. handle_food_haccp
        res5 = rpc_server.handle_food_haccp({
            "facility_id_or_name": "Cơ sở Đóng gói Atiso",
            "auditor_name": "Trần Quốc Tuấn",
            "total_ccps": 3,
        })
        d5 = json.loads(res5)
        assert d5["audit_verdict"] == "CERTIFIED"

        # 6. handle_food_list
        res6 = rpc_server.handle_food_list({"resource": "declarations", "limit": 10})
        d6 = json.loads(res6)
        assert isinstance(d6, list)

        # 7. handle_food_status
        res7 = rpc_server.handle_food_status({})
        d7 = json.loads(res7)
        assert d7["status"] == "HEALTHY"

    def test_fastmcp_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. _handle_food_declare
        res1 = server._handle_food_declare(
            product_name="Trà Xanh Oolong",
            product_category="PROCESSED_PACKAGED_FOOD",
            enterprise_name="Công ty Chè Mekong",
            tax_id="0109988555",
            manufacturer_name="Nhà máy Chè",
            origin_country="Việt Nam",
            ingredients=["Búp chè"],
            shelf_life_months=24,
            lab_test_cert="TEST-CHE-01",
        )
        d1 = json.loads(res1)
        assert d1["status"] == "PUBLISHED"

        # 2. _handle_food_facility
        res2 = server._handle_food_facility(
            facility_name="Xưởng Chế Biến Chè",
            enterprise_name="Công ty Chè Mekong",
            tax_id="0109988555",
            activity_type="PROCESSING",
            exemption_type="HACCP",
        )
        d2 = json.loads(res2)
        assert d2["is_exempt_from_gcn"] is True

        # 3. _handle_food_inspect
        res3 = server._handle_food_inspect(
            shipment_id="SHP-FASTMCP-001",
            product_name="Dầu ô liu Hy Lạp",
            origin_country="Hy Lạp",
            quantity_kg=3000.0,
        )
        d3 = json.loads(res3)
        assert d3["clearance_status"] == "CLEARED"

        # 4. _handle_food_recall
        res4 = server._handle_food_recall(
            product_name="Dầu ô liu",
            batch_number="LOT-OLIVE-01",
            recall_class="CLASS_3",
            reason="Nhãn mờ",
            hazard_description="Không nguy hiểm",
            affected_quantity=100.0,
        )
        d4 = json.loads(res4)
        assert d4["recall_completion_days"] == 15

        # 5. _handle_food_haccp
        res5 = server._handle_food_haccp(
            facility_id_or_name="Xưởng Chế Biến Chè",
            auditor_name="Trần Quốc Tuấn",
            total_ccps=2,
        )
        d5 = json.loads(res5)
        assert d5["audit_verdict"] == "CERTIFIED"

        # 6. _handle_food_list
        res6 = server._handle_food_list(resource="facilities", limit=10)
        d6 = json.loads(res6)
        assert isinstance(d6, list)

        # 7. _handle_food_status
        res7 = server._handle_food_status()
        d7 = json.loads(res7)
        assert d7["status"] == "HEALTHY"

    def test_mcp_core_handlers_and_spec_parity(self) -> None:
        import scripts.mcp_server as rpc_server

        expected_tools = [
            "mekong_food_declare",
            "mekong_food_facility",
            "mekong_food_inspect",
            "mekong_food_recall",
            "mekong_food_haccp",
            "mekong_food_list",
            "mekong_food_status",
        ]

        spec_tool_names = {t["name"] for t in rpc_server.CORE_TOOLS_SPEC}
        for tool in expected_tools:
            assert tool in spec_tool_names, f"Tool {tool} missing in CORE_TOOLS_SPEC"
            assert tool in rpc_server.CORE_HANDLERS, f"Tool {tool} missing in CORE_HANDLERS"
            short_name = tool.removeprefix("mekong_")
            assert short_name in rpc_server.CORE_HANDLERS, f"Short alias {short_name} missing in CORE_HANDLERS"
