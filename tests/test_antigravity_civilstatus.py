"""
Unit & Integration Tests for Vietnamese Civil Status, Vital Statistics & Population Registration Suite.
Compliant with:
- Law on Civil Status 2014 (Luật Hộ tịch - Law No. 60/2014/QH13)
- Decree No. 123/2015/ND-CP detailing the implementation of the Law on Civil Status
- Decree No. 87/2020/ND-CP on Electronic Civil Status Database & Shared National Population Database
- Circular No. 04/2020/TT-BTP guiding the Law on Civil Status and Decree No. 123/2015/ND-CP
- Law on Identification 2023 (Law No. 26/2023/QH15) on Personal Identification Numbers (Số định danh cá nhân)
- tests/test_core_boundary.py (Strict zero vendor-sdk / AST boundary compliance)
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.civilstatus_engine import (
    CivilStatusEngine,
    CivilStatusEventType,
    CompetentLevel,
    RectificationType,
    RegistrationStatus,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as script_mcp

runner = CliRunner()


@pytest.fixture
def engine(tmp_path):
    db_file = tmp_path / "test_civilstatus.db"
    return CivilStatusEngine(db_path=str(db_file))


class TestCivilStatusEngine:
    def test_register_birth_success(self, engine):
        # 21st century male child
        res = engine.register_birth(
            child_name="Nguyen Gia Bao",
            gender="MALE",
            birth_date="2024-05-18",
            birth_place="Benh vien Phu san Ha Noi",
            ethnicity="Kinh",
            nationality="Việt Nam",
            mother_name="Tran Thi Hoa",
            mother_citizen_id="001192001122",
            father_name="Nguyen Van Long",
            father_citizen_id="001090003344",
            registrant_name="Nguyen Van Long",
            competent_authority="UBND Phường Hàng Trống, Hoàn Kiếm, Hà Nội",
            competent_level="COMMUNE",
            notes="Standard domestic birth registration",
        )
        assert res["registration_id"].startswith("BIRTH-")
        assert res["child_name"] == "Nguyen Gia Bao"
        assert res["gender"] == "MALE"
        assert res["status"] == "REGISTERED"
        assert res["foreign_element"] == 0

        # Check 12-digit DDCN: [3 prov][1 gen/century][2 year][6 rand]
        ddcn = res["personal_id_number"]
        assert len(ddcn) == 12
        # Year 2024 male -> gen_code is 2, year is 24
        assert ddcn[3] == "2"
        assert ddcn[4:6] == "24"

    def test_register_birth_century_gender_encoding(self, engine):
        # 20th century female (born 1995)
        res_f20 = engine.register_birth(
            child_name="Le Thi Thao",
            gender="FEMALE",
            birth_date="1995-10-10",
            birth_place="Benh vien Tu Du, TP.HCM",
            registrant_name="Le Van Ba",
            competent_authority="UBND Phuong Ben Nghe, Quan 1, TP.HCM",
        )
        ddcn_f20 = res_f20["personal_id_number"]
        assert len(ddcn_f20) == 12
        assert ddcn_f20[3] == "1"  # 20th century female = 1
        assert ddcn_f20[4:6] == "95"

        # 20th century male (born 1988)
        res_m20 = engine.register_birth(
            child_name="Pham Minh Tri",
            gender="NAM",
            birth_date="1988-03-25",
            birth_place="Ha Noi",
            registrant_name="Pham Minh Duc",
            competent_authority="UBND Phuong Hang Gai",
        )
        ddcn_m20 = res_m20["personal_id_number"]
        assert ddcn_m20[3] == "0"  # 20th century male = 0
        assert ddcn_m20[4:6] == "88"

        # 21st century female (born 2023)
        res_f21 = engine.register_birth(
            child_name="Do Mai Linh",
            gender="NU",
            birth_date="2023-07-04",
            birth_place="Da Nang",
            registrant_name="Do Tuan",
            competent_authority="UBND Hai Chau",
        )
        ddcn_f21 = res_f21["personal_id_number"]
        assert ddcn_f21[3] == "3"  # 21st century female = 3
        assert ddcn_f21[4:6] == "23"

    def test_register_birth_foreign_element_jurisdiction(self, engine):
        # Foreign element birth MUST NOT be registered at COMMUNE level (Art 35 Law 60/2014)
        with pytest.raises(ValueError, match="Births with foreign element must be registered at District level"):
            engine.register_birth(
                child_name="Alexander Nguyen",
                gender="MALE",
                birth_date="2024-01-01",
                birth_place="Hanoi French Hospital",
                registrant_name="Tran Thi Mai",
                competent_authority="UBND Phường Hàng Gai",
                competent_level="COMMUNE",
                foreign_element=True,
            )

        # Foreign element registered at DISTRICT level succeeds
        res = engine.register_birth(
            child_name="Alexander Nguyen",
            gender="MALE",
            birth_date="2024-01-01",
            birth_place="Hanoi French Hospital",
            registrant_name="Tran Thi Mai",
            competent_authority="UBND Quận Hoàn Kiếm, Hà Nội",
            competent_level="DISTRICT",
            foreign_element=True,
        )
        assert res["foreign_element"] == 1
        assert res["competent_level"] == "DISTRICT"

    def test_register_birth_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Child full name cannot be empty"):
            engine.register_birth(child_name="", gender="MALE", birth_date="2024-01-01", birth_place="Hanoi", registrant_name="Father")
        with pytest.raises(ValueError, match="Gender cannot be empty"):
            engine.register_birth(child_name="Baby", gender="", birth_date="2024-01-01", birth_place="Hanoi", registrant_name="Father")
        with pytest.raises(ValueError, match="Birth date cannot be empty"):
            engine.register_birth(child_name="Baby", gender="MALE", birth_date="", birth_place="Hanoi", registrant_name="Father")
        with pytest.raises(ValueError, match="Birth place cannot be empty"):
            engine.register_birth(child_name="Baby", gender="MALE", birth_date="2024-01-01", birth_place="", registrant_name="Father")
        with pytest.raises(ValueError, match="Registrant name cannot be empty"):
            engine.register_birth(child_name="Baby", gender="MALE", birth_date="2024-01-01", birth_place="Hanoi", registrant_name="")
        with pytest.raises(ValueError, match="Invalid competent level"):
            engine.register_birth(child_name="Baby", gender="MALE", birth_date="2024-01-01", birth_place="Hanoi", registrant_name="Father", competent_level="INVALID_LEVEL")

    def test_register_marriage_success(self, engine):
        res = engine.register_marriage(
            male_name="Vu Dinh Khoi",
            male_birth_date="1992-04-12",
            male_citizen_id="001092004455",
            male_nationality="Việt Nam",
            female_name="Hoang Ngoc Diep",
            female_birth_date="1995-08-20",
            female_citizen_id="001195006677",
            female_nationality="Việt Nam",
            registration_date="2025-02-14",
            competent_authority="UBND Phường Hàng Bài, Hoàn Kiếm, Hà Nội",
            competent_level="COMMUNE",
        )
        assert res["registration_id"].startswith("MAR-")
        assert res["male_name"] == "Vu Dinh Khoi"
        assert res["female_name"] == "Hoang Ngoc Diep"
        assert res["certificate_number"].startswith("KH-")
        assert res["status"] == "REGISTERED"
        assert res["foreign_element"] == 0

    def test_register_marriage_foreign_element_jurisdiction(self, engine):
        # Involves foreign citizen: must be registered at DISTRICT level (Art 37 Law 60/2014)
        with pytest.raises(ValueError, match="Marriages with foreign element must be registered at District level"):
            engine.register_marriage(
                male_name="John Smith",
                male_birth_date="1989-11-05",
                male_citizen_id="US99887766",
                male_nationality="Hoa Kỳ",
                female_name="Nguyen Thi Mai",
                female_birth_date="1994-06-15",
                female_citizen_id="001194002233",
                female_nationality="Việt Nam",
                competent_authority="UBND Phường Hàng Gai",
                competent_level="COMMUNE",
                foreign_element=True,
            )

        # Registered at District level succeeds
        res = engine.register_marriage(
            male_name="John Smith",
            male_birth_date="1989-11-05",
            male_citizen_id="US99887766",
            male_nationality="Hoa Kỳ",
            female_name="Nguyen Thi Mai",
            female_birth_date="1994-06-15",
            female_citizen_id="001194002233",
            female_nationality="Việt Nam",
            competent_authority="UBND Quận Hoàn Kiếm, Hà Nội",
            competent_level="DISTRICT",
            foreign_element=True,
        )
        assert res["foreign_element"] == 1
        assert res["competent_level"] == "DISTRICT"

    def test_register_marriage_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Male partner name cannot be empty"):
            engine.register_marriage(
                male_name="", male_birth_date="1990-01-01", male_citizen_id="123",
                female_name="Jane", female_birth_date="1992-01-01", female_citizen_id="456",
            )
        with pytest.raises(ValueError, match="Female partner name cannot be empty"):
            engine.register_marriage(
                male_name="John", male_birth_date="1990-01-01", male_citizen_id="123",
                female_name="", female_birth_date="1992-01-01", female_citizen_id="456",
            )

    def test_register_death_success(self, engine):
        res = engine.register_death(
            deceased_name="Tran Dinh Luong",
            gender="MALE",
            birth_date="1940-02-15",
            death_date="2024-06-10",
            death_place="Benh vien Viet Duc, Ha Noi",
            cause_of_death="Old age and cardiovascular failure",
            informant_name="Tran Dinh Nam",
            competent_authority="UBND Phường Hàng Gai, Hoàn Kiếm, Hà Nội",
            citizen_id="001040001234",
            notes="Natural death reported within 15 days statutory limit",
        )
        assert res["registration_id"].startswith("DEATH-")
        assert res["deceased_name"] == "Tran Dinh Luong"
        assert res["death_certificate_number"].startswith("KT-")
        assert res["status"] == "REGISTERED"

    def test_register_death_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Deceased name cannot be empty"):
            engine.register_death(
                deceased_name="", gender="MALE", birth_date="1950-01-01",
                death_date="2024-01-01", death_place="Hanoi", cause_of_death="Illness",
                informant_name="Son", competent_authority="UBND",
            )
        with pytest.raises(ValueError, match="Cause of death cannot be empty"):
            engine.register_death(
                deceased_name="John", gender="MALE", birth_date="1950-01-01",
                death_date="2024-01-01", death_place="Hanoi", cause_of_death="",
                informant_name="Son", competent_authority="UBND",
            )

    def test_rectify_civil_status_success(self, engine):
        res = engine.rectify_civil_status(
            person_name="Le Van Binh",
            citizen_id="001090123456",
            rectification_type="NAME_CHANGE",
            original_content="Le Van Binh",
            corrected_content="Le Hoang Binh",
            legal_basis="Điều 26 Luật Hộ tịch 2014 & Điều 28 Bộ luật Dân sự 2015",
            decision_number="QD-456/UBND-TP",
            competent_authority="UBND Quận Hoàn Kiếm, Hà Nội",
            decision_date="2025-01-15",
            status="APPROVED",
        )
        assert res["rectification_id"].startswith("REC-")
        assert res["rectification_type"] == "NAME_CHANGE"
        assert res["original_content"] == "Le Van Binh"
        assert res["corrected_content"] == "Le Hoang Binh"
        assert res["status"] == "APPROVED"

    def test_rectify_civil_status_validation_errors(self, engine):
        with pytest.raises(ValueError, match="Invalid rectification type"):
            engine.rectify_civil_status(
                person_name="Le Van Binh",
                citizen_id="001090123456",
                rectification_type="INVALID_TYPE",
                original_content="Old",
                corrected_content="New",
                legal_basis="Law",
                decision_number="QD-1",
                competent_authority="UBND",
            )
        with pytest.raises(ValueError, match="Legal basis cannot be empty"):
            engine.rectify_civil_status(
                person_name="Le Van Binh",
                citizen_id="001090123456",
                rectification_type="NAME_CHANGE",
                original_content="Old",
                corrected_content="New",
                legal_basis="",
                decision_number="QD-1",
                competent_authority="UBND",
            )

    def test_issue_extract_success(self, engine):
        # Register a birth first
        b_res = engine.register_birth(
            child_name="Dang Quoc An",
            gender="MALE",
            birth_date="2024-03-01",
            birth_place="Hanoi",
            registrant_name="Dang Quoc Cuong",
            competent_authority="UBND Phuong Hang Bac",
        )
        # Issue digital extract
        ext = engine.issue_extract(
            event_type="BIRTH",
            source_record_id=b_res["registration_id"],
            subject_name="Dang Quoc An",
            issuing_authority="Sở Tư pháp TP Hà Nội",
        )
        assert ext["extract_id"].startswith("EXT-")
        assert ext["event_type"] == "BIRTH"
        assert ext["source_record_id"] == b_res["registration_id"]
        assert ext["extract_number"].startswith("TL-")
        assert ext["digital_signature"].startswith("DIGITAL-SIG-MOJ-")
        assert ext["status"] == "VALID"

    def test_get_and_list_records(self, engine):
        b1 = engine.register_birth(
            child_name="Child One", gender="FEMALE", birth_date="2024-02-01",
            birth_place="Hanoi", registrant_name="Parent", competent_authority="UBND",
        )
        b2 = engine.register_birth(
            child_name="Child Two", gender="MALE", birth_date="2024-02-02",
            birth_place="Hanoi", registrant_name="Parent", competent_authority="UBND",
        )

        # get_record
        rec = engine.get_record("birth", b1["registration_id"])
        assert rec["child_name"] == "Child One"

        # list_records
        b_list = engine.list_records("birth", limit=10)
        assert len(b_list) >= 2
        names = [x["child_name"] for x in b_list]
        assert "Child One" in names and "Child Two" in names

        # Invalid category
        with pytest.raises(ValueError, match="Unknown category"):
            engine.get_record("invalid_cat", "123")
        with pytest.raises(ValueError, match="Unknown category"):
            engine.list_records("invalid_cat")

    def test_telemetry_status(self, engine):
        engine.register_birth(
            child_name="Baby A", gender="MALE", birth_date="2024-01-01",
            birth_place="Hanoi", registrant_name="Parent", competent_authority="UBND",
        )
        engine.register_marriage(
            male_name="Man A", male_birth_date="1990-01-01", male_citizen_id="123",
            female_name="Woman B", female_birth_date="1992-01-01", female_citizen_id="456",
            competent_authority="UBND",
        )
        status = engine.get_telemetry_status()
        assert status["total_birth_registrations"] >= 1
        assert status["total_marriage_registrations"] >= 1
        assert status["system_status"] == "ONLINE_HEALTHY"
        assert "National Population Database" in status["national_database"]


class TestCivilStatusCLI:
    def test_cli_help(self):
        app = build_app()
        res = runner.invoke(app, ["civilstatus", "--help"])
        assert res.exit_code == 0
        assert "Vietnamese Civil Status" in res.output
        assert "birth" in res.output
        assert "marriage" in res.output
        assert "death" in res.output
        assert "rectify" in res.output
        assert "extract" in res.output
        assert "list" in res.output
        assert "status" in res.output

    def test_cli_alias_hothich_help(self):
        app = build_app()
        res = runner.invoke(app, ["hothich", "--help"])
        assert res.exit_code == 0
        assert "birth" in res.output

    def test_cli_status_json(self):
        app = build_app()
        res = runner.invoke(app, ["civilstatus", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "total_birth_registrations" in data
        assert "system_status" in data

    def test_cli_birth_command(self):
        app = build_app()
        res = runner.invoke(app, [
            "civilstatus", "birth",
            "--name", "Nguyen Van An",
            "--gender", "MALE",
            "--birth-date", "2024-06-01",
            "--birth-place", "Hanoi",
            "--registrant", "Nguyen Van Bo",
            "--mother", "Tran Thi Me",
            "--mother-id", "001190001122",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["child_name"] == "Nguyen Van An"
        assert len(data["personal_id_number"]) == 12

    def test_cli_marriage_command(self):
        app = build_app()
        res = runner.invoke(app, [
            "civilstatus", "marriage",
            "--husband", "Hoang Van Nam",
            "--husband-dob", "1991-05-12",
            "--husband-id", "001091001122",
            "--wife", "Phung Thi Nga",
            "--wife-dob", "1993-09-18",
            "--wife-id", "001193003344",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["male_name"] == "Hoang Van Nam"
        assert data["female_name"] == "Phung Thi Nga"

    def test_cli_death_command(self):
        app = build_app()
        res = runner.invoke(app, [
            "civilstatus", "death",
            "--deceased", "Do Van Canh",
            "--gender", "MALE",
            "--birth-date", "1942-03-01",
            "--death-date", "2024-08-20",
            "--death-place", "Ha Noi",
            "--cause", "Heart failure",
            "--informant", "Do Van Con",
            "--authority", "UBND Phuong Hang Dao",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["deceased_name"] == "Do Van Canh"

    def test_cli_rectify_command(self):
        app = build_app()
        res = runner.invoke(app, [
            "civilstatus", "rectify",
            "--name", "Bui Thi Hoa",
            "--citizen-id", "001194005566",
            "--type", "NAME_CHANGE",
            "--original", "Bui Thi Hoa",
            "--corrected", "Bui Hoang Mai Hoa",
            "--legal-basis", "Dieu 26 Luat Ho tich 2014",
            "--decision", "QD-789/UBND",
            "--authority", "UBND Quan Ba Dinh, Ha Noi",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["corrected_content"] == "Bui Hoang Mai Hoa"

    def test_cli_extract_and_list_command(self):
        app = build_app()
        # Create birth
        b_res = runner.invoke(app, [
            "civilstatus", "birth",
            "--name", "Nguyen Tuong Vy",
            "--gender", "FEMALE",
            "--birth-date", "2024-04-10",
            "--birth-place", "Hanoi",
            "--registrant", "Nguyen Van Bo",
            "--json",
        ])
        b_id = json.loads(b_res.output)["registration_id"]

        # Issue extract
        ext_res = runner.invoke(app, [
            "civilstatus", "extract",
            "--type", "BIRTH",
            "--record-id", b_id,
            "--name", "Nguyen Tuong Vy",
            "--authority", "So Tu phap TP Ha Noi",
            "--json",
        ])
        assert ext_res.exit_code == 0
        ext_data = json.loads(ext_res.output)
        assert ext_data["source_record_id"] == b_id

        # List records
        list_res = runner.invoke(app, ["civilstatus", "list", "--category", "birth", "--json"])
        assert list_res.exit_code == 0
        records = json.loads(list_res.output)
        assert isinstance(records, list)
        assert len(records) >= 1


class TestCivilStatusMCP:
    def test_core_mcp_server_handlers(self):
        server = MekongMcpServer()

        # 1. Birth
        b_raw = server._handle_civilstatus_birth(
            child_name="Dang Minh Tri",
            gender="MALE",
            birth_date="2024-07-21",
            birth_place="Benh vien Viet Phap, Ha Noi",
            registrant_name="Dang Minh Quan",
        )
        b_data = json.loads(b_raw)
        assert b_data["child_name"] == "Dang Minh Tri"
        assert len(b_data["personal_id_number"]) == 12

        # 2. Marriage
        m_raw = server._handle_civilstatus_marriage(
            male_name="Tran Tuan",
            male_birth_date="1990-01-01",
            male_citizen_id="001090111222",
            female_name="Le Van",
            female_birth_date="1993-02-02",
            female_citizen_id="001193333444",
        )
        m_data = json.loads(m_raw)
        assert m_data["male_name"] == "Tran Tuan"

        # 3. Death
        d_raw = server._handle_civilstatus_death(
            deceased_name="Vu Tien Dat",
            gender="MALE",
            birth_date="1948-12-12",
            death_date="2024-09-01",
            death_place="Ha Noi",
            cause_of_death="Old age",
            informant_name="Vu Tien Dung",
            competent_authority="UBND Phuong Hang Bong",
        )
        d_data = json.loads(d_raw)
        assert d_data["deceased_name"] == "Vu Tien Dat"

        # 4. Rectify
        r_raw = server._handle_civilstatus_rectify(
            person_name="Vu Tien Dung",
            citizen_id="001080555666",
            rectification_type="NAME_CHANGE",
            original_content="Vu Tien Dung",
            corrected_content="Vu Tien Anh Dung",
            legal_basis="Dieu 26 Luat Ho tich",
            decision_number="QD-001/UBND",
            competent_authority="UBND Quan Hoan Kiem",
        )
        r_data = json.loads(r_raw)
        assert r_data["corrected_content"] == "Vu Tien Anh Dung"

        # 5. Extract
        e_raw = server._handle_civilstatus_extract(
            event_type="BIRTH",
            source_record_id=b_data["registration_id"],
            subject_name="Dang Minh Tri",
            issuing_authority="So Tu phap Ha Noi",
        )
        e_data = json.loads(e_raw)
        assert e_data["extract_number"].startswith("TL-")

        # 6. List
        l_raw = server._handle_civilstatus_list(category="birth", limit=10)
        l_data = json.loads(l_raw)
        assert isinstance(l_data, list)

        # 7. Status
        s_raw = server._handle_civilstatus_status()
        s_data = json.loads(s_raw)
        assert s_data["system_status"] == "ONLINE_HEALTHY"

        # Error handling
        err_raw = server._handle_civilstatus_birth(child_name="")
        err_data = json.loads(err_raw)
        assert err_data["ok"] is False
        assert "error" in err_data

    def test_scripts_mcp_server_handlers_and_dispatch(self):
        # Test script_mcp handlers directly
        res_raw = script_mcp.handle_civilstatus_status({})
        res = json.loads(res_raw)
        assert "total_birth_registrations" in res

        # Test CORE_HANDLERS dispatch
        assert "mekong_civilstatus_birth" in script_mcp.CORE_HANDLERS
        assert "civilstatus_birth" in script_mcp.CORE_HANDLERS
        assert "mekong_civilstatus_status" in script_mcp.CORE_HANDLERS
        assert "civilstatus_status" in script_mcp.CORE_HANDLERS

        handler = script_mcp.CORE_HANDLERS["mekong_civilstatus_birth"]
        b_raw = handler({
            "child_name": "Phan Hoang Nam",
            "gender": "MALE",
            "birth_date": "2024-08-15",
            "birth_place": "Hai Phong",
            "registrant_name": "Phan Hoang Minh",
        })
        b_data = json.loads(b_raw)
        assert b_data["child_name"] == "Phan Hoang Nam"
