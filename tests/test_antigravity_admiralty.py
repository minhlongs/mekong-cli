"""
Comprehensive Unit & Integration Test Suite for Vietnamese Maritime Court, Admiralty Jurisdiction, Vessel Arrest & Maritime Liens Suite.
Statutory Framework:
- Bộ luật Hàng hải Việt Nam 2015 (Luật số 95/2015/QH13)
- Pháp lệnh Thủ tục bắt giữ tàu biển 2008 (Pháp lệnh số 05/2008/PL-UBTVQH12)
- Quy tắc York-Antwerp 2016 (YAR 2016)
- Quy tắc quốc tế phòng ngừa đâm va tàu thuyền trên biển (COLREGS 1972)
"""

import json
import datetime
import pytest
from typer.testing import CliRunner

from src.core.admiralty_engine import AdmiraltyEngine
from src.cli.commands.admiralty_command import admiralty_app
import scripts.mcp_server as mcp_script
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path):
    db_file = str(tmp_path / "test_admiralty.db")
    return AdmiraltyEngine(db_path=db_file)


class TestAdmiraltyEngine:
    def test_register_vessel_valid(self, temp_engine):
        res = temp_engine.register_vessel(
            imo_number="IMO9345678",
            vessel_name="Mekong Mariner",
            flag_state="VIETNAM",
            gross_tonnage=15800.0,
            deadweight_dwt=24000.0,
            vessel_type="CONTAINER",
            registered_owner="Tổng công ty Hàng hải Việt Nam (VIMC)",
        )
        assert res["is_valid"] is True
        assert res["status"] == "VESSEL_REGISTERED"
        assert res["imo_number"] == "IMO9345678"
        assert res["vessel_id"].startswith("VES-")
        assert len(res["violations"]) == 0

    def test_register_vessel_invalid_imo(self, temp_engine):
        # IMO must have exactly 7 digits
        res = temp_engine.register_vessel(
            imo_number="IMO12345",  # Only 5 digits
            vessel_name="Short IMO Vessel",
        )
        assert res["is_valid"] is False
        assert res["status"] == "REGISTRATION_DEFICIENT"
        assert any("đúng 7 chữ số" in v for v in res["violations"])

    def test_register_vessel_invalid_tonnage(self, temp_engine):
        res = temp_engine.register_vessel(
            imo_number="9876543",
            vessel_name="Negative Tonnage Vessel",
            gross_tonnage=-500.0,
            deadweight_dwt=0.0,
        )
        assert res["is_valid"] is False
        assert any("phải lớn hơn 0" in v for v in res["violations"])

    def test_register_vessel_invalid_type(self, temp_engine):
        res = temp_engine.register_vessel(
            imo_number="9876543",
            vessel_name="Submarine 01",
            vessel_type="MILITARY_SUBMARINE",
        )
        assert res["is_valid"] is False
        assert any("Loại tàu biển không hợp lệ" in v for v in res["violations"])

    def test_petition_vessel_arrest_sufficient_counter_security(self, temp_engine):
        temp_engine.register_vessel(
            imo_number="IMO9456789",
            vessel_name="VIMC Glory",
        )
        # 30,000 / 150,000 = 20.0% >= 15.0%
        res = temp_engine.petition_vessel_arrest(
            vessel_imo="IMO9456789",
            applicant_name="Công ty Hoa tiêu Khu vực I",
            claim_type="PORT_NAVIGATION_DUES",
            claim_amount_usd=150000.0,
            counter_security_usd=30000.0,
            court_name="Tòa án nhân dân Thành phố Hải Phòng",
            port_location="Cảng Lạch Huyện",
        )
        assert res["is_warrant_granted"] is True
        assert res["is_counter_security_sufficient"] is True
        assert res["status"] == "ARREST_WARRANT_ISSUED"
        assert res["arrest_id"].startswith("ARR-")
        assert res["counter_security_ratio_pct"] == 20.0
        assert res["vessel_name"] == "VIMC Glory"

    def test_petition_vessel_arrest_insufficient_counter_security(self, temp_engine):
        # 10,000 / 200,000 = 5.0% < 15.0% (Under Ordinance 05/2008 Art 14)
        res = temp_engine.petition_vessel_arrest(
            vessel_imo="IMO9111222",
            applicant_name="Công ty Nhiên liệu Biển",
            claim_type="CREW_WAGES",
            claim_amount_usd=200000.0,
            counter_security_usd=10000.0,
        )
        assert res["is_warrant_granted"] is False
        assert res["is_counter_security_sufficient"] is False
        assert res["status"] == "ARREST_PETITION_REJECTED"
        assert any("tối thiểu 15%" in v for v in res["violations"])

    def test_petition_vessel_arrest_invalid_claim_type(self, temp_engine):
        res = temp_engine.petition_vessel_arrest(
            vessel_imo="IMO9111222",
            applicant_name="Khách sạn ven biển",
            claim_type="HOTEL_ROOM_BILL",
            claim_amount_usd=5000.0,
            counter_security_usd=1000.0,
        )
        assert res["is_warrant_granted"] is False
        assert any("Loại khiếu nại hàng hải không thuộc thẩm quyền" in v for v in res["violations"])

    def test_petition_vessel_arrest_zero_claim_amount(self, temp_engine):
        res = temp_engine.petition_vessel_arrest(
            vessel_imo="IMO9111222",
            applicant_name="Thuyền viên X",
            claim_type="CREW_WAGES",
            claim_amount_usd=0.0,
            counter_security_usd=0.0,
        )
        assert res["is_warrant_granted"] is False
        assert any("phải lớn hơn 0 USD" in v for v in res["violations"])

    def test_evaluate_maritime_lien_crew_wages_rank_1(self, temp_engine):
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        res = temp_engine.evaluate_maritime_lien(
            vessel_imo="IMO9555666",
            claimant_name="Đại diện Thuyền bộ Vận tải Biển",
            lien_category="CREW_WAGES",
            claim_amount_usd=60000.0,
            incident_date=now_str,
        )
        assert res["is_valid"] is True
        assert res["status"] == "LIEN_ENFORCEABLE_VALID"
        assert res["priority_rank"] == 1
        assert res["is_time_barred"] is False
        assert res["lien_id"].startswith("MLN-")

    def test_evaluate_maritime_lien_salvage_rank_3(self, temp_engine):
        res = temp_engine.evaluate_maritime_lien(
            vessel_imo="IMO9555666",
            claimant_name="Công ty Trục vớt Cứu hộ Hải Vân",
            lien_category="SALVAGE_REWARD",
            claim_amount_usd=120000.0,
        )
        assert res["is_valid"] is True
        assert res["priority_rank"] == 3

    def test_evaluate_maritime_lien_time_barred(self, temp_engine):
        # 450 days ago > 365 days limit under Article 42
        past_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=450)).strftime("%Y-%m-%d")
        res = temp_engine.evaluate_maritime_lien(
            vessel_imo="IMO9555666",
            claimant_name="Chủ hàng phân bón",
            lien_category="COLLISION_DAMAGE",
            claim_amount_usd=80000.0,
            incident_date=past_date,
        )
        assert res["is_valid"] is False
        assert res["is_time_barred"] is True
        assert res["status"] == "LIEN_EXTINGUISHED_OR_INVALID"
        assert any("01 năm (365 ngày)" in v for v in res["violations"])

    def test_evaluate_maritime_lien_invalid_category(self, temp_engine):
        res = temp_engine.evaluate_maritime_lien(
            vessel_imo="IMO9555666",
            claimant_name="Nhà hàng ăn uống",
            lien_category="CATERING_DEBT",
            claim_amount_usd=15000.0,
        )
        assert res["is_valid"] is False
        assert any("không được hưởng quyền cầm giữ hàng hải" in v for v in res["violations"])

    def test_apportion_collision_liability_divided_fault(self, temp_engine):
        # Vessel A 75% fault, damage $200k
        # Vessel B 25% fault, damage $600k
        # Total damages: $800k
        # Liability A: $800k * 0.75 = $600k
        # Liability B: $800k * 0.25 = $200k
        # Vessel A suffered $200k, owes $600k -> Net payment: Vessel A pays $400k to Vessel B.
        res = temp_engine.apportion_collision_liability(
            vessel_a_imo="IMO9111111",
            vessel_b_imo="IMO9222222",
            collision_date="2026-07-20",
            colregs_violation="RULE_15_CROSSING_GIVE_WAY_FAILED",
            fault_ratio_a_pct=75.0,
            damage_vessel_a_usd=200000.0,
            damage_vessel_b_usd=600000.0,
        )
        assert res["is_valid"] is True
        assert res["status"] == "COLLISION_SETTLEMENT_ADOPTED"
        assert res["total_damages_usd"] == 800000.0
        assert res["liability_a_usd"] == 600000.0
        assert res["liability_b_usd"] == 200000.0
        assert "IMO9111111" in res["net_settlement_payer"]
        assert res["net_settlement_usd"] == 400000.0

    def test_apportion_collision_liability_balanced(self, temp_engine):
        # 50/50 with equal damages -> 0 net settlement
        res = temp_engine.apportion_collision_liability(
            vessel_a_imo="IMO9111111",
            vessel_b_imo="IMO9222222",
            collision_date="2026-08-01",
            fault_ratio_a_pct=50.0,
            damage_vessel_a_usd=300000.0,
            damage_vessel_b_usd=300000.0,
        )
        assert res["net_settlement_payer"] == "NONE_BALANCED"
        assert res["net_settlement_usd"] == 0.0

    def test_apportion_collision_liability_invalid_fault_ratio(self, temp_engine):
        res = temp_engine.apportion_collision_liability(
            vessel_a_imo="IMO9111111",
            vessel_b_imo="IMO9222222",
            collision_date="2026-08-01",
            fault_ratio_a_pct=120.0,  # > 100%
            damage_vessel_a_usd=100000.0,
            damage_vessel_b_usd=100000.0,
        )
        assert res["is_valid"] is False
        assert any("từ 0.0% đến 100.0%" in v for v in res["violations"])

    def test_adjust_general_average_valid(self, temp_engine):
        # GA Sacrifice: $300k, GA Expenditure: $200k -> Total GA: $500k
        # Vessel Value: $10,000,000, Cargo: $12,000,000, Freight: $3,000,000 -> Total Contributory: $25,000,000
        # GA Rate: $500,000 / $25,000,000 = 2.0%
        # Vessel Contribution: $10,000,000 * 2% = $200,000
        # Cargo Contribution: $12,000,000 * 2% = $240,000
        # Freight Contribution: $3,000,000 * 2% = $60,000
        res = temp_engine.adjust_general_average(
            vessel_imo="IMO9333444",
            incident_date="2026-06-15",
            ga_sacrifice_usd=300000.0,
            ga_expenditure_usd=200000.0,
            vessel_value_usd=10000000.0,
            cargo_value_usd=12000000.0,
            freight_value_usd=3000000.0,
        )
        assert res["is_valid"] is True
        assert res["status"] == "GENERAL_AVERAGE_ADJUSTED"
        assert res["ga_id"].startswith("GAV-")
        assert res["total_ga_loss_usd"] == 500000.0
        assert res["total_contributory_value_usd"] == 25000000.0
        assert res["ga_contribution_rate_pct"] == 2.0
        assert res["vessel_contribution_usd"] == 200000.0
        assert res["cargo_contribution_usd"] == 240000.0
        assert res["freight_contribution_usd"] == 60000.0

    def test_adjust_general_average_zero_loss(self, temp_engine):
        res = temp_engine.adjust_general_average(
            vessel_imo="IMO9333444",
            incident_date="2026-06-15",
            ga_sacrifice_usd=0.0,
            ga_expenditure_usd=0.0,
            vessel_value_usd=10000000.0,
            cargo_value_usd=10000000.0,
            freight_value_usd=1000000.0,
        )
        assert res["is_valid"] is False
        assert any("phải lớn hơn 0 USD" in v for v in res["violations"])

    def test_list_admiralty_records_all_and_filtered(self, temp_engine):
        temp_engine.register_vessel(imo_number="IMO9123456", vessel_name="Tàu Nam Triệu")
        temp_engine.petition_vessel_arrest(
            vessel_imo="IMO9123456",
            applicant_name="Chủ nợ Biển Đông",
            claim_type="CREW_WAGES",
            claim_amount_usd=100000.0,
            counter_security_usd=20000.0,
        )
        all_records = temp_engine.list_admiralty_records(category="ALL")
        assert "vessels" in all_records
        assert "vessel_arrests" in all_records
        assert len(all_records["vessels"]) >= 1

        vessels_only = temp_engine.list_admiralty_records(category="VESSELS")
        assert "vessels" in vessels_only
        assert "vessel_arrests" not in vessels_only

    def test_get_admiralty_telemetry(self, temp_engine):
        temp_engine.register_vessel(imo_number="IMO9888999", vessel_name="Tàu Sài Gòn")
        telemetry = temp_engine.get_admiralty_telemetry()
        assert telemetry["total_vessels"] >= 1
        assert "statutory_min_counter_security_pct" in telemetry
        assert telemetry["statutory_min_counter_security_pct"] == 15.0
        assert "compliance_framework" in telemetry


