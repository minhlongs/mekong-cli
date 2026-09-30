# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit and integration test suite for Vietnamese Press, Media & OTT Broadcasting Suite (Phase 102)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.press_engine import (
    PressEngine,
    STATUTORY_ONLINE_CORRECTION_DEADLINE_HOURS,
    STATUTORY_CORRECTION_RETENTION_DAYS,
    MAX_ICP_SELF_PRODUCED_RATIO_PCT,
    STATUTORY_ICP_TAKEDOWN_SLA_HOURS,
)


@pytest.fixture
def temp_press_engine(tmp_path: Path) -> PressEngine:
    """Fixture providing an isolated PressEngine backed by a temporary SQLite database."""
    db_file = tmp_path / "test_press.db"
    return PressEngine(db_path=db_file)


class TestPressEngine:
    """Tests for core Press, ICP, OTT, and Correction engine."""

    def test_engine_init_and_tables(self, temp_press_engine: PressEngine) -> None:
        """Verify engine initialization and schema creation."""
        status = temp_press_engine.get_status()
        assert status["status"] == "active"
        assert "Law on Press 2016" in status["statute"]
        assert status["credentials"]["total_assessed"] == 0
        assert status["icp"]["total_audited"] == 0

    def test_credential_press_card_eligible(self, temp_press_engine: PressEngine) -> None:
        """Verify eligibility for standard press card issuance."""
        res = temp_press_engine.verify_credential(
            holder_name="Nguyễn Văn Hưng",
            credential_type="PRESS_CARD",
            press_agency="Báo Tuổi Trẻ",
            education_degree="BACHELOR_JOURNALISM",
            experience_years=3.0,
            disciplinary_clean=True,
        )
        assert res["credential_id"].startswith("crd_")
        assert res["status"] == "ELIGIBLE"
        assert len(res["deficiencies"]) == 0

    def test_credential_press_card_disqualified_experience(self, temp_press_engine: PressEngine) -> None:
        """Verify press card requires at least 2 years continuous experience."""
        res = temp_press_engine.verify_credential(
            holder_name="Lê Minh Anh",
            credential_type="PRESS_CARD",
            press_agency="Báo Thanh Niên",
            education_degree="BACHELOR_JOURNALISM",
            experience_years=1.0,
            disciplinary_clean=True,
        )
        assert res["status"] == "DISQUALIFIED"
        assert any("dưới 02 năm" in d for d in res["deficiencies"])

    def test_credential_press_card_disqualified_discipline(self, temp_press_engine: PressEngine) -> None:
        """Verify disciplinary action disqualifies applicant."""
        res = temp_press_engine.verify_credential(
            holder_name="Trần Quốc Huy",
            credential_type="PRESS_CARD",
            press_agency="Báo Lao Động",
            experience_years=4.0,
            disciplinary_clean=False,
        )
        assert res["status"] == "DISQUALIFIED"
        assert any("kỷ luật" in d for d in res["deficiencies"])

    def test_credential_editor_in_chief_eligible(self, temp_press_engine: PressEngine) -> None:
        """Verify Editor-in-Chief appointment requires advanced political theory & 5 years experience."""
        res = temp_press_engine.verify_credential(
            holder_name="Phạm Hoàng Long",
            credential_type="EDITOR_IN_CHIEF",
            press_agency="Báo Sài Gòn Giải Phóng",
            experience_years=7.0,
            political_theory_advanced=True,
            disciplinary_clean=True,
        )
        assert res["status"] == "ELIGIBLE"

    def test_credential_editor_in_chief_disqualified_politics(self, temp_press_engine: PressEngine) -> None:
        """Verify Editor-in-Chief without political theory is disqualified."""
        res = temp_press_engine.verify_credential(
            holder_name="Võ Văn Nam",
            credential_type="EDITOR_IN_CHIEF",
            press_agency="Tạp chí Công Thương",
            experience_years=8.0,
            political_theory_advanced=False,
            disciplinary_clean=True,
        )
        assert res["status"] == "DISQUALIFIED"
        assert any("lý luận chính trị" in d for d in res["deficiencies"])

    def test_icp_audit_compliant(self, temp_press_engine: PressEngine) -> None:
        """Verify compliant general information website."""
        res = temp_press_engine.audit_icp_compliance(
            website_domain="tapchitaichinh.vn",
            organization_name="Công ty CP Truyền thông Tài Chính",
            server_located_in_vietnam=True,
            has_source_copyright_agreement=True,
            exact_source_attribution=True,
            self_produced_ratio_pct=6.0,
            takedown_sla_hours=2,
        )
        assert res["audit_id"].startswith("icp_")
        assert res["compliance_status"] == "COMPLIANT"
        assert not res["is_commercialized_journalism"]

    def test_icp_audit_commercialized_journalism_warning(self, temp_press_engine: PressEngine) -> None:
        """Verify warning triggered when self-produced news exceeds 10% (báo hóa)."""
        res = temp_press_engine.audit_icp_compliance(
            website_domain="tintuc247.vn",
            organization_name="Công ty TNHH Truyền thông Số",
            server_located_in_vietnam=True,
            has_source_copyright_agreement=True,
            exact_source_attribution=True,
            self_produced_ratio_pct=25.0,
            takedown_sla_hours=3,
        )
        assert res["is_commercialized_journalism"] is True
        assert res["compliance_status"] == "NON_COMPLIANT_WARNING"
        assert any("báo hóa" in d for d in res["deficiencies"])

    def test_icp_audit_missing_copyright_and_server_abroad(self, temp_press_engine: PressEngine) -> None:
        """Verify server located abroad and missing copyright agreement are flagged."""
        res = temp_press_engine.audit_icp_compliance(
            website_domain="hotnews.org",
            organization_name="Công ty Quốc Tế",
            server_located_in_vietnam=False,
            has_source_copyright_agreement=False,
            exact_source_attribution=False,
            takedown_sla_hours=5,
        )
        assert res["compliance_status"] == "NON_COMPLIANT_WARNING"
        assert len(res["deficiencies"]) >= 3

    def test_ott_vod_license_approved(self, temp_press_engine: PressEngine) -> None:
        """Verify OTT TV and VOD license approval conditions."""
        res = temp_press_engine.license_ott_vod(
            service_name="MekongPlay",
            provider_name="Tập đoàn Viễn thông Mekong",
            service_type="SVOD",
            age_rating_system_active=True,
            content_editing_committee_approved=True,
            essential_national_channels_carried=True,
            copyright_clearance_confirmed=True,
        )
        assert res["license_id"].startswith("ott_")
        assert res["status"] == "LICENSED_APPROVED"

    def test_ott_vod_license_rejected_missing_age_rating(self, temp_press_engine: PressEngine) -> None:
        """Verify missing age rating system rejects license."""
        res = temp_press_engine.license_ott_vod(
            service_name="StreamVN",
            provider_name="Công ty CP Truyền thông Stream",
            service_type="TVOD",
            age_rating_system_active=False,
            content_editing_committee_approved=True,
            essential_national_channels_carried=True,
            copyright_clearance_confirmed=True,
        )
        assert res["status"] == "LICENSE_REJECTED"
        assert any("độ tuổi" in d for d in res["deficiencies"])

    def test_press_correction_compliant_within_24h(self, temp_press_engine: PressEngine) -> None:
        """Verify online press correction compliant within 24h statutory window."""
        res = temp_press_engine.file_correction(
            press_agency="Báo Điện tử Người Đô Thị",
            article_title="Phản ánh về nguồn gốc nông sản của Hợp tác xã A",
            publication_date="2026-09-20",
            medium_type="ONLINE",
            violation_nature="THÔNG TIN SAI SỰ THẬT VỀ TIÊU CHUẨN VIETGAP",
            correction_text="Đính chính: Hợp tác xã A đạt chuẩn chứng nhận VietGAP số 123/2026",
            public_apology_included=True,
            published_hours_after_request=10,
            retention_days=7,
            right_of_reply_granted=True,
        )
        assert res["correction_id"].startswith("cor_")
        assert res["within_statutory_deadline"] is True
        assert res["retention_compliant"] is True
        assert res["status"] == "CORRECTION_COMPLIANT"

    def test_press_correction_delayed_violation(self, temp_press_engine: PressEngine) -> None:
        """Verify online press correction taking > 24h triggers violation."""
        res = temp_press_engine.file_correction(
            press_agency="Báo Tin Nhanh",
            article_title="Bài viết về doanh nghiệp B",
            publication_date="2026-09-18",
            medium_type="ONLINE",
            violation_nature="THÔNG TIN KHÔNG CHÍNH XÁC",
            published_hours_after_request=36,
            retention_days=7,
        )
        assert res["within_statutory_deadline"] is False
        assert res["status"] == "DELAYED_CORRECTION_VIOLATION"

    def test_list_records_and_telemetry(self, temp_press_engine: PressEngine) -> None:
        """Verify list_records across all categories and status metrics."""
        temp_press_engine.verify_credential("Phóng viên 1", "PRESS_CARD")
        temp_press_engine.audit_icp_compliance("web1.vn", "Công ty 1")
        temp_press_engine.license_ott_vod("OTT 1", "Công ty 2")
        temp_press_engine.file_correction("Báo 1", "Bài 1", "2026-09-25")

        records = temp_press_engine.list_records(category="all")
        assert len(records) == 4

        status = temp_press_engine.get_status()
        assert status["credentials"]["total_assessed"] == 1
        assert status["icp"]["total_audited"] == 1
        assert status["ott_vod"]["total_services"] == 1
        assert status["corrections"]["total_corrections"] == 1


