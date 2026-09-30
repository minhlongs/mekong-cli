"""
Comprehensive Unit & Integration Test Suite for Vietnamese Bailiff & Vi Bằng Evidence Suite.
Statutory Framework:
- Nghị định số 08/2020/NĐ-CP của Chính phủ về tổ chức và hoạt động của Thừa phát lại
- Thông tư số 05/2020/TT-BTP của Bộ Tư pháp
- Bộ luật Tố tụng dân sự 2015 (Điều 95)
- Luật Thi hành án dân sự 2008 (sửa đổi, bổ sung 2014)
"""

import json
import pytest
from typer.testing import CliRunner

from src.core.bailiff_engine import BailiffEngine
from src.cli.commands.bailiff_command import bailiff_app
import scripts.mcp_server as mcp_script
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path):
    db_file = str(tmp_path / "test_bailiff.db")
    return BailiffEngine(db_path=db_file)


class TestBailiffEngine:
    def test_create_valid_evidence_protocol(self, temp_engine):
        res = temp_engine.create_evidence_protocol(
            requester_name="Bà Trần Thị Lan",
            event_description="Ghi nhận hiện trạng nứt tường nhà số 15 do công trình liền kề đang thi công ép cọc móng",
            event_category="PROPERTY_STATUS",
            location="Số 15 Phố Tràng Tiền, Quận Hoàn Kiếm, Hà Nội",
            media_attachments_count=12,
            bailiff_name="Thừa phát lại Nguyễn Đức Toàn",
            office_name="Văn phòng Thừa phát lại Ba Đình",
            doj_registered=True,
            registration_days_elapsed=2,
        )
        assert res["is_valid"] is True
        assert res["status"] == "PROTOCOL_REGISTERED"
        assert res["protocol_id"].startswith("BLF-VB-")
        assert res["media_attachments_count"] == 12
        assert len(res["violations"]) == 0
        assert "giá trị chứng cứ" in res["statutory_notes"]

    def test_create_protocol_prohibited_land_without_title(self, temp_engine):
        res = temp_engine.create_evidence_protocol(
            requester_name="Ông Lê Văn B",
            event_description="Ghi nhận mua bán nhà đất không có sổ đỏ và giấy tờ hợp lệ giữa hai bên",
            event_category="PROPERTY_STATUS",
        )
        assert res["is_valid"] is False
        assert res["status"] == "REJECTED_PROHIBITED_SCOPE"
        assert any("mua bán nhà đất không có sổ đỏ" in v for v in res["violations"])

    def test_create_protocol_prohibited_state_secrets(self, temp_engine):
        res = temp_engine.create_evidence_protocol(
            requester_name="Người ẩn danh",
            event_description="Ghi nhận tài liệu thuộc diện bí mật nhà nước trong cơ quan hành chính",
            event_category="PROPERTY_STATUS",
        )
        assert res["is_valid"] is False
        assert res["status"] == "REJECTED_PROHIBITED_SCOPE"
        assert any("bí mật nhà nước" in v for v in res["violations"])

    def test_create_protocol_doj_unregistered(self, temp_engine):
        res = temp_engine.create_evidence_protocol(
            requester_name="Công ty Hoàng Hà",
            event_description="Ghi nhận giao nhận tài sản máy tính văn phòng",
            event_category="TRANSACTION_DELIVERY",
            doj_registered=False,
        )
        assert res["is_valid"] is False
        assert any("chưa được gửi đăng ký tại Sở Tư pháp" in v for v in res["violations"])

    def test_create_protocol_registration_overdue(self, temp_engine):
        res = temp_engine.create_evidence_protocol(
            requester_name="Công ty CP Công Nghệ",
            event_description="Ghi nhận hành vi xâm phạm quyền tác giả trên internet",
            event_category="INTERNET_IP_INFRINGEMENT",
            doj_registered=True,
            registration_days_elapsed=5,
        )
        assert res["is_valid"] is False
        assert any("Quá thời hạn gửi đăng ký Sở Tư pháp" in v for v in res["violations"])

    def test_serve_process_direct_delivery(self, temp_engine):
        res = temp_engine.serve_process_document(
            recipient_name="Ông Hoàng Văn Nam",
            document_title="Thông báo thụ lý vụ án số 88/TB-TLVA",
            court_or_agency="TAND Quận Cầu Giấy, Hà Nội",
            service_method="DIRECT_DELIVERY",
            recipient_present=True,
        )
        assert res["status"] == "SERVED_SUCCESSFULLY"
        assert res["service_id"].startswith("BLF-SRV-")
        assert "ký nhận biên bản tống đạt" in res["statutory_notes"]

    def test_serve_process_postal_affixed(self, temp_engine):
        res = temp_engine.serve_process_document(
            recipient_name="Bà Nguyễn Thị Mai",
            document_title="Giấy triệu tập đương sự số 12/GTT",
            service_method="POSTAL_AFFIXED",
            recipient_present=False,
        )
        assert res["status"] == "SERVED_BY_POSTING"
        assert "niêm yết công khai" in res["statutory_notes"]

    def test_serve_process_authority_assistance(self, temp_engine):
        res = temp_engine.serve_process_document(
            recipient_name="Ông Vũ Tiến Đạt",
            document_title="Bản án sơ thẩm số 23/2026/DS-ST",
            service_method="AUTHORITY_ASSISTANCE",
            recipient_present=False,
        )
        assert res["status"] == "SERVED_VIA_AUTHORITY"
        assert "tổ dân phố" in res["statutory_notes"]

    def test_serve_process_failed_absent(self, temp_engine):
        res = temp_engine.serve_process_document(
            recipient_name="Ông Lưu Văn C",
            document_title="Giấy triệu tập số 01/GTT",
            service_method="DIRECT_DELIVERY",
            recipient_present=False,
        )
        assert res["status"] == "FAILED_ABSENT"

    def test_verify_asset_conditions_enforceable(self, temp_engine):
        res = temp_engine.verify_asset_conditions(
            debtor_name="Công ty TNHH Vận Tải An Bình",
            judgment_number="Bản án số 45/2025/KDTM-ST",
            bank_accounts_found=2,
            total_bank_balance_vnd=500000000.0,
            real_estate_found=1,
            vehicles_found=3,
        )
        assert res["is_enforceable"] is True
        assert res["status"] == "CONDITIONS_CONFIRMED"
        assert res["verification_id"].startswith("BLF-VER-")

    def test_verify_asset_conditions_insolvent(self, temp_engine):
        res = temp_engine.verify_asset_conditions(
            debtor_name="Ông Phạm Văn Nghèo",
            judgment_number="Bản án số 02/2026/DS-ST",
            bank_accounts_found=0,
            total_bank_balance_vnd=0.0,
            real_estate_found=0,
            vehicles_found=0,
        )
        assert res["is_enforceable"] is False
        assert res["status"] == "INSOLVENT_NO_ASSETS"

    def test_execute_civil_judgment_fully_satisfied(self, temp_engine):
        res = temp_engine.execute_civil_judgment(
            debtor_name="Công ty Hưng Thịnh",
            judgment_amount_vnd=200000000.0,
            amount_collected_vnd=200000000.0,
        )
        assert res["status"] == "FULLY_SATISFIED"
        assert res["enforcement_id"].startswith("BLF-ENF-")

    def test_execute_civil_judgment_partially_executed(self, temp_engine):
        res = temp_engine.execute_civil_judgment(
            debtor_name="Công ty Hưng Thịnh",
            judgment_amount_vnd=200000000.0,
            amount_collected_vnd=50000000.0,
        )
        assert res["status"] == "PARTIALLY_EXECUTED"

    def test_execute_civil_judgment_voluntary_notice(self, temp_engine):
        res = temp_engine.execute_civil_judgment(
            debtor_name="Ông Đỗ Mạnh Cường",
            judgment_amount_vnd=150000000.0,
            amount_collected_vnd=0.0,
            voluntary_compliance=True,
        )
        assert res["status"] == "VOLUNTARY_NOTICE_ISSUED"

    def test_execute_civil_judgment_coercion_prepared(self, temp_engine):
        res = temp_engine.execute_civil_judgment(
            debtor_name="Ông Đỗ Mạnh Cường",
            judgment_amount_vnd=150000000.0,
            amount_collected_vnd=0.0,
            voluntary_compliance=False,
        )
        assert res["status"] == "COERCION_PREPARED"

    def test_list_bailiff_records_and_telemetry(self, temp_engine):
        temp_engine.create_evidence_protocol("Người A", "Ghi nhận hiện trạng tài sản", "PROPERTY_STATUS")
        temp_engine.serve_process_document("Người B", "Bản án số 1")
        temp_engine.verify_asset_conditions("Người C", total_bank_balance_vnd=100000000.0)
        temp_engine.execute_civil_judgment("Người D", 100000000.0, amount_collected_vnd=100000000.0)

        records = temp_engine.list_bailiff_records("ALL")
        assert len(records["evidence_protocols"]) >= 1
        assert len(records["process_services"]) >= 1
        assert len(records["asset_verifications"]) >= 1
        assert len(records["civil_enforcements"]) >= 1

        telemetry = temp_engine.get_bailiff_telemetry()
        assert telemetry["total_evidence_protocols"] >= 1
        assert telemetry["valid_evidence_protocols"] >= 1
        assert telemetry["total_process_services"] >= 1
        assert telemetry["total_asset_verifications"] >= 1
        assert telemetry["total_civil_enforcements"] >= 1


