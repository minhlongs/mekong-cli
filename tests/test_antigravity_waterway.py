# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Inland Waterway Transport, River Ports & Canal Navigation (Phase 74)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.waterway_engine import (
    BARGE_BASE_FREIGHT_RATES,
    CAPTAIN_LICENSE_TIERS,
    CHANNEL_TECHNICAL_GRADES,
    VESSEL_LIFESPAN_CAPS,
    WaterwayEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestWaterwayCoreBoundary:
    """Ensure WaterwayEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/waterway_engine.py")
        assert source_path.exists(), "waterway_engine.py must exist"

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


class TestWaterwayEngine:
    """Test WaterwayEngine channel grades, port registration, vessel lifespan caps, clearances, captains, and freight."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> WaterwayEngine:
        db_file = tmp_path / "test_waterway.db"
        return WaterwayEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Channel technical grades under TCVN 5664:2009
        assert "GRADE_I" in CHANNEL_TECHNICAL_GRADES
        assert CHANNEL_TECHNICAL_GRADES["GRADE_I"]["min_depth_m"] == 3.0
        assert CHANNEL_TECHNICAL_GRADES["GRADE_I"]["min_bridge_clearance_m"] == 10.0
        assert "SPECIAL" in CHANNEL_TECHNICAL_GRADES
        assert CHANNEL_TECHNICAL_GRADES["SPECIAL"]["min_depth_m"] == 4.0
        assert "GRADE_V" in CHANNEL_TECHNICAL_GRADES

        # Vessel lifespan caps under Decree 111/2014/NĐ-CP
        assert "PASSENGER_STEEL" in VESSEL_LIFESPAN_CAPS
        assert VESSEL_LIFESPAN_CAPS["PASSENGER_STEEL"]["max_lifespan_years"] == 30
        assert "PASSENGER_HIGH_SPEED" in VESSEL_LIFESPAN_CAPS
        assert VESSEL_LIFESPAN_CAPS["PASSENGER_HIGH_SPEED"]["max_lifespan_years"] == 20
        assert "CARGO_BARGE_CONTAINER" in VESSEL_LIFESPAN_CAPS
        assert VESSEL_LIFESPAN_CAPS["CARGO_BARGE_CONTAINER"]["max_lifespan_years"] == 35
        assert "TANKER_DANGEROUS_LIQUID" in VESSEL_LIFESPAN_CAPS
        assert VESSEL_LIFESPAN_CAPS["TANKER_DANGEROUS_LIQUID"]["max_lifespan_years"] == 25

        # Captain License Tiers under Circular 40/2020/TT-BGTVT
        assert "T1" in CAPTAIN_LICENSE_TIERS
        assert CAPTAIN_LICENSE_TIERS["T1"]["min_experience_months"] == 36
        assert "T4" in CAPTAIN_LICENSE_TIERS
        assert CAPTAIN_LICENSE_TIERS["T4"]["min_experience_months"] == 12

        # Freight rates
        assert "CONTAINER_TEU" in BARGE_BASE_FREIGHT_RATES
        assert "BULK_AGRICULTURE" in BARGE_BASE_FREIGHT_RATES

    def test_register_channel_success(self, engine: WaterwayEngine) -> None:
        res = engine.register_channel(
            channel_code="CH-CHO-GAO",
            channel_name="Tuyến Kênh Huyết Mạch Chợ Gạo",
            technical_grade="GRADE_I",
            length_km=28.5,
            depth_m=3.5,
            bridge_clearance_m=10.0,
            river_basin="Đồng bằng Sông Cửu Long",
        )
        assert res["status"] == "success"
        prof = res["channel_profile"]
        assert prof["channel_code"] == "CH-CHO-GAO"
        assert prof["technical_grade"] == "GRADE_I"
        assert prof["is_depth_standard_compliant"] is True
        assert prof["length_km"] == 28.5

    def test_register_channel_invalid_grade(self, engine: WaterwayEngine) -> None:
        with pytest.raises(ValueError, match="Cấp kỹ thuật luồng không hợp lệ"):
            engine.register_channel(
                channel_code="CH-INVALID",
                channel_name="Luồng Sai Chuẩn",
                technical_grade="GRADE_INVALID_99",
                length_km=10.0,
                depth_m=2.0,
                bridge_clearance_m=5.0,
            )

    def test_register_port_success(self, engine: WaterwayEngine) -> None:
        res = engine.register_port(
            port_code="PRT-MY-THO",
            port_name="Cảng Mỹ Tho Tiền Giang",
            port_type="CARGO_PORT",
            channel_code="CH-TIEN-01",
            province="Tiền Giang",
            max_dwt=3000.0,
            max_teu_capacity=500,
        )
        assert res["status"] == "success"
        prof = res["port_profile"]
        assert prof["port_code"] == "PRT-MY-THO"
        assert prof["province"] == "Tiền Giang"
        assert prof["max_dwt"] == 3000.0
        assert prof["status"] == "ACTIVE"

    def test_register_vessel_valid_and_expired_lifespan(self, engine: WaterwayEngine) -> None:
        # Valid vessel: built 2021, container barge (max 35 yrs)
        res_valid = engine.register_vessel(
            vr_number="VR-22001188",
            vessel_name="Sà lan Container Mekong Star",
            vessel_type="CARGO_BARGE_CONTAINER",
            year_built=2021,
            hull_material="STEEL",
            dwt_or_passengers=1500.0,
            has_ais=True,
            has_vhf=True,
        )
        assert res_valid["status"] == "success"
        assert res_valid["vessel_profile"]["is_lifespan_valid"] is True
        assert res_valid["vessel_profile"]["age_years"] == 5

        # Expired vessel: high speed craft built in 2000 (max 20 yrs -> age 26 > 20)
        res_expired = engine.register_vessel(
            vr_number="VR-19999999",
            vessel_name="Tàu Cánh Ngầm Cao Tốc Vũng Tàu",
            vessel_type="PASSENGER_HIGH_SPEED",
            year_built=2000,
            hull_material="COMPOSITE",
            dwt_or_passengers=120.0,
            has_ais=True,
            has_vhf=True,
        )
        assert res_expired["status"] == "success"
        assert res_expired["vessel_profile"]["is_lifespan_valid"] is False

    def test_register_vessel_invalid_type(self, engine: WaterwayEngine) -> None:
        with pytest.raises(ValueError, match="Loại phương tiện thủy nội địa không hợp lệ"):
            engine.register_vessel(
                vr_number="VR-UNKNOWN",
                vessel_name="Tàu Không Tên",
                vessel_type="SUBMARINE",
                year_built=2022,
            )

    def test_issue_port_clearance_approved(self, engine: WaterwayEngine) -> None:
        res = engine.issue_port_clearance(
            vr_number="VR-22001188",
            port_code="PRT-MY-THO",
            captain_name="Nguyễn Văn Hải",
            captain_license_tier="T2",
            cargo_type="CONTAINER",
            cargo_volume=48.0,
            passengers_count=0,
            ais_online=True,
            vhf_online=True,
            lifejackets_sufficient=True,
        )
        assert res["status"] == "success"
        prof = res["clearance_profile"]
        assert prof["is_cleared"] is True
        assert prof["rejection_reason"] is None
        assert prof["clearance_id"].startswith("CLR-")

    def test_issue_port_clearance_rejected_missing_equipment(self, engine: WaterwayEngine) -> None:
        res = engine.issue_port_clearance(
            vr_number="VR-22001188",
            port_code="PRT-MY-THO",
            captain_name="Nguyễn Văn Hải",
            captain_license_tier="T2",
            cargo_type="CONTAINER",
            cargo_volume=48.0,
            passengers_count=0,
            ais_online=False,
            vhf_online=False,
            lifejackets_sufficient=False,
        )
        assert res["status"] == "success"
        prof = res["clearance_profile"]
        assert prof["is_cleared"] is False
        assert "AIS" in prof["rejection_reason"]
        assert "VHF" in prof["rejection_reason"]
        assert "áo phao" in prof["rejection_reason"]

    def test_verify_captain_license_valid(self, engine: WaterwayEngine) -> None:
        res = engine.verify_captain_license(
            full_name="Trần Đình Trọng",
            tier="T1",
            experience_months=48,
            health_class=1,
        )
        assert res["status"] == "success"
        prof = res["license_profile"]
        assert prof["is_valid"] is True
        assert prof["tier"] == "T1"
        assert prof["license_number"].startswith("TT-T1-")

    def test_verify_captain_license_invalid_experience_or_health(self, engine: WaterwayEngine) -> None:
        # Inadequate experience for T1 (requires 36 months, given 12)
        res_exp = engine.verify_captain_license(
            full_name="Lê Văn Tân",
            tier="T1",
            experience_months=12,
            health_class=1,
        )
        assert res_exp["license_profile"]["is_valid"] is False

        # Inadequate health (class 3 not eligible)
        res_health = engine.verify_captain_license(
            full_name="Phạm Văn Ba",
            tier="T2",
            experience_months=30,
            health_class=3,
        )
        assert res_health["license_profile"]["is_valid"] is False

    def test_verify_captain_license_invalid_tier(self, engine: WaterwayEngine) -> None:
        with pytest.raises(ValueError, match="Hạng bằng thuyền trưởng không hợp lệ"):
            engine.verify_captain_license(
                full_name="Lê Văn Tân",
                tier="T99",
                experience_months=50,
            )

    def test_calculate_barge_freight(self, engine: WaterwayEngine) -> None:
        res = engine.calculate_barge_freight(
            shipper_name="Công ty Xuất Nhập Khẩu Nông Sản Cần Thơ",
            cargo_type="CONTAINER_TEU",
            volume=40.0,
            distance_km=150.0,
            channel_grade="GRADE_I",
        )
        assert res["status"] == "success"
        bill = res["freight_bill"]
        # base_rate = 450 VND / TEU-km, mult = 1.0 -> 450 VND
        # freight = 40 * 150 * 450 = 2,700,000 VND
        # handling = 40 * 300,000 = 12,000,000 VND
        # total = 14,700,000 VND
        assert bill["base_rate_vnd"] == 450.0
        assert bill["handling_fee_vnd"] == 12000000.0
        assert bill["total_charge_vnd"] == 14700000.0

    def test_calculate_barge_freight_invalid_cargo(self, engine: WaterwayEngine) -> None:
        with pytest.raises(ValueError, match="Loại hàng hóa sà lan không hợp lệ"):
            engine.calculate_barge_freight(
                shipper_name="Test Shipper",
                cargo_type="UNSUPPORTED_GOODS",
                volume=10.0,
                distance_km=50.0,
            )

    def test_list_and_status(self, engine: WaterwayEngine) -> None:
        # Populate
        engine.register_channel("CH-1", "Kênh 1", "GRADE_I", 15.0, 3.2, 10.0)
        engine.register_port("PRT-1", "Cảng 1", "CARGO_PORT", "CH-1", "Cần Thơ", 2000.0, 300)
        engine.register_vessel("VR-001", "Tàu 1", "CARGO_BARGE_DRY", 2022)
        engine.issue_port_clearance("VR-001", "PRT-1", "Thuyền Trưởng A", "T2")
        engine.verify_captain_license("Thuyền Trưởng A", "T2", 30)
        engine.calculate_barge_freight("Chủ hàng 1", "BULK_AGRICULTURE", 500.0, 100.0)

        # Lists
        assert len(engine.list_channels()) == 1
        assert len(engine.list_ports()) == 1
        assert len(engine.list_vessels()) == 1
        assert len(engine.list_clearances()) == 1
        assert len(engine.list_captains()) == 1
        assert len(engine.list_freight_bills()) == 1

        # Status
        status = engine.get_status()
        assert status["status"] == "online"
        m = status["metrics"]
        assert m["registered_waterway_channels"] == 1
        assert m["active_river_ports"] == 1
        assert m["registered_vessels"] == 1
        assert m["valid_lifespan_vessels"] == 1
        assert m["total_clearance_requests"] == 1
        assert m["cleared_port_departures"] == 1
        assert m["certified_captains"] == 1
        assert m["barge_freight_bills"] == 1
        assert m["total_barge_freight_revenue_vnd"] > 0


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestWaterwayCLI:
    """Test Typer CLI commands for waterway suite."""

    @pytest.fixture
    def app(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        return build_app()

    def test_waterway_help(self, app) -> None:
        result = runner.invoke(app, ["waterway", "--help"])
        assert result.exit_code == 0
        assert "Vietnamese Inland Waterway Transport" in result.output

    def test_waterway_main_console_and_json(self, app) -> None:
        res_con = runner.invoke(app, ["waterway"])
        assert res_con.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ GIAO THÔNG ĐƯỜNG THỦY NỘI ĐỊA" in res_con.output

        res_json = runner.invoke(app, ["waterway", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "online"
        assert "metrics" in data

    def test_waterway_channel_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "waterway",
                "channel",
                "CH-CHO-GAO",
                "Tuyến Kênh Chợ Gạo",
                "--grade",
                "GRADE_I",
                "--length",
                "28.5",
                "--depth",
                "3.5",
                "--clearance",
                "10.0",
                "--basin",
                "ĐBSCL",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["channel_profile"]["channel_code"] == "CH-CHO-GAO"

        # Console mode
        res_con = runner.invoke(
            app,
            ["waterway", "channel", "CH-TIEN", "Sông Tiền", "--grade", "GRADE_I"],
        )
        assert res_con.exit_code == 0
        assert "CH-TIEN" in res_con.output

    def test_waterway_port_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "waterway",
                "port",
                "PRT-CAN-THO",
                "Cảng Tân Cảng Thốt Nốt",
                "--type",
                "CONTAINER_PORT",
                "--channel",
                "CH-HAU-01",
                "--province",
                "Cần Thơ",
                "--dwt",
                "5000",
                "--teu",
                "1000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["port_profile"]["port_code"] == "PRT-CAN-THO"

        # Console mode
        res_con = runner.invoke(
            app,
            ["waterway", "port", "PRT-MY-THO", "Cảng Mỹ Tho"],
        )
        assert res_con.exit_code == 0
        assert "PRT-MY-THO" in res_con.output

    def test_waterway_vessel_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "waterway",
                "vessel",
                "VR-22001188",
                "Sà lan Tân Cảng 01",
                "--type",
                "CARGO_BARGE_CONTAINER",
                "--year",
                "2021",
                "--material",
                "STEEL",
                "--capacity",
                "2000",
                "--ais",
                "--vhf",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["vessel_profile"]["is_lifespan_valid"] is True

        # Console mode
        res_con = runner.invoke(
            app,
            ["waterway", "vessel", "VR-22001199", "Sà lan Tân Cảng 02"],
        )
        assert res_con.exit_code == 0
        assert "VR-22001199" in res_con.output

    def test_waterway_clearance_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "waterway",
                "clearance",
                "VR-22001188",
                "PRT-CAN-THO",
                "Nguyễn Văn An",
                "--tier",
                "T2",
                "--cargo",
                "CONTAINER",
                "--volume",
                "50",
                "--ais-online",
                "--vhf-online",
                "--lifejackets",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["clearance_profile"]["is_cleared"] is True

        # Console mode
        res_con = runner.invoke(
            app,
            ["waterway", "clearance", "VR-22001188", "PRT-CAN-THO", "Nguyễn Văn An"],
        )
        assert res_con.exit_code == 0
        assert "CHẤP THUẬN RỜI CẢNG BẾN" in res_con.output

    def test_waterway_captain_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "waterway",
                "captain",
                "Lê Hoàng Nam",
                "--tier",
                "T1",
                "--exp",
                "48",
                "--health",
                "1",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["license_profile"]["is_valid"] is True

        # Console mode
        res_con = runner.invoke(
            app,
            ["waterway", "captain", "Lê Hoàng Nam", "--tier", "T2"],
        )
        assert res_con.exit_code == 0
        assert "Lê Hoàng Nam" in res_con.output

    def test_waterway_freight_cmd(self, app) -> None:
        res = runner.invoke(
            app,
            [
                "waterway",
                "freight",
                "Tập đoàn Gạo Lộc Trời",
                "--cargo",
                "BULK_AGRICULTURE",
                "--volume",
                "1000",
                "--distance",
                "180",
                "--grade",
                "GRADE_I",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "success"
        assert data["freight_bill"]["total_charge_vnd"] > 0

        # Console mode
        res_con = runner.invoke(
            app,
            ["waterway", "freight", "Tập đoàn Gạo Lộc Trời"],
        )
        assert res_con.exit_code == 0
        assert "Vận Đơn Vận Tải Sà Lan" in res_con.output

    def test_waterway_list_all_resources(self, app) -> None:
        # Pre-seed items
        runner.invoke(app, ["waterway", "channel", "CH-SEED", "Luồng Mẫu", "--json"])
        runner.invoke(app, ["waterway", "port", "PRT-SEED", "Cảng Mẫu", "--json"])
        runner.invoke(app, ["waterway", "vessel", "VR-SEED", "Tàu Mẫu", "--json"])
        runner.invoke(app, ["waterway", "clearance", "VR-SEED", "PRT-SEED", "Thuyền Trưởng Mẫu", "--json"])
        runner.invoke(app, ["waterway", "captain", "Thuyền Trưởng Mẫu", "--json"])
        runner.invoke(app, ["waterway", "freight", "Chủ Hàng Mẫu", "--json"])

        resources = ["channels", "ports", "vessels", "clearances", "captains", "bills"]
        for r in resources:
            res = runner.invoke(app, ["waterway", "list", r, "--json"])
            assert res.exit_code == 0
            items = json.loads(res.output)
            assert isinstance(items, list)
            assert len(items) >= 1

            # Console mode
            res_con = runner.invoke(app, ["waterway", "list", r])
            assert res_con.exit_code == 0

    def test_waterway_status_cmd(self, app) -> None:
        res_con = runner.invoke(app, ["waterway", "status"])
        assert res_con.exit_code == 0
        assert "Báo Cáo Telemetry" in res_con.output

        res_json = runner.invoke(app, ["waterway", "status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "online"


# ---------------------------------------------------------------------------
# MCP Server Tool Parity Tests
# ---------------------------------------------------------------------------


class TestWaterwayMCP:
    """Ensure FastMCP and Pure-Python JSON-RPC 2.0 dual server parity for waterway tools."""

    def test_src_core_mcp_waterway_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. channel
        res_ch = json.loads(server._handle_waterway_channel(
            channel_code="CH-MCP-01",
            channel_name="Luồng Kênh MCP",
            technical_grade="GRADE_I",
            length_km=30.0,
            depth_m=3.5,
            bridge_clearance_m=10.0,
        ))
        assert res_ch["status"] == "success"

        # 2. port
        res_pt = json.loads(server._handle_waterway_port(
            port_code="PRT-MCP-01",
            port_name="Cảng Bến MCP",
            port_type="CARGO_PORT",
            channel_code="CH-MCP-01",
            province="Bến Tre",
        ))
        assert res_pt["status"] == "success"

        # 3. vessel
        res_vs = json.loads(server._handle_waterway_vessel(
            vr_number="VR-MCP-9999",
            vessel_name="Sà Lan MCP Test",
            vessel_type="CARGO_BARGE_CONTAINER",
            year_built=2022,
        ))
        assert res_vs["status"] == "success"

        # 4. clearance
        res_clr = json.loads(server._handle_waterway_clearance(
            vr_number="VR-MCP-9999",
            port_code="PRT-MCP-01",
            captain_name="Nguyễn Văn MCP",
            captain_license_tier="T2",
        ))
        assert res_clr["status"] == "success"

        # 5. captain
        res_cpt = json.loads(server._handle_waterway_captain(
            full_name="Nguyễn Văn MCP",
            tier="T2",
            experience_months=36,
        ))
        assert res_cpt["status"] == "success"

        # 6. freight
        res_fr = json.loads(server._handle_waterway_freight(
            shipper_name="Công ty MCP Logistics",
            cargo_type="CONTAINER_TEU",
            volume=20.0,
            distance_km=100.0,
        ))
        assert res_fr["status"] == "success"

        # 7. list
        res_lst = json.loads(server._handle_waterway_list(resource="channels"))
        assert isinstance(res_lst, list)

        # 8. status
        res_st = json.loads(server._handle_waterway_status())
        assert res_st["status"] == "online"

    def test_scripts_mcp_waterway_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        from scripts.mcp_server import (
            handle_waterway_captain,
            handle_waterway_channel,
            handle_waterway_clearance,
            handle_waterway_freight,
            handle_waterway_list,
            handle_waterway_port,
            handle_waterway_status,
            handle_waterway_vessel,
        )

        # 1. channel
        res_ch = json.loads(handle_waterway_channel({
            "channel_code": "CH-SCRIPT-01",
            "channel_name": "Luồng Script Test",
            "technical_grade": "GRADE_I",
            "length_km": 25.0,
            "depth_m": 3.2,
            "bridge_clearance_m": 10.0,
        }))
        assert res_ch["status"] == "success"

        # 2. port
        res_pt = json.loads(handle_waterway_port({
            "port_code": "PRT-SCRIPT-01",
            "port_name": "Cảng Script Test",
            "channel_code": "CH-SCRIPT-01",
        }))
        assert res_pt["status"] == "success"

        # 3. vessel
        res_vs = json.loads(handle_waterway_vessel({
            "vr_number": "VR-SCRIPT-01",
            "vessel_name": "Tàu Script Test",
            "vessel_type": "CARGO_BARGE_DRY",
            "year_built": 2020,
        }))
        assert res_vs["status"] == "success"

        # 4. clearance
        res_clr = json.loads(handle_waterway_clearance({
            "vr_number": "VR-SCRIPT-01",
            "port_code": "PRT-SCRIPT-01",
            "captain_name": "Trần Script",
        }))
        assert res_clr["status"] == "success"

        # 5. captain
        res_cpt = json.loads(handle_waterway_captain({
            "full_name": "Trần Script",
            "tier": "T2",
            "experience_months=30": 30,
        }))
        assert res_cpt["status"] == "success"

        # 6. freight
        res_fr = json.loads(handle_waterway_freight({
            "shipper_name": "Shipper Script",
            "cargo_type": "CONTAINER_TEU",
            "volume": 10.0,
            "distance_km": 80.0,
        }))
        assert res_fr["status"] == "success"

        # 7. list
        res_lst = json.loads(handle_waterway_list({"resource": "channels"}))
        assert isinstance(res_lst, list)

        # 8. status
        res_st = json.loads(handle_waterway_status({}))
        assert res_st["status"] == "online"

    def test_scripts_mcp_core_tools_spec_and_handlers(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        waterway_tools = [
            "mekong_waterway_channel",
            "mekong_waterway_port",
            "mekong_waterway_vessel",
            "mekong_waterway_clearance",
            "mekong_waterway_captain",
            "mekong_waterway_freight",
            "mekong_waterway_list",
            "mekong_waterway_status",
        ]

        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for wt in waterway_tools:
            assert wt in spec_names, f"Tool {wt} missing from CORE_TOOLS_SPEC"
            assert wt in CORE_HANDLERS, f"Tool {wt} missing from CORE_HANDLERS"
            bare_name = wt.replace("mekong_", "")
            assert bare_name in CORE_HANDLERS, f"Alias {bare_name} missing from CORE_HANDLERS"