class TestAdmiraltyCli:
    def test_cli_vessel(self):
        res = runner.invoke(admiralty_app, [
            "vessel",
            "IMO9654321",
            "Mekong Pioneer",
            "--flag", "VIETNAM",
            "--gt", "16000",
            "--dwt", "25000",
            "--type", "CONTAINER",
        ])
        assert res.exit_code == 0
        assert "Hồ Sơ Đăng Ký Tàu Biển Quốc Gia" in res.stdout

    def test_cli_vessel_json(self):
        res = runner.invoke(admiralty_app, [
            "vessel",
            "IMO9765432",
            "VIMC Fortune",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_valid"] is True
        assert data["imo_number"] == "IMO9765432"

    def test_cli_arrest(self):
        res = runner.invoke(admiralty_app, [
            "arrest",
            "IMO9654321",
            "Công ty Nhiên liệu Cảng Hải Phòng",
            "--claim-type", "PORT_NAVIGATION_DUES",
            "--amount", "100000",
            "--counter-security", "20000",
            "--court", "TAND TP Hải Phòng",
        ])
        assert res.exit_code == 0
        assert "Thẩm Tra Đơn Bắt Giữ Tàu Biển" in res.stdout

    def test_cli_arrest_json(self):
        res = runner.invoke(admiralty_app, [
            "arrest",
            "IMO9654321",
            "Đại diện Thuyền viên",
            "--claim-type", "CREW_WAGES",
            "--amount", "80000",
            "--counter-security", "16000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_warrant_granted"] is True
        assert data["status"] == "ARREST_WARRANT_ISSUED"

    def test_cli_lien(self):
        res = runner.invoke(admiralty_app, [
            "lien",
            "IMO9654321",
            "Thuyền bộ Tàu Mekong Pioneer",
            "--category", "CREW_WAGES",
            "--amount", "50000",
        ])
        assert res.exit_code == 0
        assert "Thẩm Định Quyền Cầm Giữ Hàng Hải" in res.stdout

    def test_cli_lien_json(self):
        res = runner.invoke(admiralty_app, [
            "lien",
            "IMO9654321",
            "Công ty Cứu hộ Đại Dương",
            "--category", "SALVAGE_REWARD",
            "--amount", "90000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_valid"] is True
        assert data["priority_rank"] == 3

    def test_cli_collision(self):
        res = runner.invoke(admiralty_app, [
            "collision",
            "IMO9654321",
            "IMO9111222",
            "2026-07-15",
            "--fault-a", "70",
            "--damage-a", "200000",
            "--damage-b", "500000",
        ])
        assert res.exit_code == 0
        assert "Phân Định Trách Nhiệm Đâm Va Tàu Thuyền" in res.stdout

    def test_cli_collision_json(self):
        res = runner.invoke(admiralty_app, [
            "collision",
            "IMO9654321",
            "IMO9111222",
            "2026-07-15",
            "--fault-a", "60",
            "--damage-a", "300000",
            "--damage-b", "400000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_valid"] is True
        assert data["total_damages_usd"] == 700000.0

    def test_cli_ga(self):
        res = runner.invoke(admiralty_app, [
            "ga",
            "IMO9654321",
            "2026-08-10",
            "--sacrifice", "400000",
            "--expenditure", "200000",
            "--vessel-val", "15000000",
            "--cargo-val", "20000000",
            "--freight-val", "2500000",
        ])
        assert res.exit_code == 0
        assert "Bản Tính Phân Bổ Tổn Thất Chung" in res.stdout

    def test_cli_ga_json(self):
        res = runner.invoke(admiralty_app, [
            "ga",
            "IMO9654321",
            "2026-08-10",
            "--sacrifice", "300000",
            "--expenditure", "150000",
            "--vessel-val", "12000000",
            "--cargo-val", "16000000",
            "--freight-val", "2000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert data["is_valid"] is True
        assert data["total_ga_loss_usd"] == 450000.0

    def test_cli_list(self):
        res = runner.invoke(admiralty_app, ["list", "--category", "ALL", "--limit", "10"])
        assert res.exit_code == 0
        assert "Danh mục" in res.stdout

    def test_cli_list_json(self):
        res = runner.invoke(admiralty_app, ["list", "--category", "VESSELS", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert "vessels" in data

    def test_cli_status(self):
        res = runner.invoke(admiralty_app, ["status"])
        assert res.exit_code == 0
        assert "Chỉ Số Telemetry Tư Pháp Hàng Hải Quốc Gia" in res.stdout

    def test_cli_status_json(self):
        res = runner.invoke(admiralty_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.stdout)
        assert "total_vessels" in data
        assert data["statutory_min_counter_security_pct"] == 15.0


class TestAdmiraltyMcp:
    def test_scripts_mcp_vessel(self):
        raw = mcp_script.handle_admiralty_vessel({
            "imo_number": "IMO9876543",
            "vessel_name": "Tàu Vận tải Cát Lái",
            "gross_tonnage": 18500.0,
            "deadweight_dwt": 28000.0,
        })
        res = json.loads(raw)
        assert res["is_valid"] is True
        assert res["vessel_id"].startswith("VES-")

    def test_scripts_mcp_arrest(self):
        raw = mcp_script.handle_admiralty_arrest({
            "vessel_imo": "IMO9876543",
            "applicant_name": "Công ty Dịch vụ Hàng hải Tân Cảng",
            "claim_type": "PORT_NAVIGATION_DUES",
            "claim_amount_usd": 160000.0,
            "counter_security_usd": 32000.0,
        })
        res = json.loads(raw)
        assert res["is_warrant_granted"] is True

    def test_scripts_mcp_lien(self):
        raw = mcp_script.handle_admiralty_lien({
            "vessel_imo": "IMO9876543",
            "claimant_name": "Thuyền bộ Tàu Cát Lái",
            "lien_category": "CREW_WAGES",
            "claim_amount_usd": 55000.0,
        })
        res = json.loads(raw)
        assert res["is_valid"] is True
        assert res["priority_rank"] == 1

    def test_scripts_mcp_collision(self):
        raw = mcp_script.handle_admiralty_collision({
            "vessel_a_imo": "IMO9876543",
            "vessel_b_imo": "IMO9123123",
            "collision_date": "2026-08-20",
            "fault_ratio_a_pct": 80.0,
            "damage_vessel_a_usd": 150000.0,
            "damage_vessel_b_usd": 450000.0,
        })
        res = json.loads(raw)
        assert res["is_valid"] is True
        assert res["total_damages_usd"] == 600000.0

    def test_scripts_mcp_ga(self):
        raw = mcp_script.handle_admiralty_ga({
            "vessel_imo": "IMO9876543",
            "incident_date": "2026-09-01",
            "ga_sacrifice_usd": 250000.0,
            "ga_expenditure_usd": 100000.0,
            "vessel_value_usd": 10000000.0,
            "cargo_value_usd": 15000000.0,
            "freight_value_usd": 2000000.0,
        })
        res = json.loads(raw)
        assert res["is_valid"] is True

    def test_scripts_mcp_list(self):
        raw = mcp_script.handle_admiralty_list({"category": "ALL", "limit": 10})
        res = json.loads(raw)
        assert "vessels" in res

    def test_scripts_mcp_status(self):
        raw = mcp_script.handle_admiralty_status({})
        res = json.loads(raw)
        assert "total_vessels" in res

    def test_core_mcp_server_handlers(self):
        server = MekongMcpServer()
        v_raw = server._handle_admiralty_vessel(
            imo_number="IMO9543210",
            vessel_name="Tàu Sao Mai",
            gross_tonnage=14000.0,
            deadweight_dwt=20000.0,
        )
        v_res = json.loads(v_raw)
        assert v_res["is_valid"] is True

        a_raw = server._handle_admiralty_arrest(
            vessel_imo="IMO9543210",
            applicant_name="Chủ tàu A",
            claim_type="COLLISION_DAMAGE",
            claim_amount_usd=200000.0,
            counter_security_usd=40000.0,
        )
        a_res = json.loads(a_raw)
        assert a_res["is_warrant_granted"] is True

        l_raw = server._handle_admiralty_lien(
            vessel_imo="IMO9543210",
            claimant_name="Thuyền viên B",
            lien_category="CREW_WAGES",
            claim_amount_usd=30000.0,
        )
        l_res = json.loads(l_raw)
        assert l_res["is_valid"] is True

        c_raw = server._handle_admiralty_collision(
            vessel_a_imo="IMO9543210",
            vessel_b_imo="IMO9321456",
            collision_date="2026-09-10",
            fault_ratio_a_pct=65.0,
            damage_vessel_a_usd=200000.0,
            damage_vessel_b_usd=500000.0,
        )
        c_res = json.loads(c_raw)
        assert c_res["is_valid"] is True

        g_raw = server._handle_admiralty_ga(
            vessel_imo="IMO9543210",
            incident_date="2026-09-15",
            ga_sacrifice_usd=200000.0,
            ga_expenditure_usd=100000.0,
            vessel_value_usd=8000000.0,
            cargo_value_usd=12000000.0,
            freight_value_usd=1500000.0,
        )
        g_res = json.loads(g_raw)
        assert g_res["is_valid"] is True

        lst_raw = server._handle_admiralty_list(category="ALL", limit=5)
        lst_res = json.loads(lst_raw)
        assert "vessels" in lst_res

        stat_raw = server._handle_admiralty_status()
        stat_res = json.loads(stat_raw)
        assert "total_vessels" in stat_res
