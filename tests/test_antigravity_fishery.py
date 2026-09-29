# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Fisheries, VMS Fleet Tracking & EU IUU Yellow Card Compliance (Phase 65)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.fishery_engine import (
    DESIGNATED_FISHING_PORTS,
    FISHING_SEA_ZONES,
    TARGET_SPECIES_STANDARDS,
    FisheryEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestFisheryCoreBoundary:
    """Ensure FisheryEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/fishery_engine.py")
        assert source_path.exists(), "fishery_engine.py must exist"

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


class TestFisheryEngine:
    """Test FisheryEngine vessel registration, VMS telemetry, eCDT catch certs, and HACCP quality audits."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> FisheryEngine:
        db_file = tmp_path / "test_fishery.db"
        return FisheryEngine(db_path=db_file)

    def test_constants_and_sea_zones(self) -> None:
        assert "TONKIN_GULF" in FISHING_SEA_ZONES
        assert "CENTRAL_WATERS" in FISHING_SEA_ZONES
        assert "SOUTHEAST_WATERS" in FISHING_SEA_ZONES
        assert "SOUTHWEST_GULF" in FISHING_SEA_ZONES

        assert "PORT_TAC_CAU" in DESIGNATED_FISHING_PORTS
        assert "PORT_QUY_NHON" in DESIGNATED_FISHING_PORTS
        assert "PORT_CAT_LO" in DESIGNATED_FISHING_PORTS

        assert "YELLOWFIN_TUNA" in TARGET_SPECIES_STANDARDS
        assert "WHITELEG_SHRIMP" in TARGET_SPECIES_STANDARDS
        assert "PANGASIUS" in TARGET_SPECIES_STANDARDS

    def test_register_fishing_vessel_vms_mandated_compliant(self, engine: FisheryEngine) -> None:
        # Lmax = 19.5m (>= 15m) with VMS installed -> Compliant and Approved
        res = engine.register_fishing_vessel(
            vessel_plate="VN-92345-TS",
            owner_name="Trần Văn Hải",
            home_port="PORT_TAC_CAU",
            length_meters=19.5,
            engine_power_hp=500.0,
            vms_device_id="VMS-KG-92345",
            assigned_zone="SOUTHWEST_GULF",
        )
        assert res["ok"] is True
        assert res["vessel_id"].startswith("VES-")
        sc = res["statutory_compliance"]
        assert sc["is_vms_mandated"] is True
        assert sc["is_vms_installed"] is True
        assert sc["is_license_approved"] is True
        assert sc["vms_compliance_verdict"] == "COMPLIANT_VMS_CERTIFIED"
        assert res["fishing_license"]["license_number"].startswith("GP-TS-")

    def test_register_fishing_vessel_vms_missing_non_compliant(self, engine: FisheryEngine) -> None:
        # Lmax = 18.0m (>= 15m) without VMS -> Denied under Decree 26/2019
        res = engine.register_fishing_vessel(
            vessel_plate="VN-98888-TS",
            owner_name="Lê Văn Vi Phạm",
            home_port="PORT_TAC_CAU",
            length_meters=18.0,
            engine_power_hp=420.0,
            vms_device_id=None,
        )
        sc = res["statutory_compliance"]
        assert sc["is_vms_mandated"] is True
        assert sc["is_vms_installed"] is False
        assert sc["is_license_approved"] is False
        assert sc["vms_compliance_verdict"] == "NON_COMPLIANT_VMS_MISSING"
        assert res["fishing_license"]["license_number"] == "REVOKED_OR_DENIED"

    def test_register_small_boat_vms_optional(self, engine: FisheryEngine) -> None:
        # Lmax = 12.0m (< 15m) without VMS -> VMS not mandated, license approved
        res = engine.register_fishing_vessel(
            vessel_plate="VN-51234-TS",
            owner_name="Phạm Văn Nhỏ",
            length_meters=12.0,
            vms_device_id=None,
        )
        sc = res["statutory_compliance"]
        assert sc["is_vms_mandated"] is False
        assert sc["is_license_approved"] is True

    def test_track_vms_telemetry_normal(self, engine: FisheryEngine) -> None:
        # Coordinates inside Southwest Gulf: 9.2N, 103.8E
        res = engine.track_vms_telemetry(
            vessel_plate="VN-92345-TS",
            latitude=9.2,
            longitude=103.8,
            speed_knots=8.0,
            heading_degrees=140.0,
            is_signal_active=True,
            disconnection_hours=0.0,
            assigned_zone="SOUTHWEST_GULF",
        )
        assert res["ok"] is True
        assert res["log_id"].startswith("VMS-")
        vi = res["vms_integrity"]
        assert vi["is_boundary_violation"] is False
        assert vi["disconnection_alert"] is False
        assert res["iuu_compliance_verdict"]["risk_level"] == "LOW_RISK_NORMAL_OPERATIONS"
        assert res["iuu_compliance_verdict"]["is_iuu_flagged"] is False

    def test_track_vms_telemetry_border_crossing(self, engine: FisheryEngine) -> None:
        # Coordinates outside Southwest Gulf (e.g. 5.0N, 108.0E) -> boundary violation
        res = engine.track_vms_telemetry(
            vessel_plate="VN-92345-TS",
            latitude=5.0,
            longitude=108.0,
            assigned_zone="SOUTHWEST_GULF",
        )
        vi = res["vms_integrity"]
        assert vi["is_boundary_violation"] is True
        ic = res["iuu_compliance_verdict"]
        assert ic["risk_level"] == "CRITICAL_BORDER_CROSSING_VIOLATION"
        assert ic["is_iuu_flagged"] is True

    def test_track_vms_telemetry_disconnection(self, engine: FisheryEngine) -> None:
        # Disconnection 8 hours on sea (> 6 hours alert)
        res = engine.track_vms_telemetry(
            vessel_plate="VN-92345-TS",
            latitude=9.2,
            longitude=103.8,
            is_signal_active=False,
            disconnection_hours=8.0,
            assigned_zone="SOUTHWEST_GULF",
        )
        assert res["vms_integrity"]["disconnection_alert"] is True
        assert res["iuu_compliance_verdict"]["risk_level"] == "MEDIUM_RISK_VMS_SIGNAL_LOSS"
        assert res["iuu_compliance_verdict"]["is_iuu_flagged"] is True

    def test_issue_catch_certificate(self, engine: FisheryEngine) -> None:
        res = engine.issue_catch_certificate(
            vessel_plate="VN-92345-TS",
            species_code="YELLOWFIN_TUNA",
            catch_volume_kg=15000.0,
            landing_port="PORT_QUY_NHON",
            destination_market="EU_MARKET",
            certificate_type="CATCH_CERTIFICATE_CC",
        )
        assert res["ok"] is True
        assert res["certificate_id"].startswith("CC-VN-")
        assert res["ecdt_hash"].startswith("eCDT:")
        cb = res["catch_batch"]
        assert cb["species_name"] == "Cá ngừ vây vàng (Thunnus albacares)"
        assert cb["volume_tons"] == 15.0
        assert res["landing_and_export"]["is_designated_port"] is True
        assert res["iuu_clearance"]["is_iuu_cleared"] is True
        assert res["iuu_clearance"]["verdict"] == "IUU_VALIDATED_FOR_EXPORT"

    def test_audit_seafood_quality(self, engine: FisheryEngine) -> None:
        # Clean export batch (HACCP 96, zero chloramphenicol, zero nitrofurans)
        res_pass = engine.audit_seafood_quality(
            facility_eu_code="DL-482",
            facility_name="Minh Phu Seafood Corp",
            lot_number="LOT-2026-001",
            species_code="WHITELEG_SHRIMP",
            haccp_score=96.0,
            chloramphenicol_ppb=0.0,
            nitrofurans_ppb=0.0,
            heavy_metal_pass=True,
        )
        assert res_pass["ok"] is True
        assert res_pass["export_eligibility"]["is_export_eligible"] is True
        assert res_pass["export_eligibility"]["status"] == "APPROVED_FOR_GLOBAL_EXPORT"

        # Contaminated batch with Chloramphenicol 0.4 ppb (limit <= 0.1)
        res_fail = engine.audit_seafood_quality(
            facility_eu_code="DL-100",
            facility_name="Factory Contaminated",
            lot_number="LOT-2026-BAD",
            species_code="BLACK_TIGER_SHRIMP",
            haccp_score=75.0,
            chloramphenicol_ppb=0.4,
            nitrofurans_ppb=0.8,
            heavy_metal_pass=False,
        )
        assert res_fail["export_eligibility"]["is_export_eligible"] is False
        assert res_fail["export_eligibility"]["status"] == "REJECTED_ANTIBIOTIC_OR_HACCP_CONTAMINATION"

    def test_list_records_and_status(self, engine: FisheryEngine) -> None:
        engine.register_fishing_vessel(vessel_plate="VN-91111-TS", owner_name="Owner A", vms_device_id="VMS-01")
        engine.track_vms_telemetry(vessel_plate="VN-91111-TS", latitude=9.2, longitude=103.8)
        engine.issue_catch_certificate(vessel_plate="VN-91111-TS", catch_volume_kg=5000.0)
        engine.audit_seafood_quality(facility_eu_code="DL-01", facility_name="Plant 01", lot_number="LOT-01")

        vessels = engine.list_fishing_vessels()
        vms = engine.list_vms_telemetry()
        certs = engine.list_catch_certificates()
        audits = engine.list_seafood_quality_audits()

        assert len(vessels) == 1
        assert len(vms) == 1
        assert len(certs) == 1
        assert len(audits) == 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["metrics"]["registered_vessels_count"] == 1
        assert status["metrics"]["vms_telemetry_events"] == 1
        assert status["metrics"]["catch_certificates_issued"] == 1
        assert status["metrics"]["seafood_quality_audits_logged"] == 1


