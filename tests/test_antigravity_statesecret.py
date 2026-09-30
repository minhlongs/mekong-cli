"""
Unit and integration tests for Vietnamese State Secrets & Classified Intelligence Protection Suite.
Governed by:
- Law on Protection of State Secrets 2018 (Law No. 35/2018/QH14)
- Decree No. 26/2020/NĐ-CP (Guiding the Implementation of Law on Protection of State Secrets)
- Circular No. 24/2020/TT-BCA (Forms, Stamps, and Registers in State Secret Protection)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.statesecret_command import app as statesecret_app
from src.core.statesecret_engine import (
    VALID_CARRIER_TYPES,
    VALID_CLASSIFICATION_LEVELS,
    VALID_DECLASSIFICATION_TYPES,
    VALID_DESTRUCTION_METHODS,
    VALID_INCIDENT_TYPES,
    VALID_OPERATION_TYPES,
    VALID_SEVERITY_LEVELS,
    StateSecretEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_STATETSECRET_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestStateSecretEngine:
    def test_register_classified_item_valid(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        res = engine.register_classified_item(
            item_id="SEC-2026-001",
            item_title="Kế hoạch Chiến lược Quốc phòng Vùng biển Đảo",
            classification_level="TUYET_MAT",
            originating_agency="Bộ Quốc phòng",
            approving_authority="Bộ trưởng Bộ Quốc phòng",
            carrier_type="DOCUMENT_PAPER",
            registered_date="2026-01-10",
            recipient_scope=["Bộ Tổng Tham mưu", "Quân chủng Hải quân"],
            stamp_code="DAU-TM-BQP-01",
        )
        assert res["item_id"] == "SEC-2026-001"
        assert res["classification_level"] == "TUYET_MAT"
        assert res["protection_years"] == 30
        assert res["status"] == "ACTIVE"
        assert "2056" in res["expiry_date"]

    def test_register_classified_item_duplicate(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-DUP",
            item_title="Văn bản Trùng",
            classification_level="MAT",
            originating_agency="Bộ Công an",
            approving_authority="Thủ trưởng Cơ quan",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_classified_item(
                item_id="SEC-DUP",
                item_title="Văn bản Trùng",
                classification_level="MAT",
                originating_agency="Bộ Công an",
                approving_authority="Thủ trưởng Cơ quan",
            )

    def test_register_classified_item_invalid_inputs(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_classified_item(
                item_id="",
                item_title="Tiêu đề",
                classification_level="MAT",
                originating_agency="Bộ",
                approving_authority="Thủ trưởng",
            )

        with pytest.raises(ValueError, match="Invalid classification_level"):
            engine.register_classified_item(
                item_id="SEC-INV-LVL",
                item_title="Tiêu đề",
                classification_level="ULTRA_SECRET",
                originating_agency="Bộ",
                approving_authority="Thủ trưởng",
            )

        with pytest.raises(ValueError, match="Invalid carrier_type"):
            engine.register_classified_item(
                item_id="SEC-INV-CARR",
                item_title="Tiêu đề",
                classification_level="MAT",
                originating_agency="Bộ",
                approving_authority="Thủ trưởng",
                carrier_type="FLOPPY_DISK",
            )

    def test_authorize_access_valid(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-AUTH-01",
            item_title="Phương án An ninh Hội nghị Quốc tế APEC",
            classification_level="TOI_MAT",
            originating_agency="Bộ Công an",
            approving_authority="Thứ trưởng Bộ Công an",
        )
        auth = engine.authorize_access(
            auth_id="AUTH-2026-001",
            item_id="SEC-AUTH-01",
            authorized_person="Đại tá Trần Quốc Tuấn - Trưởng phòng PA01",
            authorizing_official="Trung tướng Cục trưởng Cục An ninh đối ngoại",
            operation_type="COPY_DUPLICATE",
            purpose="Sao y bản chính phục vụ phương án dẫn đoàn nguyên thủ quốc gia",
            copy_count=3,
        )
        assert auth["auth_id"] == "AUTH-2026-001"
        assert auth["operation_type"] == "COPY_DUPLICATE"
        assert auth["copy_count"] == 3
        assert auth["status"] == "GRANTED"

    def test_authorize_access_nonexistent_item(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="not found"):
            engine.authorize_access(
                auth_id="AUTH-MISSING",
                item_id="SEC-NONEXISTENT",
                authorized_person="Cán bộ",
                authorizing_official="Lãnh đạo",
                operation_type="READ_ACCESS",
                purpose="Nghiên cứu",
            )

    def test_authorize_access_duplicate(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-AUTH-DUP",
            item_title="Tài liệu mẫu",
            classification_level="MAT",
            originating_agency="Bộ Tư pháp",
            approving_authority="Bộ trưởng",
        )
        engine.authorize_access(
            auth_id="AUTH-DUP",
            item_id="SEC-AUTH-DUP",
            authorized_person="Nguyễn Văn A",
            authorizing_official="Lãnh đạo",
            operation_type="READ_ACCESS",
            purpose="Đọc",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.authorize_access(
                auth_id="AUTH-DUP",
                item_id="SEC-AUTH-DUP",
                authorized_person="Nguyễn Văn A",
                authorizing_official="Lãnh đạo",
                operation_type="READ_ACCESS",
                purpose="Đọc",
            )

    def test_authorize_access_invalid_inputs(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-AUTH-INV",
            item_title="Tài liệu mẫu",
            classification_level="MAT",
            originating_agency="Bộ Tư pháp",
            approving_authority="Bộ trưởng",
        )
        with pytest.raises(ValueError, match="Invalid operation_type"):
            engine.authorize_access(
                auth_id="AUTH-INV-OP",
                item_id="SEC-AUTH-INV",
                authorized_person="Nguyễn Văn A",
                authorizing_official="Lãnh đạo",
                operation_type="PUBLISH_ON_FACEBOOK",
                purpose="Chia sẻ",
            )
        with pytest.raises(ValueError, match="cannot be negative"):
            engine.authorize_access(
                auth_id="AUTH-NEG-COPY",
                item_id="SEC-AUTH-INV",
                authorized_person="Nguyễn Văn A",
                authorizing_official="Lãnh đạo",
                operation_type="COPY_DUPLICATE",
                purpose="Sao",
                copy_count=-2,
            )

    def test_adjust_classification_valid(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-ADJ-01",
            item_title="Hồ sơ Đàm phán Hiệp định Thương mại Bí mật",
            classification_level="TOI_MAT",
            originating_agency="Bộ Công Thương",
            approving_authority="Bộ trưởng Bộ Công Thương",
        )
        # Downgrade grade
        adj_down = engine.adjust_classification(
            declass_id="DECLAS-2026-001",
            item_id="SEC-ADJ-01",
            declass_type="GRADE_DOWNGRADE",
            new_level="MAT",
            decision_number="QĐ 35/QĐ-BCT",
            decision_authority="Bộ trưởng Bộ Công Thương",
            reason_summary="Đàm phán đã ký kết sơ bộ, điều chỉnh độ mật để xin ý kiến ban ngành",
        )
        assert adj_down["declass_type"] == "GRADE_DOWNGRADE"
        assert adj_down["new_level"] == "MAT"

        # Check item reflects new level
        records = engine.list_records(record_type="items")
        item = [i for i in records["items"] if i["item_id"] == "SEC-ADJ-01"][0]
        assert item["classification_level"] == "MAT"
        assert item["status"] == "RECLASSIFIED"

        # Term extension
        adj_ext = engine.adjust_classification(
            declass_id="DECLAS-2026-002",
            item_id="SEC-ADJ-01",
            declass_type="TERM_EXTENSION",
            decision_number="QĐ 99/QĐ-BCT",
            decision_authority="Bộ trưởng Bộ Công Thương",
            reason_summary="Gia hạn thời hạn bảo vệ thêm 5 năm do còn điều khoản bảo mật công nghệ",
            extension_years=5,
        )
        assert adj_ext["declass_type"] == "TERM_EXTENSION"

        records2 = engine.list_records(record_type="items")
        item2 = [i for i in records2["items"] if i["item_id"] == "SEC-ADJ-01"][0]
        assert item2["status"] == "EXTENDED"

    def test_adjust_classification_full_declassify(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-FULL-DEC",
            item_title="Kế hoạch Nghiên cứu đã hết thời hạn",
            classification_level="MAT",
            originating_agency="Viện Hàn lâm KH&CN",
            approving_authority="Viện trưởng",
        )
        adj_full = engine.adjust_classification(
            declass_id="DECLAS-FULL-01",
            item_id="SEC-FULL-DEC",
            declass_type="FULL_DECLASSIFICATION",
            decision_number="QĐ 101/QĐ-VHL",
            decision_authority="Viện trưởng",
            reason_summary="Giải mật toàn phần theo Điều 22 để công bố công khai",
        )
        assert adj_full["declass_type"] == "FULL_DECLASSIFICATION"

        records = engine.list_records(record_type="items")
        item = [i for i in records["items"] if i["item_id"] == "SEC-FULL-DEC"][0]
        assert item["status"] == "DECLASSIFIED"
        assert item["classification_level"] == "UNCLASSIFIED"

    def test_adjust_classification_duplicate_and_errors(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="not found"):
            engine.adjust_classification(
                declass_id="DECLAS-ERR-01",
                item_id="SEC-MISSING",
                declass_type="FULL_DECLASSIFICATION",
                decision_number="QĐ 01",
                decision_authority="Lãnh đạo",
                reason_summary="Lý do",
            )

    def test_execute_destruction_valid_and_status(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-DEST-01",
            item_title="Bản nháp Mật hỏng không sử dụng",
            classification_level="MAT",
            originating_agency="Văn phòng Chính phủ",
            approving_authority="Bộ trưởng, Chủ nhiệm VPCP",
        )
        dest = engine.execute_destruction(
            destruct_id="DEST-2026-001",
            item_id="SEC-DEST-01",
            destruction_council_chair="Chánh Văn phòng VPCP",
            destruction_method="INCINERATION_HIGH_TEMP",
            minutes_reference="BB-TH-01/VPCP",
            destruction_date="2026-03-30",
            witness_list=["Trưởng ban Cơ yếu", "Trưởng phòng Văn thư Lưu trữ"],
        )
        assert dest["destruct_id"] == "DEST-2026-001"
        assert dest["item_status"] == "DESTROYED"
        assert len(dest["witness_list"]) == 2

        # Check item status in db
        records = engine.list_records(record_type="items")
        item = [i for i in records["items"] if i["item_id"] == "SEC-DEST-01"][0]
        assert item["status"] == "DESTROYED"

        # Attempting to authorize access to destroyed item raises error
        with pytest.raises(ValueError, match="Cannot authorize access to item with status 'DESTROYED'"):
            engine.authorize_access(
                auth_id="AUTH-DEST-ERR",
                item_id="SEC-DEST-01",
                authorized_person="Cán bộ",
                authorizing_official="Lãnh đạo",
                operation_type="READ_ACCESS",
                purpose="Đọc tài liệu đã tiêu hủy",
            )

        # Attempting to destroy again raises error
        with pytest.raises(ValueError, match="already destroyed"):
            engine.execute_destruction(
                destruct_id="DEST-2026-002",
                item_id="SEC-DEST-01",
                destruction_council_chair="Chánh Văn phòng",
                destruction_method="INCINERATION_HIGH_TEMP",
                minutes_reference="BB-TH-02",
            )

    def test_report_security_incident_valid_and_critical_compromise(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-INC-01",
            item_title="Bản thiết kế Hệ thống Vũ khí Tên lửa Chiến thuật",
            classification_level="TUYET_MAT",
            originating_agency="Tổng cục Công nghiệp Quốc phòng",
            approving_authority="Chủ nhiệm Tổng cục",
        )
        inc = engine.report_security_incident(
            incident_id="INC-2026-001",
            item_id="SEC-INC-01",
            incident_type="CYBER_INTERCEPTION",
            severity_level="CRITICAL",
            suspect_person="Hacker APT nhóm Shadow Eagle",
            quarantine_measures="Ngắt kết nối mạng toàn bộ phân khu viện nghiên cứu, cô lập máy chủ",
            referral_agency="Cục An ninh chính trị nội bộ (A03) & Cục Điều tra hình sự BQP",
        )
        assert inc["incident_id"] == "INC-2026-001"
        assert inc["severity_level"] == "CRITICAL"
        assert inc["status"] == "INVESTIGATING"

        # Critical severity marks item as COMPROMISED
        records = engine.list_records(record_type="items")
        item = [i for i in records["items"] if i["item_id"] == "SEC-INC-01"][0]
        assert item["status"] == "COMPROMISED"

    def test_list_records_and_telemetry(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        telemetry_empty = engine.get_telemetry_status()
        assert telemetry_empty["total_classified_items"] == 0
        assert telemetry_empty["active_authorizations"] == 0

        # Seed data
        engine.register_classified_item(
            item_id="SEC-SEED-01",
            item_title="Tài liệu Hạt nhân Dân sự",
            classification_level="TOI_MAT",
            originating_agency="Viện Năng lượng Nguyên tử Việt Nam",
            approving_authority="Viện trưởng",
        )
        engine.authorize_access(
            auth_id="AUTH-SEED-01",
            item_id="SEC-SEED-01",
            authorized_person="Tiến sĩ Phạm A",
            authorizing_official="Viện trưởng",
            operation_type="READ_ACCESS",
            purpose="Nghiên cứu an toàn lò phản ứng",
        )
        engine.adjust_classification(
            declass_id="DECLAS-SEED-01",
            item_id="SEC-SEED-01",
            declass_type="GRADE_DOWNGRADE",
            new_level="MAT",
            decision_number="QĐ 12/NLNT",
            decision_authority="Viện trưởng",
            reason_summary="Điều chỉnh độ mật",
        )
        engine.report_security_incident(
            incident_id="INC-SEED-01",
            item_id="SEC-SEED-01",
            incident_type="LOSS_MISPLACEMENT",
            severity_level="MODERATE",
            suspect_person="Chuyên viên B",
            quarantine_measures="Tìm kiếm và lập biên bản thất lạc",
        )

        telemetry = engine.get_telemetry_status()
        assert telemetry["total_classified_items"] == 1
        assert telemetry["active_authorizations"] == 1
        assert telemetry["total_declassifications"] == 1
        assert telemetry["active_security_incidents"] == 1

        all_rec = engine.list_records(record_type="all")
        assert len(all_rec["items"]) == 1
        assert len(all_rec["authorizations"]) == 1
        assert len(all_rec["declassifications"]) == 1
        assert len(all_rec["incidents"]) == 1


class TestStateSecretCLI:
    def test_cli_default_dashboard_text(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(statesecret_app, [])
        assert result.exit_code == 0
        assert "Total Classified Items" in result.output

    def test_cli_default_dashboard_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(statesecret_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_classified_items" in data
        assert "active_authorizations" in data

    def test_cli_classify_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            statesecret_app,
            [
                "classify",
                "--id", "SEC-CLI-01",
                "--title", "Chiến lược Đàm phán Biên giới Lãnh thổ",
                "--level", "TUYET_MAT",
                "--agency", "Bộ Ngoại giao",
                "--auth", "Bộ trưởng Bộ Ngoại giao",
                "--carrier", "DOCUMENT_PAPER",
                "--scope", "Ủy ban Biên giới Quốc gia, VPCP",
                "--stamp", "DAU-TM-BNG-01",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["item_id"] == "SEC-CLI-01"
        assert data["classification_level"] == "TUYET_MAT"
        assert data["protection_years"] == 30

    def test_cli_classify_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            statesecret_app,
            [
                "classify",
                "--id", "SEC-CLI-ERR",
                "--title", "Lỗi Cấp độ",
                "--level", "INVALID_LEVEL",
                "--agency", "Bộ",
                "--auth", "Thủ trưởng",
            ],
        )
        assert result.exit_code == 1

    def test_cli_authorize_command(self, temp_db: str) -> None:
        runner = CliRunner()
        # Seed item
        runner.invoke(
            statesecret_app,
            [
                "classify",
                "--id", "SEC-CLI-AUTH",
                "--title", "Kế hoạch Điều tra Chuyên án C03",
                "--level", "TOI_MAT",
                "--agency", "Bộ Công an",
                "--auth", "Cục trưởng C03",
                "--json",
            ],
        )
        result = runner.invoke(
            statesecret_app,
            [
                "authorize",
                "--id", "AUTH-CLI-01",
                "--item-id", "SEC-CLI-AUTH",
                "--person", "Thượng tá Nguyễn Văn Long",
                "--auth-by", "Cục trưởng C03",
                "--op", "EXTRACT_SUMMARY",
                "--purpose", "Trích lục phục vụ phê chuẩn khởi tố",
                "--copies", "1",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["auth_id"] == "AUTH-CLI-01"
        assert data["operation_type"] == "EXTRACT_SUMMARY"

    def test_cli_adjust_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            statesecret_app,
            [
                "classify",
                "--id", "SEC-CLI-ADJ",
                "--title", "Tài liệu Cần Giải Mật",
                "--level", "MAT",
                "--agency", "Bộ Nội vụ",
                "--auth", "Bộ trưởng",
                "--json",
            ],
        )
        result = runner.invoke(
            statesecret_app,
            [
                "adjust",
                "--id", "DECLAS-CLI-01",
                "--item-id", "SEC-CLI-ADJ",
                "--type", "FULL_DECLASSIFICATION",
                "--decision", "QĐ 88/QĐ-BNV",
                "--authority", "Bộ trưởng Bộ Nội vụ",
                "--reason", "Đã hết thời hạn theo quy định",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["declass_type"] == "FULL_DECLASSIFICATION"

    def test_cli_destruct_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            statesecret_app,
            [
                "classify",
                "--id", "SEC-CLI-DEST",
                "--title", "Tài liệu Cần Tiêu Hủy",
                "--level", "MAT",
                "--agency", "Bộ Tài chính",
                "--auth", "Bộ trưởng",
                "--json",
            ],
        )
        result = runner.invoke(
            statesecret_app,
            [
                "destruct",
                "--id", "DEST-CLI-01",
                "--item-id", "SEC-CLI-DEST",
                "--chair", "Chánh Văn phòng Bộ",
                "--method", "INCINERATION_HIGH_TEMP",
                "--minutes", "BB-TH-05/BTC",
                "--witnesses", "Cục Kế hoạch Tài chính, Ban Cơ yếu",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["destruct_id"] == "DEST-CLI-01"
        assert data["item_status"] == "DESTROYED"

    def test_cli_incident_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            statesecret_app,
            [
                "classify",
                "--id", "SEC-CLI-INC",
                "--title", "Tài liệu Bị Thất Lạc",
                "--level", "MAT",
                "--agency", "UBND Thành phố Hà Nội",
                "--auth", "Chủ tịch UBND",
                "--json",
            ],
        )
        result = runner.invoke(
            statesecret_app,
            [
                "incident",
                "--id", "INC-CLI-01",
                "--item-id", "SEC-CLI-INC",
                "--type", "LOSS_MISPLACEMENT",
                "--severity", "MAJOR",
                "--suspect", "Chuyên viên văn phòng",
                "--quarantine", "Kiểm tra camera an ninh và đình chỉ công tác 15 ngày",
                "--referral", "Công an Thành phố Hà Nội",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["incident_id"] == "INC-CLI-01"

    def test_cli_list_and_status(self, temp_db: str) -> None:
        runner = CliRunner()
        res_list = runner.invoke(statesecret_app, ["list", "--type", "all", "--json"])
        assert res_list.exit_code == 0
        list_data = json.loads(res_list.output)
        assert "items" in list_data

        res_stat = runner.invoke(statesecret_app, ["status", "--json"])
        assert res_stat.exit_code == 0
        stat_data = json.loads(res_stat.output)
        assert "total_classified_items" in stat_data


class TestStateSecretMcp:
    def test_mcp_standalone_classify(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_statesecret_classify

        res_str = handle_statesecret_classify({
            "item_id": "SEC-MCP-01",
            "item_title": "Phương án Cơ yếu Chiến lược",
            "classification_level": "TUYET_MAT",
            "originating_agency": "Ban Cơ yếu Chính phủ",
            "approving_authority": "Trưởng ban Cơ yếu Chính phủ",
            "carrier_type": "CRYPTOGRAPHIC_KEY_DEVICE",
        })
        res = json.loads(res_str)
        assert res["item_id"] == "SEC-MCP-01"
        assert res["classification_level"] == "TUYET_MAT"
        assert res["carrier_type"] == "CRYPTOGRAPHIC_KEY_DEVICE"

    def test_mcp_standalone_authorize(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_statesecret_authorize, handle_statesecret_classify

        handle_statesecret_classify({
            "item_id": "SEC-MCP-AUTH",
            "item_title": "Tài liệu Mật MCP",
            "classification_level": "MAT",
            "originating_agency": "Bộ",
            "approving_authority": "Lãnh đạo",
        })
        res_str = handle_statesecret_authorize({
            "auth_id": "AUTH-MCP-01",
            "item_id": "SEC-MCP-AUTH",
            "authorized_person": "Cán bộ A",
            "authorizing_official": "Thủ trưởng B",
            "operation_type": "READ_ACCESS",
            "purpose": "Nghiên cứu",
        })
        res = json.loads(res_str)
        assert res["auth_id"] == "AUTH-MCP-01"
        assert res["status"] == "GRANTED"

    def test_mcp_standalone_adjust(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_statesecret_adjust, handle_statesecret_classify

        handle_statesecret_classify({
            "item_id": "SEC-MCP-ADJ",
            "item_title": "Tài liệu Điều chỉnh MCP",
            "classification_level": "TOI_MAT",
            "originating_agency": "Bộ",
            "approving_authority": "Lãnh đạo",
        })
        res_str = handle_statesecret_adjust({
            "declass_id": "DECLAS-MCP-01",
            "item_id": "SEC-MCP-ADJ",
            "declass_type": "GRADE_DOWNGRADE",
            "new_level": "MAT",
            "decision_number": "QĐ 10",
            "decision_authority": "Bộ trưởng",
            "reason_summary": "Giảm độ mật",
        })
        res = json.loads(res_str)
        assert res["declass_id"] == "DECLAS-MCP-01"
        assert res["new_level"] == "MAT"

    def test_mcp_standalone_destruct(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_statesecret_classify, handle_statesecret_destruct

        handle_statesecret_classify({
            "item_id": "SEC-MCP-DEST",
            "item_title": "Tài liệu Tiêu hủy MCP",
            "classification_level": "MAT",
            "originating_agency": "Bộ",
            "approving_authority": "Lãnh đạo",
        })
        res_str = handle_statesecret_destruct({
            "destruct_id": "DEST-MCP-01",
            "item_id": "SEC-MCP-DEST",
            "destruction_council_chair": "Chủ tịch Hội đồng",
            "destruction_method": "INCINERATION_HIGH_TEMP",
            "minutes_reference": "BB-01",
        })
        res = json.loads(res_str)
        assert res["destruct_id"] == "DEST-MCP-01"
        assert res["item_status"] == "DESTROYED"

    def test_mcp_standalone_incident(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_statesecret_classify, handle_statesecret_incident

        handle_statesecret_classify({
            "item_id": "SEC-MCP-INC",
            "item_title": "Tài liệu Sự cố MCP",
            "classification_level": "MAT",
            "originating_agency": "Bộ",
            "approving_authority": "Lãnh đạo",
        })
        res_str = handle_statesecret_incident({
            "incident_id": "INC-MCP-01",
            "item_id": "SEC-MCP-INC",
            "incident_type": "LEAK_DISCLOSURE",
            "severity_level": "MAJOR",
            "suspect_person": "Cá nhân Y",
            "quarantine_measures": "Đình chỉ và thu hồi",
        })
        res = json.loads(res_str)
        assert res["incident_id"] == "INC-MCP-01"

    def test_mcp_standalone_list_and_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_statesecret_list, handle_statesecret_status

        list_str = handle_statesecret_list({"category": "all", "limit": 10})
        lst = json.loads(list_str)
        assert "items" in lst

        stat_str = handle_statesecret_status({})
        stat = json.loads(stat_str)
        assert "total_classified_items" in stat

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")
        cls_str = server._handle_statesecret_classify(
            item_id="SEC-CORE-01",
            item_title="Phương án Tác chiến Phòng thủ Quốc gia",
            classification_level="TUYET_MAT",
            originating_agency="Bộ Quốc phòng",
            approving_authority="Đại tướng Bộ trưởng",
        )
        cls_data = json.loads(cls_str)
        assert cls_data["item_id"] == "SEC-CORE-01"

        stat_str = server._handle_statesecret_status()
        stat = json.loads(stat_str)
        assert stat["total_classified_items"] >= 1


class TestStateSecretEdgeCases:
    def test_all_classification_levels(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        for i, lvl in enumerate(VALID_CLASSIFICATION_LEVELS):
            res = engine.register_classified_item(
                item_id=f"SEC-LVL-{i}",
                item_title=f"Tài liệu cấp độ {lvl}",
                classification_level=lvl,
                originating_agency="Cơ quan",
                approving_authority="Thủ trưởng",
            )
            assert res["classification_level"] == lvl
            expected_years = VALID_CLASSIFICATION_LEVELS[lvl]["default_years"]
            assert res["protection_years"] == expected_years

    def test_all_carrier_types(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        for i, carr in enumerate(VALID_CARRIER_TYPES):
            res = engine.register_classified_item(
                item_id=f"SEC-CARR-{i}",
                item_title=f"Vật mang {carr}",
                classification_level="MAT",
                originating_agency="Cơ quan",
                approving_authority="Thủ trưởng",
                carrier_type=carr,
            )
            assert res["carrier_type"] == carr

    def test_all_operation_types(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        engine.register_classified_item(
            item_id="SEC-OP-ALL",
            item_title="Tài liệu kiểm tra thao tác",
            classification_level="MAT",
            originating_agency="Cơ quan",
            approving_authority="Thủ trưởng",
        )
        for i, op in enumerate(VALID_OPERATION_TYPES):
            res = engine.authorize_access(
                auth_id=f"AUTH-OP-{i}",
                item_id="SEC-OP-ALL",
                authorized_person=f"Cán bộ {i}",
                authorizing_official="Thủ trưởng",
                operation_type=op,
                purpose=f"Thực hiện thao tác {op}",
            )
            assert res["operation_type"] == op

    def test_all_declassification_types(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        for i, dt in enumerate(VALID_DECLASSIFICATION_TYPES):
            item_id = f"SEC-DT-{i}"
            engine.register_classified_item(
                item_id=item_id,
                item_title=f"Tài liệu {dt}",
                classification_level="TOI_MAT",
                originating_agency="Cơ quan",
                approving_authority="Thủ trưởng",
            )
            res = engine.adjust_classification(
                declass_id=f"DECLAS-DT-{i}",
                item_id=item_id,
                declass_type=dt,
                new_level="MAT" if "GRADE" in dt else None,
                decision_number=f"QĐ-{i}",
                decision_authority="Thẩm quyền",
                reason_summary=f"Căn cứ {dt}",
            )
            assert res["declass_type"] == dt

    def test_all_destruction_methods(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        for i, meth in enumerate(VALID_DESTRUCTION_METHODS):
            item_id = f"SEC-METH-{i}"
            engine.register_classified_item(
                item_id=item_id,
                item_title=f"Tài liệu tiêu hủy {meth}",
                classification_level="MAT",
                originating_agency="Cơ quan",
                approving_authority="Thủ trưởng",
            )
            res = engine.execute_destruction(
                destruct_id=f"DEST-METH-{i}",
                item_id=item_id,
                destruction_council_chair="Chủ tịch Hội đồng",
                destruction_method=meth,
                minutes_reference=f"BB-{i}",
            )
            assert res["destruction_method"] == meth

    def test_all_incident_types(self, temp_db: str) -> None:
        engine = StateSecretEngine(db_path=temp_db)
        for i, it in enumerate(VALID_INCIDENT_TYPES):
            item_id = f"SEC-INC-TYPE-{i}"
            engine.register_classified_item(
                item_id=item_id,
                item_title=f"Tài liệu sự cố {it}",
                classification_level="MAT",
                originating_agency="Cơ quan",
                approving_authority="Thủ trưởng",
            )
            res = engine.report_security_incident(
                incident_id=f"INC-TYPE-{i}",
                item_id=item_id,
                incident_type=it,
                severity_level="MODERATE",
                suspect_person=f"Đối tượng {i}",
                quarantine_measures=f"Biện pháp xử lý {it}",
            )
            assert res["incident_type"] == it
