"""
Test suite for Vietnamese Child Adoption & Hague Intercountry Adoption Suite (Phase 144).
Compliant with:
- Law on Adoption 2010 (Luật Nuôi con nuôi - Law No. 52/2010/QH12)
- Decree No. 19/2011/ND-CP & Decree No. 24/2019/ND-CP
- Circular No. 10/2020/TT-BTP
- 1993 Hague Convention on Protection of Children and Co-operation in Respect of Intercountry Adoption

Covers:
- AdoptionEngine (pure standard library, SQLite WAL persistence, age checks, consent, Hague dossiers, 3-year post-placement, certificates, terminations).
- CLI surface (mekong adoption / mekong connuoi: apply, intercountry, report, certificate, terminate, list, status).
- MCP parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.adoption_engine import (
    AdoptionEngine,
    AdoptionType,
    AdopterRelationship,
    AdoptionStatus,
    PostPlacementRating,
)
from src.cli.commands.adoption_command import adoption_app
from src.cli.app_setup import build_app


@pytest.fixture
def temp_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_adoption.db")
        monkeypatch.setenv("MEKONG_ADOPTION_DB", db_path)
        yield db_path


class TestAdoptionEngine:
    def test_engine_init_and_tables(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        with engine._get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
        assert "adoption_applications" in tables
        assert "intercountry_dossiers" in tables
        assert "post_placement_reports" in tables
        assert "adoption_certificates" in tables
        assert "adoption_terminations" in tables
        assert "compliance_audit_logs" in tables

    def test_apply_domestic_valid(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        res = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Nguyễn Văn A",
            adopter_dob="1985-05-15",
            adopter_id="001085001234",
            child_name="Nguyễn Thị Bé",
            child_dob="2018-06-20",
            child_gender="FEMALE",
            child_origin="Trung tâm Bảo trợ Xã hội số 1 Hà Nội",
            relationship="UNRELATED",
            adopter_nationality="Việt Nam",
            adopter_marital_status="MARRIED",
            co_adopter_name="Trần Thị B",
            co_adopter_dob="1987-08-22",
            co_adopter_id="001187005678",
            biological_parents_consent=True,
            child_consent=True,
        )
        assert res["application_id"].startswith("ADP-")
        assert res["adoption_type"] == "DOMESTIC"
        assert res["relationship"] == "UNRELATED"
        assert res["status"] == "SUBMITTED"
        assert res["adopter_name"] == "Nguyễn Văn A"
        assert res["child_name"] == "Nguyễn Thị Bé"
        assert res["competent_authority"] == "UBND Phường Hàng Bài, Hoàn Kiếm, Hà Nội"

    def test_apply_child_age_over_18_rejected(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="18 years of age or older cannot be adopted"):
            engine.apply_adoption(
                adoption_type="DOMESTIC",
                adopter_name="Lê Văn C",
                adopter_dob="1970-01-01",
                adopter_id="001070001111",
                child_name="Lê Văn D",
                child_dob="2004-01-01",  # >= 18 years
                child_gender="MALE",
                child_origin="Gia đình",
                relationship="UNRELATED",
            )

    def test_apply_child_16_to_18_unrelated_rejected(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Children aged 16 to under 18 can only be adopted by step-parent"):
            engine.apply_adoption(
                adoption_type="DOMESTIC",
                adopter_name="Hoàng Văn E",
                adopter_dob="1975-02-10",
                adopter_id="001075002222",
                child_name="Hoàng Thị F",
                child_dob="2009-01-10",  # ~17 years old
                child_gender="FEMALE",
                child_origin="Gia đình",
                relationship="UNRELATED",
            )

    def test_apply_child_16_to_18_step_parent_allowed(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        res = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Phạm Văn G",
            adopter_dob="1980-03-15",
            adopter_id="001080003333",
            child_name="Trần Văn H",
            child_dob="2009-03-01",  # ~17 years old
            child_gender="MALE",
            child_origin="Gia đình",
            relationship="STEP_PARENT",
            biological_parents_consent=True,
            child_consent=True,
        )
        assert res["relationship"] == "STEP_PARENT"
        assert res["status"] == "SUBMITTED"

    def test_apply_child_16_to_18_aunt_uncle_allowed(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        res = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Vũ Thị K",
            adopter_dob="1982-04-20",
            adopter_id="001182004444",
            child_name="Vũ Văn L",
            child_dob="2009-02-01",
            child_gender="MALE",
            child_origin="Gia đình",
            relationship="NATURAL_AUNT_UNCLE",
            biological_parents_consent=True,
            child_consent=True,
        )
        assert res["relationship"] == "NATURAL_AUNT_UNCLE"

    def test_apply_adopter_age_gap_unrelated_rejected(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="at least 20 years older"):
            engine.apply_adoption(
                adoption_type="DOMESTIC",
                adopter_name="Đặng Văn M",
                adopter_dob="2000-01-01",  # 26 years old
                adopter_id="001100005555",
                child_name="Đặng Thị N",
                child_dob="2015-01-01",  # 11 years old -> age gap 15 < 20
                child_gender="FEMALE",
                child_origin="Trung tâm",
                relationship="UNRELATED",
            )

    def test_apply_adopter_age_gap_step_parent_exempt(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        # 15-year gap is acceptable for step-parents
        res = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Bùi Văn P",
            adopter_dob="2000-01-01",
            adopter_id="001100006666",
            child_name="Bùi Thị Q",
            child_dob="2015-01-01",
            child_gender="FEMALE",
            child_origin="Gia đình",
            relationship="STEP_PARENT",
            biological_parents_consent=True,
            child_consent=True,
        )
        assert res["relationship"] == "STEP_PARENT"

    def test_apply_child_consent_at_9_required(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        # Child is ~11 years old, child_consent=False must raise ValueError
        with pytest.raises(ValueError, match="Child aged 9 or older .* must give direct consent"):
            engine.apply_adoption(
                adoption_type="DOMESTIC",
                adopter_name="Đỗ Văn R",
                adopter_dob="1975-01-01",
                adopter_id="001075007777",
                child_name="Đỗ Thị S",
                child_dob="2015-01-01",
                child_gender="FEMALE",
                child_origin="Trung tâm",
                relationship="UNRELATED",
                child_consent=False,
            )

        # Child under 9 (e.g. 5 years old) does not raise even if child_consent is False
        res = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Đỗ Văn R",
            adopter_dob="1975-01-01",
            adopter_id="001075007777",
            child_name="Đỗ Văn T",
            child_dob="2021-01-01",  # 5 years old
            child_gender="MALE",
            child_origin="Trung tâm",
            relationship="UNRELATED",
            child_consent=False,
        )
        assert res["child_name"] == "Đỗ Văn T"

    def test_apply_biological_consent_required(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Adoption requires statutory consent of natural parents"):
            engine.apply_adoption(
                adoption_type="DOMESTIC",
                adopter_name="Hồ Văn U",
                adopter_dob="1980-01-01",
                adopter_id="001080008888",
                child_name="Hồ Văn V",
                child_dob="2020-01-01",
                child_gender="MALE",
                child_origin="Trung tâm",
                relationship="UNRELATED",
                biological_parents_consent=False,
            )

    def test_apply_validation_errors(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Adopter full name cannot be empty"):
            engine.apply_adoption("DOMESTIC", "", "1980-01-01", "123", "Child", "2020-01-01", "MALE", "Origin")
        with pytest.raises(ValueError, match="Child full name cannot be empty"):
            engine.apply_adoption("DOMESTIC", "Adopter", "1980-01-01", "123", "", "2020-01-01", "MALE", "Origin")
        with pytest.raises(ValueError, match="Invalid adoption type"):
            engine.apply_adoption("UNKNOWN_TYPE", "Adopter", "1980-01-01", "123", "Child", "2020-01-01", "MALE", "Origin")
        with pytest.raises(ValueError, match="Invalid relationship"):
            engine.apply_adoption("DOMESTIC", "Adopter", "1980-01-01", "123", "Child", "2020-01-01", "MALE", "Origin", relationship="UNKNOWN_REL")

    def test_process_intercountry_success(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="INTERCOUNTRY",
            adopter_name="John Michael Smith",
            adopter_dob="1978-07-12",
            adopter_id="USA-PASS-998877",
            child_name="Nguyễn Mai Linh",
            child_dob="2020-09-15",
            child_gender="FEMALE",
            child_origin="Làng Trẻ em SOS Việt Trì, Phú Thọ",
            adopter_nationality="Hoa Kỳ",
            adopter_marital_status="MARRIED",
            co_adopter_name="Sarah Jane Smith",
            co_adopter_dob="1980-11-25",
            co_adopter_id="USA-PASS-998878",
            relationship="UNRELATED",
        )
        assert app_rec["status"] == "SUBMITTED"

        dossier = engine.process_intercountry(
            application_id=app_rec["application_id"],
            foreign_country="United States",
            foreign_central_authority="Office of Children's Issues - US Department of State",
            accredited_adoption_agency="Holt International Children's Services",
            home_study_date="2025-11-10",
            department_approval_number="98/CCN-BTP",
            provincial_decision_number="1245/QD-UBND-PT",
            hague_compliant=True,
            handover_date="2026-04-15",
            notes="Full dossier completed with Hague accreditation certificate.",
        )
        assert dossier["dossier_id"].startswith("HAGUE-")
        assert dossier["application_id"] == app_rec["application_id"]
        assert dossier["foreign_country"] == "United States"
        assert dossier["hague_compliant"] == 1
        assert dossier["status"] == "APPROVED"

        # Check application status updated to APPROVED
        updated_app = engine.get_record("application", app_rec["application_id"])
        assert updated_app["status"] == "APPROVED"

    def test_process_intercountry_on_domestic_rejected(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Trần Văn M",
            adopter_dob="1980-01-01",
            adopter_id="001080009999",
            child_name="Trần Bé Con",
            child_dob="2021-01-01",
            child_gender="MALE",
            child_origin="Gia đình",
            relationship="UNRELATED",
        )
        with pytest.raises(ValueError, match="is marked as DOMESTIC, not INTERCOUNTRY"):
            engine.process_intercountry(
                application_id=app_rec["application_id"],
                foreign_country="France",
                foreign_central_authority="French Central Authority",
                accredited_adoption_agency="Agency XYZ",
                home_study_date="2025-01-01",
                department_approval_number="123/CCN",
                provincial_decision_number="456/QD",
            )

    def test_submit_post_placement_report_success(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Lê Hồng Sơn",
            adopter_dob="1978-02-15",
            adopter_id="001078000111",
            child_name="Lê Thùy Dương",
            child_dob="2022-04-10",
            child_gender="FEMALE",
            child_origin="Trung tâm",
            relationship="UNRELATED",
        )
        rep = engine.submit_post_placement_report(
            application_id=app_rec["application_id"],
            reporting_period_months=6,
            health_status="Sức khỏe tốt, tiêm chủng đầy đủ, thể trạng phát triển chuẩn WHO",
            educational_adaptation="Tham gia trường mầm non hòa nhập tốt, nói sõi tiếng Việt",
            psychological_state="Vui vẻ, gắn kết tình cảm sâu sắc với cha mẹ nuôi",
            assessor_name="Trần Mai Chi",
            assessor_organization="Phòng LĐ-TB&XH Quận Hoàn Kiếm",
            welfare_rating="EXCELLENT",
            recommendations="Tiếp tục theo dõi chu kỳ 12 tháng",
        )
        assert rep["report_id"].startswith("POST-")
        assert rep["reporting_period_months"] == 6
        assert rep["welfare_rating"] == "EXCELLENT"

    def test_submit_post_placement_report_invalid_period(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Lê Hồng Sơn",
            adopter_dob="1978-02-15",
            adopter_id="001078000111",
            child_name="Lê Thùy Dương",
            child_dob="2022-04-10",
            child_gender="FEMALE",
            child_origin="Trung tâm",
            relationship="UNRELATED",
        )
        with pytest.raises(ValueError, match="Reporting period must be 6, 12, 18, 24, 30, or 36 months"):
            engine.submit_post_placement_report(
                application_id=app_rec["application_id"],
                reporting_period_months=9,  # invalid period
                health_status="Good",
                educational_adaptation="Good",
                psychological_state="Good",
                assessor_name="Assessor",
                assessor_organization="Org",
            )

    def test_submit_post_placement_report_invalid_rating(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Lê Hồng Sơn",
            adopter_dob="1978-02-15",
            adopter_id="001078000111",
            child_name="Lê Thùy Dương",
            child_dob="2022-04-10",
            child_gender="FEMALE",
            child_origin="Trung tâm",
            relationship="UNRELATED",
        )
        with pytest.raises(ValueError, match="Invalid welfare rating"):
            engine.submit_post_placement_report(
                application_id=app_rec["application_id"],
                reporting_period_months=12,
                health_status="Good",
                educational_adaptation="Good",
                psychological_state="Good",
                assessor_name="Assessor",
                assessor_organization="Org",
                welfare_rating="SUPER_EXCELLENT",
            )

    def test_issue_adoption_certificate_success(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Đoàn Trọng Kim",
            adopter_dob="1976-06-25",
            adopter_id="001076000222",
            child_name="Nguyễn Bảo Nam",
            child_dob="2023-01-10",
            child_gender="MALE",
            child_origin="Bệnh viện Phụ sản Hà Nội",
            relationship="UNRELATED",
        )
        cert = engine.issue_adoption_certificate(
            application_id=app_rec["application_id"],
            child_new_name="Đoàn Bảo Kim Nam",
            issuing_authority="UBND Phường Hàng Bài, Hoàn Kiếm, Hà Nội",
        )
        assert cert["certificate_id"].startswith("CERT-")
        assert cert["child_new_name"] == "Đoàn Bảo Kim Nam"
        assert cert["adopter_full_name"] == "Đoàn Trọng Kim"
        assert cert["digital_signature"].startswith("DIGITAL-SIG-MOJ-ADOPT-")
        assert cert["status"] == "VALID"

        # Check application status updated to REGISTERED
        updated_app = engine.get_record("application", app_rec["application_id"])
        assert updated_app["status"] == "REGISTERED"

    def test_terminate_adoption_success(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Phan Văn X",
            adopter_dob="1970-01-01",
            adopter_id="001070000333",
            child_name="Phan Văn Y",
            child_dob="2020-01-01",
            child_gender="MALE",
            child_origin="Gia đình",
            relationship="UNRELATED",
        )
        cert = engine.issue_adoption_certificate(application_id=app_rec["application_id"])
        assert cert["status"] == "VALID"

        term = engine.terminate_adoption(
            application_id=app_rec["application_id"],
            court_judgment_number="12/2026/HNGĐ-ST",
            court_name="Tòa án nhân dân TP Hà Nội",
            grounds="Cha mẹ nuôi ngược đãi, hành hạ con nuôi theo quy định tại Điều 25 Luật Nuôi con nuôi",
            child_custody_arrangement="Giao lại cho cha mẹ đẻ và Trung tâm Bảo trợ Xã hội chăm sóc",
        )
        assert term["termination_id"].startswith("TERM-")
        assert term["status"] == "TERMINATED"
        assert term["court_judgment_number"] == "12/2026/HNGĐ-ST"

        # Check certificate revoked
        revoked_cert = engine.get_record("certificate", cert["certificate_id"])
        assert revoked_cert["status"] == "REVOKED"

        # Check application terminated
        terminated_app = engine.get_record("application", app_rec["application_id"])
        assert terminated_app["status"] == "TERMINATED"

    def test_get_record_and_list_records(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Trịnh Thăng Long",
            adopter_dob="1982-12-12",
            adopter_id="001082000444",
            child_name="Trịnh Kim Chi",
            child_dob="2022-10-10",
            child_gender="FEMALE",
            child_origin="Trung tâm",
            relationship="UNRELATED",
        )
        retrieved = engine.get_record("application", app_rec["application_id"])
        assert retrieved["application_id"] == app_rec["application_id"]

        with pytest.raises(KeyError):
            engine.get_record("application", "NON-EXISTENT-ID")

        with pytest.raises(ValueError, match="Unknown category"):
            engine.get_record("unknown_category", "ID")

        apps = engine.list_records("application", limit=10)
        assert len(apps) >= 1

        audits = engine.list_records("audit", limit=10)
        assert len(audits) >= 1
        assert "entity_type" in audits[0]

    def test_get_telemetry_status(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        status = engine.get_telemetry_status()
        assert status["system_status"] == "ONLINE_HEALTHY"
        assert "statutory_framework" in status
        assert "total_adoption_applications" in status
        assert "domestic_adoptions" in status
        assert "intercountry_adoptions" in status
        assert "completed_registrations" in status
        assert "hague_dossiers_processed" in status
        assert "post_placement_reports_filed" in status
        assert "valid_adoption_certificates" in status
        assert "court_terminations" in status
        assert "audit_logs_count" in status


class TestAdoptionCli:
    def test_cli_help(self):
        runner = CliRunner()
        res = runner.invoke(adoption_app, ["--help"])
        assert res.exit_code == 0
        assert "Vietnamese Child Adoption & Hague Intercountry Adoption Suite" in res.output

    def test_cli_status_console_and_json(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(adoption_app, ["status"])
        assert res.exit_code == 0
        assert "QUẢN LÝ NUÔI CON NUÔI QUỐC GIA" in res.output

        res_cb = runner.invoke(adoption_app, [])
        assert res_cb.exit_code == 0
        assert "QUẢN LÝ NUÔI CON NUÔI QUỐC GIA" in res_cb.output

        res_json = runner.invoke(adoption_app, ["status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["system_status"] == "ONLINE_HEALTHY"

    def test_cli_apply_domestic(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(adoption_app, [
            "apply",
            "--adopter", "Võ Hoài Nam",
            "--adopter-dob", "1983-09-09",
            "--adopter-id", "001083000555",
            "--child", "Võ Hoài An",
            "--child-dob", "2023-05-05",
            "--gender", "MALE",
            "--origin", "Bảo trợ xã hội",
            "--rel", "UNRELATED",
        ])
        assert res.exit_code == 0
        assert "✓ Adoption Application Registered:" in res.output

    def test_cli_apply_domestic_json(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(adoption_app, [
            "apply",
            "--adopter", "Ngô Quỳnh Mai",
            "--adopter-dob", "1984-04-14",
            "--adopter-id", "001084000666",
            "--child", "Ngô Phúc Lộc",
            "--child-dob", "2024-01-01",
            "--origin", "Gia đình",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["application_id"].startswith("ADP-")
        assert data["adopter_name"] == "Ngô Quỳnh Mai"

    def test_cli_apply_validation_error(self, temp_db: str):
        runner = CliRunner()
        res = runner.invoke(adoption_app, [
            "apply",
            "--adopter", "Adopter Too Young",
            "--adopter-dob", "2005-01-01",
            "--adopter-id", "001005000777",
            "--child", "Child",
            "--child-dob", "2020-01-01",  # 5 years old, adopter is 21 -> gap 16 < 20
            "--origin", "Trung tâm",
            "--rel", "UNRELATED",
        ])
        assert res.exit_code == 1
        assert "Error registering adoption application" in res.output

    def test_cli_intercountry_cmd(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="INTERCOUNTRY",
            adopter_name="Robert Taylor",
            adopter_dob="1975-08-10",
            adopter_id="UK-PASS-123456",
            child_name="Trần Thúy Nga",
            child_dob="2021-04-12",
            child_gender="FEMALE",
            child_origin="Trung tâm Bảo trợ Trẻ em Tàn tật",
            adopter_nationality="Vương Quốc Anh",
        )

        runner = CliRunner()
        res = runner.invoke(adoption_app, [
            "intercountry",
            "--app-id", app_rec["application_id"],
            "--country", "United Kingdom",
            "--central-authority", "Department for Education - UK",
            "--agency", "IAC - The Centre for Voluntary Adoption",
            "--home-study", "2025-10-15",
            "--dept-approval", "45/CCN-BTP",
            "--provincial-decision", "890/QD-UBND",
            "--hague",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["dossier_id"].startswith("HAGUE-")
        assert data["status"] == "APPROVED"

    def test_cli_report_cmd(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Dương Quý Phi",
            adopter_dob="1980-01-01",
            adopter_id="001080000888",
            child_name="Dương Bảo Ngọc",
            child_dob="2022-02-02",
            child_gender="FEMALE",
            child_origin="Gia đình",
        )

        runner = CliRunner()
        res = runner.invoke(adoption_app, [
            "report",
            "--app-id", app_rec["application_id"],
            "--period", "6",
            "--health", "Sức khỏe xuất sắc",
            "--edu", "Thích nghi tốt",
            "--psych", "Gắn kết yêu thương",
            "--assessor", "Nguyễn Thu Hà",
            "--org", "UBND Phường Hàng Bài",
            "--rating", "EXCELLENT",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["report_id"].startswith("POST-")
        assert data["welfare_rating"] == "EXCELLENT"

    def test_cli_certificate_cmd(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Phùng Văn Hưng",
            adopter_dob="1981-03-03",
            adopter_id="001081000999",
            child_name="Phùng Tuấn Kiệt",
            child_dob="2023-03-03",
            child_gender="MALE",
            child_origin="Bảo trợ",
        )

        runner = CliRunner()
        res = runner.invoke(adoption_app, [
            "certificate",
            "--app-id", app_rec["application_id"],
            "--new-name", "Phùng Tuấn Anh",
            "--authority", "UBND Quận Cầu Giấy",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["certificate_id"].startswith("CERT-")
        assert data["child_new_name"] == "Phùng Tuấn Anh"

    def test_cli_terminate_cmd(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        app_rec = engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Chu Văn An",
            adopter_dob="1975-05-05",
            adopter_id="001075001010",
            child_name="Chu Tiểu Bảo",
            child_dob="2021-06-06",
            child_gender="MALE",
            child_origin="Gia đình",
        )
        engine.issue_adoption_certificate(application_id=app_rec["application_id"])

        runner = CliRunner()
        res = runner.invoke(adoption_app, [
            "terminate",
            "--app-id", app_rec["application_id"],
            "--judgment", "99/2026/QĐ-ST",
            "--court", "TAND Quận Hoàn Kiếm",
            "--grounds", "Không còn khả năng chăm sóc và có hành vi vi phạm",
            "--custody", "Chuyển giao cho Trung tâm bảo trợ xã hội",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "TERMINATED"

    def test_cli_list_cmd(self, temp_db: str):
        engine = AdoptionEngine(db_path=temp_db)
        engine.apply_adoption(
            adoption_type="DOMESTIC",
            adopter_name="Lý Nam Đế",
            adopter_dob="1979-07-07",
            adopter_id="001079001111",
            child_name="Lý Phật Tử",
            child_dob="2022-08-08",
            child_gender="MALE",
            child_origin="Gia đình",
        )

        runner = CliRunner()
        res_table = runner.invoke(adoption_app, ["list", "--category", "application"])
        assert res_table.exit_code == 0
        assert "Adoption Records" in res_table.output

        res_json = runner.invoke(adoption_app, ["list", "--category", "application", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert len(data) >= 1

    def test_cli_alias_connuoi(self, temp_db: str):
        root_app = build_app()
        runner = CliRunner()
        res = runner.invoke(root_app, ["connuoi", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["system_status"] == "ONLINE_HEALTHY"


class TestAdoptionMcpParity:
    def test_scripts_mcp_server_handlers(self, temp_db: str):
        from scripts.mcp_server import (
            handle_adoption_apply,
            handle_adoption_intercountry,
            handle_adoption_report,
            handle_adoption_certificate,
            handle_adoption_terminate,
            handle_adoption_list,
            handle_adoption_status,
            CORE_TOOLS_SPEC,
            CORE_HANDLERS,
        )

        # 1. Spec check
        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_adoption_apply" in tool_names
        assert "mekong_adoption_intercountry" in tool_names
        assert "mekong_adoption_report" in tool_names
        assert "mekong_adoption_certificate" in tool_names
        assert "mekong_adoption_terminate" in tool_names
        assert "mekong_adoption_list" in tool_names
        assert "mekong_adoption_status" in tool_names

        # 2. Handlers mapping check
        assert "mekong_adoption_apply" in CORE_HANDLERS
        assert "adoption_apply" in CORE_HANDLERS
        assert "mekong_adoption_status" in CORE_HANDLERS
        assert "adoption_status" in CORE_HANDLERS

        # 3. Execution check
        res_app = handle_adoption_apply({
            "adoption_type": "INTERCOUNTRY",
            "adopter_name": "David Miller",
            "adopter_dob": "1977-01-15",
            "adopter_id": "CAN-PASS-776655",
            "child_name": "Nguyễn Thị Sen",
            "child_dob": "2021-05-20",
            "child_gender": "FEMALE",
            "child_origin": "Làng trẻ SOS Hải Phòng",
            "adopter_nationality": "Canada",
        })
        data_app = json.loads(res_app)
        assert data_app["application_id"].startswith("ADP-")
        app_id = data_app["application_id"]

        res_hague = handle_adoption_intercountry({
            "application_id": app_id,
            "foreign_country": "Canada",
            "foreign_central_authority": "Ontario Central Authority for Intercountry Adoption",
            "accredited_adoption_agency": "Loving Connections Adoption Services",
            "home_study_date": "2025-09-01",
            "department_approval_number": "77/CCN-BTP",
            "provincial_decision_number": "334/QD-UBND",
            "hague_compliant": True,
        })
        data_hague = json.loads(res_hague)
        assert data_hague["dossier_id"].startswith("HAGUE-")
        assert data_hague["status"] == "APPROVED"

        res_rep = handle_adoption_report({
            "application_id": app_id,
            "reporting_period_months": 6,
            "health_status": "Tốt",
            "educational_adaptation": "Hòa nhập tốt",
            "psychological_state": "Vui vẻ",
            "assessor_name": "Emma Watson",
            "assessor_organization": "Children Aid Society",
            "welfare_rating": "EXCELLENT",
        })
        data_rep = json.loads(res_rep)
        assert data_rep["report_id"].startswith("POST-")
        assert data_rep["welfare_rating"] == "EXCELLENT"

        res_cert = handle_adoption_certificate({
            "application_id": app_id,
            "child_new_name": "Emily Miller Sen",
        })
        data_cert = json.loads(res_cert)
        assert data_cert["certificate_id"].startswith("CERT-")
        assert data_cert["child_new_name"] == "Emily Miller Sen"

        res_term = handle_adoption_terminate({
            "application_id": app_id,
            "court_judgment_number": "01/2026/ST-HNGD",
            "court_name": "TAND Cấp cao",
            "grounds": "Thỏa thuận tự nguyện hủy quan hệ nuôi con nuôi",
            "child_custody_arrangement": "Cha mẹ đẻ nhận lại",
        })
        data_term = json.loads(res_term)
        assert data_term["termination_id"].startswith("TERM-")
        assert data_term["status"] == "TERMINATED"

        res_list = handle_adoption_list({"category": "application", "limit": 10})
        data_list = json.loads(res_list)
        assert isinstance(data_list, list)
        assert len(data_list) >= 1

        res_st = handle_adoption_status({})
        data_st = json.loads(res_st)
        assert data_st["system_status"] == "ONLINE_HEALTHY"

    def test_core_mcp_server_handlers(self, temp_db: str):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-adoption-server")

        res_app = server._handle_adoption_apply(
            adoption_type="DOMESTIC",
            adopter_name="Lưu Bá Ôn",
            adopter_dob="1976-08-08",
            adopter_id="001076001212",
            child_name="Lưu Bá Đạt",
            child_dob="2022-09-09",
            child_gender="MALE",
            child_origin="Bảo trợ",
        )
        data_app = json.loads(res_app)
        assert data_app["application_id"].startswith("ADP-")
        app_id = data_app["application_id"]

        res_cert = server._handle_adoption_certificate(
            application_id=app_id,
            child_new_name="Lưu Bá Thành Đạt",
        )
        data_cert = json.loads(res_cert)
        assert data_cert["certificate_id"].startswith("CERT-")
        assert data_cert["child_new_name"] == "Lưu Bá Thành Đạt"

        res_rep = server._handle_adoption_report(
            application_id=app_id,
            reporting_period_months=12,
            health_status="Khỏe mạnh bình thường",
            educational_adaptation="Phát triển ngôn ngữ tốt",
            psychological_state="Hòa thuận gia đình",
            assessor_name="Nguyễn Văn Kiểm",
            assessor_organization="UBND Phường",
            welfare_rating="GOOD",
        )
        data_rep = json.loads(res_rep)
        assert data_rep["report_id"].startswith("POST-")
        assert data_rep["welfare_rating"] == "GOOD"

        res_term = server._handle_adoption_terminate(
            application_id=app_id,
            court_judgment_number="05/2026/QD-HNGD",
            court_name="TAND TP Hà Nội",
            grounds="Hủy quyết định công nhận",
            child_custody_arrangement="Giao cơ sở trợ giúp xã hội",
        )
        data_term = json.loads(res_term)
        assert data_term["termination_id"].startswith("TERM-")
        assert data_term["status"] == "TERMINATED"

        res_list = server._handle_adoption_list(category="certificate", limit=5)
        data_list = json.loads(res_list)
        assert isinstance(data_list, list)
        assert len(data_list) >= 1

        res_st = server._handle_adoption_status()
        data_st = json.loads(res_st)
        assert data_st["system_status"] == "ONLINE_HEALTHY"
        assert "total_adoption_applications" in data_st
