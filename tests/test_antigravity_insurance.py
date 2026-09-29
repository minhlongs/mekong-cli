# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Insurance Business, Actuarial Solvency & Underwriting Suite (Phase 77)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.insurance_engine import (
    INSURANCE_LICENSE_TYPES,
    INSURANCE_PRODUCT_LINES,
    SOLVENCY_STATUSES,
    InsuranceEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestInsuranceCoreBoundary:
    """Ensure InsuranceEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/insurance_engine.py")
        assert source_path.exists(), "insurance_engine.py must exist"

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


class TestInsuranceEngine:
    """Test InsuranceEngine licensing, underwriting, solvency margins, claims, and actuarial reserves."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> InsuranceEngine:
        db_file = tmp_path / "test_insurance.db"
        return InsuranceEngine(db_path=db_file)

    def test_statutory_constants(self) -> None:
        # Insurance License Configs under Law on Insurance Business 2022 & Decree 46/2023/NĐ-CP
        assert "NON_LIFE_INSURANCE" in INSURANCE_LICENSE_TYPES
        assert INSURANCE_LICENSE_TYPES["NON_LIFE_INSURANCE"]["min_capital_vnd"] == 400_000_000_000.0
        assert "NON_LIFE_SPECIALTY" in INSURANCE_LICENSE_TYPES
        assert INSURANCE_LICENSE_TYPES["NON_LIFE_SPECIALTY"]["min_capital_vnd"] == 450_000_000_000.0
        assert "LIFE_INSURANCE" in INSURANCE_LICENSE_TYPES
        assert INSURANCE_LICENSE_TYPES["LIFE_INSURANCE"]["min_capital_vnd"] == 750_000_000_000.0
        assert "LIFE_UNIT_LINKED" in INSURANCE_LICENSE_TYPES
        assert INSURANCE_LICENSE_TYPES["LIFE_UNIT_LINKED"]["min_capital_vnd"] == 1_000_000_000_000.0
        assert "REINSURANCE" in INSURANCE_LICENSE_TYPES
        assert INSURANCE_LICENSE_TYPES["REINSURANCE"]["min_capital_vnd"] == 500_000_000_000.0
        assert "INSURANCE_BROKERAGE" in INSURANCE_LICENSE_TYPES
        assert INSURANCE_LICENSE_TYPES["INSURANCE_BROKERAGE"]["min_capital_vnd"] == 50_000_000_000.0

        # Insurance Product Lines
        assert "MOTOR_VEHICLE" in INSURANCE_PRODUCT_LINES
        assert "FIRE_EXPLOSION" in INSURANCE_PRODUCT_LINES
        assert "CARGO_MARINE" in INSURANCE_PRODUCT_LINES
        assert "HEALTH_ACCIDENT" in INSURANCE_PRODUCT_LINES
        assert "LIFE_TERM" in INSURANCE_PRODUCT_LINES
        assert "LIFE_ENDOWMENT" in INSURANCE_PRODUCT_LINES
        assert "LIFE_UNIT_LINKED" in INSURANCE_PRODUCT_LINES

        # Solvency Statuses
        assert "HEALTHY" in SOLVENCY_STATUSES
        assert "COMPLIANT" in SOLVENCY_STATUSES
        assert "WARNING_SUPERVISED" in SOLVENCY_STATUSES
        assert "INSOLVENT_ALERT" in SOLVENCY_STATUSES

    def test_issue_insurer_license_non_life_success(self, engine: InsuranceEngine) -> None:
        res = engine.issue_insurer_license(
            enterprise_name="Tổng Công ty Cổ phần Bảo hiểm Quân đội (MIC)",
            tax_id="0102456789",
            license_type="NON_LIFE_INSURANCE",
            charter_capital_vnd=500_000_000_000.0,
            legal_representative="Đinh Như Hạnh",
            head_office="Hà Nội",
        )
        assert res["status"] == "success"
        prof = res["license_profile"]
        assert prof["enterprise_name"] == "Tổng Công ty Cổ phần Bảo hiểm Quân đội (MIC)"
        assert prof["license_type"] == "NON_LIFE_INSURANCE"
        assert prof["charter_capital_vnd"] == 500_000_000_000.0
        assert prof["min_required_capital_vnd"] == 400_000_000_000.0
        assert prof["status"] == "ACTIVE"
        assert prof["license_number"].startswith("GP-BH-NON_-")

    def test_issue_insurer_license_life_unit_linked_success(self, engine: InsuranceEngine) -> None:
        res = engine.issue_insurer_license(
            enterprise_name="Công ty TNHH Bảo hiểm Nhân thọ Prudential Việt Nam",
            tax_id="0301234567",
            license_type="LIFE_UNIT_LINKED",
            charter_capital_vnd=1_200_000_000_000.0,
        )
        assert res["status"] == "success"
        prof = res["license_profile"]
        assert prof["license_type"] == "LIFE_UNIT_LINKED"
        assert prof["min_required_capital_vnd"] == 1_000_000_000_000.0
        assert prof["licensing_authority"] == "Bộ Tài chính"

    def test_issue_insurer_license_insufficient_capital(self, engine: InsuranceEngine) -> None:
        with pytest.raises(ValueError, match="Vốn điều lệ không đủ điều kiện"):
            # Non-life requires 400B, providing only 250B
            engine.issue_insurer_license(
                enterprise_name="Bảo hiểm Thiếu Vốn",
                tax_id="0109999888",
                license_type="NON_LIFE_INSURANCE",
                charter_capital_vnd=250_000_000_000.0,
            )

    def test_issue_insurer_license_invalid_type(self, engine: InsuranceEngine) -> None:
        with pytest.raises(ValueError, match="Loại giấy phép bảo hiểm không hợp lệ"):
            engine.issue_insurer_license(
                enterprise_name="Bảo hiểm Không Hợp Lệ",
                tax_id="0109999888",
                license_type="GALAXY_INSURANCE",
                charter_capital_vnd=1_000_000_000_000.0,
            )

    def test_underwrite_policy_motor_vehicle(self, engine: InsuranceEngine) -> None:
        res = engine.underwrite_policy(
            policyholder_name="Công ty TNHH Vận tải Mekong",
            product_line="MOTOR_VEHICLE",
            sum_insured_vnd=800_000_000.0,
            premium_vnd=12_000_000.0,
            deductible_vnd=1_000_000.0,
            term_months=12,
            start_date="2026-10-01",
        )
        assert res["status"] == "success"
        prof = res["policy_profile"]
        assert prof["policy_id"].startswith("POL-MOTO-")
        assert prof["category"] == "NON_LIFE"
        assert prof["sum_insured_vnd"] == 800_000_000.0
        assert prof["premium_vnd"] == 12_000_000.0
        assert prof["free_look_days"] == 0
        assert prof["status"] == "IN_FORCE"

    def test_underwrite_policy_life_with_free_look(self, engine: InsuranceEngine) -> None:
        res = engine.underwrite_policy(
            policyholder_name="Trần Thị Lan",
            product_line="LIFE_ENDOWMENT",
            sum_insured_vnd=2_000_000_000.0,
            premium_vnd=40_000_000.0,
            deductible_vnd=0.0,
            term_months=120,
            start_date="2026-10-01",
        )
        assert res["status"] == "success"
        prof = res["policy_profile"]
        assert prof["category"] == "LIFE"
        assert prof["free_look_days"] == 21
        assert prof["term_months"] == 120

    def test_underwrite_policy_invalid_inputs(self, engine: InsuranceEngine) -> None:
        with pytest.raises(ValueError, match="Nghiệp vụ bảo hiểm không hợp lệ"):
            engine.underwrite_policy(policyholder_name="Khách", product_line="CRYPTO_INSURANCE")

        with pytest.raises(ValueError, match="Số tiền bảo hiểm phải lớn hơn 0"):
            engine.underwrite_policy(policyholder_name="Khách", sum_insured_vnd=-1000.0)

        with pytest.raises(ValueError, match="Phí bảo hiểm phải lớn hơn 0"):
            engine.underwrite_policy(policyholder_name="Khách", premium_vnd=0.0)

        with pytest.raises(ValueError, match="Thời hạn hợp đồng bảo hiểm phải lớn hơn 0"):
            engine.underwrite_policy(policyholder_name="Khách", term_months=0)

    def test_audit_solvency_margin_healthy_non_life(self, engine: InsuranceEngine) -> None:
        # Min margin = max(25% of 2T, 16% of 1T) = max(500B, 160B) = 500B
        # Actual margin = 1,000B -> CAR = 1000/500 = 2.0 (200% >= 150% -> HEALTHY)
        res = engine.audit_solvency_margin(
            insurer_name="Bảo Việt Non-Life",
            actual_solvency_margin_vnd=1_000_000_000_000.0,
            net_premium_retained_vnd=2_000_000_000_000.0,
            avg_annual_claims_vnd=1_000_000_000_000.0,
            is_life=False,
        )
        assert res["status"] == "success"
        prof = res["solvency_profile"]
        assert prof["minimum_margin_vnd"] == 500_000_000_000.0
        assert prof["capital_adequacy_ratio"] == 2.0
        assert prof["solvency_status"] == "HEALTHY"
        assert prof["is_solvent"] is True

    def test_audit_solvency_margin_warning_supervised(self, engine: InsuranceEngine) -> None:
        # Min margin = 500B, Actual margin = 425B -> CAR = 0.85 (85% -> WARNING_SUPERVISED)
        res = engine.audit_solvency_margin(
            insurer_name="Bảo hiểm Rủi ro Cao",
            actual_solvency_margin_vnd=425_000_000_000.0,
            net_premium_retained_vnd=2_000_000_000_000.0,
            avg_annual_claims_vnd=1_000_000_000_000.0,
            is_life=False,
        )
        assert res["status"] == "success"
        prof = res["solvency_profile"]
        assert prof["solvency_status"] == "WARNING_SUPERVISED"
        assert prof["is_solvent"] is False

    def test_audit_solvency_margin_life(self, engine: InsuranceEngine) -> None:
        # Life: 4% of 10,000B + 0.1% of 50,000B = 400B + 50B = 450B
        # Actual margin = 675B -> CAR = 675/450 = 1.50 -> HEALTHY
        res = engine.audit_solvency_margin(
            insurer_name="Bảo Việt Life",
            actual_solvency_margin_vnd=675_000_000_000.0,
            mathematical_reserve_vnd=10_000_000_000_000.0,
            sum_at_risk_vnd=50_000_000_000_000.0,
            is_life=True,
        )
        assert res["status"] == "success"
        prof = res["solvency_profile"]
        assert prof["minimum_margin_vnd"] == 450_000_000_000.0
        assert prof["capital_adequacy_ratio"] == 1.50
        assert prof["solvency_status"] == "HEALTHY"

    def test_settle_claim_approved(self, engine: InsuranceEngine) -> None:
        # Underwrite policy first
        pol = engine.underwrite_policy(
            policyholder_name="Công ty Vận tải ABC",
            product_line="MOTOR_VEHICLE",
            deductible_vnd=2_000_000.0,
        )
        policy_id = pol["policy_id"]

        # Claim 30M, Deductible 2M -> Net settled 28M
        res = engine.settle_claim(
            policy_id=policy_id,
            incident_description="Xe va chạm tường rào gãy gương và móp cản trước",
            claimed_amount_vnd=30_000_000.0,
            damage_proof_verified=True,
            is_approved=True,
        )
        assert res["status"] == "success"
        prof = res["claim_profile"]
        assert prof["claimed_amount_vnd"] == 30_000_000.0
        assert prof["deductible_vnd"] == 2_000_000.0
        assert prof["net_settled_amount_vnd"] == 28_000_000.0
        assert prof["settlement_status"] == "SETTLED_APPROVED"

    def test_settle_claim_disapproved(self, engine: InsuranceEngine) -> None:
        res = engine.settle_claim(
            policy_id="POL-MV-9999",
            incident_description="Gian lận hồ sơ tổn thất",
            claimed_amount_vnd=50_000_000.0,
            damage_proof_verified=False,
            is_approved=False,
        )
        assert res["status"] == "success"
        prof = res["claim_profile"]
        assert prof["net_settled_amount_vnd"] == 0.0
        assert prof["settlement_status"] == "REJECTED_DISAPPROVED"

    def test_calculate_technical_reserves(self, engine: InsuranceEngine) -> None:
        # Written premium = 100B, UPR ratio = 0.40 -> UPR = 40B
        # OCR = 15B
        # IBNR = 5% of 100B = 5B
        # Total = 40 + 15 + 5 = 60B
        res = engine.calculate_technical_reserves(
            insurer_name="Bảo hiểm MIC",
            product_line="MOTOR_VEHICLE",
            written_premium_vnd=100_000_000_000.0,
            unearned_ratio=0.40,
            outstanding_claims_vnd=15_000_000_000.0,
            ibnr_rate=0.05,
        )
        assert res["status"] == "success"
        prof = res["reserve_profile"]
        assert prof["unearned_premium_reserve_vnd"] == 40_000_000_000.0
        assert prof["outstanding_claim_reserve_vnd"] == 15_000_000_000.0
        assert prof["ibnr_reserve_vnd"] == 5_000_000_000.0
        assert prof["total_reserves_vnd"] == 60_000_000_000.0

    def test_listing_apis(self, engine: InsuranceEngine) -> None:
        # Prepopulate
        engine.issue_insurer_license("Insurer List 1", "0108889991", "NON_LIFE_INSURANCE", 400_000_000_000.0)
        engine.underwrite_policy("Policyholder List 1", "FIRE_EXPLOSION")
        engine.audit_solvency_margin("Insurer List 1", 800_000_000_000.0)
        engine.settle_claim("POL-01", "Vụ việc test", 10_000_000.0)
        engine.calculate_technical_reserves("Insurer List 1", "FIRE_EXPLOSION")

        # Check listings
        licenses = engine.list_licenses(limit=10)
        assert len(licenses) >= 1
        assert len(licenses.data) >= 1

        policies = engine.list_policies(limit=10)
        assert len(policies) >= 1

        solvency_audits = engine.list_solvency_audits(limit=10)
        assert len(solvency_audits) >= 1

        claims = engine.list_claims(limit=10)
        assert len(claims) >= 1

        reserves = engine.list_reserves(limit=10)
        assert len(reserves) >= 1

    def test_get_status_metrics(self, engine: InsuranceEngine) -> None:
        engine.issue_insurer_license("Status Insurer", "0109998811", "NON_LIFE_INSURANCE", 450_000_000_000.0)
        engine.underwrite_policy("Khách Status", "MOTOR_VEHICLE", sum_insured_vnd=1_000_000_000.0, premium_vnd=20_000_000.0)
        engine.settle_claim("POL-01", "Tổn thất Status", 5_000_000.0, custom_deductible_vnd=1_000_000.0)
        engine.audit_solvency_margin("Status Insurer", 1_000_000_000_000.0)
        engine.calculate_technical_reserves("Status Insurer", "MOTOR_VEHICLE")

        status_data = engine.get_status()
        assert status_data["status"] == "online"
        metrics = status_data["metrics"]
        assert metrics["active_insurers"] >= 1
        assert metrics["in_force_policies"] >= 1
        assert metrics["total_sum_insured_vnd"] >= 1_000_000_000.0
        assert metrics["total_written_premium_vnd"] >= 20_000_000.0
        assert metrics["total_claims_processed"] >= 1
        assert metrics["total_claims_settled_vnd"] >= 4_000_000.0
        assert metrics["solvency_audits_count"] >= 1
        assert metrics["capital_compliant_insurers"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Integration Tests
# ---------------------------------------------------------------------------


class TestInsuranceCLI:
    """Ensure all Typer CLI commands run cleanly in console and --json modes."""

    @pytest.fixture
    def app(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        return build_app()

    def test_insurance_help(self, app) -> None:
        result = runner.invoke(app, ["insurance", "--help"])
        assert result.exit_code == 0
        assert "Insurance — Vietnamese Insurance" in result.output

    def test_insurance_main_callback(self, app) -> None:
        res_con = runner.invoke(app, ["insurance"])
        assert res_con.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ KINH DOANH BẢO HIỂM" in res_con.output

        res_json = runner.invoke(app, ["insurance", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "online"

    def test_insurance_license_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "insurance",
                "license",
                "Tổng Công ty Bảo hiểm Bảo Việt CLI",
                "0100111999",
                "--type",
                "NON_LIFE_INSURANCE",
                "--capital",
                "450000000000",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["license_profile"]["enterprise_name"] == "Tổng Công ty Bảo hiểm Bảo Việt CLI"

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "insurance",
                "license",
                "Bảo hiểm Nhân thọ CLI",
                "0100111888",
                "--type",
                "LIFE_INSURANCE",
                "--capital",
                "800000000000",
            ],
        )
        assert res_con.exit_code == 0
        assert "Giấy Phép Thành Lập & Hoạt Động Bảo Hiểm" in res_con.output

    def test_insurance_policy_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "insurance",
                "policy",
                "Tập đoàn Vinfast",
                "MOTOR_VEHICLE",
                "--sum-insured",
                "1500000000",
                "--premium",
                "22000000",
                "--deductible",
                "1000000",
                "--months",
                "12",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["policy_profile"]["sum_insured_vnd"] == 1_500_000_000.0

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "insurance",
                "policy",
                "Nguyễn Văn A",
                "HEALTH_ACCIDENT",
                "--sum-insured",
                "500000000",
                "--premium",
                "8000000",
            ],
        )
        assert res_con.exit_code == 0
        assert "Hợp Đồng / Giấy Chứng Nhận Bảo Hiểm" in res_con.output

    def test_insurance_solvency_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "insurance",
                "solvency",
                "Bảo hiểm Quân đội MIC",
                "--actual-margin",
                "1200000000000",
                "--net-premium",
                "2000000000000",
                "--avg-claims",
                "1000000000000",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["solvency_profile"]["is_solvent"] is True

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "insurance",
                "solvency",
                "Bảo hiểm Bảo Minh",
                "--actual-margin",
                "800000000000",
                "--net-premium",
                "1500000000000",
                "--avg-claims",
                "800000000000",
            ],
        )
        assert res_con.exit_code == 0
        assert "Kiểm Tra Biên Khả Năng Thanh Toán" in res_con.output

    def test_insurance_claim_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "insurance",
                "claim",
                "POL-MOTO-123456",
                "Va chạm xe làm hỏng kính chắn gió",
                "15000000",
                "--verified",
                "--approved",
                "--deductible",
                "1000000",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["claim_profile"]["net_settled_amount_vnd"] == 14_000_000.0

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "insurance",
                "claim",
                "POL-FIRE-999",
                "Chập điện cháy kho hàng mẫu",
                "50000000",
            ],
        )
        assert res_con.exit_code == 0
        assert "Quyết Định Giải Quyết Bồi Thường" in res_con.output

    def test_insurance_reserve_cmd(self, app) -> None:
        # JSON mode
        res_json = runner.invoke(
            app,
            [
                "insurance",
                "reserve",
                "Bảo hiểm PVI",
                "CARGO_MARINE",
                "--written-premium",
                "60000000000",
                "--unearned-ratio",
                "0.40",
                "--outstanding-claims",
                "8000000000",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "success"
        assert data["reserve_profile"]["unearned_premium_reserve_vnd"] == 24_000_000_000.0

        # Console mode
        res_con = runner.invoke(
            app,
            [
                "insurance",
                "reserve",
                "Bảo Việt",
                "MOTOR_VEHICLE",
            ],
        )
        assert res_con.exit_code == 0
        assert "Báo Cáo Trích Lập Dự Phòng Nghiệp Vụ" in res_con.output

    def test_insurance_list_cmd(self, app) -> None:
        # Prepopulate
        runner.invoke(app, ["insurance", "license", "Insurer CLI", "0109990001", "--capital", "400000000000"])
        runner.invoke(app, ["insurance", "policy", "Holder CLI", "MOTOR_VEHICLE"])
        runner.invoke(app, ["insurance", "solvency", "Insurer CLI", "--actual-margin", "900000000000"])
        runner.invoke(app, ["insurance", "claim", "POL-CLI", "Va chạm CLI", "10000000"])
        runner.invoke(app, ["insurance", "reserve", "Insurer CLI", "MOTOR_VEHICLE"])

        resources = ["licenses", "policies", "solvency", "claims", "reserves"]
        for r in resources:
            # JSON mode
            res_json = runner.invoke(app, ["insurance", "list", r, "--json"])
            assert res_json.exit_code == 0
            items = json.loads(res_json.output)
            assert isinstance(items, list)
            assert len(items) >= 1

            # Console mode
            res_con = runner.invoke(app, ["insurance", "list", r])
            assert res_con.exit_code == 0

    def test_insurance_status_cmd(self, app) -> None:
        res_con = runner.invoke(app, ["insurance", "status"])
        assert res_con.exit_code == 0
        assert "Báo Cáo Telemetry Thị Trường Bảo Hiểm" in res_con.output

        res_json = runner.invoke(app, ["insurance", "status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "online"


# ---------------------------------------------------------------------------
# MCP Server Tool Parity Tests
# ---------------------------------------------------------------------------


class TestInsuranceMCP:
    """Ensure FastMCP and Pure-Python JSON-RPC 2.0 dual server parity for insurance tools."""

    def test_src_core_mcp_insurance_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. license
        res_lic = json.loads(server._handle_insurance_license(
            enterprise_name="Bảo hiểm MCP Core",
            tax_id="0109988771",
            license_type="NON_LIFE_INSURANCE",
            charter_capital_vnd=400_000_000_000.0,
        ))
        assert res_lic["status"] == "success"

        # 2. policy
        res_pol = json.loads(server._handle_insurance_policy(
            policyholder_name="Bên Mua MCP Core",
            product_line="MOTOR_VEHICLE",
            sum_insured_vnd=1_000_000_000.0,
            premium_vnd=15_000_000.0,
        ))
        assert res_pol["status"] == "success"

        # 3. solvency
        res_solv = json.loads(server._handle_insurance_solvency(
            insurer_name="Bảo hiểm MCP Core",
            actual_solvency_margin_vnd=1_000_000_000_000.0,
        ))
        assert res_solv["status"] == "success"

        # 4. claim
        res_clm = json.loads(server._handle_insurance_claim(
            policy_id="POL-MCP-01",
            incident_description="Va chạm nhẹ",
            claimed_amount_vnd=20_000_000.0,
        ))
        assert res_clm["status"] == "success"

        # 5. reserve
        res_res = json.loads(server._handle_insurance_reserve(
            insurer_name="Bảo hiểm MCP Core",
            product_line="MOTOR_VEHICLE",
            written_premium_vnd=50_000_000_000.0,
        ))
        assert res_res["status"] == "success"

        # 6. list
        res_lst = json.loads(server._handle_insurance_list(resource="licenses"))
        assert isinstance(res_lst, list)

        # 7. status
        res_st = json.loads(server._handle_insurance_status())
        assert res_st["status"] == "online"

    def test_scripts_mcp_insurance_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MEKONG_DATA_DIR", str(tmp_path))
        from scripts.mcp_server import (
            handle_insurance_claim,
            handle_insurance_license,
            handle_insurance_list,
            handle_insurance_policy,
            handle_insurance_reserve,
            handle_insurance_solvency,
            handle_insurance_status,
        )

        # 1. license
        res_lic = json.loads(handle_insurance_license({
            "enterprise_name": "Bảo hiểm Script",
            "tax_id": "0109988772",
            "license_type": "LIFE_INSURANCE",
            "charter_capital_vnd": 750_000_000_000.0,
        }))
        assert res_lic["status"] == "success"

        # 2. policy
        res_pol = json.loads(handle_insurance_policy({
            "policyholder_name": "Bên Mua Script",
            "product_line": "HEALTH_ACCIDENT",
            "sum_insured_vnd": 500_000_000.0,
            "premium_vnd": 10_000_000.0,
        }))
        assert res_pol["status"] == "success"

        # 3. solvency
        res_solv = json.loads(handle_insurance_solvency({
            "insurer_name": "Bảo hiểm Script",
            "actual_solvency_margin_vnd": 800_000_000_000.0,
        }))
        assert res_solv["status"] == "success"

        # 4. claim
        res_clm = json.loads(handle_insurance_claim({
            "policy_id": "POL-SCRIPT-01",
            "incident_description": "Nằm viện điều trị",
            "claimed_amount_vnd": 12_000_000.0,
        }))
        assert res_clm["status"] == "success"

        # 5. reserve
        res_res = json.loads(handle_insurance_reserve({
            "insurer_name": "Bảo hiểm Script",
            "product_line": "HEALTH_ACCIDENT",
        }))
        assert res_res["status"] == "success"

        # 6. list
        res_lst = json.loads(handle_insurance_list({"resource": "policies"}))
        assert isinstance(res_lst, list)

        # 7. status
        res_st = json.loads(handle_insurance_status({}))
        assert res_st["status"] == "online"

    def test_scripts_mcp_core_tools_spec_and_handlers(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        insurance_tools = [
            "mekong_insurance_license",
            "mekong_insurance_policy",
            "mekong_insurance_solvency",
            "mekong_insurance_claim",
            "mekong_insurance_reserve",
            "mekong_insurance_list",
            "mekong_insurance_status",
        ]

        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for it in insurance_tools:
            assert it in spec_names, f"Tool {it} missing from CORE_TOOLS_SPEC"
            assert it in CORE_HANDLERS, f"Tool {it} missing from CORE_HANDLERS"
            bare_name = it.replace("mekong_", "")
            assert bare_name in CORE_HANDLERS, f"Alias {bare_name} missing from CORE_HANDLERS"
