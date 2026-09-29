# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Personal Data Protection Decree (PDPD Decree 13/2023/ND-CP) Engine (Phase 59)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.privacy_engine import (
    BASIC_DATA_CATEGORIES,
    SENSITIVE_DATA_CATEGORIES,
    DATA_SUBJECT_RIGHTS,
    CONTROLLER_TYPES,
    BREACH_MAX_NOTIFICATION_HOURS,
    DPIA_FILING_DEADLINE_DAYS,
    PrivacyEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestPrivacyCoreBoundary:
    """Ensure PrivacyEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/privacy_engine.py")
        assert source_path.exists(), "privacy_engine.py must exist"

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


class TestPrivacyEngine:
    """Test PrivacyEngine audit, DPIA Form 04, cross-border TIA, 72h breach response, and DSAR."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> PrivacyEngine:
        db_file = tmp_path / "test_privacy.db"
        return PrivacyEngine(db_path=db_file)

    def test_constants_and_categories(self) -> None:
        assert "FULL_NAME" in BASIC_DATA_CATEGORIES
        assert "PHONE_NUMBER" in BASIC_DATA_CATEGORIES
        assert "BIOMETRICS" in SENSITIVE_DATA_CATEGORIES
        assert "BANKING_FINANCIAL" in SENSITIVE_DATA_CATEGORIES
        assert len(DATA_SUBJECT_RIGHTS) == 11
        assert "RIGHT_TO_DELETE" in DATA_SUBJECT_RIGHTS
        assert BREACH_MAX_NOTIFICATION_HOURS == 72
        assert DPIA_FILING_DEADLINE_DAYS == 60

    def test_audit_enterprise_compliance_compliant(self, engine: PrivacyEngine) -> None:
        # Enterprise with sensitive data, appointed DPO, and completed DPIA dossier
        res = engine.audit_enterprise_compliance(
            enterprise_name="VinBrain Healthcare AI",
            controller_type="CONTROLLER_AND_PROCESSOR",
            has_sensitive_data=True,
            has_dpo=True,
            has_cross_border=False,
            has_dpia_dossier=True,
        )
        assert res["ok"] is True
        assert res["audit_id"].startswith("AUD-")
        assert res["compliance_score"] == 100.0
        assert res["compliance_status"] == "COMPLIANT"
        assert len(res["compliance_gaps"]) == 0

    def test_audit_enterprise_compliance_missing_dpo(self, engine: PrivacyEngine) -> None:
        # Article 28 violation: processing sensitive data without a DPO
        res = engine.audit_enterprise_compliance(
            enterprise_name="Fintech Micro Lending JSC",
            controller_type="CONTROLLER",
            has_sensitive_data=True,
            has_dpo=False,  # Violation!
            has_dpia_dossier=True,
        )
        assert res["ok"] is True
        assert res["compliance_score"] < 100.0
        assert any("DPO" in gap for gap in res["compliance_gaps"])
        assert any("Điều 28" in rec for rec in res["statutory_recommendations"])

    def test_audit_enterprise_compliance_missing_dpia(self, engine: PrivacyEngine) -> None:
        # Article 24 violation: missing DPIA assessment dossier
        res = engine.audit_enterprise_compliance(
            enterprise_name="E-Commerce Retail Co",
            controller_type="CONTROLLER",
            has_sensitive_data=False,
            has_dpo=False,
            has_dpia_dossier=False,  # Violation!
        )
        assert res["ok"] is True
        assert res["compliance_score"] <= 70.0
        assert any("DPIA" in gap for gap in res["compliance_gaps"])

    def test_create_dpia_assessment_sensitive(self, engine: PrivacyEngine) -> None:
        # Processing sensitive biometric & financial data -> High Risk, DPO mandatory
        res = engine.create_dpia_assessment(
            activity_name="Xác thực eKYC & Mở tài khoản số",
            processing_purpose="Định danh điện tử khách hàng ngân hàng số",
            data_categories=["FULL_NAME", "ID_CARD_NUMBER", "BIOMETRICS", "BANKING_FINANCIAL"],
            legal_basis="CONSENT",
            security_measures="AES-256 HSM, Zero Trust RBAC, TLS 1.3",
        )
        assert res["ok"] is True
        assert res["dpia_id"].startswith("DPIA-")
        assert res["is_sensitive_data_processed"] is True
        assert res["risk_assessment"]["risk_level"] == "HIGH_RISK"
        assert res["risk_assessment"]["dpo_mandatory"] is True
        assert res["form_04_a05"]["status"] == "DOSSIER_COMPILED"
        assert "A05" in res["form_04_a05"]["filing_recipient"]

    def test_create_dpia_assessment_basic(self, engine: PrivacyEngine) -> None:
        # Basic customer contact processing -> Low Risk
        res = engine.create_dpia_assessment(
            activity_name="Gửi bản tin Marketing qua Email",
            processing_purpose="Chăm sóc khách hàng định kỳ",
            data_categories=["FULL_NAME", "EMAIL"],
            legal_basis="CONSENT",
        )
        assert res["ok"] is True
        assert res["is_sensitive_data_processed"] is False
        assert res["risk_assessment"]["risk_level"] == "LOW_RISK"
        assert res["risk_assessment"]["dpo_mandatory"] is False

    def test_evaluate_cross_border_transfer_with_scc(self, engine: PrivacyEngine) -> None:
        # Article 25: Overseas transfer with signed SCC agreement
        res = engine.evaluate_cross_border_transfer(
            transfer_name="Lưu trữ Dữ liệu AWS Singapore",
            recipient_entity="Amazon Web Services Inc",
            destination_country="Singapore",
            data_types=["FULL_NAME", "PHONE_NUMBER", "EMAIL"],
            record_count=25000,
            has_scc=True,
        )
        assert res["ok"] is True
        assert res["transfer_id"].startswith("XFER-")
        assert res["transfer_status"] == "PERMITTED_WITH_FILING"
        assert res["compliance_checks"]["has_data_transfer_agreement"] is True

    def test_evaluate_cross_border_transfer_missing_scc(self, engine: PrivacyEngine) -> None:
        # Article 25 violation: transfer without SCC / data protection agreement
        res = engine.evaluate_cross_border_transfer(
            transfer_name="Chuyển dữ liệu cho đối tác nước ngoài",
            recipient_entity="Unknown Third Party Corp",
            destination_country="Cayman Islands",
            data_types=["FULL_NAME", "BANKING_FINANCIAL"],
            record_count=5000,
            has_scc=False,
        )
        assert res["ok"] is True
        assert res["transfer_status"] == "RESTRICTED_MISSING_SCC"
        assert any("Chưa có văn bản cam kết" in res["status_note"] for _ in [1])

    def test_report_data_breach_within_72h(self, engine: PrivacyEngine) -> None:
        # Article 26: Breach detected 4 hours ago -> within 72h window
        res = engine.report_data_breach(
            incident_name="Lỗ hổng API rò rỉ số điện thoại",
            severity="HIGH",
            affected_count=12000,
            breach_type="UNAUTHORIZED_API_ACCESS",
            hours_elapsed=4.0,
            mitigation_plan="Revoked leaked JWT secrets, blocked offending IPs, patched rate limiter",
        )
        assert res["ok"] is True
        assert res["incident_id"].startswith("BRC-")
        assert res["statutory_timeline"]["is_72h_compliant"] is True
        assert res["statutory_timeline"]["hours_remaining_to_report_a05"] == 68.0
        assert res["a05_reporting"]["status"] == "IMMEDIATE_ACTION_REQUIRED"

    def test_report_data_breach_exceeding_72h(self, engine: PrivacyEngine) -> None:
        # Article 26: Breach detected 80 hours ago -> statutory deadline exceeded
        res = engine.report_data_breach(
            incident_name="Ransomware mã hóa cơ sở dữ liệu cũ",
            severity="CRITICAL",
            affected_count=50000,
            breach_type="RANSOMWARE",
            hours_elapsed=80.0,
        )
        assert res["ok"] is True
        assert res["statutory_timeline"]["is_72h_compliant"] is False
        assert res["statutory_timeline"]["hours_remaining_to_report_a05"] == 0.0
        assert res["a05_reporting"]["status"] == "DEADLINE_EXCEEDED"

    def test_handle_dsar_request_deletion_and_access(self, engine: PrivacyEngine) -> None:
        # Article 9: Right to delete (3 days deadline)
        res_del = engine.handle_dsar_request(
            request_type="RIGHT_TO_DELETE",
            subject_id="CCCD-079090012345",
            details="Yêu cầu xóa toàn bộ lịch sử giao dịch và tài khoản",
        )
        assert res_del["ok"] is True
        assert res_del["request_id"].startswith("DSAR-")
        assert res_del["statutory_deadline"]["deadline_days"] == 3

        # Article 9: Right to access (7 days deadline)
        res_acc = engine.handle_dsar_request(
            request_type="RIGHT_TO_ACCESS",
            subject_id="USER-998877",
            details="Yêu cầu trích xuất dữ liệu cá nhân đang lưu trữ",
        )
        assert res_acc["ok"] is True
        assert res_acc["statutory_deadline"]["deadline_days"] == 7

    def test_list_records_and_status(self, engine: PrivacyEngine) -> None:
        engine.audit_enterprise_compliance("Test Corp", "CONTROLLER")
        engine.create_dpia_assessment("Act 1", "Purpose 1", ["FULL_NAME", "BIOMETRICS"])
        engine.evaluate_cross_border_transfer("Xfer 1", "Recip 1", "Singapore", ["FULL_NAME"])
        engine.report_data_breach("Breach 1", "HIGH", 500, "EXFILTRATION", 2.0)
        engine.handle_dsar_request("RIGHT_TO_ACCESS", "SUBJ-01")

        dpias = engine.list_dpia_assessments()
        assert dpias["ok"] is True
        assert len(dpias["assessments"]) >= 1

        xfers = engine.list_cross_border_transfers()
        assert xfers["ok"] is True
        assert len(xfers["transfers"]) >= 1

        breaches = engine.list_breach_incidents()
        assert breaches["ok"] is True
        assert len(breaches["breaches"]) >= 1

        dsars = engine.list_dsar_requests()
        assert dsars["ok"] is True
        assert len(dsars["requests"]) >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["metrics"]["total_compliance_audits"] >= 1
        assert status["metrics"]["total_dpia_assessments"] >= 1
        assert status["metrics"]["total_cross_border_transfers"] >= 1
        assert status["metrics"]["total_breach_incidents"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestPrivacyCli:
    """Test mekong privacy command group execution."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_main_json(self) -> None:
        result = runner.invoke(self.app, ["privacy", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "governing_law" in data
        assert "Nghị định 13/2023" in data["governing_law"]

    def test_cli_audit_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "audit",
                "Tập đoàn Công nghệ Alpha",
                "--role",
                "CONTROLLER_AND_PROCESSOR",
                "--sensitive",
                "--dpo",
                "--dpia",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["enterprise_name"] == "Tập đoàn Công nghệ Alpha"
        assert data["compliance_status"] == "COMPLIANT"

    def test_cli_audit_console(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "audit",
                "Công ty Khởi nghiệp Beta",
                "--role",
                "CONTROLLER",
            ],
        )
        assert result.exit_code == 0
        assert "Công ty Khởi nghiệp Beta" in result.output

    def test_cli_dpia_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "dpia",
                "Thu thập dữ liệu khuôn mặt cửa ra vào",
                "Kiểm soát an ninh văn phòng",
                "FULL_NAME,BIOMETRICS,IMAGE",
                "--basis",
                "CONSENT",
                "--security",
                "AES-256",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["is_sensitive_data_processed"] is True
        assert data["risk_assessment"]["risk_level"] == "HIGH_RISK"

    def test_cli_transfer_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "transfer",
                "Đồng bộ máy chủ Tokyo",
                "Line Corp",
                "Japan",
                "FULL_NAME,EMAIL",
                "--count",
                "5000",
                "--scc",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["destination_country"] == "Japan"
        assert data["transfer_status"] == "PERMITTED_WITH_FILING"

    def test_cli_breach_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "breach",
                "Rò rỉ cơ sở dữ liệu thử nghiệm",
                "HIGH",
                "3500",
                "UNPROTECTED_S3_BUCKET",
                "--hours",
                "1.5",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["statutory_timeline"]["is_72h_compliant"] is True

    def test_cli_dsar_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "dsar",
                "RIGHT_TO_DELETE",
                "CCCD-012345678999",
                "--details",
                "Yêu cầu xóa tài khoản người dùng",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["subject_id"] == "CCCD-012345678999"
        assert data["statutory_deadline"]["deadline_days"] == 3

    def test_cli_list_json(self) -> None:
        res = runner.invoke(self.app, ["privacy", "list", "--type", "dpia", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "assessments" in data

    def test_cli_status_json(self) -> None:
        res = runner.invoke(self.app, ["privacy", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestPrivacyMcpParity:
    """Test FastMCP and fallback pure JSON-RPC tool parity for privacy tools."""

    def test_fastmcp_handlers_exist(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_privacy_audit")
        assert hasattr(server, "_handle_privacy_dpia")
        assert hasattr(server, "_handle_privacy_transfer")
        assert hasattr(server, "_handle_privacy_breach")
        assert hasattr(server, "_handle_privacy_dsar")
        assert hasattr(server, "_handle_privacy_list")
        assert hasattr(server, "_handle_privacy_status")

    def test_scripts_mcp_handlers_wired(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected = [
            "mekong_privacy_audit",
            "mekong_privacy_dpia",
            "mekong_privacy_transfer",
            "mekong_privacy_breach",
            "mekong_privacy_dsar",
            "mekong_privacy_list",
            "mekong_privacy_status",
        ]
        for name in expected:
            assert name in tool_names, f"{name} must be in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"{name} must be in CORE_HANDLERS"

    def test_pure_json_rpc_invocation(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        a_handler = CORE_HANDLERS["mekong_privacy_audit"]
        a_raw = a_handler({
            "enterprise_name": "Tiki Vietnam",
            "controller_type": "CONTROLLER_AND_PROCESSOR",
            "has_sensitive_data": True,
            "has_dpo": True,
            "has_dpia_dossier": True,
        })
        a_res = json.loads(a_raw)
        assert a_res["ok"] is True
        assert a_res["enterprise_name"] == "Tiki Vietnam"
        assert a_res["compliance_score"] == 100.0

        d_handler = CORE_HANDLERS["mekong_privacy_dpia"]
        d_raw = d_handler({
            "activity_name": "Phân tích hành vi mua sắm",
            "processing_purpose": "Gợi ý sản phẩm thương mại điện tử",
            "data_categories": ["FULL_NAME", "EMAIL", "PHONE_NUMBER"],
        })
        d_res = json.loads(d_raw)
        assert d_res["ok"] is True
        assert d_res["is_sensitive_data_processed"] is False

        b_handler = CORE_HANDLERS["mekong_privacy_breach"]
        b_raw = b_handler({
            "incident_name": "Rò rỉ mã khóa xác thực",
            "severity": "HIGH",
            "affected_count": 800,
            "breach_type": "KEY_EXPOSURE",
            "hours_elapsed": 5.0,
        })
        b_res = json.loads(b_raw)
        assert b_res["ok"] is True
        assert b_res["statutory_timeline"]["is_72h_compliant"] is True
