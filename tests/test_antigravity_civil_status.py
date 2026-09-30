"""
Test suite for Vietnamese Civil Registration, Vital Statistics & Identification Registry Suite (Phase 108).
Covers:
- CivilStatusEngine (pure standard-library engine, SQLite WAL persistence).
- Statutory compliance: Law on Civil Status 2014 (Law 60/2014/QH13), Decree 123/2015/NĐ-CP,
  Circular 04/2020/TT-BTP, Law on Marriage and Family 2014 (Article 8),
  Law on Identification 2023 (Law 26/2023/QH15) & VNeID Level 2.
- CLI surface (mekong civil-status birth/marriage/death/identity/extract/list/status).
- MCP parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.civil_status_engine import CivilStatusEngine
from src.cli.commands.civil_status_command import civil_status_app


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_civil_status.db")
        yield db_path


class TestCivilStatusEngine:
    def test_engine_init_and_tables(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        with engine._get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
        assert "birth_registrations" in tables
        assert "marriage_registrations" in tables
        assert "death_registrations" in tables
        assert "identity_cards" in tables
        assert "civil_extracts" in tables

    def test_register_birth_on_time(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.register_birth(
            child_name="Trần Bảo An",
            date_of_birth="2026-09-01",
            gender="NAM",
            mother_name="Nguyễn Thị Mai",
            father_name="Trần Văn Hùng",
            birth_place="Bệnh viện Phụ sản Hà Nội",
            province="Hà Nội",
            hospital_birth_notice=True,
            registration_date="2026-09-15",
        )
        assert res["cert_id"].startswith("CS-BRT-")
        assert res["status"] == "BIRTH_REGISTERED"
        assert res["is_registered"] is True
        assert res["registered_on_time"] is True
        assert len(res["personal_id"]) == 12
        assert res["personal_id"].startswith("001226")  # 001 (HN), 2 (21st cent Male), 26 (year 2026)

    def test_register_birth_late_60_days(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.register_birth(
            child_name="Lê Minh Đạt",
            date_of_birth="2026-01-01",
            gender="NAM",
            mother_name="Lê Thị Hằng",
            province="TP. Hồ Chí Minh",
            hospital_birth_notice=True,
            registration_date="2026-05-01",  # 120 days after birth > 60 days
        )
        assert res["status"] == "BIRTH_REGISTERED"
        assert res["registered_on_time"] is False
        assert any("quá thời hạn 60 ngày" in v for v in res["violations"])

    def test_register_birth_missing_notice_rejected(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.register_birth(
            child_name="Vũ Thiên Ân",
            date_of_birth="2026-09-10",
            gender="NỮ",
            mother_name="Hoàng Kim Ngân",
            hospital_birth_notice=False,  # Missing birth notice
        )
        assert res["status"] == "REJECTED_MISSING_NOTICE"
        assert res["is_registered"] is False
        assert any("Giấy chứng sinh" in v for v in res["violations"])

    def test_register_marriage_approved(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.register_marriage(
            groom_name="Lê Hoàng Long",
            groom_dob="1998-05-15",
            groom_pid="001098012345",
            bride_name="Phạm Quỳnh Anh",
            bride_dob="2000-08-20",
            bride_pid="001100067890",
            single_status_verified=True,
            voluntary_consent=True,
        )
        assert res["cert_id"].startswith("CS-MAR-")
        assert res["status"] == "MARRIAGE_REGISTERED"
        assert res["is_approved"] is True
        assert res["is_legal_age"] is True
        assert len(res["violations"]) == 0

    def test_register_marriage_underage_rejected(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.register_marriage(
            groom_name="Nguyễn Văn A",
            groom_dob="2010-01-01",  # 16 years old (<20)
            groom_pid="001010012345",
            bride_name="Trần Thị B",
            bride_dob="2011-01-01",  # 15 years old (<18)
            bride_pid="001111067890",
            single_status_verified=True,
            voluntary_consent=True,
        )
        assert res["status"] == "REJECTED_INADMISSIBLE"
        assert res["is_approved"] is False
        assert res["is_legal_age"] is False
        assert any("chưa đủ 20 tuổi" in v for v in res["violations"])
        assert any("chưa đủ 18 tuổi" in v for v in res["violations"])

    def test_register_marriage_missing_single_cert_rejected(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.register_marriage(
            groom_name="Đoàn Trọng Tấn",
            groom_dob="1995-02-10",
            groom_pid="001095012345",
            bride_name="Đỗ Mỹ Linh",
            bride_dob="1997-04-18",
            bride_pid="001197067890",
            single_status_verified=False,  # Missing single status cert
            voluntary_consent=True,
        )
        assert res["status"] == "REJECTED_INADMISSIBLE"
        assert res["is_approved"] is False
        assert any("tình trạng hôn nhân" in v for v in res["violations"])

    def test_register_death_on_time(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.register_death(
            deceased_name="Nguyễn Văn Hưởng",
            personal_id="001050012345",
            date_of_death="2026-09-20",
            cause_of_death="Bệnh tim mạch",
            place_of_death="Bệnh viện Bạch Mai",
            death_notice_verified=True,
            registration_date="2026-09-25",  # 5 days <= 15 days
        )
        assert res["cert_id"].startswith("CS-DTH-")
        assert res["status"] == "DEATH_REGISTERED"
        assert res["is_registered"] is True
        assert res["on_time"] is True
        assert len(res["violations"]) == 0

    def test_register_death_missing_notice_rejected(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.register_death(
            deceased_name="Trần Đình C",
            personal_id="001045012345",
            date_of_death="2026-09-10",
            death_notice_verified=False,  # Missing death notice
        )
        assert res["status"] == "REJECTED_MISSING_NOTICE"
        assert res["is_registered"] is False
        assert any("Giấy báo tử" in v for v in res["violations"])

    def test_issue_identity_card_approved(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.issue_identity_card(
            full_name="Nguyễn Minh Khang",
            date_of_birth="1998-10-12",
            personal_id="001098055667",
            gender="NAM",
            has_iris_biometrics=True,
            has_fingerprints=True,
            has_facial_photo=True,
        )
        assert res["card_id"].startswith("CS-CID-")
        assert res["status"] == "IDENTITY_CARD_ISSUED"
        assert res["is_eligible"] is True
        assert res["vneid_level2_active"] is True
        assert len(res["violations"]) == 0

    def test_issue_identity_card_missing_iris_rejected(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        res = engine.issue_identity_card(
            full_name="Trương Công Định",
            date_of_birth="2002-03-25",
            personal_id="001002055667",
            gender="NAM",
            has_iris_biometrics=False,  # Lacks iris scan
            has_fingerprints=True,
            has_facial_photo=True,
        )
        assert res["status"] == "REJECTED_BIOMETRICS_INCOMPLETE"
        assert res["is_eligible"] is False
        assert any("mống mắt" in v for v in res["violations"])

    def test_issue_civil_extract(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        birth = engine.register_birth(
            child_name="Đặng Tuấn Anh",
            date_of_birth="2026-08-01",
            gender="NAM",
            mother_name="Đặng Thị Lan",
        )
        extract = engine.issue_civil_extract(
            event_type="BIRTH",
            source_cert_id=birth["cert_id"],
            applicant_name="Đặng Thị Lan",
            purpose="Nhập học mẫu giáo",
        )
        assert extract["extract_id"].startswith("CS-EXT-")
        assert extract["status"] == "EXTRACT_ISSUED"
        assert extract["event_type"] == "BIRTH"

    def test_list_civil_records(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        birth = engine.register_birth(
            child_name="Bé A",
            date_of_birth="2026-09-01",
            gender="NỮ",
            mother_name="Mẹ A",
        )
        engine.register_marriage(
            groom_name="Chồng A",
            groom_dob="1995-01-01",
            groom_pid="001095000001",
            bride_name="Vợ A",
            bride_dob="1997-01-01",
            bride_pid="001197000002",
        )
        engine.register_death(
            deceased_name="Cụ A",
            personal_id="001030000001",
            date_of_death="2026-09-01",
        )
        engine.issue_identity_card(
            full_name="Anh A",
            date_of_birth="1996-05-05",
            personal_id="001096000001",
        )
        engine.issue_civil_extract(
            event_type="BIRTH",
            source_cert_id=birth["cert_id"],
            applicant_name="Mẹ A",
        )

        records = engine.list_civil_records(category="ALL", limit=20)
        assert "births" in records
        assert "marriages" in records
        assert "deaths" in records
        assert "identity_cards" in records
        assert "extracts" in records

        assert len(records["births"]) >= 1
        assert len(records["marriages"]) >= 1
        assert len(records["deaths"]) >= 1

    def test_civil_status_telemetry(self, temp_db: str):
        engine = CivilStatusEngine(db_path=temp_db)
        engine.register_birth(
            child_name="Bé B",
            date_of_birth="2026-09-01",
            gender="NAM",
            mother_name="Mẹ B",
        )
        engine.register_death(
            deceased_name="Cụ B",
            personal_id="001025000001",
            date_of_death="2026-09-10",
        )
        telemetry = engine.get_civil_status_telemetry()
        assert telemetry["total_birth_registrations"] >= 1
        assert telemetry["total_death_registrations"] >= 1
        assert "population_natural_growth" in telemetry


class TestCivilStatusCLI:
    runner = CliRunner()

    def test_cli_birth_json(self):
        result = self.runner.invoke(
            civil_status_app,
            [
                "birth",
                "Phan Minh Khang",
                "--dob",
                "2026-09-05",
                "--gender",
                "NAM",
                "--mother",
                "Đỗ Thị Thu",
                "--province",
                "Hà Nội",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "BIRTH_REGISTERED"
        assert len(data["personal_id"]) == 12

    def test_cli_birth_console(self):
        result = self.runner.invoke(
            civil_status_app,
            [
                "birth",
                "Trịnh Gia Hân",
                "--dob",
                "2026-09-10",
                "--gender",
                "NỮ",
                "--mother",
                "Nguyễn Thúy Hằng",
            ],
        )
        assert result.exit_code == 0
        assert "CS-BRT-" in result.output

    def test_cli_marriage_json(self):
        result = self.runner.invoke(
            civil_status_app,
            [
                "marriage",
                "Lý Hải Đăng",
                "Bùi Phương Thảo",
                "--groom-dob",
                "1997-03-20",
                "--groom-pid",
                "001097011223",
                "--bride-dob",
                "1999-07-15",
                "--bride-pid",
                "001199044556",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "MARRIAGE_REGISTERED"
        assert data["is_approved"] is True

    def test_cli_death_json(self):
        result = self.runner.invoke(
            civil_status_app,
            [
                "death",
                "Ngô Văn Quyết",
                "--pid",
                "001048099887",
                "--dod",
                "2026-09-18",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "DEATH_REGISTERED"
        assert data["is_registered"] is True

    def test_cli_identity_json(self):
        result = self.runner.invoke(
            civil_status_app,
            [
                "identity",
                "Tạ Quang Bửu",
                "--dob",
                "1995-12-01",
                "--pid",
                "001095033445",
                "--iris",
                "--fingerprint",
                "--face",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "IDENTITY_CARD_ISSUED"
        assert data["vneid_level2_active"] is True

    def test_cli_extract_json(self):
        # Create a birth first
        b_res = self.runner.invoke(
            civil_status_app,
            ["birth", "Bé Chi", "--dob", "2026-08-15", "--gender", "NỮ", "--mother", "Mẹ Chi", "--json"],
        )
        b_data = json.loads(b_res.output)
        cid = b_data["cert_id"]

        result = self.runner.invoke(
            civil_status_app,
            ["extract", "BIRTH", cid, "--applicant", "Mẹ Chi", "--purpose", "Thủ tục visa", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "EXTRACT_ISSUED"

    def test_cli_list_json(self):
        result = self.runner.invoke(
            civil_status_app,
            ["list", "--category", "ALL", "--limit", "10", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "births" in data

    def test_cli_status_json(self):
        result = self.runner.invoke(civil_status_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_birth_registrations" in data
        assert "population_natural_growth" in data


class TestCivilStatusMcpParity:
    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_civil_status_birth,
            handle_civil_status_marriage,
            handle_civil_status_death,
            handle_civil_status_identity,
            handle_civil_status_extract,
            handle_civil_status_list,
            handle_civil_status_status,
        )

        res_b = handle_civil_status_birth({
            "child_name": "Ngô Bảo Châu",
            "date_of_birth": "2026-09-02",
            "gender": "NAM",
            "mother_name": "Trần Thị Lan",
            "province": "Hà Nội",
        })
        data_b = json.loads(res_b)
        assert data_b["status"] == "BIRTH_REGISTERED"

        res_m = handle_civil_status_marriage({
            "groom_name": "Nguyễn Văn Hải",
            "groom_dob": "1996-06-10",
            "groom_pid": "001096055443",
            "bride_name": "Lê Thị Mai",
            "bride_dob": "1998-09-12",
            "bride_pid": "001198088776",
        })
        data_m = json.loads(res_m)
        assert data_m["status"] == "MARRIAGE_REGISTERED"

        res_d = handle_civil_status_death({
            "deceased_name": "Hoàng Văn D",
            "personal_id": "001040088991",
            "date_of_death": "2026-09-22",
        })
        data_d = json.loads(res_d)
        assert data_d["status"] == "DEATH_REGISTERED"

        res_i = handle_civil_status_identity({
            "full_name": "Phạm Văn Minh",
            "date_of_birth": "1999-01-15",
            "personal_id": "001099044332",
        })
        data_i = json.loads(res_i)
        assert data_i["status"] == "IDENTITY_CARD_ISSUED"

        res_e = handle_civil_status_extract({
            "event_type": "BIRTH",
            "source_cert_id": data_b["cert_id"],
            "applicant_name": "Trần Thị Lan",
        })
        data_e = json.loads(res_e)
        assert data_e["status"] == "EXTRACT_ISSUED"

        res_l = handle_civil_status_list({"category": "ALL", "limit": 10})
        data_l = json.loads(res_l)
        assert "births" in data_l

        res_st = handle_civil_status_status({})
        data_st = json.loads(res_st)
        assert "total_birth_registrations" in data_st

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        res_b = server._handle_civil_status_birth(
            child_name="Đặng Thùy Trâm",
            date_of_birth="2026-09-08",
            gender="NỮ",
            mother_name="Doãn Ngọc Trâm",
            province="Hà Nội",
        )
        data_b = json.loads(res_b)
        assert data_b["status"] == "BIRTH_REGISTERED"

        res_m = server._handle_civil_status_marriage(
            groom_name="Trần Trọng Kim",
            groom_dob="1994-08-08",
            groom_pid="001094011229",
            bride_name="Võ Thị Sáu",
            bride_dob="1996-03-03",
            bride_pid="001196022338",
        )
        data_m = json.loads(res_m)
        assert data_m["status"] == "MARRIAGE_REGISTERED"

        res_d = server._handle_civil_status_death(
            deceased_name="Cụ Nguyễn Văn E",
            personal_id="001035077889",
            date_of_death="2026-09-24",
        )
        data_d = json.loads(res_d)
        assert data_d["status"] == "DEATH_REGISTERED"

        res_i = server._handle_civil_status_identity(
            full_name="Vũ Trọng Phụng",
            date_of_birth="1997-11-20",
            personal_id="001097055441",
        )
        data_i = json.loads(res_i)
        assert data_i["status"] == "IDENTITY_CARD_ISSUED"

        res_e = server._handle_civil_status_extract(
            event_type="BIRTH",
            source_cert_id=data_b["cert_id"],
            applicant_name="Doãn Ngọc Trâm",
        )
        data_e = json.loads(res_e)
        assert data_e["status"] == "EXTRACT_ISSUED"

        res_l = server._handle_civil_status_list(category="ALL", limit=10)
        data_l = json.loads(res_l)
        assert "births" in data_l

        res_st = server._handle_civil_status_status()
        data_st = json.loads(res_st)
        assert "total_birth_registrations" in data_st
