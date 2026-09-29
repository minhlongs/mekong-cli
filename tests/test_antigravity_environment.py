# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Environmental Protection, EIA & Carbon Credits Suite (Phase 81)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.environment_engine import (
    EPR_RECYCLING_RATES,
    GHG_MANDATORY_INVENTORY_THRESHOLD_TCO2E,
    GRID_ELECTRICITY_EMISSION_FACTOR_KG_CO2_PER_KWH,
    PROJECT_IMPACT_GROUPS,
    QCVN_THRESHOLDS,
    EnvironmentEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestEnvironmentCoreBoundary:
    """Ensure EnvironmentEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/environment_engine.py")
        assert source_path.exists(), "environment_engine.py must exist"

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


class TestEnvironmentEngine:
    """Test EnvironmentEngine EIA classification, GPMT, GHG carbon accounting, EPR & monitoring."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> EnvironmentEngine:
        db_file = tmp_path / "test_environment.db"
        return EnvironmentEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Project groups
        assert "GROUP_I" in PROJECT_IMPACT_GROUPS
        assert PROJECT_IMPACT_GROUPS["GROUP_I"]["requires_eia"] is True
        assert PROJECT_IMPACT_GROUPS["GROUP_I"]["requires_pre_eia"] is True
        assert PROJECT_IMPACT_GROUPS["GROUP_I"]["license_term_years"] == 7
        assert "GROUP_II" in PROJECT_IMPACT_GROUPS
        assert PROJECT_IMPACT_GROUPS["GROUP_II"]["requires_eia"] is True
        assert PROJECT_IMPACT_GROUPS["GROUP_II"]["requires_pre_eia"] is False
        assert PROJECT_IMPACT_GROUPS["GROUP_II"]["license_term_years"] == 10
        assert "GROUP_III" in PROJECT_IMPACT_GROUPS
        assert PROJECT_IMPACT_GROUPS["GROUP_III"]["requires_eia"] is False
        assert PROJECT_IMPACT_GROUPS["GROUP_IV"]["requires_license"] is False

        # EPR Recycling Rates
        assert "PACKAGING_PLASTIC_PET" in EPR_RECYCLING_RATES
        assert EPR_RECYCLING_RATES["PACKAGING_PLASTIC_PET"]["mandatory_rate_pct"] == 22.0
        assert EPR_RECYCLING_RATES["PACKAGING_PLASTIC_PET"]["vepf_cost_vnd_per_kg"] == 2150.0
        assert "PACKAGING_PAPER" in EPR_RECYCLING_RATES
        assert EPR_RECYCLING_RATES["PACKAGING_PAPER"]["mandatory_rate_pct"] == 20.0
        assert "BATTERIES" in EPR_RECYCLING_RATES
        assert EPR_RECYCLING_RATES["BATTERIES"]["mandatory_rate_pct"] == 12.0

        # GHG thresholds
        assert GHG_MANDATORY_INVENTORY_THRESHOLD_TCO2E == 3000.0
        assert GRID_ELECTRICITY_EMISSION_FACTOR_KG_CO2_PER_KWH == 0.7221

        # QCVN Thresholds
        assert QCVN_THRESHOLDS["WASTEWATER"]["COD_MAX_MG_L"] == 75.0
        assert QCVN_THRESHOLDS["EXHAUST"]["DUST_MAX_MG_NM3"] == 200.0

    def test_classify_project_impact_group_i(self, engine: EnvironmentEngine) -> None:
        res = engine.classify_project_impact(
            project_name="Nhà máy Nhiệt điện Mekong 1",
            investor_name="Tập đoàn Năng lượng Mekong",
            investment_capital_vnd=25_000_000_000_000.0,
            sector_type="THERMAL_POWER",
            location="Trà Vinh, Việt Nam",
            is_environmentally_sensitive=True,
            daily_capacity=1200.0,
            capacity_unit="MW",
        )
        assert res["impact_group"] == "GROUP_I"
        assert res["requires_pre_eia"] is True
        assert res["requires_eia"] is True
        assert res["requires_license"] is True
        assert "Bộ Tài nguyên và Môi trường" in res["licensing_authority"]

        projects = engine.list_projects()
        assert len(projects) == 1
        assert projects[0]["impact_group"] == "GROUP_I"

    def test_classify_project_impact_group_ii(self, engine: EnvironmentEngine) -> None:
        res = engine.classify_project_impact(
            project_name="Nhà máy Dệt Nhuộm Vải Mekong",
            investor_name="Công ty Dệt May Sài Gòn",
            investment_capital_vnd=150_000_000_000.0,
            sector_type="TEXTILE_DYEING",
            location="KCN Nhơn Trạch, Đồng Nai",
            is_environmentally_sensitive=False,
        )
        assert res["impact_group"] == "GROUP_II"
        assert res["requires_pre_eia"] is False
        assert res["requires_eia"] is True
        assert res["requires_license"] is True
        assert "Ủy ban nhân dân cấp tỉnh" in res["licensing_authority"]

    def test_classify_project_impact_group_iii_and_iv(self, engine: EnvironmentEngine) -> None:
        # Group III
        res_iii = engine.classify_project_impact(
            project_name="Xưởng Cơ khí Lắp ráp Nhỏ",
            investor_name="Hộ kinh doanh Minh Long",
            investment_capital_vnd=5_000_000_000.0,
            sector_type="ASSEMBLY",
            daily_capacity=10.0,
        )
        assert res_iii["impact_group"] == "GROUP_III"
        assert res_iii["requires_eia"] is False
        assert res_iii["requires_license"] is True

        # Group IV
        res_iv = engine.classify_project_impact(
            project_name="Văn phòng Công ty Phần mềm",
            investor_name="Mekong Tech",
            investment_capital_vnd=0.0,
            sector_type="SOFTWARE",
            daily_capacity=0.0,
        )
        assert res_iv["impact_group"] == "GROUP_IV"
        assert res_iv["requires_license"] is False

    def test_classify_project_invalid_inputs(self, engine: EnvironmentEngine) -> None:
        with pytest.raises(ValueError, match="Vốn đầu tư của dự án không được âm"):
            engine.classify_project_impact("Dự án Sai", "Chủ đầu tư", -100.0)

        with pytest.raises(ValueError, match="Công suất dự án không được âm"):
            engine.classify_project_impact("Dự án Sai", "Chủ đầu tư", 100.0, daily_capacity=-5.0)

    def test_issue_environmental_license_group_i_and_ii(self, engine: EnvironmentEngine) -> None:
        # Group I: 7 years
        res_i = engine.issue_environmental_license(
            facility_name="Tổ hợp Hóa chất Mekong",
            tax_id="0109988771",
            facility_address="KCN Phú Mỹ, BR-VT",
            impact_group="GROUP_I",
            max_wastewater_m3_day=2000.0,
            max_exhaust_m3_hour=50000.0,
            max_hazardous_waste_tons_year=50.0,
        )
        assert res_i["status"] == "ACTIVE"
        assert res_i["validity_years"] == 7
        assert res_i["license_id"].startswith("GPMT-")

        # Group II: 10 years
        res_ii = engine.issue_environmental_license(
            facility_name="Nhà máy Chế biến Thủy sản Mekong",
            tax_id="0308877662",
            facility_address="Cần Thơ, Việt Nam",
            impact_group="GROUP_II",
            max_wastewater_m3_day=600.0,
        )
        assert res_ii["validity_years"] == 10

        licenses = engine.list_licenses()
        assert len(licenses) == 2

    def test_issue_environmental_license_exempt_group_iv(self, engine: EnvironmentEngine) -> None:
        with pytest.raises(ValueError, match="thuộc diện miễn Giấy phép Môi trường"):
            engine.issue_environmental_license(
                facility_name="Cơ sở Không Ô Nhiễm",
                tax_id="0101112223",
                facility_address="Hà Nội",
                impact_group="GROUP_IV",
            )

    def test_audit_ghg_emissions_and_offsetting(self, engine: EnvironmentEngine) -> None:
        # Scope 1 = 1500 tCO2e, 4,000,000 kWh -> Scope 2 = 4,000,000 * 0.7221 / 1000 = 2,888.4 tCO2e
        # Scope 3 = 200 tCO2e -> Total = 4,588.4 tCO2e >= 3000 -> mandatory!
        # Quota = 4,000 tCO2e. Credits retired = 600 tCO2e -> Net = 4,588.4 - 600 = 3,988.4 <= 4,000 -> COMPLIANT
        res = engine.audit_ghg_emissions(
            facility_name="Nhà máy Xi măng Mekong",
            reporting_year=2026,
            scope1_fuel_tco2e=1500.0,
            electricity_kwh=4_000_000.0,
            scope3_indirect_tco2e=200.0,
            allocated_quota_tco2e=4000.0,
            carbon_credits_retired=600.0,
        )
        assert res["scope2_tco2e"] == 2888.4
        assert res["total_emissions_tco2e"] == 4588.4
        assert res["is_mandatory_reporting"] is True
        assert res["net_emissions_tco2e"] == 3988.4
        assert res["compliance_status"] == "COMPLIANT"

        # Exceeded quota
        res_exceeded = engine.audit_ghg_emissions(
            facility_name="Nhà máy Luyện Kim Ô Nhiễm",
            reporting_year=2026,
            scope1_fuel_tco2e=3000.0,
            electricity_kwh=2_000_000.0,
            scope3_indirect_tco2e=100.0,
            allocated_quota_tco2e=2000.0,
            carbon_credits_retired=0.0,
        )
        assert res_exceeded["compliance_status"] == "QUOTA_EXCEEDED"

    def test_calculate_epr_obligations_fulfilled_and_vepf_deficit(self, engine: EnvironmentEngine) -> None:
        # PET packaging: 22% rate, 2150 VND/kg
        # Volume = 100,000 kg -> required = 22,000 kg
        # Recycled = 22,000 kg -> deficit = 0 -> FULFILLED
        res_fulfilled = engine.calculate_epr_obligations(
            producer_name="Công ty Nước khoáng Tinh khiết",
            tax_id="0109988111",
            product_code="PACKAGING_PLASTIC_PET",
            total_volume_kg=100_000.0,
            actual_recycled_kg=22_000.0,
        )
        assert res_fulfilled["required_recycling_kg"] == 22_000.0
        assert res_fulfilled["deficit_kg"] == 0.0
        assert res_fulfilled["vepf_contribution_vnd"] == 0.0
        assert res_fulfilled["fulfillment_status"] == "FULFILLED"
        assert res_fulfilled["is_fully_recycled"] is True

        # Deficit: Recycled = 10,000 kg -> deficit = 12,000 kg -> VEPF = 12,000 * 2,150 = 25,800,000 VND
        res_deficit = engine.calculate_epr_obligations(
            producer_name="Công ty Bia Rượu Mekong",
            tax_id="0305544332",
            product_code="PACKAGING_PLASTIC_PET",
            total_volume_kg=100_000.0,
            actual_recycled_kg=10_000.0,
        )
        assert res_deficit["deficit_kg"] == 12_000.0
        assert res_deficit["vepf_contribution_vnd"] == 25_800_000.0
        assert res_deficit["fulfillment_status"] == "CONTRIBUTION_REQUIRED"
        assert res_deficit["is_fully_recycled"] is False

    def test_audit_monitoring_telemetry_wastewater_and_exhaust(self, engine: EnvironmentEngine) -> None:
        # Wastewater Compliant: pH 7.2, COD 50 (<= 75), TSS 30 (<= 50), Temp 35 (<= 40)
        res_ww = engine.audit_monitoring_telemetry(
            facility_name="Trạm XLNT KCN VSIP",
            monitoring_type="WASTEWATER",
            ph=7.2,
            cod_mg_l=50.0,
            tss_mg_l=30.0,
            temperature_c=35.0,
        )
        assert res_ww["is_compliant"] is True
        assert len(res_ww["violations"]) == 0

        # Wastewater Violation: COD = 120 mg/L (> 75)
        res_ww_viol = engine.audit_monitoring_telemetry(
            facility_name="Trạm XLNT KCN VSIP",
            monitoring_type="WASTEWATER",
            ph=7.2,
            cod_mg_l=120.0,
        )
        assert res_ww_viol["is_compliant"] is False
        assert len(res_ww_viol["violations"]) == 1

        # Exhaust Violation: Dust 350 mg/Nm3 (> 200)
        res_ex_viol = engine.audit_monitoring_telemetry(
            facility_name="Ống khói Lò hơi Mekong",
            monitoring_type="EXHAUST",
            dust_mg_nm3=350.0,
        )
        assert res_ex_viol["is_compliant"] is False
        assert len(res_ex_viol["violations"]) == 1

    def test_get_status_telemetry(self, engine: EnvironmentEngine) -> None:
        engine.classify_project_impact("Dự án A", "Chủ A", 500_000_000.0)
        engine.issue_environmental_license("Cơ sở B", "010011", "Hà Nội")
        engine.audit_ghg_emissions("Cơ sở B", electricity_kwh=1_000_000.0)
        engine.calculate_epr_obligations("Doanh nghiệp C", "030022")
        engine.audit_monitoring_telemetry("Trạm D")

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["engine"] == "EnvironmentEngine"
        assert status["project_classification"]["total_projects"] == 1
        assert status["environmental_licenses"]["total_issued"] == 1
        assert status["ghg_and_carbon"]["total_audits"] == 1
        assert status["extended_producer_responsibility"]["total_declarations"] == 1
        assert status["automated_monitoring"]["total_audits"] == 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestEnvironmentCli:
    """Test CLI commands for mekong environment."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_environment_root_json(self) -> None:
        result = runner.invoke(self.app, ["environment", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["engine"] == "EnvironmentEngine"
        assert data["status"] == "HEALTHY"

    def test_environment_root_panel(self) -> None:
        result = runner.invoke(self.app, ["environment"])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ BẢO VỆ MÔI TRƯỜNG" in result.output

    def test_environment_classify_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "environment",
                "classify",
                "Nhà máy Luyện thép Mekong",
                "Tập đoàn Thép Xanh",
                "800000000000",
                "--sector",
                "STEEL_METALLURGY",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["impact_group"] == "GROUP_I"
        assert data["requires_eia"] is True

    def test_environment_license_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "environment",
                "license",
                "Nhà máy Sữa Mekong",
                "0309988775",
                "KCN Sóng Thần, Bình Dương",
                "--group",
                "GROUP_II",
                "--wastewater",
                "600",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "ACTIVE"
        assert data["validity_years"] == 10

    def test_environment_ghg_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "environment",
                "ghg",
                "Tổ hợp Lọc hóa dầu Mekong",
                "--year",
                "2026",
                "--scope1",
                "2000",
                "--electricity",
                "5000000",
                "--offset-credits",
                "500",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_mandatory_reporting"] is True
        assert data["carbon_credits_offset"] == 500.0

    def test_environment_epr_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "environment",
                "epr",
                "Công ty Nước tinh khiết Mekong",
                "0309988443",
                "--product",
                "PACKAGING_PLASTIC_PET",
                "--volume",
                "200000",
                "--recycled",
                "20000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["mandatory_recycling_rate_pct"] == 22.0
        assert data["fulfillment_status"] == "CONTRIBUTION_REQUIRED"

    def test_environment_monitor_cli(self) -> None:
        res = runner.invoke(
            self.app,
            [
                "environment",
                "monitor",
                "Trạm Quan trắc Nước thải KCN",
                "--type",
                "WASTEWATER",
                "--ph",
                "7.5",
                "--cod",
                "60",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_compliant"] is True

    def test_environment_list_and_status_cli(self) -> None:
        res_list = runner.invoke(self.app, ["environment", "list", "--type", "projects", "--json"])
        assert res_list.exit_code == 0
        data_list = json.loads(res_list.output)
        assert isinstance(data_list, list)

        res_status = runner.invoke(self.app, ["environment", "status", "--json"])
        assert res_status.exit_code == 0
        data_status = json.loads(res_status.output)
        assert data_status["engine"] == "EnvironmentEngine"


# ---------------------------------------------------------------------------
# MCP Tool Parity Tests
# ---------------------------------------------------------------------------


class TestEnvironmentMcp:
    """Test MCP tool registration and handlers for both scripts/mcp_server.py and src/core/mcp_server.py."""

    def test_scripts_mcp_environment_tools(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        expected_tools = [
            "mekong_environment_classify",
            "mekong_environment_license",
            "mekong_environment_ghg",
            "mekong_environment_epr",
            "mekong_environment_monitor",
            "mekong_environment_list",
            "mekong_environment_status",
        ]

        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool {tool_name} must be in scripts CORE_TOOLS_SPEC"
            assert tool_name in CORE_HANDLERS, f"Tool {tool_name} must be in scripts CORE_HANDLERS"

        # Test execution through handler
        status_res = json.loads(CORE_HANDLERS["mekong_environment_status"]({}))
        assert status_res["status"] == "HEALTHY"
        assert status_res["engine"] == "EnvironmentEngine"

    def test_core_mcp_environment_tools(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_environment_classify")
        assert hasattr(server, "_handle_environment_license")
        assert hasattr(server, "_handle_environment_ghg")
        assert hasattr(server, "_handle_environment_epr")
        assert hasattr(server, "_handle_environment_monitor")
        assert hasattr(server, "_handle_environment_list")
        assert hasattr(server, "_handle_environment_status")

        # Test dispatch
        res_stat = json.loads(server._handle_environment_status())
        assert res_stat["engine"] == "EnvironmentEngine"
        assert res_stat["status"] == "HEALTHY"
