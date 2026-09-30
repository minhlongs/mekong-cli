"""
Test suite for Vietnamese Cultural Heritage, Antiquities & National Treasures Suite (Phase 104).
Covers:
- HeritageEngine (pure standard-library engine, SQLite WAL persistence).
- CLI surface (mekong heritage relic/artifact/excavate/exhibit/list/status).
- MCP parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.heritage_engine import HeritageEngine
from src.cli.commands.heritage_command import heritage_app


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_heritage.db")
        yield db_path


class TestHeritageEngine:
    def test_engine_init_and_tables(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        with engine._get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
        assert "heritage_relic_sites" in tables
        assert "heritage_artifacts" in tables
        assert "heritage_excavations" in tables
        assert "heritage_exhibitions" in tables

    def test_relic_site_compliant(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.assess_relic_site(
            name="Khu Di tích Cố đô Huế",
            classification="SPECIAL_NATIONAL",
            province="Thừa Thiên Huế",
            zone1_area_sqm=120000.0,
            zone2_area_sqm=350000.0,
            construction_in_zone1=False,
            minister_approved=True,
        )
        assert res.status == "PROTECTED_COMPLIANT"
        assert res.site_id.startswith("SITE-SPE-")
        assert len(res.reasons) == 0

    def test_relic_site_zone1_encroachment_violation(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.assess_relic_site(
            name="Di tích Chùa Một Cột",
            classification="NATIONAL",
            province="Hà Nội",
            zone1_area_sqm=2000.0,
            zone2_area_sqm=5000.0,
            construction_in_zone1=True,
            minister_approved=True,
        )
        assert res.status == "PROTECTION_VIOLATION"
        assert any("Khu vực bảo vệ I" in r for r in res.reasons)

    def test_relic_site_buffer_missing_minister_approval(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.assess_relic_site(
            name="Quần thể Di tích Cố đô Hoa Lư",
            classification="SPECIAL_NATIONAL",
            province="Ninh Bình",
            zone1_area_sqm=50000.0,
            zone2_area_sqm=100000.0,
            construction_in_zone1=False,
            minister_approved=False,
        )
        assert res.status == "PROTECTION_VIOLATION"
        assert any("Bộ trưởng Bộ VHTTDL" in r for r in res.reasons)

    def test_artifact_antiquity_compliant(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.register_artifact(
            name="Bình gốm hoa nâu thời Lý",
            category="ANTIQUITY",
            origin_period="Lý",
            material="Gốm men",
            owner_type="PRIVATE",
            is_unique=False,
            age_years=900,
        )
        assert res.status == "REGISTERED_COMPLIANT"
        assert res.registration_cert_no.startswith("DSVH-DK-")
        assert not res.export_prohibited

    def test_artifact_antiquity_age_below_100_rejected(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.register_artifact(
            name="Đĩa gốm sản xuất năm 1970",
            category="ANTIQUITY",
            origin_period="Hiện đại",
            material="Gốm",
            owner_type="PRIVATE",
            age_years=55,
        )
        assert res.status == "REGISTRATION_REJECTED"
        assert any("100 năm tuổi" in r for r in res.reasons)

    def test_artifact_national_treasure_compliant(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.register_artifact(
            name="Trống đồng Cảnh Thịnh thời Tây Sơn",
            category="NATIONAL_TREASURE",
            origin_period="Tây Sơn",
            material="Đồng",
            owner_type="STATE",
            is_unique=True,
            age_years=225,
            historical_scientific_value=True,
        )
        assert res.status == "REGISTERED_COMPLIANT"
        assert res.recognized_as_treasure
        assert res.export_prohibited

    def test_artifact_national_treasure_non_unique_rejected(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.register_artifact(
            name="Tiền xu cổ đúc hàng loạt",
            category="NATIONAL_TREASURE",
            origin_period="Lê",
            material="Đồng",
            owner_type="STATE",
            is_unique=False,
            age_years=300,
        )
        assert res.status == "REGISTRATION_REJECTED"
        assert not res.recognized_as_treasure
        assert any("độc bản" in r for r in res.reasons)

    def test_excavation_permit_approved(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.permit_excavation(
            project_name="Thăm dò di chỉ Đồng Đậu 2026",
            location="Vĩnh Phúc",
            lead_archaeologist="TS. Lê Văn Khảo",
            degree_major="Khảo cổ học",
            experience_years=6,
            permit_days=90,
            artifacts_handed_over=True,
        )
        assert res.is_approved
        assert res.status == "EXCAVATION_PERMITTED"
        assert res.permit_id.startswith("EXC-")

    def test_excavation_permit_rejected_major_and_experience(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.permit_excavation(
            project_name="Khai quật di chỉ ven sông Mã",
            location="Thanh Hóa",
            lead_archaeologist="Nguyễn Văn Kỹ",
            degree_major="Kỹ thuật Xây dựng",
            experience_years=1,
            permit_days=30,
            artifacts_handed_over=True,
        )
        assert not res.is_approved
        assert res.status == "PERMIT_DENIED"
        assert any("khảo cổ học hoặc lịch sử" in r for r in res.reasons)
        assert any("kinh nghiệm thực tế" in r for r in res.reasons)

    def test_excavation_permit_rejected_missing_handover(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.permit_excavation(
            project_name="Khai quật di tích Óc Eo",
            location="An Giang",
            lead_archaeologist="ThS. Nguyễn Nam",
            degree_major="Khảo cổ học",
            experience_years=5,
            permit_days=60,
            artifacts_handed_over=False,
        )
        assert not res.is_approved
        assert any("bàn giao" in r for r in res.reasons)

    def test_museum_exhibition_display_approved(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.audit_exhibition(
            museum_name="Bảo tàng Lịch sử Quốc gia",
            artifact_id="ART-001",
            artifact_name="Trống đồng Đông Sơn",
            is_national_treasure=False,
            is_overseas_tour=False,
            temp_celsius=21.0,
            humidity_pct=52.0,
        )
        assert res.status == "APPROVED_FOR_DISPLAY"
        assert len(res.reasons) == 0

    def test_museum_exhibition_overseas_tour_approved(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.audit_exhibition(
            museum_name="Bảo tàng Lịch sử TP.HCM",
            artifact_id="ART-TREASURE-01",
            artifact_name="Tượng Phật Đồng Dương",
            is_national_treasure=True,
            is_overseas_tour=True,
            insurance_covered_100pct=True,
            prime_minister_approval=True,
            temp_celsius=20.0,
            humidity_pct=50.0,
        )
        assert res.status == "OVERSEAS_TOUR_APPROVED"
        assert len(res.reasons) == 0

    def test_museum_exhibition_overseas_uninsured_rejected(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.audit_exhibition(
            museum_name="Bảo tàng Cổ vật Cung đình Huế",
            artifact_id="ART-002",
            artifact_name="Áo Nhật Bình hoàng thái hậu",
            is_national_treasure=False,
            is_overseas_tour=True,
            insurance_covered_100pct=False,
            temp_celsius=21.0,
            humidity_pct=52.0,
        )
        assert res.status == "EXHIBITION_REJECTED"
        assert any("bảo hiểm toàn diện" in r for r in res.reasons)

    def test_museum_exhibition_overseas_treasure_missing_pm_approval(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.audit_exhibition(
            museum_name="Bảo tàng Mỹ thuật Việt Nam",
            artifact_id="ART-TREASURE-02",
            artifact_name="Bức tranh Vườn xuân Trung Nam Bắc",
            is_national_treasure=True,
            is_overseas_tour=True,
            insurance_covered_100pct=True,
            prime_minister_approval=False,
            temp_celsius=22.0,
            humidity_pct=55.0,
        )
        assert res.status == "EXHIBITION_REJECTED"
        assert any("Thủ tướng Chính phủ" in r for r in res.reasons)

    def test_museum_exhibition_microclimate_violation(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        res = engine.audit_exhibition(
            museum_name="Nhà Trưng bày Di tích Địa phương",
            artifact_id="ART-003",
            artifact_name="Sắc phong triều Nguyễn",
            is_national_treasure=False,
            is_overseas_tour=False,
            temp_celsius=32.0,
            humidity_pct=85.0,
        )
        assert res.status == "EXHIBITION_REJECTED"
        assert any("Nhiệt độ" in r for r in res.reasons)
        assert any("Độ ẩm" in r for r in res.reasons)

    def test_telemetry_and_list_records(self, temp_db: str):
        engine = HeritageEngine(db_path=temp_db)
        engine.assess_relic_site("Di tích A", "SPECIAL_NATIONAL", "Hà Nội", 5000, 10000)
        engine.register_artifact("Bảo vật A", "NATIONAL_TREASURE", "Đông Sơn", "Đồng", "STATE", True, 2000, True)
        engine.permit_excavation("Khảo cổ A", "Hà Nội", "TS A", "Khảo cổ học", 5)
        engine.audit_exhibition("Bảo tàng A", "ART-1", "Hiện vật 1", False, False)

        telemetry = engine.get_status()
        assert telemetry.total_relic_sites >= 1
        assert telemetry.special_national_sites >= 1
        assert telemetry.national_treasures_count >= 1
        assert telemetry.active_excavation_permits >= 1
        assert telemetry.approved_exhibitions >= 1

        records = engine.list_records(category="all", limit=10)
        assert "relic_sites" in records
        assert "artifacts" in records
        assert "excavations" in records
        assert "exhibitions" in records


class TestHeritageCli:
    def setup_method(self):
        self.runner = CliRunner()

    def test_cli_overview_and_json(self):
        res = self.runner.invoke(heritage_app, [])
        assert res.exit_code == 0
        assert "HỆ THỐNG QUẢN TRỊ BẢO TỒN DI SẢN VĂN HÓA" in res.output

        res_json = self.runner.invoke(heritage_app, ["--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_relic_sites" in data

    def test_cli_relic_cmd(self):
        res = self.runner.invoke(
            heritage_app,
            [
                "relic",
                "Khu Di tích Hoàng thành Thăng Long",
                "--class", "SPECIAL_NATIONAL",
                "--province", "Hà Nội",
                "--zone1", "150000",
                "--zone2", "400000",
                "--no-construction-z1",
                "--minister-approved",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "PROTECTED_COMPLIANT"

    def test_cli_artifact_cmd(self):
        res = self.runner.invoke(
            heritage_app,
            [
                "artifact",
                "Trống đồng Đền Hùng",
                "--cat", "NATIONAL_TREASURE",
                "--period", "Đông Sơn",
                "--material", "Đồng",
                "--owner", "STATE",
                "--unique",
                "--age", "2500",
                "--value",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["recognized_as_treasure"] is True
        assert data["status"] == "REGISTERED_COMPLIANT"

    def test_cli_excavate_cmd(self):
        res = self.runner.invoke(
            heritage_app,
            [
                "excavate",
                "Khai quật Thành Nhà Hồ 2026",
                "Vĩnh Lộc, Thanh Hóa",
                "PGS.TS. Đỗ Khảo",
                "--major", "Khảo cổ học",
                "--exp", "7",
                "--days", "120",
                "--handover",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_approved"] is True
        assert data["status"] == "EXCAVATION_PERMITTED"

    def test_cli_exhibit_cmd(self):
        res = self.runner.invoke(
            heritage_app,
            [
                "exhibit",
                "Bảo tàng Lịch sử Quốc gia",
                "ART-DH01",
                "Trống đồng Ngọc Lũ I",
                "--treasure",
                "--overseas",
                "--insurance",
                "--pm-approval",
                "--temp", "21.0",
                "--humidity", "52.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "OVERSEAS_TOUR_APPROVED"

    def test_cli_list_and_status_cmds(self):
        res_list = self.runner.invoke(heritage_app, ["list", "--category", "all", "--json"])
        assert res_list.exit_code == 0
        data_list = json.loads(res_list.output)
        assert isinstance(data_list, dict)

        res_status = self.runner.invoke(heritage_app, ["status", "--json"])
        assert res_status.exit_code == 0
        data_status = json.loads(res_status.output)
        assert "total_relic_sites" in data_status


class TestHeritageMcpHandlers:
    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_heritage_relic,
            handle_heritage_artifact,
            handle_heritage_excavate,
            handle_heritage_exhibit,
            handle_heritage_list,
            handle_heritage_status,
        )

        res_relic = json.loads(handle_heritage_relic({
            "name": "Chùa Tây Phương",
            "classification": "SPECIAL_NATIONAL",
            "province": "Hà Nội",
        }))
        assert res_relic["status"] == "PROTECTED_COMPLIANT"

        res_art = json.loads(handle_heritage_artifact({
            "name": "Bình gốm Chu Đậu",
            "category": "ANTIQUITY",
            "age_years": 500,
        }))
        assert res_art["status"] == "REGISTERED_COMPLIANT"

        res_exc = json.loads(handle_heritage_excavate({
            "project_name": "Khai quật Óc Eo",
            "location": "An Giang",
            "lead_archaeologist": "TS. Nam",
            "degree_major": "Khảo cổ học",
            "experience_years": 5,
        }))
        assert res_exc["is_approved"] is True

        res_exh = json.loads(handle_heritage_exhibit({
            "museum_name": "Bảo tàng Mỹ thuật",
            "artifact_id": "ART-005",
            "artifact_name": "Tượng Quan Âm nghìn mắt nghìn tay",
            "temp_celsius": 21.0,
            "humidity_pct": 52.0,
        }))
        assert res_exh["status"] == "APPROVED_FOR_DISPLAY"

        res_list = json.loads(handle_heritage_list({"category": "all"}))
        assert isinstance(res_list, dict)

        res_status = json.loads(handle_heritage_status({}))
        assert "total_relic_sites" in res_status

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        res_relic = json.loads(server._handle_heritage_relic(
            name="Văn Miếu - Quốc Tử Giám",
            classification="SPECIAL_NATIONAL",
            province="Hà Nội",
        ))
        assert res_relic["status"] == "PROTECTED_COMPLIANT"

        res_art = json.loads(server._handle_heritage_artifact(
            name="Bia Tiến sĩ Văn Miếu",
            category="NATIONAL_TREASURE",
            is_unique=True,
            age_years=500,
            historical_scientific_value=True,
        ))
        assert res_art["recognized_as_treasure"] is True

        res_exc = json.loads(server._handle_heritage_excavate(
            project_name="Thăm dò địa tầng",
            location="Hà Nội",
            lead_archaeologist="TS. Tuấn",
            degree_major="Khảo cổ học",
            experience_years=4,
        ))
        assert res_exc["is_approved"] is True

        res_exh = json.loads(server._handle_heritage_exhibit(
            museum_name="Bảo tàng Lịch sử",
            artifact_id="ART-009",
            artifact_name="Hiện vật gốm",
            temp_celsius=22.0,
            humidity_pct=53.0,
        ))
        assert res_exh["status"] == "APPROVED_FOR_DISPLAY"

        res_list = json.loads(server._handle_heritage_list(category="all"))
        assert isinstance(res_list, dict)

        res_status = json.loads(server._handle_heritage_status())
        assert "total_relic_sites" in res_status
