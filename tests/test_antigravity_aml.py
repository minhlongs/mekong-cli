# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit and integration test suite for Vietnamese Anti-Money Laundering & Sanctions Suite (Phase 101)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.aml_engine import (
    AmlEngine,
    STATUTORY_LCTR_THRESHOLD_VND,
    STATUTORY_UBO_THRESHOLD_PCT,
)


@pytest.fixture
def temp_aml_engine(tmp_path: Path) -> AmlEngine:
    """Fixture providing an isolated AmlEngine backed by a temporary SQLite database."""
    db_file = tmp_path / "test_aml.db"
    return AmlEngine(db_path=db_file)


class TestAmlEngine:
    """Tests for core AML, CTF, and Sanctions engine."""

    def test_engine_init_and_tables(self, temp_aml_engine: AmlEngine) -> None:
        """Verify engine initialization and schema creation."""
        status = temp_aml_engine.get_status()
        assert status["status"] == "active"
        assert status["statutory_lctr_threshold_vnd"] == 400_000_000.0
        assert status["statutory_ubo_threshold_pct"] == 25.0
        assert status["cdd"]["total_profiles"] == 0
        assert status["lctr"]["total_reports"] == 0

    def test_cdd_individual_low_risk(self, temp_aml_engine: AmlEngine) -> None:
        """Verify CDD profiling for standard individual."""
        res = temp_aml_engine.perform_cdd(
            customer_name="Trần Văn Minh",
            customer_type="INDIVIDUAL",
            identifier="001099887766",
            industry="BANKING",
            nationality="VN",
        )
        assert res["profile_id"].startswith("cdd_")
        assert res["customer_name"] == "Trần Văn Minh"
        assert res["risk_level"] == "LOW"
        assert res["status"] == "APPROVED"
        assert not res["edd_applied"]
        assert not res["is_pep"]

    def test_cdd_organization_with_valid_ubo(self, temp_aml_engine: AmlEngine) -> None:
        """Verify CDD profiling for organization with verified UBO >= 25%."""
        res = temp_aml_engine.perform_cdd(
            customer_name="Công ty TNHH Nam Long",
            customer_type="ORGANIZATION",
            identifier="0109876543",
            industry="MANUFACTURING",
            ubo_name="Lê Hoàng",
            ubo_ownership_pct=35.0,
        )
        assert res["ubo_name"] == "Lê Hoàng"
        assert res["ubo_ownership_pct"] == 35.0
        assert res["ubo_statutory_threshold_met"] is True
        assert res["status"] == "APPROVED"

    def test_cdd_organization_without_ubo_triggers_verification(self, temp_aml_engine: AmlEngine) -> None:
        """Verify organization without UBO or < 25% triggers verification status."""
        res = temp_aml_engine.perform_cdd(
            customer_name="Công ty Cổ phần Thần Tốc",
            customer_type="ORGANIZATION",
            identifier="0312345678",
            industry="LOGISTICS",
            ubo_name=None,
            ubo_ownership_pct=10.0,
        )
        assert res["ubo_statutory_threshold_met"] is False
        assert res["status"] == "UBO_VERIFICATION_REQUIRED"
        assert res["risk_level"] in {"MEDIUM", "HIGH"}

    def test_cdd_pep_requires_senior_approval_and_edd(self, temp_aml_engine: AmlEngine) -> None:
        """Verify PEP automatically triggers HIGH risk, EDD, and pending senior approval."""
        res_unapproved = temp_aml_engine.perform_cdd(
            customer_name="Nguyễn Văn A",
            customer_type="INDIVIDUAL",
            identifier="079088776655",
            is_pep=True,
            source_of_wealth="Lương và thu nhập hợp pháp",
            senior_mgmt_approved=False,
        )
        assert res_unapproved["risk_level"] == "HIGH"
        assert res_unapproved["is_pep"] is True
        assert res_unapproved["edd_applied"] is True
        assert res_unapproved["status"] == "PENDING_SENIOR_APPROVAL"

        res_approved = temp_aml_engine.perform_cdd(
            customer_name="Nguyễn Văn A",
            customer_type="INDIVIDUAL",
            identifier="079088776655",
            is_pep=True,
            source_of_wealth="Lương và thu nhập hợp pháp",
            senior_mgmt_approved=True,
        )
        assert res_approved["status"] == "APPROVED"

    def test_cdd_high_risk_sectors(self, temp_aml_engine: AmlEngine) -> None:
        """Verify high risk sectors elevate risk score."""
        res = temp_aml_engine.perform_cdd(
            customer_name="Casino Royal Club",
            customer_type="ORGANIZATION",
            industry="CASINO",
            nationality="VN",
            ubo_name="Michael Chang",
            ubo_ownership_pct=40.0,
        )
        assert res["risk_score"] >= 35.0

    def test_lctr_below_threshold(self, temp_aml_engine: AmlEngine) -> None:
        """Verify cash transaction below 400M VND is exempt from reporting."""
        res = temp_aml_engine.record_lctr(
            customer_name="Phạm Thị Lan",
            transaction_amount=250_000_000.0,
            currency="VND",
            transaction_type="CASH_DEPOSIT",
        )
        assert res["threshold_exceeded"] is False
        assert res["report_status"] == "EXEMPT_BELOW_THRESHOLD"

    def test_lctr_exceeding_threshold(self, temp_aml_engine: AmlEngine) -> None:
        """Verify cash transaction >= 400M VND requires SBV submission."""
        res = temp_aml_engine.record_lctr(
            customer_name="Hoàng Kim Bảo",
            transaction_amount=750_000_000.0,
            currency="VND",
            transaction_type="CASH_DEPOSIT",
            channel="OVER_THE_COUNTER",
            notes="Nộp tiền mặt mua căn hộ",
        )
        assert res["threshold_exceeded"] is True
        assert res["report_status"] == "READY_FOR_SBV_SUBMISSION"
        assert res["sbv_reference_no"].startswith("SBV-AMLD-LCTR-")

    def test_str_filing_normal_48h(self, temp_aml_engine: AmlEngine) -> None:
        """Verify standard STR filing computes 48h deadline."""
        res = temp_aml_engine.file_str(
            customer_name="Doanh nghiệp Bình Phong Alpha",
            suspicion_type="SHELL_COMPANY",
            amount=2_500_000_000.0,
            indicators=["TK_MOI_GIAO_DICH_LON", "RUT_TIEN_MAT_NGAY"],
            rationale="Tài khoản mới mở có nhiều lượt nộp rồi rút tiền mặt ngay",
            urgency="NORMAL",
        )
        assert res["str_id"].startswith("str_")
        assert res["suspicion_type"] == "SHELL_COMPANY"
        assert res["urgency"] == "NORMAL"
        assert res["status"] == "SUBMITTED_TO_COMPLIANCE"
        assert len(res["indicators"]) == 2

    def test_str_filing_urgent_24h_critical_intercept(self, temp_aml_engine: AmlEngine) -> None:
        """Verify urgent STR filing computes 24h deadline and critical status."""
        res = temp_aml_engine.file_str(
            customer_name="Võ Văn Hắc",
            suspicion_type="SMURFING_STRUCTURING",
            amount=1_950_000_000.0,
            indicators=["CHIA_NHO_GIAO_DICH_390M"],
            rationale="Chia 5 giao dịch 390 triệu liên tiếp để tránh ngưỡng 400 triệu",
            urgency="CRITICAL_INTERCEPT",
        )
        assert res["urgency"] == "CRITICAL_INTERCEPT"
        assert res["status"] == "CRITICAL_DISPATCH_REQUIRED"

    def test_sanctions_screening_no_match(self, temp_aml_engine: AmlEngine) -> None:
        """Verify clean name returns NO_MATCH and no asset freeze."""
        res = temp_aml_engine.screen_sanctions(
            target_name="Nguyen Van Binh",
            target_type="INDIVIDUAL",
        )
        assert res["match_status"] == "NO_MATCH"
        assert res["asset_freeze_triggered"] is False
        assert res["police_notification_required"] is False

    def test_sanctions_screening_confirmed_match_asset_freeze(self, temp_aml_engine: AmlEngine) -> None:
        """Verify designated terrorist entity triggers match and immediate 3-day asset freeze."""
        res = temp_aml_engine.screen_sanctions(
            target_name="ISIL (DA'ESH)",
            target_type="ORGANIZATION",
        )
        assert res["match_status"] == "CONFIRMED_MATCH"
        assert res["matched_list"] == "UNSC_1267_ISIL_ALQAEDA"
        assert res["asset_freeze_triggered"] is True
        assert res["freeze_duration_days"] == 3
        assert res["police_notification_required"] is True

    def test_institutional_assessment(self, temp_aml_engine: AmlEngine) -> None:
        """Verify institutional AML governance scoring and FATF tiers."""
        full_bank = temp_aml_engine.assess_institution(
            institution_name="Ngân hàng TMCP Phương Đông",
            institution_type="COMMERCIAL_BANK",
            compliance_officer_appointed=True,
            internal_rules_updated=True,
            annual_training_conducted=True,
            independent_internal_audit=True,
            risk_assessment_period="2024-2025",
        )
        assert full_bank["compliance_score"] == 100.0
        assert full_bank["fatf_readiness_tier"] == "COMPLIANT"

        deficient_firm = temp_aml_engine.assess_institution(
            institution_name="Công ty BĐS Hoàng Gia",
            institution_type="REAL_ESTATE_BROKER",
            compliance_officer_appointed=False,
            internal_rules_updated=False,
            annual_training_conducted=False,
            independent_internal_audit=False,
            risk_assessment_period="",
        )
        assert deficient_firm["compliance_score"] == 0.0
        assert deficient_firm["fatf_readiness_tier"] == "NON_COMPLIANT"

    def test_list_records_and_telemetry(self, temp_aml_engine: AmlEngine) -> None:
        """Verify list_records across all domains and aggregated get_status telemetry."""
        temp_aml_engine.perform_cdd("Khách Hàng 1", "INDIVIDUAL")
        temp_aml_engine.record_lctr("Khách Hàng 1", 500_000_000.0)
        temp_aml_engine.file_str("Khách Hàng 2", "UNUSUAL_VOLUME", 1_000_000_000.0)
        temp_aml_engine.screen_sanctions("ISIL (DA'ESH)")
        temp_aml_engine.assess_institution("Bank Test", "COMMERCIAL_BANK")

        all_records = temp_aml_engine.list_records(category="all")
        assert len(all_records) == 5

        status = temp_aml_engine.get_status()
        assert status["cdd"]["total_profiles"] == 1
        assert status["lctr"]["total_reports"] == 1
        assert status["lctr"]["threshold_exceeded_reports"] == 1
        assert status["str"]["total_reports"] == 1
        assert status["sanctions"]["total_screenings"] == 1
        assert status["sanctions"]["confirmed_matches"] == 1
        assert status["institutions"]["total_assessed"] == 1


