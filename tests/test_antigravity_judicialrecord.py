"""
Test suite for Vietnamese Judicial Records, Criminal Clearance & VNeID Electronic Certificates Suite (Phase 145).
Compliant with:
- Law on Judicial Records 2009 (Luật Lý lịch tư pháp - Law No. 28/2009/QH12)
- Decree No. 111/2010/ND-CP & Decree No. 82/2020/ND-CP
- Circular No. 06/2013/TT-BTP & Circular No. 04/2024/TT-BTP
- Penal Code 2015, amended 2017 (Articles 69, 70, 71, 72, 73 on Criminal Record Remission)
- Decree No. 59/2022/ND-CP on VNeID Level 2 Authentication

Covers:
- JudicialRecordEngine (pure standard library, SQLite WAL persistence, automated clearance, Form 1 vs Form 2 synthesis).
- CLI surface (mekong judicialrecord / mekong lylich / mekong criminalrecord).
- MCP parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.judicialrecord_engine import (
    JudicialRecordEngine,
    CertificateFormType,
    ClearanceStatus,
    RequestStatus,
    CrimeSeverity,
)
from src.cli.commands.judicialrecord_command import judicialrecord_app
from src.cli.app_setup import build_app


@pytest.fixture
def temp_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_judicialrecord.db")
        monkeypatch.setenv("MEKONG_JUDICIALRECORD_DB", db_path)
        yield db_path


class TestJudicialRecordEngine:
    def test_engine_init_and_tables(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        with engine._get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
        assert "judicial_record_requests" in tables
        assert "criminal_conviction_records" in tables
        assert "record_clearance_evaluations" in tables
        assert "prohibition_orders" in tables
        assert "issued_certificates" in tables
        assert "compliance_audit_logs" in tables

    def test_request_certificate_form_1_success(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        req = engine.request_certificate(
            form_type="FORM_1",
            citizen_name="Nguyễn Văn Hùng",
            citizen_id="001088001234",
            dob="1988-06-15",
            gender="MALE",
            permanent_address="Số 25 Lý Thường Kiệt, Hoàn Kiếm, Hà Nội",
            current_address="Số 25 Lý Thường Kiệt, Hoàn Kiếm, Hà Nội",
            request_purpose="Xin việc làm và công chứng",
            vneid_verified=True,
        )
        assert req["request_id"].startswith("REQ-LLTP-")
        assert req["form_type"] == "FORM_1"
        assert req["citizen_name"] == "Nguyễn Văn Hùng"
        assert req["vneid_verified"] == 1
        assert req["competent_authority"] == "Sở Tư pháp Thành phố Hà Nội"
        assert req["status"] == "SUBMITTED"

    def test_request_certificate_form_2_success(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        req = engine.request_certificate(
            form_type="FORM_2",
            citizen_name="Trần Thị Mai",
            citizen_id="001190005678",
            dob="1990-09-20",
            gender="FEMALE",
            permanent_address="Quận 1, TP. Hồ Chí Minh",
            current_address="Quận 1, TP. Hồ Chí Minh",
            request_purpose="Phục vụ tố tụng hình sự",
            vneid_verified=True,
            include_prohibition=True,
        )
        assert req["form_type"] == "FORM_2"
        assert req["include_prohibition"] == 1

    def test_request_certificate_validation_errors(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Citizen full name cannot be empty"):
            engine.request_certificate("FORM_1", "", "123", "1990-01-01", "MALE", "Addr", "Addr")
        with pytest.raises(ValueError, match="Citizen ID .* cannot be empty"):
            engine.request_certificate("FORM_1", "Name", "", "1990-01-01", "MALE", "Addr", "Addr")
        with pytest.raises(ValueError, match="Date of birth cannot be empty"):
            engine.request_certificate("FORM_1", "Name", "123", "", "MALE", "Addr", "Addr")
        with pytest.raises(ValueError, match="Gender cannot be empty"):
            engine.request_certificate("FORM_1", "Name", "123", "1990-01-01", "", "Addr", "Addr")
        with pytest.raises(ValueError, match="Permanent address cannot be empty"):
            engine.request_certificate("FORM_1", "Name", "123", "1990-01-01", "MALE", "", "Addr")
        with pytest.raises(ValueError, match="Current residential address cannot be empty"):
            engine.request_certificate("FORM_1", "Name", "123", "1990-01-01", "MALE", "Addr", "")
        with pytest.raises(ValueError, match="Invalid form type"):
            engine.request_certificate("INVALID_FORM", "Name", "123", "1990-01-01", "MALE", "Addr", "Addr")

    def test_record_conviction_success(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        conv = engine.record_conviction(
            citizen_id="001088001234",
            court_judgment_number="45/2020/HS-ST",
            deciding_court="Tòa án nhân dân TP Hà Nội",
            judgment_date="2020-05-15",
            offense_name="Vi phạm quy định về tham gia giao thông đường bộ",
            severity="LESS_SERIOUS",
            primary_penalty="01 năm tù cho hưởng án treo, thử thách 02 năm",
            penalty_completed_date="2022-05-15",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )
        assert conv["conviction_id"].startswith("CONV-")
        assert conv["severity"] == "LESS_SERIOUS"
        assert conv["civil_obligation_completed"] == 1
        assert conv["court_fee_completed"] == 1

    def test_record_conviction_validation_errors(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Citizen ID cannot be empty"):
            engine.record_conviction("", "45/2020", "Court", "2020-01-01", "Offense", "SERIOUS", "Penalty", "2022-01-01")
        with pytest.raises(ValueError, match="Court judgment number cannot be empty"):
            engine.record_conviction("ID", "", "Court", "2020-01-01", "Offense", "SERIOUS", "Penalty", "2022-01-01")
        with pytest.raises(ValueError, match="Invalid severity"):
            engine.record_conviction("ID", "45/2020", "Court", "2020-01-01", "Offense", "SUPER_SERIOUS", "Penalty", "2022-01-01")

    def test_evaluate_clearance_article_70_automatic_success(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        # Less serious crime: 1 year required. Penalty completed 2022-05-15, reference date 2024-01-01 (> 1.5 yrs) -> CLEARED
        conv = engine.record_conviction(
            citizen_id="001088001234",
            court_judgment_number="45/2020/HS-ST",
            deciding_court="TAND TP Hà Nội",
            judgment_date="2020-05-15",
            offense_name="Tội phạm ít nghiêm trọng",
            severity="LESS_SERIOUS",
            primary_penalty="06 tháng tù",
            penalty_completed_date="2021-01-01",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )
        eval_res = engine.evaluate_clearance(
            conviction_id=conv["conviction_id"],
            reference_date="2023-01-01",
        )
        assert eval_res["clearance_status"] == "CLEARED"
        assert eval_res["statutory_years_required"] == 1
        assert eval_res["years_elapsed"] >= 1.0

    def test_evaluate_clearance_article_70_time_not_enough(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        # Particularly serious crime: 5 years required. Completed 2022-01-01, ref date 2024-01-01 (only 2 yrs) -> ACTIVE_RECORD
        conv = engine.record_conviction(
            citizen_id="001099009999",
            court_judgment_number="88/2021/HS-ST",
            deciding_court="TAND Cấp cao",
            judgment_date="2021-01-01",
            offense_name="Tội phạm đặc biệt nghiêm trọng",
            severity="PARTICULARLY_SERIOUS",
            primary_penalty="16 năm tù",
            penalty_completed_date="2022-01-01",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )
        eval_res = engine.evaluate_clearance(
            conviction_id=conv["conviction_id"],
            reference_date="2024-01-01",
        )
        assert eval_res["clearance_status"] == "ACTIVE_RECORD"
        assert eval_res["statutory_years_required"] == 5
        assert eval_res["years_elapsed"] < 5.0

    def test_evaluate_clearance_unfulfilled_obligations(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        # Even if enough years elapsed, unpaid civil damages keep record active
        conv = engine.record_conviction(
            citizen_id="001088005555",
            court_judgment_number="12/2015/HS-ST",
            deciding_court="TAND Quận 1",
            judgment_date="2015-01-01",
            offense_name="Trộm cắp tài sản",
            severity="LESS_SERIOUS",
            primary_penalty="01 năm tù",
            penalty_completed_date="2016-01-01",
            civil_obligation_completed=False,  # Unpaid damages
            court_fee_completed=True,
        )
        eval_res = engine.evaluate_clearance(
            conviction_id=conv["conviction_id"],
            reference_date="2024-01-01",
        )
        assert eval_res["clearance_status"] == "ACTIVE_RECORD"
        assert "Chưa hoàn thành hình phạt bổ sung" in eval_res["legal_basis"]

    def test_evaluate_clearance_recidivism(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        conv = engine.record_conviction(
            citizen_id="001088006666",
            court_judgment_number="33/2018/HS-ST",
            deciding_court="TAND Hà Nội",
            judgment_date="2018-01-01",
            offense_name="Đánh bạc",
            severity="LESS_SERIOUS",
            primary_penalty="Phạt tiền",
            penalty_completed_date="2018-06-01",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )
        eval_res = engine.evaluate_clearance(
            conviction_id=conv["conviction_id"],
            reference_date="2024-01-01",
            recidivism_committed=True,
        )
        assert eval_res["clearance_status"] == "ACTIVE_RECORD"
        assert "tái phạm hoặc phạm tội mới" in eval_res["legal_basis"]

    def test_evaluate_clearance_court_decision_override(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        conv = engine.record_conviction(
            citizen_id="001088007777",
            court_judgment_number="10/2021/HS-ST",
            deciding_court="TAND TP Đà Nẵng",
            judgment_date="2021-01-01",
            offense_name="Xâm phạm an ninh quốc gia",
            severity="VERY_SERIOUS",
            primary_penalty="05 năm tù",
            penalty_completed_date="2023-01-01",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )
        eval_res = engine.evaluate_clearance(
            conviction_id=conv["conviction_id"],
            court_decision_ref="02/2024/QĐ-XAT của TAND TP Đà Nẵng",
        )
        assert eval_res["clearance_status"] == "CLEARED"
        assert "Xóa án tích theo Quyết định Tòa án" in eval_res["legal_basis"]

    def test_record_prohibition_success(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        prohib = engine.record_prohibition(
            citizen_id="001088001234",
            prohibition_type="Cấm đảm nhiệm chức vụ quản lý doanh nghiệp",
            issuing_court="TAND Cấp cao tại Hà Nội",
            judgment_number="15/2021/KDTM-PT",
            start_date="2021-06-01",
            end_date="2026-06-01",
            details="Cấm làm Giám đốc, Tổng giám đốc theo Luật Phá sản 2014",
        )
        assert prohib["prohibition_id"].startswith("PROHIB-")
        assert prohib["status"] == "ACTIVE"

    def test_issue_certificate_form_1_clean_record(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        req = engine.request_certificate(
            form_type="FORM_1",
            citizen_name="Lê Minh Tâm",
            citizen_id="001095000111",
            dob="1995-01-01",
            gender="MALE",
            permanent_address="Quận Đống Đa, Hà Nội",
            current_address="Quận Đống Đa, Hà Nội",
        )
        cert = engine.issue_certificate(request_id=req["request_id"])
        assert cert["certificate_id"].startswith("CERT-LLTP-")
        assert cert["form_type"] == "FORM_1"
        assert cert["criminal_record_entry"] == "Không có án tích"
        assert "Không yêu cầu xác nhận" in cert["prohibition_entry"]
        assert cert["status"] == "ISSUED"

        # Check request updated to ISSUED
        updated_req = engine.get_record("request", req["request_id"])
        assert updated_req["status"] == "ISSUED"

    def test_issue_certificate_form_1_cleared_record(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        citizen_id = "001080000222"
        # Conviction completed in 2015, less serious -> Cleared
        engine.record_conviction(
            citizen_id=citizen_id,
            court_judgment_number="01/2014/HS-ST",
            deciding_court="TAND Quận Hoàn Kiếm",
            judgment_date="2014-01-01",
            offense_name="Trộm cắp vặt",
            severity="LESS_SERIOUS",
            primary_penalty="06 tháng cải tạo không giam giữ",
            penalty_completed_date="2014-07-01",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )

        req = engine.request_certificate(
            form_type="FORM_1",
            citizen_name="Trương Quốc Huy",
            citizen_id=citizen_id,
            dob="1980-05-05",
            gender="MALE",
            permanent_address="Hà Nội",
            current_address="Hà Nội",
        )
        cert = engine.issue_certificate(request_id=req["request_id"])
        # Form 1 for person with all cleared convictions shows "Không có án tích" under Art 41
        assert cert["criminal_record_entry"] == "Không có án tích"

    def test_issue_certificate_form_1_active_conviction(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        citizen_id = "001080000333"
        # Serious crime completed recently -> Active record
        engine.record_conviction(
            citizen_id=citizen_id,
            court_judgment_number="99/2025/HS-ST",
            deciding_court="TAND Hà Nội",
            judgment_date="2025-01-01",
            offense_name="Cố ý gây thương tích",
            severity="SERIOUS",
            primary_penalty="04 năm tù",
            penalty_completed_date="2025-12-01",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )

        req = engine.request_certificate(
            form_type="FORM_1",
            citizen_name="Ngô Bá Khá",
            citizen_id=citizen_id,
            dob="1980-01-01",
            gender="MALE",
            permanent_address="Bắc Ninh",
            current_address="Bắc Ninh",
        )
        cert = engine.issue_certificate(request_id=req["request_id"])
        assert "Có án tích:" in cert["criminal_record_entry"]
        assert "99/2025/HS-ST" in cert["criminal_record_entry"]

    def test_issue_certificate_form_2_full_history(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        citizen_id = "001080000444"
        # 1 conviction cleared, 1 conviction active
        engine.record_conviction(
            citizen_id=citizen_id,
            court_judgment_number="11/2010/HS-ST",
            deciding_court="TAND Quận 1",
            judgment_date="2010-01-01",
            offense_name="Gây rối trật tự công cộng",
            severity="LESS_SERIOUS",
            primary_penalty="Cảnh cáo",
            penalty_completed_date="2010-02-01",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )
        engine.record_prohibition(
            citizen_id=citizen_id,
            prohibition_type="Cấm hành nghề y",
            issuing_court="TAND Cấp cao",
            judgment_number="22/2022/HS-PT",
            start_date="2022-01-01",
            details="Cấm hành nghề 05 năm",
        )

        req = engine.request_certificate(
            form_type="FORM_2",
            citizen_name="Vũ Đức Đam",
            citizen_id=citizen_id,
            dob="1975-01-01",
            gender="MALE",
            permanent_address="Hải Dương",
            current_address="Hà Nội",
        )
        cert = engine.issue_certificate(request_id=req["request_id"])
        assert cert["form_type"] == "FORM_2"
        assert "Lịch sử án tích (Đầy đủ):" in cert["criminal_record_entry"]
        assert "Đã được xóa án tích" in cert["criminal_record_entry"]
        assert "Cấm hành nghề y" in cert["prohibition_entry"]

    def test_get_record_and_list_records(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        req = engine.request_certificate(
            form_type="FORM_1",
            citizen_name="Citizen Test",
            citizen_id="001099999999",
            dob="1999-09-09",
            gender="FEMALE",
            permanent_address="Hà Nội",
            current_address="Hà Nội",
        )
        fetched = engine.get_record("request", req["request_id"])
        assert fetched["request_id"] == req["request_id"]

        with pytest.raises(KeyError):
            engine.get_record("request", "NON-EXISTENT-ID")

        with pytest.raises(ValueError, match="Unknown category"):
            engine.get_record("unknown_cat", "ID")

        reqs = engine.list_records("request", limit=10)
        assert len(reqs) >= 1

        audits = engine.list_records("audit", limit=10)
        assert len(audits) >= 1
        assert "entity_type" in audits[0]

    def test_get_telemetry_status(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        status = engine.get_telemetry_status()
        assert status["system_status"] == "ONLINE_HEALTHY"
        assert "statutory_framework" in status
        assert "central_authority" in status
        assert "total_certificate_requests" in status
        assert "form_1_requests" in status
        assert "form_2_requests" in status
        assert "vneid_verified_requests" in status
        assert "criminal_convictions_recorded" in status
        assert "clearance_evaluations_performed" in status
        assert "cleared_criminal_records" in status
        assert "active_prohibition_orders" in status
        assert "issued_certificates_total" in status
        assert "audit_logs_count" in status


class TestJudicialRecordCli:
    def test_cli_help(self):
        runner = CliRunner()
        res = runner.invoke(judicialrecord_app, ["--help"])
        assert res.exit_code == 0
        assert "Vietnamese Judicial Records & Criminal Clearance Suite" in res.output

    def test_cli_status_console_and_json(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(judicialrecord_app, ["status"])
        assert res.exit_code == 0
        assert "QUẢN LÝ LÝ LỊCH TƯ PHÁP" in res.output

        res_cb = runner.invoke(judicialrecord_app, [])
        assert res_cb.exit_code == 0
        assert "QUẢN LÝ LÝ LỊCH TƯ PHÁP" in res_cb.output

        res_json = runner.invoke(judicialrecord_app, ["status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["system_status"] == "ONLINE_HEALTHY"

    def test_cli_request_form_1(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(judicialrecord_app, [
            "request",
            "--form", "FORM_1",
            "--name", "Đinh Tiên Hoàng",
            "--id", "001090001111",
            "--dob", "1990-01-01",
            "--gender", "MALE",
            "--permanent", "Ninh Bình",
            "--current", "Hà Nội",
            "--vneid",
        ])
        assert res.exit_code == 0
        assert "✓ Judicial Record Request Submitted:" in res.output

    def test_cli_request_form_2_json(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(judicialrecord_app, [
            "request",
            "--form", "FORM_2",
            "--name", "Lê Đại Hành",
            "--id", "001091002222",
            "--dob", "1991-02-02",
            "--gender", "MALE",
            "--permanent", "Thanh Hóa",
            "--current", "Hà Nội",
            "--prohibition",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["request_id"].startswith("REQ-LLTP-")
        assert data["form_type"] == "FORM_2"

    def test_cli_conviction_cmd(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(judicialrecord_app, [
            "conviction",
            "--id", "001091002222",
            "--judgment", "12/2021/HS-ST",
            "--court", "TAND Tỉnh Thanh Hóa",
            "--date", "2021-03-03",
            "--offense", "Vi phạm quy định về đất đai",
            "--severity", "SERIOUS",
            "--primary-penalty", "03 năm tù",
            "--penalty-completed-date", "2024-03-03",
            "--civil",
            "--fees",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["conviction_id"].startswith("CONV-")
        assert data["severity"] == "SERIOUS"

    def test_cli_clearance_cmd(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        conv = engine.record_conviction(
            citizen_id="001092003333",
            court_judgment_number="09/2018/HS-ST",
            deciding_court="TAND TP Hà Nội",
            judgment_date="2018-01-01",
            offense_name="Tội ít nghiêm trọng",
            severity="LESS_SERIOUS",
            primary_penalty="01 năm cải tạo",
            penalty_completed_date="2019-01-01",
            civil_obligation_completed=True,
            court_fee_completed=True,
        )

        runner = CliRunner()
        res = runner.invoke(judicialrecord_app, [
            "clearance",
            "--conviction-id", conv["conviction_id"],
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["clearance_status"] == "CLEARED"

    def test_cli_prohibition_cmd(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(judicialrecord_app, [
            "prohibition",
            "--id", "001092003333",
            "--type", "Cấm thành lập quản lý doanh nghiệp",
            "--court", "TAND TP Hà Nội",
            "--judgment", "05/2022/KDTM-ST",
            "--start-date", "2022-01-01",
            "--details", "Cấm làm người đại diện theo pháp luật",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["prohibition_id"].startswith("PROHIB-")
        assert data["status"] == "ACTIVE"

    def test_cli_issue_cmd(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        req = engine.request_certificate(
            form_type="FORM_1",
            citizen_name="Lý Thái Tổ",
            citizen_id="001093004444",
            dob="1993-04-04",
            gender="MALE",
            permanent_address="Bắc Ninh",
            current_address="Hà Nội",
        )

        runner = CliRunner()
        res = runner.invoke(judicialrecord_app, [
            "issue",
            "--request-id", req["request_id"],
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["certificate_id"].startswith("CERT-LLTP-")
        assert data["status"] == "ISSUED"
        assert data["criminal_record_entry"] == "Không có án tích"

    def test_cli_list_cmd(self, temp_db: str):
        engine = JudicialRecordEngine(db_path=temp_db)
        engine.request_certificate(
            form_type="FORM_1",
            citizen_name="Trần Hưng Đạo",
            citizen_id="001094005555",
            dob="1994-05-05",
            gender="MALE",
            permanent_address="Nam Định",
            current_address="Hà Nội",
        )

        runner = CliRunner()
        res_table = runner.invoke(judicialrecord_app, ["list", "--category", "request"])
        assert res_table.exit_code == 0
        assert "Judicial Records" in res_table.output

        res_json = runner.invoke(judicialrecord_app, ["list", "--category", "request", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert len(data) >= 1

    def test_cli_alias_lylich_and_criminalrecord(self, temp_db: str):
        root_app = build_app()
        runner = CliRunner()
        res_lylich = runner.invoke(root_app, ["lylich", "status", "--json"])
        assert res_lylich.exit_code == 0
        data_l = json.loads(res_lylich.output)
        assert data_l["system_status"] == "ONLINE_HEALTHY"

        res_crim = runner.invoke(root_app, ["criminalrecord", "status", "--json"])
        assert res_crim.exit_code == 0
        data_c = json.loads(res_crim.output)
        assert data_c["system_status"] == "ONLINE_HEALTHY"


class TestJudicialRecordMcpParity:
    def test_scripts_mcp_server_handlers(self, temp_db: str):
        from scripts.mcp_server import (
            handle_judicialrecord_request,
            handle_judicialrecord_conviction,
            handle_judicialrecord_clearance,
            handle_judicialrecord_prohibition,
            handle_judicialrecord_issue,
            handle_judicialrecord_list,
            handle_judicialrecord_status,
            CORE_TOOLS_SPEC,
            CORE_HANDLERS,
        )

        # 1. Spec check
        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_judicialrecord_request" in tool_names
        assert "mekong_judicialrecord_conviction" in tool_names
        assert "mekong_judicialrecord_clearance" in tool_names
        assert "mekong_judicialrecord_prohibition" in tool_names
        assert "mekong_judicialrecord_issue" in tool_names
        assert "mekong_judicialrecord_list" in tool_names
        assert "mekong_judicialrecord_status" in tool_names

        # 2. Handlers mapping check
        assert "mekong_judicialrecord_request" in CORE_HANDLERS
        assert "judicialrecord_request" in CORE_HANDLERS
        assert "mekong_judicialrecord_status" in CORE_HANDLERS
        assert "judicialrecord_status" in CORE_HANDLERS

        # 3. Execution check
        res_req = handle_judicialrecord_request({
            "form_type": "FORM_1",
            "citizen_name": "Quang Trung",
            "citizen_id": "001096006666",
            "dob": "1996-06-06",
            "gender": "MALE",
            "permanent_address": "Bình Định",
            "current_address": "Hà Nội",
        })
        data_req = json.loads(res_req)
        assert data_req["request_id"].startswith("REQ-LLTP-")
        req_id = data_req["request_id"]

        res_conv = handle_judicialrecord_conviction({
            "citizen_id": "001096006666",
            "court_judgment_number": "08/2016/HS-ST",
            "deciding_court": "TAND TP Quy Nhơn",
            "judgment_date": "2016-01-01",
            "offense_name": "Tội ít nghiêm trọng",
            "severity": "LESS_SERIOUS",
            "primary_penalty": "Cải tạo 06 tháng",
            "penalty_completed_date": "2016-07-01",
        })
        data_conv = json.loads(res_conv)
        assert data_conv["conviction_id"].startswith("CONV-")
        conv_id = data_conv["conviction_id"]

        res_clear = handle_judicialrecord_clearance({
            "conviction_id": conv_id,
        })
        data_clear = json.loads(res_clear)
        assert data_clear["clearance_status"] == "CLEARED"

        res_prohib = handle_judicialrecord_prohibition({
            "citizen_id": "001096006666",
            "prohibition_type": "Cấm quản lý hợp tác xã",
            "issuing_court": "TAND Tỉnh Bình Định",
            "judgment_number": "01/2020/KDTM-ST",
            "start_date": "2020-01-01",
            "details": "Cấm quản lý trong 03 năm",
        })
        data_prohib = json.loads(res_prohib)
        assert data_prohib["prohibition_id"].startswith("PROHIB-")

        res_iss = handle_judicialrecord_issue({
            "request_id": req_id,
        })
        data_iss = json.loads(res_iss)
        assert data_iss["certificate_id"].startswith("CERT-LLTP-")
        assert data_iss["criminal_record_entry"] == "Không có án tích"

        res_list = handle_judicialrecord_list({"category": "request", "limit": 10})
        data_list = json.loads(res_list)
        assert isinstance(data_list, list)
        assert len(data_list) >= 1

        res_st = handle_judicialrecord_status({})
        data_st = json.loads(res_st)
        assert data_st["system_status"] == "ONLINE_HEALTHY"

    def test_core_mcp_server_handlers(self, temp_db: str):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-judicialrecord-server")

        res_req = server._handle_judicialrecord_request(
            form_type="FORM_2",
            citizen_name="Nguyễn Huệ",
            citizen_id="001097007777",
            dob="1997-07-07",
            gender="MALE",
            permanent_address="Bình Định",
            current_address="Hà Nội",
        )
        data_req = json.loads(res_req)
        assert data_req["request_id"].startswith("REQ-LLTP-")
        req_id = data_req["request_id"]

        res_conv = server._handle_judicialrecord_conviction(
            citizen_id="001097007777",
            court_judgment_number="02/2019/HS-ST",
            deciding_court="TAND Tỉnh Gia Lai",
            judgment_date="2019-01-01",
            offense_name="Vi phạm giao thông",
            severity="LESS_SERIOUS",
            primary_penalty="Phạt tiền 10 triệu đồng",
            penalty_completed_date="2019-02-01",
        )
        data_conv = json.loads(res_conv)
        assert data_conv["conviction_id"].startswith("CONV-")

        res_iss = server._handle_judicialrecord_issue(request_id=req_id)
        data_iss = json.loads(res_iss)
        assert data_iss["certificate_id"].startswith("CERT-LLTP-")

        res_list = server._handle_judicialrecord_list(category="certificate", limit=5)
        data_list = json.loads(res_list)
        assert isinstance(data_list, list)
        assert len(data_list) >= 1

        res_st = server._handle_judicialrecord_status()
        data_st = json.loads(res_st)
        assert data_st["system_status"] == "ONLINE_HEALTHY"
        assert "total_certificate_requests" in data_st