# ---------------------------------------------------------------------------
# CLI Surface Tests
# ---------------------------------------------------------------------------


class TestFisheryCLI:
    """Test CLI commands for fishery."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_fishery_status(self) -> None:
        res = runner.invoke(self.app, ["fishery", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "metrics" in data

    def test_cli_fishery_vessel_json(self) -> None:
        res = runner.invoke(self.app, [
            "fishery", "vessel", "VN-99999-TS", "Võ Văn Thuyền",
            "--port", "PORT_TAC_CAU",
            "--length", "21.0",
            "--power", "600",
            "--vms", "VMS-KG-99999",
            "--zone", "SOUTHWEST_GULF",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["statutory_compliance"]["is_license_approved"] is True

    def test_cli_fishery_vessel_console(self) -> None:
        res = runner.invoke(self.app, [
            "fishery", "vessel", "VN-88888-TS", "Hoàng Văn Ngư",
            "--length", "17.5",
            "--vms", "VMS-88888",
        ])
        assert res.exit_code == 0
        assert "Đăng Ký Tàu Cá" in res.output

    def test_cli_fishery_vms(self) -> None:
        res = runner.invoke(self.app, [
            "fishery", "vms", "VN-99999-TS", "9.5", "103.5",
            "--speed", "9.0",
            "--heading", "120",
            "--zone", "SOUTHWEST_GULF",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["vms_integrity"]["is_boundary_violation"] is False

    def test_cli_fishery_cert(self) -> None:
        res = runner.invoke(self.app, [
            "fishery", "cert", "VN-99999-TS",
            "--species", "YELLOWFIN_TUNA",
            "--volume", "18000",
            "--port", "PORT_QUY_NHON",
            "--market", "EU_MARKET",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["iuu_clearance"]["is_iuu_cleared"] is True

    def test_cli_fishery_quality(self) -> None:
        res = runner.invoke(self.app, [
            "fishery", "quality", "DL-500", "Soc Trang Seafood", "LOT-999",
            "--species", "WHITELEG_SHRIMP",
            "--haccp", "98.0",
            "--chloramphenicol", "0.0",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["export_eligibility"]["is_export_eligible"] is True

    def test_cli_fishery_list(self) -> None:
        res_v = runner.invoke(self.app, ["fishery", "list", "vessels", "--json"])
        assert res_v.exit_code == 0
        data_v = json.loads(res_v.output)
        assert data_v["ok"] is True
        assert "vessels" in data_v

        res_c = runner.invoke(self.app, ["fishery", "list", "--type", "certs", "--json"])
        assert res_c.exit_code == 0
        data_c = json.loads(res_c.output)
        assert data_c["ok"] is True
        assert "certs" in data_c


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestFisheryMCPIntegration:
    """Ensure FastMCP and JSON-RPC fallback handlers execute identically."""

    def test_fastmcp_core_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. Vessel
        v_res = json.loads(server._handle_fishery_vessel(
            vessel_plate="VN-77777-TS",
            owner_name="Đặng Văn Biển",
            length_meters=20.0,
            vms_device_id="VMS-777",
        ))
        assert v_res["ok"] is True

        # 2. VMS
        m_res = json.loads(server._handle_fishery_vms(
            vessel_plate="VN-77777-TS",
            latitude=9.5,
            longitude=104.0,
            assigned_zone="SOUTHWEST_GULF",
        ))
        assert m_res["ok"] is True

        # 3. Cert
        c_res = json.loads(server._handle_fishery_cert(
            vessel_plate="VN-77777-TS",
            species_code="YELLOWFIN_TUNA",
            catch_volume_kg=10000.0,
        ))
        assert c_res["ok"] is True

        # 4. Quality
        q_res = json.loads(server._handle_fishery_quality(
            facility_eu_code="DL-222",
            facility_name="Seafood Corp 222",
            lot_number="LOT-222",
        ))
        assert q_res["ok"] is True

        # 5. List & Status
        l_res = json.loads(server._handle_fishery_list(item_type="vessels"))
        assert isinstance(l_res, list)

        s_res = json.loads(server._handle_fishery_status())
        assert s_res["ok"] is True

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as smcp

        # Vessel
        v_res = json.loads(smcp.handle_fishery_vessel({
            "vessel_plate": "VN-66666-TS",
            "owner_name": "Ngô Văn Hải",
            "length_meters": 19.0,
            "vms_device_id": "VMS-666",
        }))
        assert v_res["ok"] is True

        # VMS
        m_res = json.loads(smcp.handle_fishery_vms({
            "vessel_plate": "VN-66666-TS",
            "latitude": 9.3,
            "longitude": 103.7,
            "assigned_zone": "SOUTHWEST_GULF",
        }))
        assert m_res["ok"] is True

        # Cert
        c_res = json.loads(smcp.handle_fishery_cert({
            "vessel_plate": "VN-66666-TS",
            "species_code": "WHITELEG_SHRIMP",
            "catch_volume_kg": 8000.0,
        }))
        assert c_res["ok"] is True

        # Quality
        q_res = json.loads(smcp.handle_fishery_quality({
            "facility_eu_code": "DL-333",
            "facility_name": "Seafood Corp 333",
            "lot_number": "LOT-333",
        }))
        assert q_res["ok"] is True

        # List & Status
        l_res = json.loads(smcp.handle_fishery_list({"item_type": "certs"}))
        assert isinstance(l_res, list)

        s_res = json.loads(smcp.handle_fishery_status({}))
        assert s_res["ok"] is True
