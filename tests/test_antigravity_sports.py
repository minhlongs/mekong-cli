"""
Test suite for Vietnamese Physical Training, Sports, Professional Athletics & Anti-Doping Suite (Phase 105).
Covers:
- SportsEngine (pure standard-library engine, SQLite WAL persistence).
- CLI surface (mekong sports contract/doping/extreme/tournament/list/status).
- MCP parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.sports_engine import SportsEngine
from src.cli.commands.sports_command import sports_app


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_sports.db")
        yield db_path


class TestSportsEngine:
    def test_engine_init_and_tables(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        with engine._get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
        assert "athlete_contracts" in tables
        assert "doping_tests" in tables
        assert "extreme_sports_permits" in tables
        assert "tournament_sanctions" in tables

    def test_athlete_contract_approved(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.contract_athlete(
            athlete_name="Nguyễn Văn Toàn",
            sport="BÓNG ĐÁ",
            club_name="CLB Thép Xanh Nam Định",
            contract_type="PROFESSIONAL",
            salary_vnd=60000000.0,
            duration_months=36,
            insurance_covered=True,
        )
        assert res["status"] == "APPROVED"
        assert res["is_compliant"] is True
        assert res["contract_id"].startswith("ATH-CTR-")
        assert len(res["violations"]) == 0

    def test_athlete_contract_short_duration_rejected(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.contract_athlete(
            athlete_name="Trần Văn B",
            sport="ĐIỀN KINH",
            club_name="Đoàn TDTT Quân Đội",
            duration_months=3,  # Minimum 6 months required
            insurance_covered=True,
        )
        assert res["status"] == "REJECTED"
        assert res["is_compliant"] is False
        assert any("06 tháng" in v for v in res["violations"])

    def test_athlete_contract_missing_insurance_rejected(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.contract_athlete(
            athlete_name="Lê Văn C",
            sport="BƠI LỘI",
            club_name="CLB Bơi Lội Đà Nẵng",
            duration_months=12,
            insurance_covered=False,
        )
        assert res["status"] == "REJECTED"
        assert res["is_compliant"] is False
        assert any("bảo hiểm" in v for v in res["violations"])

    def test_athlete_transfer_contract(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.contract_athlete(
            athlete_name="Nguyễn Quang Hải",
            sport="BÓNG ĐÁ",
            club_name="CLB Công An Hà Nội",
            contract_type="TRANSFER",
            salary_vnd=100000000.0,
            duration_months=24,
            insurance_covered=True,
            transfer_fee_vnd=5000000000.0,
        )
        assert res["status"] == "APPROVED"
        assert res["transfer_fee_vnd"] == 5000000000.0

    def test_doping_test_negative(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.test_doping(
            athlete_name="Nguyễn Thị Oanh",
            sport="ĐIỀN KINH",
            sample_type="URINE",
            substance_detected=None,
        )
        assert res["result"] == "NEGATIVE"
        assert res["is_adverse"] is False
        assert res["sanction_months"] == 0

    def test_doping_test_positive_anabolic_steroids(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.test_doping(
            athlete_name="VĐV Vi Phạm",
            sport="CỬ TẠ",
            sample_type="URINE",
            substance_detected="Stanozolol",
            wada_class="S1",
            has_tue=False,
        )
        assert res["result"] == "ADVERSE_ANALYTICAL_FINDING"
        assert res["is_adverse"] is True
        assert res["sanction_months"] == 48  # 4 years for S1 Anabolic
        assert "DƯƠNG TÍNH" in res["statutory_notes"]

    def test_doping_test_positive_stimulants(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.test_doping(
            athlete_name="VĐV Kích Thích",
            sport="XE ĐẠP",
            sample_type="URINE",
            substance_detected="Amphetamine",
            wada_class="S6",
            has_tue=False,
        )
        assert res["result"] == "ADVERSE_ANALYTICAL_FINDING"
        assert res["sanction_months"] == 24  # 2 years for S6 Stimulants

    def test_doping_test_tue_exemption(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.test_doping(
            athlete_name="Trần Đình Trọng",
            sport="BÓNG ĐÁ",
            sample_type="URINE",
            substance_detected="Prednisolone",
            wada_class="S9",
            has_tue=True,
            tue_approved=True,
        )
        assert res["result"] == "TUE_EXEMPTION"
        assert res["sanction_months"] == 0
        assert "miễn trừ điều trị y tế TUE" in res["statutory_notes"]

    def test_extreme_sport_licensed(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.license_extreme_sport(
            facility_name="CLB Dù lượn Đà Lạt Paragliding",
            sport_type="PARAGLIDING",
            certified_coach=True,
            rescue_certified=True,
            equipment_inspected=True,
            medical_plan=True,
        )
        assert res["status"] == "LICENSED"
        assert res["is_approved"] is True
        assert len(res["violations"]) == 0

    def test_extreme_sport_uninspected_equipment_rejected(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.license_extreme_sport(
            facility_name="Cơ sở Leo Núi Fansipan",
            sport_type="ROCK_CLIMBING",
            certified_coach=True,
            rescue_certified=True,
            equipment_inspected=False,  # Uninspected gear
            medical_plan=True,
        )
        assert res["status"] == "REJECTED"
        assert res["is_approved"] is False
        assert any("kiểm định an toàn" in v for v in res["violations"])

    def test_extreme_sport_invalid_sport_type(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.license_extreme_sport(
            facility_name="CLB Bắn Bi",
            sport_type="MARBLES_UNKNOWN",
            certified_coach=True,
            rescue_certified=True,
            equipment_inspected=True,
            medical_plan=True,
        )
        assert res["status"] == "REJECTED"
        assert any("danh mục quy định" in v for v in res["violations"])

    def test_tournament_sanctioned(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.sanction_tournament(
            tournament_name="Giải Vô địch Quốc gia V.League 1 2026",
            sport="BÓNG ĐÁ",
            scale="NATIONAL",
            organizer="VPF & VFF",
            venue_name="Sân vận động Quốc gia Mỹ Đình",
            lighting_lux=1800.0,
            medical_team=True,
            emergency_exits=True,
        )
        assert res["status"] == "SANCTIONED"
        assert res["is_approved"] is True
        assert len(res["violations"]) == 0

    def test_tournament_low_lighting_rejected(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        res = engine.sanction_tournament(
            tournament_name="Giải Thiếu Niên Phường",
            sport="BÓNG ĐÁ",
            lighting_lux=300.0,  # Below 500 lux
            medical_team=True,
            emergency_exits=True,
        )
        assert res["status"] == "REJECTED"
        assert res["is_approved"] is False
        assert any("500 lux" in v for v in res["violations"])

    def test_telemetry_and_list_records(self, temp_db: str):
        engine = SportsEngine(db_path=temp_db)
        engine.contract_athlete("VĐV A", "BÓNG ĐÁ", "CLB A", salary_vnd=40000000.0)
        engine.test_doping("VĐV A", "BÓNG ĐÁ")
        engine.license_extreme_sport("Cơ sở X", "SCUBA_DIVING")
        engine.sanction_tournament("Giải Y", "BƠI LỘI")

        telemetry = engine.get_sports_telemetry()
        assert telemetry["total_contracts"] == 1
        assert telemetry["approved_contracts"] == 1
        assert telemetry["total_doping_tests"] == 1
        assert telemetry["positive_doping_cases"] == 0
        assert telemetry["clean_doping_rate_pct"] == 100.0
        assert telemetry["licensed_extreme_facilities"] == 1
        assert telemetry["sanctioned_tournaments"] == 1

        records = engine.list_sports_records(category="ALL")
        assert len(records["contracts"]) == 1
        assert len(records["doping_tests"]) == 1
        assert len(records["extreme_permits"]) == 1
        assert len(records["tournaments"]) == 1


class TestSportsCli:
    def test_cli_overview_and_json(self):
        runner = CliRunner()
        res = runner.invoke(sports_app, [])
        assert res.exit_code == 0
        assert "HỆ THỐNG QUẢN TRỊ THỂ DỤC THỂ THAO & PHÒNG CHỐNG DOPING" in res.output

        res_json = runner.invoke(sports_app, ["--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_contracts" in data
        assert "clean_doping_rate_pct" in data

    def test_cli_contract_cmd(self):
        runner = CliRunner()
        res = runner.invoke(sports_app, [
            "contract",
            "Nguyễn Hoàng Đức",
            "--sport", "BÓNG ĐÁ",
            "--club", "CLB Thể Công Viettel",
            "--salary", "50000000",
            "--months", "24",
            "--insurance",
        ])
        assert res.exit_code == 0
        assert "Đăng Ký Hợp Đồng VĐV Chuyên Nghiệp" in res.output

        res_json = runner.invoke(sports_app, [
            "contract",
            "Nguyễn Hoàng Đức",
            "--salary", "50000000",
            "--json",
        ])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "APPROVED"

    def test_cli_doping_cmd(self):
        runner = CliRunner()
        res = runner.invoke(sports_app, [
            "doping",
            "VĐV Thử Nghiệm",
            "--sport", "ĐIỀN KINH",
        ])
        assert res.exit_code == 0
        assert "Biên Bản Kiểm Tra Doping & Chế Tài WADA" in res.output

        res_json = runner.invoke(sports_app, [
            "doping",
            "VĐV Dương Tính",
            "--substance", "Stanozolol",
            "--wada-class", "S1",
            "--json",
        ])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["result"] == "ADVERSE_ANALYTICAL_FINDING"
        assert data["sanction_months"] == 48

    def test_cli_extreme_cmd(self):
        runner = CliRunner()
        res = runner.invoke(sports_app, [
            "extreme",
            "CLB Dù Lượn Mù Cang Chải",
            "--sport-type", "PARAGLIDING",
            "--coach",
            "--rescue",
            "--equipment",
            "--medical",
        ])
        assert res.exit_code == 0
        assert "Thẩm Định Cơ Sở Kinh Doanh Thể Thao Mạo Hiểm" in res.output

    def test_cli_tournament_cmd(self):
        runner = CliRunner()
        res = runner.invoke(sports_app, [
            "tournament",
            "Giải Bơi Lội Vô Địch Quốc Gia 2026",
            "--sport", "BƠI LỘI",
            "--lighting", "1200",
            "--medical",
            "--emergency",
        ])
        assert res.exit_code == 0
        assert "Phê Duyệt Tổ Chức Giải Thi Đấu Thể Thao" in res.output

    def test_cli_list_and_status(self):
        runner = CliRunner()
        res_list = runner.invoke(sports_app, ["list", "--category", "ALL", "--limit", "10"])
        assert res_list.exit_code == 0

        res_status = runner.invoke(sports_app, ["status"])
        assert res_status.exit_code == 0
        assert "Vietnam National Sports Telemetry" in res_status.output


class TestSportsMcpHandlers:
    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_sports_contract,
            handle_sports_doping,
            handle_sports_extreme,
            handle_sports_tournament,
            handle_sports_list,
            handle_sports_status,
        )

        res_c = handle_sports_contract({
            "athlete_name": "Phan Văn Đức",
            "sport": "BÓNG ĐÁ",
            "salary_vnd": 45000000.0,
            "duration_months": 24,
            "insurance_covered": True,
        })
        data_c = json.loads(res_c)
        assert data_c["status"] == "APPROVED"

        res_d = handle_sports_doping({
            "athlete_name": "Phan Văn Đức",
            "sport": "BÓNG ĐÁ",
        })
        data_d = json.loads(res_d)
        assert data_d["result"] == "NEGATIVE"

        res_e = handle_sports_extreme({
            "facility_name": "Trung Tâm Lặn Nha Trang",
            "sport_type": "SCUBA_DIVING",
            "certified_coach": True,
            "rescue_certified": True,
            "equipment_inspected": True,
            "medical_plan": True,
        })
        data_e = json.loads(res_e)
        assert data_e["status"] == "LICENSED"

        res_t = handle_sports_tournament({
            "tournament_name": "Giải Điền Kinh Cúp Tốc Độ 2026",
            "sport": "ĐIỀN KINH",
            "lighting_lux": 1400.0,
            "medical_team": True,
            "emergency_exits": True,
        })
        data_t = json.loads(res_t)
        assert data_t["status"] == "SANCTIONED"

        res_l = handle_sports_list({"category": "ALL", "limit": 10})
        data_l = json.loads(res_l)
        assert "contracts" in data_l

        res_s = handle_sports_status({})
        data_s = json.loads(res_s)
        assert "total_contracts" in data_s

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        res_c = server._handle_sports_contract(
            athlete_name="Bùi Tiến Dũng",
            sport="BÓNG ĐÁ",
            salary_vnd=35000000.0,
            duration_months=12,
            insurance_covered=True,
        )
        data_c = json.loads(res_c)
        assert data_c["status"] == "APPROVED"

        res_d = server._handle_sports_doping(
            athlete_name="Bùi Tiến Dũng",
            sport="BÓNG ĐÁ",
        )
        data_d = json.loads(res_d)
        assert data_d["result"] == "NEGATIVE"

        res_e = server._handle_sports_extreme(
            facility_name="Cơ sở Bungee Nha Trang",
            sport_type="BUNGEE_JUMPING",
            certified_coach=True,
            rescue_certified=True,
            equipment_inspected=True,
            medical_plan=True,
        )
        data_e = json.loads(res_e)
        assert data_e["status"] == "LICENSED"

        res_t = server._handle_sports_tournament(
            tournament_name="Giải Futsal Toàn Quốc 2026",
            sport="BÓNG ĐÁ",
            lighting_lux=1000.0,
            medical_team=True,
            emergency_exits=True,
        )
        data_t = json.loads(res_t)
        assert data_t["status"] == "SANCTIONED"

        res_l = server._handle_sports_list(category="ALL", limit=10)
        data_l = json.loads(res_l)
        assert "contracts" in data_l

        res_s = server._handle_sports_status()
        data_s = json.loads(res_s)
        assert "total_contracts" in data_s