class TestPressCli:
    """Tests for Typer CLI surface (mekong press)."""

    def test_cli_overview_and_json(self) -> None:
        """Verify mekong press root status command."""
        runner = CliRunner()
        app = build_app()

        res_json = runner.invoke(app, ["press", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.stdout)
        assert data["status"] == "active"
        assert "Law on Press 2016" in data["statute"]

        res_console = runner.invoke(app, ["press"])
        assert res_console.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ BÁO CHÍ" in res_console.stdout

    def test_cli_credential_cmd(self) -> None:
        """Verify mekong press credential command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "press",
                "credential",
                "Đỗ Thu Trang",
                "--type",
                "PRESS_CARD",
                "--agency",
                "Báo Tuổi Trẻ",
                "--degree",
                "BACHELOR_JOURNALISM",
                "--exp",
                "3.5",
                "--clean",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["holder_name"] == "Đỗ Thu Trang"
        assert data["status"] == "ELIGIBLE"

    def test_cli_icp_cmd(self) -> None:
        """Verify mekong press icp command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "press",
                "icp",
                "techvietnam.vn",
                "Công ty CP Công Nghệ Số",
                "--server-vn",
                "--agreement",
                "--attribution",
                "--self-ratio",
                "4.5",
                "--sla",
                "2",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["compliance_status"] == "COMPLIANT"
        assert not data["is_commercialized_journalism"]

    def test_cli_ott_cmd(self) -> None:
        """Verify mekong press ott command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "press",
                "ott",
                "CinemaMekong",
                "Công ty TNHH Phim Số",
                "--type",
                "SVOD",
                "--age-rating",
                "--editorial",
                "--essential",
                "--copyright",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["status"] == "LICENSED_APPROVED"

    def test_cli_correct_cmd(self) -> None:
        """Verify mekong press correct command."""
        runner = CliRunner()
        app = build_app()

        res = runner.invoke(
            app,
            [
                "press",
                "correct",
                "Báo Đời Sống Mới",
                "Thông tin sai về an toàn thực phẩm cơ sở C",
                "2026-09-19",
                "--medium",
                "ONLINE",
                "--violation",
                "THÔNG TIN SAI SỰ THẬT",
                "--hours",
                "15",
                "--retention",
                "7",
                "--apology",
                "--reply",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["status"] == "CORRECTION_COMPLIANT"

    def test_cli_list_and_status_cmds(self) -> None:
        """Verify mekong press list and status subcommands."""
        runner = CliRunner()
        app = build_app()

        res_list = runner.invoke(app, ["press", "list", "all", "--limit", "10", "--json"])
        assert res_list.exit_code == 0
        records = json.loads(res_list.stdout)
        assert isinstance(records, list)

        res_status = runner.invoke(app, ["press", "status", "--json"])
        assert res_status.exit_code == 0
        status_data = json.loads(res_status.stdout)
        assert "credentials" in status_data
        assert "icp" in status_data


class TestPressMcpHandlers:
    """Tests for native MCP tool handlers with dual parity."""

    def test_scripts_mcp_server_handlers(self) -> None:
        """Verify handle_press_* handlers in scripts/mcp_server.py."""
        from scripts.mcp_server import (
            handle_press_credential,
            handle_press_icp,
            handle_press_ott,
            handle_press_correct,
            handle_press_list,
            handle_press_status,
        )

        cred_res = json.loads(handle_press_credential({"holder_name": "Pham Van E", "experience_years": 4.0}))
        assert cred_res["holder_name"] == "Pham Van E"

        icp_res = json.loads(handle_press_icp({"website_domain": "testsite.vn", "organization_name": "Org E"}))
        assert "compliance_status" in icp_res

        ott_res = json.loads(handle_press_ott({"service_name": "TestOTT", "provider_name": "Org E"}))
        assert ott_res["service_name"] == "TestOTT"

        corr_res = json.loads(handle_press_correct({
            "press_agency": "NewsCorp",
            "article_title": "Fake Headline",
            "publication_date": "2026-09-10",
        }))
        assert corr_res["press_agency"] == "NewsCorp"

        list_res = json.loads(handle_press_list({"category": "all", "limit": 10}))
        assert isinstance(list_res, list)

        status_res = json.loads(handle_press_status({}))
        assert status_res["status"] == "active"

    def test_core_mcp_server_handlers(self) -> None:
        """Verify _handle_press_* methods in src/core/mcp_server.py."""
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        cred_res = json.loads(server._handle_press_credential(holder_name="Vu Thi F", experience_years=3.0))
        assert cred_res["holder_name"] == "Vu Thi F"

        icp_res = json.loads(server._handle_press_icp(website_domain="vietpress.vn", organization_name="Viet Corp"))
        assert "compliance_status" in icp_res

        ott_res = json.loads(server._handle_press_ott(service_name="VNStream", provider_name="Viet Corp"))
        assert "status" in ott_res

        corr_res = json.loads(server._handle_press_correct(
            press_agency="Báo Kinh Tế",
            article_title="Nhầm lẫn số liệu",
            publication_date="2026-09-12",
        ))
        assert corr_res["press_agency"] == "Báo Kinh Tế"

        list_res = json.loads(server._handle_press_list(category="all", limit=5))
        assert isinstance(list_res, list)

        status_res = json.loads(server._handle_press_status())
        assert status_res["status"] == "active"
