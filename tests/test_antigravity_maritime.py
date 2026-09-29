# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Maritime Logistics, Port Terminal & ICD Customs Clearance Engine (Phase 57)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.maritime_engine import (
    SEAPORT_GROUPS,
    CONTAINER_TYPES,
    VND_PER_USD,
    MaritimeEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestMaritimeCoreBoundary:
    """Ensure MaritimeEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/maritime_engine.py")
        assert source_path.exists(), "maritime_engine.py must exist"

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


class TestMaritimeEngine:
    """Test MaritimeEngine vessel calls, container yard, tariff calculations, and e-Manifest."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> MaritimeEngine:
        db_file = tmp_path / "test_maritime.db"
        return MaritimeEngine(db_path=db_file)

    def test_constants_and_groups(self) -> None:
        assert "GROUP_1" in SEAPORT_GROUPS
        assert "GROUP_4" in SEAPORT_GROUPS
        assert "20GP" in CONTAINER_TYPES
        assert "40HC" in CONTAINER_TYPES
        assert "40RF" in CONTAINER_TYPES
        assert VND_PER_USD >= 24_000.0

    def test_register_vessel_call_cai_mep_deep_water(self, engine: MaritimeEngine) -> None:
        res = engine.register_vessel_call(
            vessel_name="MSC ISABELLA",
            imo_number="IMO9839208",
            flag_state="Panama",
            dwt=228149.0,
            grt=232618.0,
            loa_meters=399.9,
            draft_meters=16.5,
            port_code="VNVUT",
            terminal_name="Cảng Cái Mép - CMIT",
            eta="2026-10-01 08:00",
            etd="2026-10-02 20:00",
        )
        assert res["ok"] is True
        assert res["call_id"].startswith("CALL-")
        assert res["vessel_specs"]["is_deep_water_capable"] is True
        assert res["port_assignment"]["port_group"] == "GROUP_4"
        assert any("nước sâu" in adv for adv in res["navigation_advisories"])

    def test_register_vessel_call_shallow_warning(self, engine: MaritimeEngine) -> None:
        # Deep draft vessel arriving at a shallow terminal gives navigation advisory
        res = engine.register_vessel_call(
            vessel_name="MEGA CARRIER",
            imo_number="IMO9999999",
            flag_state="Liberia",
            dwt=120000.0,
            grt=110000.0,
            loa_meters=330.0,
            draft_meters=15.0,
            port_code="VNSGN",
            terminal_name="Bến Nghé Terminal",
            eta="2026-10-05 10:00",
            etd="2026-10-06 18:00",
        )
        assert res["ok"] is True
        assert res["vessel_specs"]["is_deep_water_capable"] is True
        assert any("CẢNH BÁO MỚN NƯỚC" in adv for adv in res["navigation_advisories"])

    def test_register_container_standard_and_reefer(self, engine: MaritimeEngine) -> None:
        # Standard 40HC container
        c1 = engine.register_container(
            container_no="MSCU9876543",
            container_type="40HC",
            gross_weight_kg=26500.0,
            seal_number="VN-SEAL-1122",
            booking_or_bl="BKG-SGN-202601",
            yard_slot="YARD-A01-R02-T3",
        )
        assert c1["ok"] is True
        assert c1["iso_code"] == "45G1"
        assert c1["weights"]["payload_kg"] == 26500.0 - 2300.0
        assert c1["weights"]["vgm_solas_compliant"] is True
        assert c1["yard_allocation"]["is_reefer_powered"] is False

        # Reefer 40RF container
        c2 = engine.register_container(
            container_no="ONEU1234567",
            container_type="40RF",
            gross_weight_kg=28000.0,
            seal_number="VN-SEAL-3344",
            booking_or_bl="BL-ONE-202602",
            yard_slot="YARD-REEFER-05",
            is_reefer=True,
        )
        assert c2["ok"] is True
        assert c2["iso_code"] == "45R1"
        assert c2["yard_allocation"]["is_reefer_powered"] is True

    def test_calculate_port_tariffs_circular_39(self, engine: MaritimeEngine) -> None:
        # Group 4: berth_rate = 0.0035 USD/GT/hr, pilotage_rate = 0.0032 USD/GT/NM
        # GRT = 30,000, berth_hours = 24 -> berth dues = 30000 * 24 * 0.0035 = 2,520 USD
        # pilotage: 30000 * 18 * 0.0032 = 1,728 USD
        # LoLo: 100 x 20ft full ($52) = 5,200 USD
        #       150 x 40ft full ($77) = 11,550 USD
        #       20 x 20ft empty ($32) = 640 USD
        #       10 x 40ft empty ($48) = 480 USD
        # Reefer: 10 units * 24 hrs * $2.5 = 600 USD
        # Total USD = 2520 + 1728 + 5200 + 11550 + 640 + 480 + 600 = 22,718 USD
        res = engine.calculate_port_tariffs(
            vessel_call_id="CALL-TEST-001",
            port_group="GROUP_4",
            grt=30000.0,
            berth_hours=24.0,
            pilotage_distance_nm=18.0,
            full_20ft_count=100,
            full_40ft_count=150,
            empty_20ft_count=20,
            empty_40ft_count=10,
            reefer_power_hours=24.0,
            reefer_count=10,
        )
        assert res["ok"] is True
        assert res["invoice_id"].startswith("INV-MRT-")
        assert res["breakdown_usd"]["berth_dues"] == 2520.0
        assert res["breakdown_usd"]["pilotage_dues"] == 1728.0
        assert res["breakdown_usd"]["stevedoring_lolo"]["total_lolo"] == 17870.0
        assert res["total_amount_usd"] == 22718.0
        assert res["total_amount_vnd"] == round(22718.0 * VND_PER_USD)
        assert "Thông tư 39/2023/TT-BGTVT" in res["governing_circular"]

    def test_declare_customs_manifest_vnaccs(self, engine: MaritimeEngine) -> None:
        res = engine.declare_customs_manifest(
            vessel_call_id="CALL-TEST-001",
            bill_of_lading="MSK-SGN-2026-999",
            shipper_name="Công ty CP Thủy sản Minh Phú",
            consignee_name="Seafood Imports Rotterdam B.V.",
            cargo_description="Tôm đông lạnh xuất khẩu (Frozen Shrimp)",
            container_count=8,
            total_gross_kg=195000.0,
        )
        assert res["ok"] is True
        assert res["manifest_id"].startswith("MNF-")
        assert res["customs_clearance"]["vnaccs_status"] == "MANIFEST_REGISTERED"
        assert res["customs_clearance"]["national_single_window_ack"] is True

    def test_list_and_status(self, engine: MaritimeEngine) -> None:
        engine.register_vessel_call(
            vessel_name="PACIFIC VOYAGER",
            imo_number="IMO9123456",
            flag_state="Vietnam",
            dwt=28000.0,
            grt=18000.0,
            loa_meters=185.0,
            draft_meters=9.5,
            port_code="VNHPH",
            terminal_name="Cảng Đình Vũ",
            eta="2026-10-02 12:00",
            etd="2026-10-03 18:00",
        )
        engine.register_container(
            container_no="TEMU1122334",
            container_type="20GP",
            gross_weight_kg=18000.0,
            seal_number="VN-SEAL-77",
            booking_or_bl="BL-TEST",
        )

        vessels = engine.list_vessel_calls()
        assert len(vessels) >= 1

        containers = engine.list_containers()
        assert len(containers) >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["metrics"]["total_vessel_calls"] >= 1
        assert status["metrics"]["total_containers_tracked"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Surface Tests
# ---------------------------------------------------------------------------


class TestMaritimeCLI:
    """Test mekong maritime Typer CLI commands."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_dashboard(self) -> None:
        result = runner.invoke(self.app, ["maritime"])
        assert result.exit_code == 0
        assert "HỆ THỐNG VẬN TẢI BIỂN" in result.output

    def test_cli_status_json(self) -> None:
        result = runner.invoke(self.app, ["maritime", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "regulatory_framework" in data

    def test_cli_vessel_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "maritime",
                "vessel",
                "EVER GIVEN",
                "IMO9811000",
                "Panama",
                "199320",
                "219079",
                "399.9",
                "16.0",
                "VNVUT",
                "Cảng Quốc tế Cái Mép (CMIT)",
                "2026-10-01 08:00",
                "2026-10-02 20:00",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["vessel_name"] == "EVER GIVEN"
        assert data["schedule"]["status"] == "BERTH_ALLOCATED"

    def test_cli_container_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "maritime",
                "container",
                "MSCU1234567",
                "40HC",
                "28500",
                "VN-SEAL-8899",
                "BL-MSK-20260901",
                "--slot",
                "YARD-B02-R05-T3",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["container_no"] == "MSCU1234567"
        assert data["weights"]["vgm_solas_compliant"] is True

    def test_cli_tariff_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "maritime",
                "tariff",
                "CALL-001",
                "GROUP_4",
                "45000",
                "24",
                "--f20",
                "100",
                "--f40",
                "150",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["total_amount_usd"] > 0
        assert data["total_amount_vnd"] > 0

    def test_cli_manifest_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "maritime",
                "manifest",
                "CALL-001",
                "MSK-VN-2026-001",
                "Doanh nghiệp May XK Việt Nam",
                "Hamburg Trading GmbH",
                "Hàng may mặc xuất khẩu",
                "15",
                "285000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["customs_clearance"]["vnaccs_status"] == "MANIFEST_REGISTERED"

    def test_cli_list_json(self) -> None:
        res_vessels = runner.invoke(self.app, ["maritime", "list", "--type", "vessels", "--json"])
        assert res_vessels.exit_code == 0
        d_vessels = json.loads(res_vessels.output)
        assert d_vessels["ok"] is True
        assert "vessels" in d_vessels

        res_cont = runner.invoke(self.app, ["maritime", "list", "--type", "containers", "--json"])
        assert res_cont.exit_code == 0
        d_cont = json.loads(res_cont.output)
        assert d_cont["ok"] is True
        assert "containers" in d_cont


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestMaritimeMcpParity:
    """Test FastMCP and fallback pure JSON-RPC tool parity for maritime tools."""

    def test_fastmcp_handlers_exist(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_maritime_vessel")
        assert hasattr(server, "_handle_maritime_container")
        assert hasattr(server, "_handle_maritime_tariff")
        assert hasattr(server, "_handle_maritime_manifest")
        assert hasattr(server, "_handle_maritime_list")
        assert hasattr(server, "_handle_maritime_status")

    def test_scripts_mcp_handlers_wired(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected = [
            "mekong_maritime_vessel",
            "mekong_maritime_container",
            "mekong_maritime_tariff",
            "mekong_maritime_manifest",
            "mekong_maritime_list",
            "mekong_maritime_status",
        ]
        for name in expected:
            assert name in tool_names, f"{name} must be in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"{name} must be in CORE_HANDLERS"

    def test_pure_json_rpc_invocation(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        handler = CORE_HANDLERS["mekong_maritime_vessel"]
        raw = handler({
            "name": "CMA CGM ANTOINE DE SAINT EXUPERY",
            "imo": "IMO9776418",
            "flag": "France",
            "dwt": 217672.0,
            "grt": 219277.0,
            "loa": 400.0,
            "draft": 16.0,
            "port_code": "VNVUT",
            "terminal": "Cái Mép Gemalink",
            "eta": "2026-10-01 06:00",
            "etd": "2026-10-02 18:00",
        })
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["vessel_name"] == "CMA CGM ANTOINE DE SAINT EXUPERY"
        assert res["vessel_specs"]["is_deep_water_capable"] is True

        c_handler = CORE_HANDLERS["mekong_maritime_container"]
        c_raw = c_handler({
            "container_no": "CMAU7654321",
            "container_type": "40HC",
            "gross_weight": 27000.0,
            "seal": "VN-SEAL-88",
            "booking_or_bl": "BKG-CMACGM-01",
        })
        c_res = json.loads(c_raw)
        assert c_res["ok"] is True
        assert c_res["container_no"] == "CMAU7654321"