class TestBailiffCliCommands:
    def test_cli_protocol_json(self):
        result = runner.invoke(bailiff_app, [
            "protocol",
            "Ông Đặng Văn Tân",
            "--desc", "Ghi nhận hiện trạng ranh giới đất và hàng rào phân cách",
            "--category", "PROPERTY_STATUS",
            "--media", "6",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["requester_name"] == "Ông Đặng Văn Tân"
        assert data["is_valid"] is True

    def test_cli_protocol_console(self):
        result = runner.invoke(bailiff_app, [
            "protocol",
            "Bà Hoàng Yến",
            "--desc", "Ghi nhận việc bàn giao căn hộ chung cư tại Times City",
            "--category", "TRANSACTION_DELIVERY",
        ])
        assert result.exit_code == 0
        assert "VI BẰNG" in result.output or "Thừa phát lại" in result.output or "Vi Bằng" in result.output

    def test_cli_serve_json(self):
        result = runner.invoke(bailiff_app, [
            "serve",
            "Công ty CP Bất Động Sản Á Châu",
            "--doc", "Quyết định cưỡng chế thi hành án số 05/QĐ-CCTHA",
            "--method", "DIRECT_DELIVERY",
            "--fee", "200000",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["recipient_name"] == "Công ty CP Bất Động Sản Á Châu"
        assert data["status"] == "SERVED_SUCCESSFULLY"

    def test_cli_verify_json(self):
        result = runner.invoke(bailiff_app, [
            "verify",
            "Công ty TNHH Cơ Khí Hải Phòng",
            "--judgment", "Bản án số 19/2025/KDTM-ST",
            "--balance", "1200000000",
            "--real-estate", "2",
            "--vehicles", "4",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["debtor_name"] == "Công ty TNHH Cơ Khí Hải Phòng"
        assert data["is_enforceable"] is True

    def test_cli_enforce_json(self):
        result = runner.invoke(bailiff_app, [
            "enforce",
            "Ông Vũ Đình Quân",
            "--amount", "500000000",
            "--collected", "250000000",
            "--json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["debtor_name"] == "Ông Vũ Đình Quân"
        assert data["status"] == "PARTIALLY_EXECUTED"

    def test_cli_list_json(self):
        result = runner.invoke(bailiff_app, ["list", "--category", "ALL", "--limit", "10", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "evidence_protocols" in data

    def test_cli_status_json(self):
        result = runner.invoke(bailiff_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_evidence_protocols" in data


class TestBailiffMcpParity:
    def test_scripts_mcp_bailiff_handlers(self):
        # 1. Protocol
        p_raw = mcp_script.handle_bailiff_protocol({
            "requester_name": "Công ty Đại Phát",
            "event_description": "Ghi nhận vi phạm hợp đồng xây dựng",
            "event_category": "COMMERCIAL_DEFAULT",
        })
        p_res = json.loads(p_raw)
        assert p_res["is_valid"] is True
        assert p_res["status"] == "PROTOCOL_REGISTERED"

        # 2. Serve
        s_raw = mcp_script.handle_bailiff_serve({
            "recipient_name": "Ông Lê Văn Thành",
            "document_title": "Thông báo hòa giải số 10/TB-HG",
        })
        s_res = json.loads(s_raw)
        assert s_res["status"] == "SERVED_SUCCESSFULLY"

        # 3. Verify
        v_raw = mcp_script.handle_bailiff_verify({
            "debtor_name": "Bà Nguyễn Thu Trang",
            "total_bank_balance_vnd": 250000000.0,
        })
        v_res = json.loads(v_raw)
        assert v_res["is_enforceable"] is True

        # 4. Enforce
        e_raw = mcp_script.handle_bailiff_enforce({
            "debtor_name": "Bà Nguyễn Thu Trang",
            "judgment_amount_vnd": 250000000.0,
            "amount_collected_vnd": 250000000.0,
        })
        e_res = json.loads(e_raw)
        assert e_res["status"] == "FULLY_SATISFIED"

        # 5. List
        l_raw = mcp_script.handle_bailiff_list({"category": "ALL", "limit": 10})
        l_res = json.loads(l_raw)
        assert "evidence_protocols" in l_res

        # 6. Status
        st_raw = mcp_script.handle_bailiff_status({})
        st_res = json.loads(st_raw)
        assert "total_evidence_protocols" in st_res

    def test_core_mcp_bailiff_handlers(self):
        server = MekongMcpServer()
        # 1. Protocol
        p_raw = server._handle_bailiff_protocol(
            requester_name="Ngân hàng TMCP Quốc tế",
            event_description="Ghi nhận hiện trạng nhà xưởng thế chấp",
            event_category="PROPERTY_STATUS",
        )
        p_res = json.loads(p_raw)
        assert p_res["is_valid"] is True

        # 2. Serve
        s_raw = server._handle_bailiff_serve(
            recipient_name="Công ty TNHH May Mặc",
            document_title="Quyết định thi hành án số 02/QĐ",
        )
        s_res = json.loads(s_raw)
        assert s_res["status"] == "SERVED_SUCCESSFULLY"

        # 3. Verify
        v_raw = server._handle_bailiff_verify(
            debtor_name="Công ty TNHH May Mặc",
            total_bank_balance_vnd=150000000.0,
        )
        v_res = json.loads(v_raw)
        assert v_res["is_enforceable"] is True

        # 4. Enforce
        e_raw = server._handle_bailiff_enforce(
            debtor_name="Công ty TNHH May Mặc",
            judgment_amount_vnd=150000000.0,
            amount_collected_vnd=150000000.0,
        )
        e_res = json.loads(e_raw)
        assert e_res["status"] == "FULLY_SATISFIED"

        # 5. List
        l_raw = server._handle_bailiff_list(category="ALL", limit=5)
        l_res = json.loads(l_raw)
        assert "evidence_protocols" in l_res

        # 6. Status
        st_raw = server._handle_bailiff_status()
        st_res = json.loads(st_raw)
        assert "total_evidence_protocols" in st_res
