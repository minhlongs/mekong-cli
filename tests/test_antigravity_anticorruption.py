"""
Unit and integration tests for Vietnamese Anti-Corruption, Asset Declaration & Integrity Oversight Suite.
Governed by Law on Anti-Corruption 2018 (Law No. 36/2018/QH14) & Decree No. 130/2020/NĐ-CP.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.anticorruption_command import app as anticorruption_app
from src.core.anticorruption_engine import (
    VALID_ACTION_TYPES,
    VALID_CONFLICT_CATEGORIES,
    VALID_DECLARATION_TYPES,
    VALID_GIFT_DISPOSITIONS,
    VALID_RISK_LEVELS,
    VALID_VERIFICATION_GROUNDS,
    AntiCorruptionEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_ANTICORRUPTION_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestAntiCorruptionEngine:
    def test_register_declaration_valid(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        res = engine.register_declaration(
            declaration_id="DEC-2026-001",
            declarant_id="CCCD-001",
            declarant_name="Trần Văn Minh",
            organization="Sở Xây dựng Hà Nội",
            position_title="Phó Giám đốc",
            declaration_type="ANNUAL",
            declaration_year=2025,
            real_estate_value_vnd=8_000_000_000.0,
            movable_assets_value_vnd=1_500_000_000.0,
            overseas_assets_value_vnd=0.0,
            annual_income_vnd=600_000_000.0,
        )
        assert res["declaration_id"] == "DEC-2026-001"
        assert res["declarant_id"] == "CCCD-001"
        assert res["total_declared_wealth_vnd"] == 9_500_000_000.0
        assert res["verification_status"] == "UNVERIFIED"

    def test_register_declaration_duplicate(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        engine.register_declaration(
            declaration_id="DEC-DUP",
            declarant_id="CCCD-002",
            declarant_name="Lê Văn B",
            organization="UBND Quận 1",
            position_title="Chủ tịch",
            declaration_type="FIRST_TIME",
            declaration_year=2025,
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_declaration(
                declaration_id="DEC-DUP",
                declarant_id="CCCD-002",
                declarant_name="Lê Văn B",
                organization="UBND Quận 1",
                position_title="Chủ tịch",
                declaration_type="FIRST_TIME",
                declaration_year=2025,
            )

    def test_register_declaration_invalid_inputs(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_declaration(
                declaration_id="",
                declarant_id="CCCD-003",
                declarant_name="Nguyễn C",
                organization="Sở Y tế",
                position_title="Trưởng phòng",
                declaration_type="ANNUAL",
                declaration_year=2025,
            )

        with pytest.raises(ValueError, match="Invalid declaration_type"):
            engine.register_declaration(
                declaration_id="DEC-INV-TYPE",
                declarant_id="CCCD-003",
                declarant_name="Nguyễn C",
                organization="Sở Y tế",
                position_title="Trưởng phòng",
                declaration_type="INVALID_TYPE",
                declaration_year=2025,
            )

        with pytest.raises(ValueError, match="cannot be negative"):
            engine.register_declaration(
                declaration_id="DEC-NEG",
                declarant_id="CCCD-003",
                declarant_name="Nguyễn C",
                organization="Sở Y tế",
                position_title="Trưởng phòng",
                declaration_type="ANNUAL",
                declaration_year=2025,
                real_estate_value_vnd=-100.0,
            )

    def test_execute_verification_truthful(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        engine.register_declaration(
            declaration_id="DEC-VER-01",
            declarant_id="CCCD-VER-01",
            declarant_name="Phạm Văn D",
            organization="Cục Hải quan",
            position_title="Chi cục trưởng",
            declaration_type="ANNUAL",
            declaration_year=2025,
            real_estate_value_vnd=5_000_000_000.0,
            movable_assets_value_vnd=1_000_000_000.0,
        )

        res = engine.execute_verification(
            verification_id="VER-001",
            declaration_id="DEC-VER-01",
            inspecting_agency="Thanh tra Tổng cục Hải quan",
            verification_ground="ANNUAL_RANDOM_SELECTION",
            verified_actual_wealth_vnd=6_000_000_000.0,
            findings_summary="Tài sản thực tế khớp hoàn toàn với bản kê khai.",
        )
        assert res["verification_conclusion"] == "TRUTHFUL"
        assert res["unexplained_wealth_vnd"] == 0.0
        assert res["new_declaration_status"] == "VERIFIED_CLEAR"

    def test_execute_verification_unexplained_wealth(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        engine.register_declaration(
            declaration_id="DEC-VER-02",
            declarant_id="CCCD-VER-02",
            declarant_name="Hoàng Văn E",
            organization="Sở Giao thông Vận tải",
            position_title="Giám đốc",
            declaration_type="ANNUAL",
            declaration_year=2025,
            real_estate_value_vnd=10_000_000_000.0,
        )

        res = engine.execute_verification(
            verification_id="VER-002",
            declaration_id="DEC-VER-02",
            inspecting_agency="Thanh tra Tỉnh",
            verification_ground="UNTRUTHFUL_SUSPICION",
            verified_actual_wealth_vnd=10_500_000_000.0,
            findings_summary="Phát hiện tài khoản tiết kiệm 500 triệu VND chưa giải trình.",
        )
        assert res["verification_conclusion"] == "UNEXPLAINED_WEALTH"
        assert res["unexplained_wealth_vnd"] == 500_000_000.0
        assert res["new_declaration_status"] == "DISCREPANCY_FLAGGED"

    def test_execute_verification_fraudulent_concealment(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        engine.register_declaration(
            declaration_id="DEC-VER-03",
            declarant_id="CCCD-VER-03",
            declarant_name="Vũ Văn F",
            organization="Ban Quản lý Dự án ODA",
            position_title="Phó Giám đốc BQLDA",
            declaration_type="PERSONNEL_APPOINTMENT",
            declaration_year=2025,
            real_estate_value_vnd=4_000_000_000.0,
        )

        res = engine.execute_verification(
            verification_id="VER-003",
            declaration_id="DEC-VER-03",
            inspecting_agency="Cơ quan Kiểm soát TSTN Thanh tra Chính phủ",
            verification_ground="DENUNCIATION_EVIDENCE",
            verified_actual_wealth_vnd=12_000_000_000.0,
            findings_summary="Che giấu 2 căn biệt thự và 1 xe sang đứng tên người thân nhưng thụ hưởng thực tế.",
        )
        assert res["verification_conclusion"] == "FRAUDULENT_CONCEALMENT"
        assert res["unexplained_wealth_vnd"] == 8_000_000_000.0
        assert res["new_declaration_status"] == "DISCREPANCY_FLAGGED"

    def test_record_gift_surrender(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        res = engine.record_gift_surrender(
            gift_record_id="GIFT-2026-001",
            declarant_id="CCCD-001",
            declarant_name="Trần Văn Minh",
            organization="Sở Xây dựng",
            gift_description="Bộ ấm chén ngọc bích mạ vàng",
            giver_identity="Công ty Nhà đất Á Châu",
            estimated_value_vnd=85_000_000.0,
            disposition_type="TREASURY_SURRENDER",
            treasury_receipt_voucher="KB-2026-0099",
        )
        assert res["gift_record_id"] == "GIFT-2026-001"
        assert res["estimated_value_vnd"] == 85_000_000.0
        assert res["disposition_type"] == "TREASURY_SURRENDER"

    def test_register_and_resolve_conflict_interest(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        res = engine.register_conflict_interest(
            conflict_id="COI-2026-001",
            person_id="CCCD-COI-01",
            person_name="Đỗ Văn G",
            organization="Sở Tài chính",
            conflict_category="PROCUREMENT_BIDDING",
            relative_relation="Vợ là Giám đốc công ty cung ứng vật tư",
            risk_level="HIGH",
            remediation_action="Rút khỏi Hội đồng mua sắm",
        )
        assert res["conflict_id"] == "COI-2026-001"
        assert res["resolved"] is False

        resolved = engine.resolve_conflict_interest(
            conflict_id="COI-2026-001",
            remediation_action="Đã ban hành quyết định thay thế thành viên Hội đồng",
        )
        assert resolved["conflict_id"] == "COI-2026-001"
        assert resolved["resolved"] is True

    def test_record_sanction_or_referral(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        res_warn = engine.record_sanction_or_referral(
            action_id="SANCT-001",
            target_id="CCCD-001",
            target_name="Trần Văn Minh",
            case_reference="VER-002",
            action_type="WARNING",
            issuing_authority="Chủ tịch UBND Tỉnh",
            decision_number="QĐ 99/QĐ-UBND",
        )
        assert res_warn["action_type"] == "WARNING"

        res_crim = engine.record_sanction_or_referral(
            action_id="SANCT-002",
            target_id="CCCD-VER-03",
            target_name="Vũ Văn F",
            case_reference="VER-003",
            action_type="CRIMINAL_REFERRAL",
            issuing_authority="Thanh tra Chính phủ",
            decision_number="CV 1234/TTCP-CụcIV",
            referral_target_agency="Cơ quan Cảnh sát Điều tra C03 Bộ Công an",
        )
        assert res_crim["action_type"] == "CRIMINAL_REFERRAL"
        assert "C03" in res_crim["referral_target_agency"]

    def test_list_records(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        engine.register_declaration(
            declaration_id="DEC-LIST-01",
            declarant_id="CCCD-L1",
            declarant_name="Người kê khai 1",
            organization="Cơ quan A",
            position_title="Chuyên viên",
            declaration_type="ANNUAL",
            declaration_year=2025,
        )
        records = engine.list_records(record_type="all")
        assert "declarations" in records
        assert len(records["declarations"]) >= 1

    def test_get_telemetry_status(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        engine.register_declaration(
            declaration_id="DEC-TEL-01",
            declarant_id="CCCD-T1",
            declarant_name="Người T1",
            organization="Cơ quan B",
            position_title="Trưởng ban",
            declaration_type="ANNUAL",
            declaration_year=2025,
            real_estate_value_vnd=3_000_000_000.0,
        )
        engine.execute_verification(
            verification_id="VER-TEL-01",
            declaration_id="DEC-TEL-01",
            inspecting_agency="Thanh tra B",
            verification_ground="ANNUAL_RANDOM_SELECTION",
            verified_actual_wealth_vnd=3_000_000_000.0,
            findings_summary="Khớp.",
        )
        telemetry = engine.get_telemetry_status()
        assert telemetry["total_declarations"] == 1
        assert telemetry["total_verifications"] == 1
        assert telemetry["verification_coverage_rate_pct"] == 100.0
        assert telemetry["total_declared_wealth_vnd"] == 3_000_000_000.0


class TestAntiCorruptionCli:
    def test_cli_default_callback(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(anticorruption_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_declarations" in data
        assert "total_verifications" in data

    def test_cli_status_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(anticorruption_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "verification_coverage_rate_pct" in data

    def test_cli_declare_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            anticorruption_app,
            [
                "declare",
                "--id", "DEC-CLI-01",
                "--declarant-id", "CCCD-CLI-01",
                "--name", "Vương Quốc Cường",
                "--org", "Sở Nội vụ",
                "--title", "Phó Giám đốc",
                "--type", "ANNUAL",
                "--year", "2025",
                "--real-estate", "12000000000",
                "--movable", "3000000000",
                "--income", "900000000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["declaration_id"] == "DEC-CLI-01"
        assert data["total_declared_wealth_vnd"] == 15_000_000_000.0

    def test_cli_verify_command(self, temp_db: str) -> None:
        runner = CliRunner()
        # Create declaration first
        runner.invoke(
            anticorruption_app,
            [
                "declare",
                "--id", "DEC-CLI-02",
                "--declarant-id", "CCCD-CLI-02",
                "--name", "Bùi Tiến Dũng",
                "--org", "Sở GTVT",
                "--title", "Trưởng ban QLDA",
                "--year", "2025",
                "--real-estate", "5000000000",
            ],
        )

        result = runner.invoke(
            anticorruption_app,
            [
                "verify",
                "--id", "VER-CLI-02",
                "--declaration", "DEC-CLI-02",
                "--agency", "Thanh tra Tỉnh",
                "--ground", "UNTRUTHFUL_SUSPICION",
                "--verified-wealth", "7500000000",
                "--summary", "Phát hiện khoản chênh lệch 2.5 tỷ VND chưa giải trình.",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["verification_conclusion"] == "FRAUDULENT_CONCEALMENT"
        assert data["unexplained_wealth_vnd"] == 2_500_000_000.0

    def test_cli_gift_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            anticorruption_app,
            [
                "gift",
                "--id", "GIFT-CLI-01",
                "--declarant-id", "CCCD-CLI-01",
                "--name", "Vương Quốc Cường",
                "--org", "Sở Nội vụ",
                "--desc", "Bình hoa sứ mạ vàng 24k",
                "--giver", "Tập đoàn Delta",
                "--value", "65000000",
                "--disposition", "TREASURY_SURRENDER",
                "--voucher", "KB-CLI-77",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["gift_record_id"] == "GIFT-CLI-01"
        assert data["estimated_value_vnd"] == 65_000_000.0

    def test_cli_conflict_command(self, temp_db: str) -> None:
        runner = CliRunner()
        res_reg = runner.invoke(
            anticorruption_app,
            [
                "conflict",
                "--id", "COI-CLI-01",
                "--person-id", "CCCD-CLI-01",
                "--name", "Vương Quốc Cường",
                "--org", "Sở Nội vụ",
                "--category", "RELATIVE_EMPLOYMENT",
                "--relation", "Cháu ruột ứng tuyển vị trí chuyên viên phòng trực thuộc",
                "--risk", "HIGH",
                "--remediation", "Không tham gia Hội đồng tuyển dụng",
                "--json",
            ],
        )
        assert res_reg.exit_code == 0
        data = json.loads(res_reg.output)
        assert data["conflict_id"] == "COI-CLI-01"

        res_res = runner.invoke(
            anticorruption_app,
            [
                "conflict",
                "--id", "COI-CLI-01",
                "--person-id", "CCCD-CLI-01",
                "--name", "Vương Quốc Cường",
                "--org", "Sở Nội vụ",
                "--category", "RELATIVE_EMPLOYMENT",
                "--relation", "Cháu ruột",
                "--resolve",
                "--remediation", "Đã phân công Trưởng phòng khác chủ trì",
                "--json",
            ],
        )
        assert res_res.exit_code == 0
        data_res = json.loads(res_res.output)
        assert data_res["resolved"] is True

    def test_cli_sanction_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            anticorruption_app,
            [
                "sanction",
                "--id", "SANCT-CLI-01",
                "--target-id", "CCCD-CLI-02",
                "--name", "Bùi Tiến Dũng",
                "--case-ref", "VER-CLI-02",
                "--type", "DISMISSAL",
                "--authority", "Chủ tịch UBND Tỉnh",
                "--decision", "QĐ 55/QĐ-UBND",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["action_type"] == "DISMISSAL"

    def test_cli_list_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(anticorruption_app, ["list", "--type", "all", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "declarations" in data


class TestAntiCorruptionMcp:
    def test_mcp_standalone_declare(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_anticorruption_declare

        res_str = handle_anticorruption_declare({
            "declaration_id": "DEC-MCP-01",
            "declarant_id": "CCCD-MCP-01",
            "declarant_name": "Tô Lâm Anh",
            "organization": "Bộ Công Thương",
            "position_title": "Cục trưởng",
            "declaration_year": 2025,
            "real_estate_value_vnd": 20_000_000_000.0,
        })
        res = json.loads(res_str)
        assert res["declaration_id"] == "DEC-MCP-01"
        assert res["total_declared_wealth_vnd"] == 20_000_000_000.0

    def test_mcp_standalone_verify(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_anticorruption_declare, handle_anticorruption_verify

        handle_anticorruption_declare({
            "declaration_id": "DEC-MCP-02",
            "declarant_id": "CCCD-MCP-02",
            "declarant_name": "Hoàng Hải",
            "organization": "Sở KHCN",
            "position_title": "Giám đốc",
            "declaration_year": 2025,
            "real_estate_value_vnd": 5_000_000_000.0,
        })
        res_str = handle_anticorruption_verify({
            "verification_id": "VER-MCP-02",
            "declaration_id": "DEC-MCP-02",
            "inspecting_agency": "Thanh tra Tỉnh",
            "verified_actual_wealth_vnd": 5_000_000_000.0,
        })
        res = json.loads(res_str)
        assert res["verification_conclusion"] == "TRUTHFUL"

    def test_mcp_standalone_gift(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_anticorruption_gift

        res_str = handle_anticorruption_gift({
            "gift_record_id": "GIFT-MCP-01",
            "declarant_id": "CCCD-MCP-01",
            "declarant_name": "Tô Lâm Anh",
            "organization": "Bộ Công Thương",
            "gift_description": "Đồng hồ cao cấp",
            "giver_identity": "Tập đoàn Năng lượng X",
            "estimated_value_vnd": 110_000_000.0,
            "treasury_receipt_voucher": "KB-MCP-01",
        })
        res = json.loads(res_str)
        assert res["gift_record_id"] == "GIFT-MCP-01"

    def test_mcp_standalone_conflict(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_anticorruption_conflict

        res_str = handle_anticorruption_conflict({
            "conflict_id": "COI-MCP-01",
            "person_id": "CCCD-MCP-01",
            "person_name": "Tô Lâm Anh",
            "organization": "Bộ Công Thương",
            "conflict_category": "CAPITAL_CONTRIBUTION",
            "relative_relation": "Góp vốn vào công ty phân phối điện",
            "risk_level": "PROHIBITED",
            "remediation_action": "Bắt buộc thoái vốn trong 30 ngày",
        })
        res = json.loads(res_str)
        assert res["conflict_id"] == "COI-MCP-01"

    def test_mcp_standalone_sanction(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_anticorruption_sanction

        res_str = handle_anticorruption_sanction({
            "action_id": "SANCT-MCP-01",
            "target_id": "CCCD-MCP-01",
            "target_name": "Tô Lâm Anh",
            "case_reference": "VER-MCP-02",
            "action_type": "REPRIMAND",
            "issuing_authority": "Bộ trưởng Bộ Công Thương",
            "decision_number": "QĐ 12/QĐ-BCT",
        })
        res = json.loads(res_str)
        assert res["action_type"] == "REPRIMAND"

    def test_mcp_standalone_list(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_anticorruption_list

        res_str = handle_anticorruption_list({"category": "all", "limit": 10})
        res = json.loads(res_str)
        assert "declarations" in res

    def test_mcp_standalone_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_anticorruption_status

        res_str = handle_anticorruption_status({})
        res = json.loads(res_str)
        assert "total_declarations" in res

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")
        res_decl = server._handle_anticorruption_declare(
            declaration_id="DEC-CORE-01",
            declarant_id="CCCD-CORE-01",
            declarant_name="Vũ Đức Đam",
            organization="Văn phòng Chính phủ",
            position_title="Phó Chủ nhiệm",
            declaration_type="ANNUAL",
            declaration_year=2025,
            real_estate_value_vnd=15_000_000_000.0,
        )
        res = json.loads(res_decl)
        assert res["declaration_id"] == "DEC-CORE-01"


class TestAntiCorruptionEdgeCases:
    def test_all_declaration_types(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        for i, dt in enumerate(VALID_DECLARATION_TYPES):
            res = engine.register_declaration(
                declaration_id=f"DEC-EDGE-{i}",
                declarant_id=f"CCCD-{i}",
                declarant_name=f"Declarant {i}",
                organization="Agency",
                position_title="Title",
                declaration_type=dt,
                declaration_year=2025,
            )
            assert res["declaration_type"] == dt

    def test_all_verification_grounds(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        for i, vg in enumerate(VALID_VERIFICATION_GROUNDS):
            decl_id = f"DEC-VG-{i}"
            engine.register_declaration(
                declaration_id=decl_id,
                declarant_id=f"CCCD-VG-{i}",
                declarant_name=f"Declarant VG {i}",
                organization="Agency",
                position_title="Title",
                declaration_type="ANNUAL",
                declaration_year=2025,
                real_estate_value_vnd=1_000_000_000.0,
            )
            res = engine.execute_verification(
                verification_id=f"VER-VG-{i}",
                declaration_id=decl_id,
                inspecting_agency="Agency",
                verification_ground=vg,
                verified_actual_wealth_vnd=1_000_000_000.0,
                findings_summary="Check.",
            )
            assert res["verification_ground"] == vg

    def test_all_action_types(self, temp_db: str) -> None:
        engine = AntiCorruptionEngine(db_path=temp_db)
        for i, at in enumerate(VALID_ACTION_TYPES):
            res = engine.record_sanction_or_referral(
                action_id=f"SANCT-EDGE-{i}",
                target_id=f"CCCD-AT-{i}",
                target_name=f"Target {i}",
                case_reference=f"REF-{i}",
                action_type=at,
                issuing_authority="Authority",
                decision_number=f"QD-{i}",
            )
            assert res["action_type"] == at