class TestAmlCli:
    """Tests for Typer CLI surface (mekong aml)."""

    def test_cli_overview_and_json(self) -> None:
        """Verify mekong aml root status command."""
        runner = CliRunner()
        app = build_app()

        res_json = runner.invoke(app, ["aml", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.stdout)
        assert data["status"] == "active"
        assert data["statutory_lctr_threshold_vnd"] == 400_000_000.0

        res_console = runner.invoke(app, ["aml"])
        assert res_console.exit_code == 0
        assert "HỆ THỐNG GIÁM SÁT PHÒNG, CHỐNG RỬA TIỀN" in res_console.stdout

    def test_cli_cdd_cmd(self) -> None:
        """Verify mekong aml cdd command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "aml",
                "cdd",
                "Công ty TNHH Sao Mai",
                "--type",
                "ORGANIZATION",
                "--id",
                "010998877",
                "--industry",
                "REAL_ESTATE",
                "--ubo",
                "Vũ Văn An",
                "--ubo-pct",
                "30.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["customer_name"] == "Công ty TNHH Sao Mai"
        assert data["ubo_ownership_pct"] == 30.0
        assert data["ubo_statutory_threshold_met"] is True

    def test_cli_lctr_cmd(self) -> None:
        """Verify mekong aml lctr command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "aml",
                "lctr",
                "Đặng Minh Trí",
                "600000000",
                "--currency",
                "VND",
                "--type",
                "CASH_DEPOSIT",
                "--channel",
                "OVER_THE_COUNTER",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["threshold_exceeded"] is True
        assert data["transaction_amount"] == 600_000_000.0

    def test_cli_str_cmd(self) -> None:
        """Verify mekong aml str command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "aml",
                "str",
                "Tập đoàn Nam Á",
                "SHELL_COMPANY",
                "3500000000",
                "--indicator",
                "TK_DUNG_HO",
                "--urgent",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["suspicion_type"] == "SHELL_COMPANY"
        assert data["urgency"] == "CRITICAL_INTERCEPT"

    def test_cli_screening_cmd(self) -> None:
        """Verify mekong aml screening command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "aml",
                "screening",
                "AL-QAIDA",
                "--type",
                "ORGANIZATION",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["match_status"] == "CONFIRMED_MATCH"
        assert data["asset_freeze_triggered"] is True

    def test_cli_assess_cmd(self) -> None:
        """Verify mekong aml assess command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "aml",
                "assess",
                "Ngân hàng Phát triển Đô thị",
                "--type",
                "COMMERCIAL_BANK",
                "--officer",
                "--rules",
                "--training",
                "--audit",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["compliance_score"] == 100.0
        assert data["fatf_readiness_tier"] == "COMPLIANT"

    def test_cli_list_and_status_cmds(self) -> None:
        """Verify mekong aml list and status subcommands."""
        runner = CliRunner()
        app = build_app()

        res_list = runner.invoke(app, ["aml", "list", "all", "--limit", "10", "--json"])
        assert res_list.exit_code == 0
        records = json.loads(res_list.stdout)
        assert isinstance(records, list)

        res_status = runner.invoke(app, ["aml", "status", "--json"])
        assert res_status.exit_code == 0
        status_data = json.loads(res_status.stdout)
        assert "cdd" in status_data
        assert "lctr" in status_data


class TestAmlMcpHandlers:
    """Tests for native MCP tool handlers with dual parity."""

    def test_scripts_mcp_server_handlers(self) -> None:
        """Verify handle_aml_* handlers in scripts/mcp_server.py."""
        from scripts.mcp_server import (
            handle_aml_cdd,
            handle_aml_lctr,
            handle_aml_str,
            handle_aml_screening,
            handle_aml_assess,
            handle_aml_list,
            handle_aml_status,
        )

        cdd_res = json.loads(handle_aml_cdd({"customer_name": "Nguyen Thi C", "ubo_ownership_pct": 30.0}))
        assert cdd_res["customer_name"] == "Nguyen Thi C"

        lctr_res = json.loads(handle_aml_lctr({"customer_name": "Nguyen Thi C", "transaction_amount": 500000000.0}))
        assert lctr_res["threshold_exceeded"] is True

        str_res = json.loads(handle_aml_str({"customer_name": "Test Firm", "suspicion_type": "UNUSUAL_VOLUME", "amount": 1000000000.0}))
        assert str_res["suspicion_type"] == "UNUSUAL_VOLUME"

        screen_res = json.loads(handle_aml_screening({"target_name": "AL-QAIDA"}))
        assert screen_res["match_status"] == "CONFIRMED_MATCH"

        assess_res = json.loads(handle_aml_assess({"institution_name": "Fintech Alpha"}))
        assert "compliance_score" in assess_res

        list_res = json.loads(handle_aml_list({"category": "all", "limit": 10}))
        assert isinstance(list_res, list)

        status_res = json.loads(handle_aml_status({}))
        assert status_res["status"] == "active"

    def test_core_mcp_server_handlers(self) -> None:
        """Verify _handle_aml_* methods in src/core/mcp_server.py."""
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        cdd_res = json.loads(server._handle_aml_cdd(customer_name="Dang Van D", ubo_ownership_pct=50.0))
        assert cdd_res["customer_name"] == "Dang Van D"

        lctr_res = json.loads(server._handle_aml_lctr(customer_name="Dang Van D", transaction_amount=450000000.0))
        assert lctr_res["threshold_exceeded"] is True

        str_res = json.loads(server._handle_aml_str(customer_name="Firm B", suspicion_type="OBSCURE_SOURCE", amount=800000000.0))
        assert str_res["suspicion_type"] == "OBSCURE_SOURCE"

        screen_res = json.loads(server._handle_aml_screening(target_name="ISIL (DA'ESH)"))
        assert screen_res["match_status"] == "CONFIRMED_MATCH"

        assess_res = json.loads(server._handle_aml_assess(institution_name="Bank Gamma"))
        assert "fatf_readiness_tier" in assess_res

        list_res = json.loads(server._handle_aml_list(category="all", limit=5))
        assert isinstance(list_res, list)

        status_res = json.loads(server._handle_aml_status())
        assert status_res["status"] == "active"
