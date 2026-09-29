# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Telecommunications, Radio Spectrum & OTT Services Engine (Phase 62)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.telecom_engine import (
    SPECTRUM_BANDS,
    OTT_SERVICE_CATEGORIES,
    MAX_PERMISSIBLE_EMF_W_PER_M2,
    VND_PER_USD,
    TelecomEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestTelecomCoreBoundary:
    """Ensure TelecomEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/telecom_engine.py")
        assert source_path.exists(), "telecom_engine.py must exist"

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


class TestTelecomEngine:
    """Test TelecomEngine spectrum valuations, OTT audits, BTS EMF safety, and numbering resources."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> TelecomEngine:
        db_file = tmp_path / "test_telecom.db"
        return TelecomEngine(db_path=db_file)

    def test_constants_and_spectrum_bands(self) -> None:
        assert "B7_2600" in SPECTRUM_BANDS
        assert "C2_3700" in SPECTRUM_BANDS
        assert "C3_3800" in SPECTRUM_BANDS
        assert "N28_700" in SPECTRUM_BANDS
        assert "B3_1800" in SPECTRUM_BANDS

        assert SPECTRUM_BANDS["B7_2600"]["bandwidth_mhz"] == 100.0
        assert SPECTRUM_BANDS["C2_3700"]["tech"] == "5G_NR"
        assert SPECTRUM_BANDS["C2_3700"]["min_bts_2yr"] == 3000
        assert SPECTRUM_BANDS["C2_3700"]["coverage_target_5yr_pct"] == 85.0

        assert "OTT_MESSAGING_VOICE" in OTT_SERVICE_CATEGORIES
        assert OTT_SERVICE_CATEGORIES["OTT_MESSAGING_VOICE"]["requires_kyc"] is True
        assert OTT_SERVICE_CATEGORIES["OTT_MESSAGING_VOICE"]["e2ee_compliance"] is True
        assert MAX_PERMISSIBLE_EMF_W_PER_M2 == 2.0

    def test_calculate_spectrum_auction_valuation(self, engine: TelecomEngine) -> None:
        # Band C2_3700 for 15 years with 10% deposit
        res = engine.calculate_spectrum_auction_valuation(
            band_code="C2_3700",
            license_years=15,
            deposit_pct=10.0,
        )
        assert res["ok"] is True
        assert res["auction_id"].startswith("SPEC-")
        assert res["spectrum_band"]["band_code"] == "C2_3700"
        assert res["spectrum_band"]["technology"] == "5G_NR"
        assert res["spectrum_band"]["license_tenure_years"] == 15

        fin = res["financial_valuation_vnd"]
        assert fin["reserve_starting_price_vnd"] == 3_800_000_000_000.0
        assert fin["deposit_percentage"] == 10.0
        assert fin["required_deposit_vnd"] == 380_000_000_000.0
        assert fin["annualized_spectrum_fee_vnd"] == round(3_800_000_000_000.0 / 15)

        rollout = res["network_rollout_commitments"]
        assert rollout["min_5g_bts_after_2yr"] == 3000
        assert rollout["population_coverage_target_5yr_pct"] == 85.0

    def test_calculate_spectrum_auction_custom_and_bounds(self, engine: TelecomEngine) -> None:
        # Deposit capped between 5% and 20%
        res_low = engine.calculate_spectrum_auction_valuation(
            band_code="B7_2600",
            license_years=10,
            deposit_pct=2.0,  # Below minimum 5% -> bounds to 5.0%
        )
        assert res_low["financial_valuation_vnd"]["deposit_percentage"] == 5.0

        res_high = engine.calculate_spectrum_auction_valuation(
            band_code="B7_2600",
            license_years=15,
            deposit_pct=25.0,  # Above maximum 20% -> bounds to 20.0%
            custom_reserve_price_vnd=4_000_000_000_000.0,
        )
        assert res_high["financial_valuation_vnd"]["deposit_percentage"] == 20.0
        assert res_high["financial_valuation_vnd"]["reserve_starting_price_vnd"] == 4_000_000_000_000.0

    def test_audit_ott_service_compliance_compliant(self, engine: TelecomEngine) -> None:
        res = engine.audit_ott_service_compliance(
            service_name="Zalo Messaging & Voice",
            provider_name="VNG Corporation",
            service_category="OTT_MESSAGING_VOICE",
            registered_users=75_000_000,
            has_kyc_verification=True,
            has_encryption_e2ee=True,
            has_local_data_storage=True,
            has_vnta_notification=True,
            has_consumer_dispute_system=True,
        )
        assert res["ok"] is True
        assert res["audit_id"].startswith("OTT-")
        assert res["service_profile"]["service_name"] == "Zalo Messaging & Voice"
        assert res["compliance_evaluation"]["compliance_score"] == 100.0
        assert res["compliance_evaluation"]["compliance_status"] == "COMPLIANT_APPROVED"
        assert len(res["compliance_evaluation"]["identified_gaps"]) == 0

    def test_audit_ott_service_compliance_non_compliant(self, engine: TelecomEngine) -> None:
        res = engine.audit_ott_service_compliance(
            service_name="Foreign Unknown Chat",
            provider_name="Anonymous Ltd",
            service_category="OTT_MESSAGING_VOICE",
            registered_users=500_000,
            has_kyc_verification=False,
            has_encryption_e2ee=False,
            has_local_data_storage=False,
            has_vnta_notification=False,
            has_consumer_dispute_system=False,
        )
        assert res["ok"] is True
        assert res["compliance_evaluation"]["compliance_score"] == 0.0
        assert res["compliance_evaluation"]["compliance_status"] == "NON_COMPLIANT_REJECTED"
        assert len(res["compliance_evaluation"]["identified_gaps"]) == 5
        assert len(res["compliance_evaluation"]["corrective_actions"]) == 5

    def test_evaluate_bts_emf_safety(self, engine: TelecomEngine) -> None:
        # Safe BTS station: Power 80W, Gain 18 dBi, Distance 25m
        res = engine.evaluate_bts_emf_safety(
            station_id="BTS-Q1-SGN-01",
            location="Phường Bến Nghé, Quận 1, TP.HCM",
            antenna_height_m=35.0,
            transmit_power_watts=80.0,
            frequency_mhz=2600.0,
            antenna_gain_dbi=18.0,
            distance_residential_m=25.0,
        )
        assert res["ok"] is True
        assert res["evaluation_id"].startswith("BTS-")
        assert res["bts_station"]["station_id"] == "BTS-Q1-SGN-01"
        assert res["bts_station"]["transmit_power_watts"] == 80.0

        emf = res["emf_exposure_assessment"]
        assert emf["distance_to_residence_meters"] == 25.0
        assert emf["max_permissible_limit_w_per_m2"] == 2.0
        assert emf["calculated_power_density_w_per_m2"] > 0.0
        assert emf["is_emf_safety_compliant"] is True
        assert res["standards_compliance"]["compliance_status"] == "SAFETY_CERTIFIED"

    def test_evaluate_bts_emf_safety_excessive_radiation(self, engine: TelecomEngine) -> None:
        # Excessive radiation scenario: High power 500W, High gain 24 dBi, very close distance 3m
        res = engine.evaluate_bts_emf_safety(
            station_id="BTS-OVERPOWER-09",
            location="Industrial Zone",
            antenna_height_m=10.0,
            transmit_power_watts=500.0,
            frequency_mhz=2600.0,
            antenna_gain_dbi=24.0,
            distance_residential_m=3.0,
        )
        assert res["ok"] is True
        emf = res["emf_exposure_assessment"]
        assert emf["calculated_power_density_w_per_m2"] > 2.0
        assert emf["is_emf_safety_compliant"] is False
        assert res["standards_compliance"]["compliance_status"] == "EXCEEDS_PERMISSIBLE_EMF_LIMIT"

    def test_allocate_numbering_resource_hotline_and_mobile(self, engine: TelecomEngine) -> None:
        # 1900 premium hotline allocation
        res_1900 = engine.allocate_numbering_resource(
            number_prefix="1900-8888",
            assigned_operator="Vietnamese Enterprise",
            service_purpose="CUSTOMER_CARE_HOTLINE",
        )
        assert res_1900["ok"] is True
        assert res_1900["resource_id"].startswith("NUM-")
        assert res_1900["numbering_plan"]["prefix_or_number"] == "1900-8888"
        assert res_1900["numbering_plan"]["allocated_block_size"] == 1
        assert res_1900["regulatory_fees_vnd"]["unit_fee_per_number_monthly_vnd"] == 500_000.0
        assert res_1900["regulatory_fees_vnd"]["total_monthly_maintenance_fee_vnd"] == 500_000.0

        # 1800 toll-free hotline allocation
        res_1800 = engine.allocate_numbering_resource(
            number_prefix="1800-6666",
            assigned_operator="National Bank",
            service_purpose="TOLL_FREE_HOTLINE",
        )
        assert res_1800["regulatory_fees_vnd"]["unit_fee_per_number_monthly_vnd"] == 300_000.0

        # Mobile block: 100,000 numbers
        res_mobile = engine.allocate_numbering_resource(
            number_prefix="098-BLOCK",
            assigned_operator="Viettel Telecom",
            block_size=100_000,
            service_purpose="MOBILE_SUBSCRIBER",
        )
        assert res_mobile["numbering_plan"]["allocated_block_size"] == 100_000
        assert res_mobile["regulatory_fees_vnd"]["unit_fee_per_number_monthly_vnd"] == 50.0
        assert res_mobile["regulatory_fees_vnd"]["total_monthly_maintenance_fee_vnd"] == 5_000_000.0

    def test_telecom_lists_and_status(self, engine: TelecomEngine) -> None:
        engine.calculate_spectrum_auction_valuation(band_code="B7_2600")
        engine.audit_ott_service_compliance(service_name="TestChat", provider_name="TestCorp")
        engine.evaluate_bts_emf_safety(station_id="BTS-01", location="Hanoi")
        engine.allocate_numbering_resource(number_prefix="1900-1111", assigned_operator="Telco")

        auctions = engine.list_spectrum_auctions()
        assert len(auctions) == 1
        assert auctions[0]["band_code"] == "B7_2600"

        audits = engine.list_ott_audits()
        assert len(audits) == 1
        assert audits[0]["service_name"] == "TestChat"

        bts_list = engine.list_bts_evaluations()
        assert len(bts_list) == 1
        assert bts_list[0]["station_id"] == "BTS-01"

        numbers = engine.list_numbering_resources()
        assert len(numbers) == 1
        assert numbers[0]["number_prefix"] == "1900-1111"

        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "TelecomEngine"
        assert status["metrics"]["spectrum_auctions_conducted"] == 1
        assert status["metrics"]["ott_services_audited"] == 1
        assert status["metrics"]["bts_stations_evaluated"] == 1
        assert status["metrics"]["numbering_allocations_count"] == 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestTelecomCLI:
    """Test Typer CLI surface for mekong telecom commands."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_telecom_root_callback_console_and_json(self, app) -> None:
        # Console mode
        res = runner.invoke(app, ["telecom"])
        assert res.exit_code == 0
        assert "HỆ THỐNG QUẢN TRỊ VIỄN THÔNG" in res.output or "Vietnam Telecommunications" in res.output

        # JSON mode
        res_json = runner.invoke(app, ["telecom", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["engine"] == "TelecomEngine"
        assert "metrics" in data

    def test_telecom_spectrum_cmd(self, app) -> None:
        # Console mode
        res = runner.invoke(app, ["telecom", "spectrum", "B7_2600", "--years", "15", "--deposit", "10.0"])
        assert res.exit_code == 0
        assert "PHƯƠNG ÁN ĐẤU GIÁ QUYỀN SỬ DỤNG BĂNG TẦN" in res.output

        # JSON mode
        res_json = runner.invoke(app, ["telecom", "spectrum", "C2_3700", "--years", "15", "--deposit", "12.0", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["spectrum_band"]["band_code"] == "C2_3700"
        assert data["financial_valuation_vnd"]["deposit_percentage"] == 12.0

    def test_telecom_ott_cmd(self, app) -> None:
        # Console mode
        res = runner.invoke(
            app,
            [
                "telecom",
                "ott",
                "Zalo Messaging",
                "VNG Corporation",
                "--users",
                "75000000",
                "--features",
                "MESSAGING,VOIP",
                "--kyc",
                "--encryption",
                "--vnta-notify",
                "--local-data",
            ],
        )
        assert res.exit_code == 0
        assert "THẨM ĐỊNH TUÂN THỦ DỊCH VỤ" in res.output

        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "telecom",
                "ott",
                "GlobalChat",
                "GlobalTech",
                "--users",
                "2000000",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["service_profile"]["service_name"] == "GlobalChat"

    def test_telecom_bts_cmd(self, app) -> None:
        # Console mode
        res = runner.invoke(
            app,
            [
                "telecom",
                "bts",
                "BTS-D1-SGN-01",
                "Ben Nghe, District 1, HCMC",
                "--power",
                "80.0",
                "--gain",
                "18.0",
                "--height",
                "35.0",
                "--distance",
                "25.0",
            ],
        )
        assert res.exit_code == 0
        assert "KIỂM ĐỊNH AN TOÀN" in res.output and "BỨC XẠ ĐIỆN TỪ TRẠM BTS" in res.output

        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "telecom",
                "bts",
                "BTS-HN-02",
                "Cau Giay, Hanoi",
                "--power",
                "100.0",
                "--gain",
                "20.0",
                "--distance",
                "30.0",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["bts_station"]["station_id"] == "BTS-HN-02"

    def test_telecom_number_cmd(self, app) -> None:
        # Console mode
        res = runner.invoke(
            app,
            [
                "telecom",
                "number",
                "1900-9999",
                "Viet Enterprise",
                "CUSTOMER_CARE",
                "--size",
                "1",
            ],
        )
        assert res.exit_code == 0
        assert "PHÂN BỔ TÀI NGUYÊN KHO SỐ VIỄN THÔNG" in res.output

        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "telecom",
                "number",
                "098-BLOCK",
                "Viettel",
                "MOBILE_SUBSCRIBER",
                "--size",
                "500000",
                "--unit-fee",
                "50.0",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert data["numbering_plan"]["prefix_or_number"] == "098-BLOCK"

    def test_telecom_list_cmd(self, app) -> None:
        res = runner.invoke(app, ["telecom", "list", "spectrum"])
        assert res.exit_code == 0
        assert "Danh mục Phương án Đấu giá" in res.output

        res_ott = runner.invoke(app, ["telecom", "list", "ott", "--json"])
        assert res_ott.exit_code == 0
        data_ott = json.loads(res_ott.output)
        assert data_ott["ok"] is True
        assert "ott_audits" in data_ott

        res_bts = runner.invoke(app, ["telecom", "list", "bts", "--json"])
        assert res_bts.exit_code == 0
        data_bts = json.loads(res_bts.output)
        assert data_bts["ok"] is True
        assert "bts_evals" in data_bts

        res_num = runner.invoke(app, ["telecom", "list", "numbers", "--json"])
        assert res_num.exit_code == 0
        data_num = json.loads(res_num.output)
        assert data_num["ok"] is True
        assert "numbers" in data_num

    def test_telecom_status_cmd(self, app) -> None:
        res = runner.invoke(app, ["telecom", "status"])
        assert res.exit_code == 0
        assert "CHỈ SỐ ĐIỀU HÀNH HẠ TẦNG VIỄN THÔNG" in res.output

        res_json = runner.invoke(app, ["telecom", "status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Tool & Server Parity Tests
# ---------------------------------------------------------------------------


class TestTelecomMCPIntegration:
    """Test MCP tool registration and JSON-RPC dispatch for telecom tools."""

    def test_src_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Spectrum
        res_spec = json.loads(server._handle_telecom_spectrum(band_code="B7_2600"))
        assert res_spec["ok"] is True
        assert res_spec["spectrum_band"]["band_code"] == "B7_2600"

        # OTT
        res_ott = json.loads(server._handle_telecom_ott(service_name="Zalo MCP", provider_name="VNG"))
        assert res_ott["ok"] is True
        assert res_ott["service_profile"]["service_name"] == "Zalo MCP"

        # BTS
        res_bts = json.loads(server._handle_telecom_bts(station_id="BTS-MCP-01", location="HCMC"))
        assert res_bts["ok"] is True
        assert res_bts["bts_station"]["station_id"] == "BTS-MCP-01"

        # Number
        res_num = json.loads(server._handle_telecom_number(number_prefix="1900-5555", assigned_operator="Enterprise"))
        assert res_num["ok"] is True
        assert res_num["numbering_plan"]["prefix_or_number"] == "1900-5555"

        # List & Status
        res_list = json.loads(server._handle_telecom_list(item_type="spectrum"))
        assert isinstance(res_list, list)

        res_stat = json.loads(server._handle_telecom_status())
        assert res_stat["ok"] is True
        assert "metrics" in res_stat

    def test_scripts_mcp_server_handlers(self) -> None:
        import scripts.mcp_server as script_mcp

        # Spectrum
        res_spec = json.loads(script_mcp.handle_telecom_spectrum({"band_code": "C2_3700"}))
        assert res_spec["ok"] is True

        # OTT
        res_ott = json.loads(script_mcp.handle_telecom_ott({"service_name": "App", "provider_name": "Corp"}))
        assert res_ott["ok"] is True

        # BTS
        res_bts = json.loads(script_mcp.handle_telecom_bts({"station_id": "BTS-S01", "location": "Danang"}))
        assert res_bts["ok"] is True

        # Number
        res_num = json.loads(script_mcp.handle_telecom_number({"number_prefix": "1800-8888", "assigned_operator": "Telco"}))
        assert res_num["ok"] is True

        # List & Status
        res_list = json.loads(script_mcp.handle_telecom_list({"item_type": "ott"}))
        assert isinstance(res_list, list)

        res_stat = json.loads(script_mcp.handle_telecom_status({}))
        assert res_stat["ok"] is True

        # Check CORE_TOOLS_SPEC and CORE_HANDLERS
        spec_names = {t["name"] for t in script_mcp.CORE_TOOLS_SPEC}
        assert "mekong_telecom_spectrum" in spec_names
        assert "mekong_telecom_ott" in spec_names
        assert "mekong_telecom_bts" in spec_names
        assert "mekong_telecom_number" in spec_names
        assert "mekong_telecom_list" in spec_names
        assert "mekong_telecom_status" in spec_names

        assert "mekong_telecom_spectrum" in script_mcp.CORE_HANDLERS
        assert "mekong_telecom_ott" in script_mcp.CORE_HANDLERS
        assert "mekong_telecom_bts" in script_mcp.CORE_HANDLERS
        assert "mekong_telecom_number" in script_mcp.CORE_HANDLERS
        assert "mekong_telecom_list" in script_mcp.CORE_HANDLERS
        assert "mekong_telecom_status" in script_mcp.CORE_HANDLERS
