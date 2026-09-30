"""
Test Suite for Vietnamese Meteorology, Dam Safety & Natural Disaster Prevention Suite (Phase 96).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- DisasterEngine domain logic (Luật Phòng, chống thiên tai, Nghị định 114/2018/NĐ-CP, Nghị định 78/2021/NĐ-CP, Quyết định 18/2021/QĐ-TTg).
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
from src.core.disaster_engine import DisasterEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestDisasterBoundary:
    """Verifies that disaster_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "disaster_engine.py")
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


class TestDisasterEngine:
    """Tests core domain and regulatory business logic of DisasterEngine."""

    def test_audit_reservoir_dam_safety_special_important(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        res = engine.audit_reservoir_dam_safety(
            dam_name="Thủy điện Hòa Bình",
            river_basin="Lưu vực Sông Đà - Sông Hồng",
            dam_height_m=128.0,
            reservoir_capacity_m3=9_450_000_000.0,  # > 1 tỷ m3
            downstream_population=250000,
            last_inspection_years_ago=3,
            has_emergency_plan=True,
            automatic_monitoring=True,
        )

        assert res["dam_classification"] == "SPECIAL_IMPORTANT"
        assert res["is_safe"] is True
        assert len(res["deficiencies"]) == 0
        assert "APPROVED" in res["safety_rating"]
        assert res["audit_id"].startswith("DAM-AUD-")

    def test_audit_reservoir_dam_safety_large_unsafe(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        res = engine.audit_reservoir_dam_safety(
            dam_name="Hồ chứa Suối Dầu",
            river_basin="Lưu vực Sông Cái",
            dam_height_m=28.0,  # >= 15m -> LARGE
            reservoir_capacity_m3=35_000_000.0,
            downstream_population=15000,
            last_inspection_years_ago=6,  # > 5 years limit for large dams
            has_emergency_plan=False,
            automatic_monitoring=False,
        )

        assert res["dam_classification"] == "LARGE"
        assert res["is_safe"] is False
        assert len(res["deficiencies"]) == 3
        assert "UNSAFE" in res["safety_rating"]
        assert any("Quá hạn kiểm định" in d for d in res["deficiencies"])
        assert any("Phương án ứng phó" in d for d in res["deficiencies"])
        assert any("quan trắc" in d for d in res["deficiencies"])

    def test_simulate_reservoir_flood_discharge_authorized(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        res = engine.simulate_reservoir_flood_discharge(
            dam_name="Thủy điện A Vương",
            river_basin="Lưu vực Sông Vu Gia - Thu Bồn",
            current_water_level_m=380.5,
            flood_control_water_level_m=375.0,
            inflow_rate_m3s=1800.0,
            discharge_rate_m3s=1500.0,
            advance_warning_hours=5.0,  # >= 4.0h
            siren_system_active=True,
            inter_reservoir_compliance=True,
        )

        assert res["is_authorized"] is True
        assert len(res["violations"]) == 0
        assert "AUTHORIZED" in res["alert_status"]
        assert res["discharge_id"].startswith("FLD-DIS-")

    def test_simulate_reservoir_flood_discharge_unauthorized(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        res = engine.simulate_reservoir_flood_discharge(
            dam_name="Thủy điện Sông Ba Hạ",
            river_basin="Lưu vực Sông Ba",
            current_water_level_m=104.0,
            flood_control_water_level_m=105.0,
            inflow_rate_m3s=2000.0,
            discharge_rate_m3s=3200.0,  # > inflow * 1.3 while water level below flood control
            advance_warning_hours=1.5,  # < 4.0h
            siren_system_active=False,
            inter_reservoir_compliance=False,
        )

        assert res["is_authorized"] is False
        assert len(res["violations"]) >= 3
        assert "VIOLATION" in res["alert_status"]

    def test_assess_natural_disaster_risk_tier5(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        res = engine.assess_natural_disaster_risk(
            event_name="Siêu bão cấp thảm họa",
            disaster_type="TYPHOON",
            affected_provinces_count=10,
            wind_level_beaufort=16,
            rainfall_24h_mm=500.0,
            river_flood_level=4,
            downstream_population_at_risk=450000,
        )

        assert res["risk_level"] == 5
        assert "Cấp độ 5" in res["risk_level_name"]
        assert any("TÌNH TRẠNG KHẨN CẤP" in a for a in res["emergency_actions"])

    def test_assess_natural_disaster_risk_tier4_and_tier3(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        res4 = engine.assess_natural_disaster_risk(
            event_name="Bão mạnh đổ bộ Trung Bộ",
            disaster_type="TYPHOON",
            wind_level_beaufort=12,
            rainfall_24h_mm=380.0,
            river_flood_level=3,
            downstream_population_at_risk=150000,
        )
        assert res4["risk_level"] == 4

        res3 = engine.assess_natural_disaster_risk(
            event_name="Áp thấp nhiệt đới gây mưa lớn",
            disaster_type="TYPHOON",
            wind_level_beaufort=9,
            rainfall_24h_mm=250.0,
            river_flood_level=2,
            downstream_population_at_risk=40000,
        )
        assert res3["risk_level"] == 3

    def test_calculate_disaster_prevention_fund_normal(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        res = engine.calculate_disaster_prevention_fund(
            enterprise_name="Tập đoàn Công nghệ Mekong",
            total_capital_vnd=20_000_000_000.0,  # 20B * 0.0002 = 4,000,000 VND
            employee_count=50,                   # 50 * 90,000 = 4,500,000 VND
            is_exempt=False,
        )

        assert res["enterprise_fee_vnd"] == 4_000_000.0
        assert res["employee_fee_total_vnd"] == 4_500_000.0
        assert res["total_contribution_vnd"] == 8_500_000.0
        assert res["is_exempt"] is False
        assert res["calc_id"].startswith("FND-CAL-")

    def test_calculate_disaster_prevention_fund_caps_and_exempt(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        # Test min cap: 100M VND capital * 0.0002 = 20,000 VND -> min cap 500,000 VND
        res_min = engine.calculate_disaster_prevention_fund(
            enterprise_name="Doanh nghiệp siêu nhỏ",
            total_capital_vnd=100_000_000.0,
            employee_count=2,
        )
        assert res_min["enterprise_fee_vnd"] == 500_000.0

        # Test max cap: 1,000B VND capital * 0.0002 = 200,000,000 VND -> max cap 100,000,000 VND
        res_max = engine.calculate_disaster_prevention_fund(
            enterprise_name="Tập đoàn đa quốc gia",
            total_capital_vnd=1_000_000_000_000.0,
            employee_count=1000,
        )
        assert res_max["enterprise_fee_vnd"] == 100_000_000.0

        # Test exempt
        res_ex = engine.calculate_disaster_prevention_fund(
            enterprise_name="Doanh nghiệp vùng bão lũ",
            total_capital_vnd=50_000_000_000.0,
            employee_count=200,
            is_exempt=True,
            exemption_reason="Thiệt hại nặng nề do sạt lở đất",
        )
        assert res_ex["is_exempt"] is True
        assert res_ex["total_contribution_vnd"] == 0.0
        assert res_ex["exemption_reason"] == "Thiệt hại nặng nề do sạt lở đất"

    def test_list_records_and_status(self, temp_db):
        engine = DisasterEngine(db_path=temp_db)
        engine.audit_reservoir_dam_safety(dam_name="Dam 1")
        engine.simulate_reservoir_flood_discharge(dam_name="Dam 1")
        engine.assess_natural_disaster_risk(event_name="Event 1")
        engine.calculate_disaster_prevention_fund(enterprise_name="Ent 1")

        all_records = engine.list_records("all")
        assert len(all_records) >= 4

        dams = engine.list_records("dams")
        assert len(dams) >= 1
        assert dams[0]["type"] == "dam_audit"

        discharges = engine.list_records("discharges")
        assert len(discharges) >= 1
        assert discharges[0]["type"] == "flood_discharge"

        risks = engine.list_records("risks")
        assert len(risks) >= 1
        assert risks[0]["type"] == "disaster_risk"

        funds = engine.list_records("funds")
        assert len(funds) >= 1
        assert funds[0]["type"] == "fund_calculation"

        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_reservoir_dams_audited"] >= 1
        assert status["total_flood_discharges_monitored"] >= 1
        assert status["disaster_risk_events_tracked"] >= 1
        assert status["total_disaster_fund_collected_vnd"] > 0


class TestDisasterCLI:
    """Tests Typer CLI interface for mekong disaster."""

    def test_disaster_status_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["disaster"])
        assert result.exit_code == 0
        assert "THIÊN TAI" in result.output or "Disaster" in result.output

    def test_disaster_status_json(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["disaster", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "operational"
        assert "coordinating_authority" in data

    def test_disaster_dam_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "disaster",
                "dam",
                "Thủy điện Trị An",
                "--basin", "Lưu vực Sông Đồng Nai",
                "--height", "40.0",
                "--capacity", "2760000000",
                "--population", "180000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dam_name"] == "Thủy điện Trị An"
        assert data["dam_classification"] == "SPECIAL_IMPORTANT"

    def test_disaster_discharge_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "disaster",
                "discharge",
                "Thủy điện Đa Nhim",
                "--basin", "Lưu vực Sông Đồng Nai",
                "--level", "1042.0",
                "--flood-level", "1040.0",
                "--warning-hours", "5.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_authorized"] is True

    def test_disaster_risk_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "disaster",
                "risk",
                "Mưa lũ lịch sử Miền Trung",
                "--type", "HISTORICAL_FLOOD",
                "--wind", "8",
                "--rain", "450.0",
                "--flood", "3",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["risk_level"] in (4, 5)

    def test_disaster_fund_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(
            app,
            [
                "disaster",
                "fund",
                "Công ty TNHH Sản xuất Mekong",
                "--capital", "50000000000",
                "--employees", "100",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["enterprise_fee_vnd"] == 10_000_000.0

    def test_disaster_list_cli(self):
        runner = CliRunner()
        app = build_app()
        result = runner.invoke(app, ["disaster", "list", "all", "--limit", "10", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


class TestDisasterMCP:
    """Tests dual MCP handlers for disaster prevention and dam safety tools."""

    def test_core_mcp_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-disaster-core")

        # Dam
        res1 = json.loads(server._handle_disaster_dam(dam_name="MCP Test Dam", dam_height_m=90.0))
        assert res1["dam_name"] == "MCP Test Dam"
        assert res1["dam_classification"] == "LARGE"

        # Discharge
        res2 = json.loads(server._handle_disaster_discharge(dam_name="MCP Test Dam", warning_hours=5.0))
        assert res2["is_authorized"] is True

        # Risk
        res3 = json.loads(server._handle_disaster_risk(event_name="MCP Typhoon Test", wind_level_beaufort=14))
        assert res3["risk_level"] == 4

        # Fund
        res4 = json.loads(server._handle_disaster_fund(enterprise_name="MCP Test Corp", total_capital_vnd=1e10, employee_count=20))
        assert res4["total_contribution_vnd"] > 0

        # List
        res5 = json.loads(server._handle_disaster_list(category="all", limit=5))
        assert isinstance(res5, list)

        # Status
        res6 = json.loads(server._handle_disaster_status())
        assert res6["status"] == "operational"

    def test_scripts_mcp_handlers(self):
        from scripts.mcp_server import (
            handle_disaster_dam,
            handle_disaster_discharge,
            handle_disaster_fund,
            handle_disaster_list,
            handle_disaster_risk,
            handle_disaster_status,
        )

        res1 = json.loads(handle_disaster_dam({"dam_name": "Fallback Script Dam"}))
        assert res1["dam_name"] == "Fallback Script Dam"

        res2 = json.loads(handle_disaster_discharge({"dam_name": "Fallback Script Dam"}))
        assert "alert_status" in res2

        res3 = json.loads(handle_disaster_risk({"event_name": "Fallback Storm"}))
        assert "risk_level" in res3

        res4 = json.loads(handle_disaster_fund({"enterprise_name": "Fallback Corp"}))
        assert "total_contribution_vnd" in res4

        res5 = json.loads(handle_disaster_list({"category": "all", "limit": 5}))
        assert isinstance(res5, list)

        res6 = json.loads(handle_disaster_status({}))
        assert res6["status"] == "operational"
