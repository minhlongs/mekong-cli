# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Postal, Express Delivery & Courier Logistics Suite (Phase 75)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.postal_engine import (
    POSTAL_SCOPE_CONFIGS,
    POSTAL_SERVICE_TYPES,
    PROHIBITED_POSTAL_ITEMS,
    PostalEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestPostalCoreBoundary:
    """Ensure PostalEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/postal_engine.py")
        assert source_path.exists(), "postal_engine.py must exist"

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


class TestPostalEngine:
    """Test PostalEngine licensing, waybills, volumetric weight, SLA audits, security screening, and indemnity."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> PostalEngine:
        db_file = tmp_path / "test_postal.db"
        return PostalEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Postal Scope Configs under Postal Law 2010
        assert "INTRA_PROVINCE" in POSTAL_SCOPE_CONFIGS
        assert POSTAL_SCOPE_CONFIGS["INTRA_PROVINCE"]["min_capital_vnd"] == 2_000_000_000.0
        assert "INTER_PROVINCE" in POSTAL_SCOPE_CONFIGS
        assert POSTAL_SCOPE_CONFIGS["INTER_PROVINCE"]["min_capital_vnd"] == 2_000_000_000.0
        assert "INTERNATIONAL" in POSTAL_SCOPE_CONFIGS
        assert POSTAL_SCOPE_CONFIGS["INTERNATIONAL"]["min_capital_vnd"] == 5_000_000_000.0

        # Postal Services
        assert "DOCUMENT_LETTER" in POSTAL_SERVICE_TYPES
        assert POSTAL_SERVICE_TYPES["DOCUMENT_LETTER"]["base_postage_vnd"] == 15000.0
        assert "EXPRESS_PARCEL" in POSTAL_SERVICE_TYPES
        assert POSTAL_SERVICE_TYPES["EXPRESS_PARCEL"]["base_postage_vnd"] == 35000.0
        assert "BULK_FREIGHT" in POSTAL_SERVICE_TYPES
        assert "TEMPERATURE_CONTROLLED" in POSTAL_SERVICE_TYPES

        # Prohibited Contraband
        assert "EXPLOSIVES_FIREARMS" in PROHIBITED_POSTAL_ITEMS
        assert "NARCOTICS_DRUGS" in PROHIBITED_POSTAL_ITEMS
        assert "HAZARDOUS_CHEMICALS" in PROHIBITED_POSTAL_ITEMS

    def test_issue_postal_license_success(self, engine: PostalEngine) -> None:
        res = engine.issue_postal_license(
            enterprise_name="Công ty Chuyển phát nhanh Mekong Express",
            tax_id="0109887766",
            scope="INTER_PROVINCE",
            capital_vnd=3_000_000_000.0,
        )
        assert res["status"] == "success"
        prof = res["license_profile"]
        assert prof["enterprise_name"] == "Công ty Chuyển phát nhanh Mekong Express"
        assert prof["scope"] == "INTER_PROVINCE"
        assert prof["status"] == "ACTIVE"
        assert prof["license_number"].startswith("GPBC-INTE-")

    def test_issue_postal_license_insufficient_capital(self, engine: PostalEngine) -> None:
        with pytest.raises(ValueError, match="Vốn điều lệ không đủ điều kiện"):
            # International requires 5 billion, given 1 billion
            engine.issue_postal_license(
                enterprise_name="Công ty Bưu chính Quốc tế Non Trẻ",
                tax_id="0109999999",
                scope="INTERNATIONAL",
                capital_vnd=1_000_000_000.0,
            )

    def test_issue_postal_license_invalid_scope(self, engine: PostalEngine) -> None:
        with pytest.raises(ValueError, match="Phạm vi bưu chính không hợp lệ"):
            engine.issue_postal_license(
                enterprise_name="Công ty ABC",
                tax_id="0109999999",
                scope="GLOBAL_GALAXY",
            )

    def test_create_waybill_success(self, engine: PostalEngine) -> None:
        # Actual weight = 1.0 kg, Dimensions = 30x20x15 cm -> Volumetric = 30*20*15/5000 = 1.8 kg
        # Chargeable weight = 1.8 kg
        # Service EXPRESS_PARCEL: base 1.0kg = 35,000 VND, extra 1.8 - 1.0 = 0.8 kg -> ceil(0.8) * 12,000 = 12,000 VND -> Postage = 47,000 VND
        # Declared value = 2,000,000 VND -> 1% = 20,000 VND
        # COD amount = 500,000 VND -> 1.2% = 6,000 VND -> min 10,000 VND
        # Total = 47,000 + 20,000 + 10,000 = 77,000 VND
        res = engine.create_waybill(
            sender_name="Nguyễn Văn Bình",
            sender_address="Quận Cầu Giấy, Hà Nội",
            origin_postcode="10000",
            receiver_name="Trần Thị Mai",
            receiver_address="Quận 1, TP. Hồ Chí Minh",
            dest_postcode="70000",
            service_type="EXPRESS_PARCEL",
            actual_weight_kg=1.0,
            length_cm=30.0,
            width_cm=20.0,
            height_cm=15.0,
            declared_value_vnd=2_000_000.0,
            cod_amount_vnd=500_000.0,
        )
        assert res["status"] == "success"
        prof = res["consignment_profile"]
        assert prof["volumetric_weight_kg"] == 1.8
        assert prof["chargeable_weight_kg"] == 1.8
        assert prof["postage_fee_vnd"] == 47000.0
        assert prof["insurance_fee_vnd"] == 20000.0
        assert prof["cod_fee_vnd"] == 10000.0
        assert prof["total_fee_vnd"] == 77000.0
        assert prof["status"] == "IN_TRANSIT"

    def test_create_waybill_exceed_weight_limit(self, engine: PostalEngine) -> None:
        with pytest.raises(ValueError, match="vượt quá giới hạn tối đa"):
            # DOCUMENT_LETTER max weight is 2.0 kg, given 5.0 kg
            engine.create_waybill(
                sender_name="Sender",
                sender_address="Addr 1",
                origin_postcode="10000",
                receiver_name="Receiver",
                receiver_address="Addr 2",
                dest_postcode="70000",
                service_type="DOCUMENT_LETTER",
                actual_weight_kg=5.0,
            )

    def test_create_waybill_invalid_service(self, engine: PostalEngine) -> None:
        with pytest.raises(ValueError, match="Loại dịch vụ bưu chính không hợp lệ"):
            engine.create_waybill(
                sender_name="Sender",
                sender_address="Addr 1",
                origin_postcode="10000",
                receiver_name="Receiver",
                receiver_address="Addr 2",
                dest_postcode="70000",
                service_type="DRONE_HYPERLOOP",
            )

    def test_audit_delivery_sla_compliant_and_delayed(self, engine: PostalEngine) -> None:
        # Hanoi (10000) to HCM (70000): Inter-region air corridor, target SLA = D+2
        # Compliant: 1.5 days
        res_comp = engine.audit_delivery_sla(
            waybill_id="VNPOST-TEST01",
            origin_postcode="10000",
            dest_postcode="70000",
            actual_transit_days=1.5,
        )
        assert res_comp["status"] == "success"
        assert res_comp["sla_profile"]["route_type"] == "INTER_REGION_AIR"
        assert res_comp["sla_profile"]["target_sla_days"] == 2
        assert res_comp["sla_profile"]["is_sla_met"] is True
        assert res_comp["sla_profile"]["delay_days"] == 0.0

        # Delayed: 3.5 days -> delay 1.5 days
        res_del = engine.audit_delivery_sla(
            waybill_id="VNPOST-TEST02",
            origin_postcode="10000",
            dest_postcode="70000",
            actual_transit_days=3.5,
        )
        assert res_del["status"] == "success"
        assert res_del["sla_profile"]["is_sla_met"] is False
        assert res_del["sla_profile"]["delay_days"] == 1.5

    def test_screen_postal_security_passed_and_intercepted(self, engine: PostalEngine) -> None:
        # Clean parcel
        res_clean = engine.screen_postal_security(
            waybill_id="VNPOST-CLEAN01",
            scanner_station="TRAM-SOI-NOI-BAI",
            detected_item_code=None,
        )
        assert res_clean["status"] == "success"
        assert res_clean["security_profile"]["is_passed"] is True
        assert "THÔNG QUAN" in res_clean["security_profile"]["action_taken"]

        # Intercepted contraband
        res_contra = engine.screen_postal_security(
            waybill_id="VNPOST-CONTRA01",
            scanner_station="TRAM-SOI-NOI-BAI",
            detected_item_code="EXPLOSIVES_FIREARMS",
        )
        assert res_contra["status"] == "success"
        assert res_contra["security_profile"]["is_passed"] is False
        assert "ĐÌNH CHỈ" in res_contra["security_profile"]["action_taken"]
        assert "Vũ khí" in res_contra["security_profile"]["detected_item"]

    def test_calculate_indemnity_all_incidents(self, engine: PostalEngine) -> None:
        # 1. Total loss of insured parcel
        res_ins = engine.calculate_indemnity(
            waybill_id="VNPOST-INS01",
            incident_type="LOST_TOTAL",
            postage_fee_vnd=50000.0,
            declared_value_vnd=3000000.0,
        )
        assert res_ins["status"] == "success"
        prof_ins = res_ins["indemnity_profile"]
        assert prof_ins["postage_refund_vnd"] == 50000.0
        assert prof_ins["compensation_vnd"] == 3000000.0
        assert prof_ins["total_indemnity_vnd"] == 3050000.0

        # 2. Total loss of uninsured parcel (1.0kg, 50,000 VND postage -> 4x postage = 200,000 VND vs 100k/kg = 100k -> 200,000 VND)
        res_unins = engine.calculate_indemnity(
            waybill_id="VNPOST-UNINS01",
            incident_type="LOST_TOTAL",
            postage_fee_vnd=50000.0,
            declared_value_vnd=0.0,
            actual_weight_kg=1.0,
        )
        assert res_unins["status"] == "success"
        prof_unins = res_unins["indemnity_profile"]
        assert prof_unins["compensation_vnd"] == 200000.0
        assert prof_unins["total_indemnity_vnd"] == 250000.0

        # 3. Delayed beyond SLA
        res_del = engine.calculate_indemnity(
            waybill_id="VNPOST-DELAY01",
            incident_type="DELAYED_OVERDUE",
            postage_fee_vnd=50000.0,
        )
        assert res_del["status"] == "success"
        assert res_del["indemnity_profile"]["postage_refund_vnd"] == 50000.0
        assert res_del["indemnity_profile"]["compensation_vnd"] == 0.0

        # 4. Invalid incident
        with pytest.raises(ValueError, match="Sự cố bưu phẩm không hợp lệ"):
            engine.calculate_indemnity(
                waybill_id="VNPOST-ERR",
                incident_type="ALIEN_ABDUCTION",
                postage_fee_vnd=50000.0,
            )

    def test_listing_methods_and_status(self, engine: PostalEngine) -> None:
        # Populate
        engine.issue_postal_license("Doanh Nghiệp A", "0101111111", "INTRA_PROVINCE", 2000000000.0)
        engine.create_waybill("Sender", "Addr1", "10000", "Receiver", "Addr2", "70000")
        engine.audit_delivery_sla("WB-01", "10000", "70000", 1.8)
        engine.screen_postal_security("WB-01")
        engine.calculate_indemnity("WB-01", "DELAYED_OVERDUE", 35000.0)

        # Listing
        assert len(engine.list_licenses()) == 1
        assert len(engine.list_waybills()) == 1
        assert len(engine.list_sla_audits()) == 1
        assert len(engine.list_security_screenings()) == 1
        assert len(engine.list_indemnities()) == 1

        # Status
        status = engine.get_status()
        assert status["status"] == "online"
        m = status["metrics"]
        assert m["active_postal_licenses"] == 1
        assert m["total_waybills_created"] == 1
        assert m["total_postage_revenue_vnd"] > 0
        assert m["total_sla_audits"] == 1
        assert m["sla_compliance_rate_pct"] == 100.0
        assert m["total_security_screenings"] == 1
        assert m["contraband_intercepted"] == 0
        assert m["total_indemnity_claims"] == 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestPostalCLI:
    """Test Typer CLI commands for postal suite."""

    @pytest.fixture
    def app(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        return build_app()

    def test_postal_help(self, app) -> None:
        result = runner.invoke(app, ["postal", "--help"])
        assert result.exit_code == 0
        assert "Vietnamese Postal" in result.output

    def test_postal_main_console_and_json(self, app) -> None:
        res_con = runner.invoke(app, ["postal"])
        assert res_con.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ BƯU CHÍNH & CHUYỂN PHÁT NHANH" in res_con.output

        res_json = runner.invoke(app, ["postal", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "online"
        assert "metrics" in data

    def test_postal_license_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "postal",
                "license",
                "VNPost Express EMS",
                "0101889977",
                "--scope",
                "INTER_PROVINCE",
                "--capital",
                "5000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["license_profile"]["enterprise_name"] == "VNPost Express EMS"

        # Console mode
        res_con = runner.invoke(
            app,
            ["postal", "license", "Viettel Post", "0102334455", "--scope", "INTER_PROVINCE"],
        )
        assert res_con.exit_code == 0
        assert "Viettel Post" in res_con.output

    def test_postal_waybill_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "postal",
                "waybill",
                "Nguyễn Văn Hùng",
                "Hoàn Kiếm, Hà Nội",
                "10000",
                "Lê Thị Lan",
                "Quận 1, TP.HCM",
                "70000",
                "--service",
                "EXPRESS_PARCEL",
                "--weight",
                "1.5",
                "--length",
                "30",
                "--width",
                "20",
                "--height",
                "15",
                "--declared",
                "2000000",
                "--cod",
                "500000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["consignment_profile"]["total_fee_vnd"] > 0

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "postal",
                "waybill",
                "Nguyễn Văn A",
                "Hà Nội",
                "10000",
                "Trần Văn B",
                "Đà Nẵng",
                "55000",
            ],
        )
        assert res_con.exit_code == 0
        assert "Vận Đơn Bưu Gửi Chuyển Phát Nhanh" in res_con.output

    def test_postal_sla_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "postal",
                "sla",
                "VNPOST-123456",
                "10000",
                "70000",
                "1.8",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["sla_profile"]["is_sla_met"] is True

        # Console mode
        res_con = runner.invoke(
            app,
            ["postal", "sla", "VNPOST-123456", "10000", "70000", "3.0"],
        )
        assert res_con.exit_code == 0
        assert "Đánh Giá Chất Lượng Thời Gian Toàn Trình" in res_con.output

    def test_postal_security_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "postal",
                "security",
                "VNPOST-123456",
                "--station",
                "TRAM-SOI-NOI-BAI",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["security_profile"]["is_passed"] is True

        # Console mode
        res_con = runner.invoke(
            app,
            ["postal", "security", "VNPOST-999999", "--contraband", "EXPLOSIVES_FIREARMS"],
        )
        assert res_con.exit_code == 0
        assert "PHÁT HIỆN HÀNG CẤM" in res_con.output

    def test_postal_indemnity_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "postal",
                "indemnity",
                "VNPOST-123456",
                "--incident",
                "LOST_TOTAL",
                "--postage",
                "45000",
                "--declared",
                "1500000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["indemnity_profile"]["total_indemnity_vnd"] == 1545000.0

        # Console mode
        res_con = runner.invoke(
            app,
            ["postal", "indemnity", "VNPOST-123456", "--incident", "DELAYED_OVERDUE", "--postage", "35000"],
        )
        assert res_con.exit_code == 0
        assert "Phương Án Bồi Thường Thiệt Hại Bưu Chính" in res_con.output

    def test_postal_list_all_resources(self, app) -> None:
        # Pre-seed items
        runner.invoke(app, ["postal", "license", "DN Mẫu", "0100000001", "--json"])
        runner.invoke(app, ["postal", "waybill", "Gui", "HN", "10000", "Nhan", "HCM", "70000", "--json"])
        runner.invoke(app, ["postal", "sla", "WB-SEED", "10000", "70000", "1.5", "--json"])
        runner.invoke(app, ["postal", "security", "WB-SEED", "--json"])
        runner.invoke(app, ["postal", "indemnity", "WB-SEED", "--json"])

        resources = ["licenses", "waybills", "sla", "screenings", "indemnities"]
        for r in resources:
            res = runner.invoke(app, ["postal", "list", r, "--json"])
            assert res.exit_code == 0
            items = json.loads(res.output)
            assert isinstance(items, list)
            assert len(items) >= 1

            # Console mode
            res_con = runner.invoke(app, ["postal", "list", r])
            assert res_con.exit_code == 0

    def test_postal_status_cmd(self, app) -> None:
        res_con = runner.invoke(app, ["postal", "status"])
        assert res_con.exit_code == 0
        assert "Báo Cáo Telemetry Mạng Lưới Bưu Chính" in res_con.output

        res_json = runner.invoke(app, ["postal", "status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "online"


# ---------------------------------------------------------------------------
# MCP Server Tool Parity Tests
# ---------------------------------------------------------------------------


class TestPostalMCP:
    """Ensure FastMCP and Pure-Python JSON-RPC 2.0 dual server parity for postal tools."""

    def test_src_core_mcp_postal_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. license
        res_lic = json.loads(server._handle_postal_license(
            enterprise_name="Công ty Chuyển phát MCP Core",
            tax_id="0109988771",
            scope="INTER_PROVINCE",
            capital_vnd=3000000000.0,
        ))
        assert res_lic["status"] == "success"

        # 2. waybill
        res_wb = json.loads(server._handle_postal_waybill(
            sender_name="Sender MCP",
            sender_address="Hà Nội",
            origin_postcode="10000",
            receiver_name="Receiver MCP",
            receiver_address="TP.HCM",
            dest_postcode="70000",
        ))
        assert res_wb["status"] == "success"

        # 3. sla
        res_sla = json.loads(server._handle_postal_sla(
            waybill_id="VNPOST-MCP01",
            origin_postcode="10000",
            dest_postcode="70000",
            actual_transit_days=1.8,
        ))
        assert res_sla["status"] == "success"

        # 4. security
        res_sec = json.loads(server._handle_postal_security(
            waybill_id="VNPOST-MCP01",
            scanner_station="TRAM-SOI-NOI-BAI",
        ))
        assert res_sec["status"] == "success"

        # 5. indemnity
        res_ind = json.loads(server._handle_postal_indemnity(
            waybill_id="VNPOST-MCP01",
            incident_type="LOST_TOTAL",
            postage_fee_vnd=35000.0,
            declared_value_vnd=1000000.0,
        ))
        assert res_ind["status"] == "success"

        # 6. list
        res_lst = json.loads(server._handle_postal_list(resource="waybills"))
        assert isinstance(res_lst, list)

        # 7. status
        res_st = json.loads(server._handle_postal_status())
        assert res_st["status"] == "online"

    def test_scripts_mcp_postal_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        from scripts.mcp_server import (
            handle_postal_indemnity,
            handle_postal_license,
            handle_postal_list,
            handle_postal_security,
            handle_postal_sla,
            handle_postal_status,
            handle_postal_waybill,
        )

        # 1. license
        res_lic = json.loads(handle_postal_license({
            "enterprise_name": "Công ty Chuyển phát Script",
            "tax_id": "0109988772",
            "scope": "INTER_PROVINCE",
            "capital_vnd": 2500000000.0,
        }))
        assert res_lic["status"] == "success"

        # 2. waybill
        res_wb = json.loads(handle_postal_waybill({
            "sender_name": "Sender Script",
            "sender_address": "HN",
            "origin_postcode": "10000",
            "receiver_name": "Receiver Script",
            "receiver_address": "HCM",
            "dest_postcode": "70000",
        }))
        assert res_wb["status"] == "success"

        # 3. sla
        res_sla = json.loads(handle_postal_sla({
            "waybill_id": "VNPOST-SCRIPT01",
            "origin_postcode": "10000",
            "dest_postcode": "70000",
            "actual_transit_days": 2.0,
        }))
        assert res_sla["status"] == "success"

        # 4. security
        res_sec = json.loads(handle_postal_security({
            "waybill_id": "VNPOST-SCRIPT01",
        }))
        assert res_sec["status"] == "success"

        # 5. indemnity
        res_ind = json.loads(handle_postal_indemnity({
            "waybill_id": "VNPOST-SCRIPT01",
            "incident_type": "DELAYED_OVERDUE",
            "postage_fee_vnd": 40000.0,
        }))
        assert res_ind["status"] == "success"

        # 6. list
        res_lst = json.loads(handle_postal_list({"resource": "licenses"}))
        assert isinstance(res_lst, list)

        # 7. status
        res_st = json.loads(handle_postal_status({}))
        assert res_st["status"] == "online"

    def test_scripts_mcp_core_tools_spec_and_handlers(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        postal_tools = [
            "mekong_postal_license",
            "mekong_postal_waybill",
            "mekong_postal_sla",
            "mekong_postal_security",
            "mekong_postal_indemnity",
            "mekong_postal_list",
            "mekong_postal_status",
        ]

        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for pt in postal_tools:
            assert pt in spec_names, f"Tool {pt} missing from CORE_TOOLS_SPEC"
            assert pt in CORE_HANDLERS, f"Tool {pt} missing from CORE_HANDLERS"
            bare_name = pt.replace("mekong_", "")
            assert bare_name in CORE_HANDLERS, f"Alias {bare_name} missing from CORE_HANDLERS"
