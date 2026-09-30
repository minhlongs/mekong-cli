"""
Test suite for Vietnamese Veterinary Medicine, Animal Disease Surveillance & Livestock Quarantine Suite (Phase 106).
Covers:
- VeterinaryEngine (pure standard-library engine, SQLite WAL persistence).
- CLI surface (mekong veterinary quarantine/outbreak/slaughter/medicine/list/status).
- MCP parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.veterinary_engine import VeterinaryEngine
from src.cli.commands.veterinary_command import veterinary_app


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_veterinary.db")
        yield db_path


class TestVeterinaryEngine:
    def test_engine_init_and_tables(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        with engine._get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
        assert "quarantine_certificates" in tables
        assert "disease_outbreaks" in tables
        assert "slaughter_inspections" in tables
        assert "medicine_facilities" in tables

    def test_quarantine_shipment_certified(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.quarantine_shipment(
            shipment_type="INTER_PROVINCIAL",
            animal_species="LỢN THỊT",
            quantity_head=500,
            origin_province="Đồng Nai",
            destination_province="TP. Hồ Chí Minh",
            safe_zone=True,
            tested_negative=True,
            disinfected=True,
            lead_sealed=True,
        )
        assert res["status"] == "CERTIFIED"
        assert res["is_approved"] is True
        assert res["cert_id"].startswith("VET-QC-")
        assert len(res["violations"]) == 0

    def test_quarantine_shipment_missing_tests_rejected(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.quarantine_shipment(
            shipment_type="INTER_PROVINCIAL",
            animal_species="GÀ LÔNG",
            quantity_head=1000,
            origin_province="Tiền Giang",
            destination_province="Long An",
            tested_negative=False,  # Missing negative lab tests
        )
        assert res["status"] == "REJECTED"
        assert res["is_approved"] is False
        assert any("xét nghiệm âm tính" in v for v in res["violations"])

    def test_quarantine_shipment_undisinfected_rejected(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.quarantine_shipment(
            shipment_type="INTER_PROVINCIAL",
            animal_species="BÒ THỊT",
            quantity_head=40,
            origin_province="Bình Thuận",
            destination_province="TP. Hồ Chí Minh",
            disinfected=False,  # Not disinfected
        )
        assert res["status"] == "REJECTED"
        assert any("tiêu độc, khử trùng" in v for v in res["violations"])

    def test_disease_outbreak_containment_active(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.declare_outbreak(
            disease_name="ASF",
            species="LỢN",
            location_province="Bắc Giang",
            culled_count=150,
            cull_method="DEEP_BURIAL",
            radius_km=3.5,
            ring_vaccination=True,
            quarantine_post_active=True,
        )
        assert res["status"] == "CONTAINMENT_ACTIVE"
        assert res["is_controlled"] is True
        assert res["outbreak_id"].startswith("EPI-OUT-")
        assert "African Swine Fever" in res["disease_description"]

    def test_disease_outbreak_small_radius_rejected(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.declare_outbreak(
            disease_name="H5N1",
            species="GIA CẦM",
            location_province="Thái Bình",
            culled_count=3000,
            radius_km=1.5,  # Below statutory 3.0 km
        )
        assert res["status"] == "NON_COMPLIANT_RESPONSE"
        assert res["is_controlled"] is False
        assert any("3.0 km" in v for v in res["violations"])

    def test_slaughter_inspection_passed_and_stamped(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.inspect_slaughter(
            abattoir_name="Lò Mổ Tập Trung An Hạ",
            species="LỢN",
            batch_size=200,
            antemortem_healthy=True,
            postmortem_passed=True,
            water_injected=False,
        )
        assert res["status"] == "PASSED_STAMPED"
        assert res["is_passed"] is True
        assert res["stamp_issued"] is True
        assert len(res["violations"]) == 0

    def test_slaughter_inspection_water_injected_prohibited(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.inspect_slaughter(
            abattoir_name="Lò Mổ Thủ Công B",
            species="LỢN",
            batch_size=50,
            antemortem_healthy=True,
            postmortem_passed=True,
            water_injected=True,  # Prohibited water pumping
        )
        assert res["status"] == "REJECTED_DISPOSAL"
        assert res["is_passed"] is False
        assert res["stamp_issued"] is False
        assert any("Bơm nước" in v for v in res["violations"])

    def test_medicine_facility_certified(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.certify_medicine_facility(
            facility_name="Công Ty Cổ Phần Dược Thú Y Vemedim",
            license_type="MANUFACTURE",
            chief_vet_licensed=True,
            gmp_certified=True,
            has_prohibited_substances=False,
        )
        assert res["status"] == "CERTIFIED"
        assert res["is_certified"] is True
        assert len(res["violations"]) == 0

    def test_medicine_facility_prohibited_substance_rejected(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        res = engine.certify_medicine_facility(
            facility_name="Cơ sở Chế Biến Thức Ăn X",
            license_type="MANUFACTURE",
            chief_vet_licensed=True,
            gmp_certified=True,
            has_prohibited_substances=True,  # Banned substances
        )
        assert res["status"] == "REJECTED"
        assert res["is_certified"] is False
        assert any("chất cấm" in v for v in res["violations"])

    def test_telemetry_and_list_records(self, temp_db: str):
        engine = VeterinaryEngine(db_path=temp_db)
        engine.quarantine_shipment("INTER_PROVINCIAL", "LỢN THỊT", 300, "Đồng Nai", "TP.HCM")
        engine.declare_outbreak("ASF", "LỢN", "Hà Tĩnh", 80)
        engine.inspect_slaughter("Lò Mổ X", "BÒ", 20)
        engine.certify_medicine_facility("Nhà Máy Thuốc Y", "TRADING", gmp_certified=False)

        telemetry = engine.get_veterinary_telemetry()
        assert telemetry["total_quarantine_certs"] == 1
        assert telemetry["approved_quarantine_certs"] == 1
        assert telemetry["total_quarantined_animals"] == 300
        assert telemetry["total_outbreaks_recorded"] == 1
        assert telemetry["total_culled_animals"] == 80
        assert telemetry["total_slaughter_inspections"] == 1
        assert telemetry["passed_slaughter_batches"] == 1
        assert telemetry["slaughter_pass_rate_pct"] == 100.0

        records = engine.list_veterinary_records(category="ALL")
        assert len(records["quarantine"]) == 1
        assert len(records["outbreaks"]) == 1
        assert len(records["slaughter"]) == 1
        assert len(records["medicine"]) == 1


class TestVeterinaryCli:
    def test_cli_overview_and_json(self):
        runner = CliRunner()
        res = runner.invoke(veterinary_app, [])
        assert res.exit_code == 0
        assert "HỆ THỐNG QUẢN TRỊ DỊCH TỄ THÚ Y & KIỂM DỊCH ĐỘNG VẬT" in res.output

        res_json = runner.invoke(veterinary_app, ["--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_quarantine_certs" in data
        assert "slaughter_pass_rate_pct" in data

    def test_cli_quarantine_cmd(self):
        runner = CliRunner()
        res = runner.invoke(veterinary_app, [
            "quarantine",
            "BÒ VỖ BÉO",
            "--qty", "80",
            "--origin", "Gia Lai",
            "--dest", "Bình Dương",
            "--safe-zone",
            "--tested",
            "--disinfected",
            "--sealed",
        ])
        assert res.exit_code == 0
        assert "Giấy Chứng Nhận Kiểm Dịch Thú Y" in res.output

        res_json = runner.invoke(veterinary_app, [
            "quarantine",
            "LỢN THỊT",
            "--qty", "200",
            "--json",
        ])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["status"] == "CERTIFIED"

    def test_cli_outbreak_cmd(self):
        runner = CliRunner()
        res = runner.invoke(veterinary_app, [
            "outbreak",
            "ASF",
            "--species", "LỢN",
            "--location", "Nghệ An",
            "--culled", "180",
            "--radius", "4.0",
            "--vaccine",
            "--post",
        ])
        assert res.exit_code == 0
        assert "Hồ Sơ Giám Sát & Công Bố Ổ Dịch Thú Y" in res.output

    def test_cli_slaughter_cmd(self):
        runner = CliRunner()
        res = runner.invoke(veterinary_app, [
            "slaughter",
            "Lò Mổ Tập Trung Xuân Thới Thượng",
            "--species", "LỢN",
            "--batch", "350",
            "--ante",
            "--post",
            "--no-water",
        ])
        assert res.exit_code == 0
        assert "Biên Bản Kiểm Soát Giết Mổ Thú Y" in res.output

    def test_cli_medicine_cmd(self):
        runner = CliRunner()
        res = runner.invoke(veterinary_app, [
            "medicine",
            "Công Ty Thuốc Thú Y Marphavet",
            "--type", "MANUFACTURE",
            "--chief-vet",
            "--gmp",
            "--no-prohibited",
        ])
        assert res.exit_code == 0
        assert "Thẩm Định Cơ Sở Dược Phẩm Thú Y & GMP" in res.output

    def test_cli_list_and_status(self):
        runner = CliRunner()
        res_list = runner.invoke(veterinary_app, ["list", "--category", "ALL", "--limit", "10"])
        assert res_list.exit_code == 0

        res_status = runner.invoke(veterinary_app, ["status"])
        assert res_status.exit_code == 0
        assert "Vietnam National Veterinary Telemetry" in res_status.output


class TestVeterinaryMcpHandlers:
    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_veterinary_quarantine,
            handle_veterinary_outbreak,
            handle_veterinary_slaughter,
            handle_veterinary_medicine,
            handle_veterinary_list,
            handle_veterinary_status,
        )

        res_q = handle_veterinary_quarantine({
            "animal_species": "LỢN GIỐNG",
            "quantity_head": 120,
            "origin_province": "Bình Phước",
            "destination_province": "Đồng Nai",
            "safe_zone": True,
            "tested_negative": True,
            "disinfected": True,
            "lead_sealed": True,
        })
        data_q = json.loads(res_q)
        assert data_q["status"] == "CERTIFIED"

        res_o = handle_veterinary_outbreak({
            "disease_name": "FMD",
            "species": "BÒ",
            "location_province": "Quảng Trị",
            "culled_count": 30,
            "radius_km": 3.0,
            "ring_vaccination": True,
            "quarantine_post_active": True,
        })
        data_o = json.loads(res_o)
        assert data_o["status"] == "CONTAINMENT_ACTIVE"

        res_s = handle_veterinary_slaughter({
            "abattoir_name": "Lò Mổ Tập Trung Bình Điền",
            "species": "LỢN",
            "batch_size": 300,
            "antemortem_healthy": True,
            "postmortem_passed": True,
            "water_injected": False,
        })
        data_s = json.loads(res_s)
        assert data_s["status"] == "PASSED_STAMPED"

        res_m = handle_veterinary_medicine({
            "facility_name": "Công Ty Bio-Pharmachemie",
            "license_type": "MANUFACTURE",
            "chief_vet_licensed": True,
            "gmp_certified": True,
            "has_prohibited_substances": False,
        })
        data_m = json.loads(res_m)
        assert data_m["status"] == "CERTIFIED"

        res_l = handle_veterinary_list({"category": "ALL", "limit": 10})
        data_l = json.loads(res_l)
        assert "quarantine" in data_l

        res_st = handle_veterinary_status({})
        data_st = json.loads(res_st)
        assert "total_quarantine_certs" in data_st

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        res_q = server._handle_veterinary_quarantine(
            animal_species="GÀ ĐẺ",
            quantity_head=5000,
            origin_province="Hải Dương",
            destination_province="Hà Nội",
            safe_zone=True,
            tested_negative=True,
            disinfected=True,
            lead_sealed=True,
        )
        data_q = json.loads(res_q)
        assert data_q["status"] == "CERTIFIED"

        res_o = server._handle_veterinary_outbreak(
            disease_name="RABIES",
            species="CHÓ",
            location_province="Bến Tre",
            culled_count=5,
            radius_km=3.0,
            ring_vaccination=True,
            quarantine_post_active=True,
        )
        data_o = json.loads(res_o)
        assert data_o["status"] == "CONTAINMENT_ACTIVE"

        res_s = server._handle_veterinary_slaughter(
            abattoir_name="Lò Mổ Yên Thường",
            species="LỢN",
            batch_size=180,
            antemortem_healthy=True,
            postmortem_passed=True,
            water_injected=False,
        )
        data_s = json.loads(res_s)
        assert data_s["status"] == "PASSED_STAMPED"

        res_m = server._handle_veterinary_medicine(
            facility_name="Cơ Sở Thuốc Thú Y Minh Phát",
            license_type="TRADING",
            chief_vet_licensed=True,
            gmp_certified=False,
            has_prohibited_substances=False,
        )
        data_m = json.loads(res_m)
        assert data_m["status"] == "CERTIFIED"

        res_l = server._handle_veterinary_list(category="ALL", limit=10)
        data_l = json.loads(res_l)
        assert "quarantine" in data_l

        res_st = server._handle_veterinary_status()
        data_st = json.loads(res_st)
        assert "total_quarantine_certs" in data_st
