"""
Unit and integration tests for Vietnamese National Cryptography, State Cipher & Civil Cryptography Suite.
Governed by:
- Law on Cryptography 2011 (Law No. 05/2011/QH13 — Luật Cơ yếu 2011)
- Decree No. 58/2016/NĐ-CP & Decree No. 53/2018/NĐ-CP (Civil Cryptography Business & Import/Export Licensing)
- Decree No. 09/2014/NĐ-CP (Guiding Implementation of Law on Cryptography)
- Circular No. 23/2022/TT-BQP (Technical Standards on Cryptographic Equipment & Evaluation)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.cipher_command import app as cipher_app
from src.core.cipher_engine import (
    VALID_BRANCH_TYPES,
    VALID_EQUIPMENT_TYPES,
    VALID_KEY_STATUS,
    VALID_KEY_TYPES,
    VALID_LICENSE_STATUS,
    VALID_LICENSE_TYPES,
    VALID_PRODUCT_CATEGORIES,
    VALID_SECURITY_LEVELS,
    VALID_SEVERITY_LEVELS,
    VALID_SYSTEM_STATUS,
    VALID_TAMPER_LEVELS,
    CipherEngine,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_CIPHER_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestCipherEngine:
    def test_register_system_valid(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        res = engine.register_system(
            system_id="SYS-GOV-01",
            system_name="Mạng Thông tin Mật mã Chính phủ điện tử Trục Quốc gia",
            branch_type="PARTY_GOVERNMENT",
            security_level="TUYET_MAT_TOP_SECRET",
            deployment_location="Trung tâm Dữ liệu Quốc gia, Hà Nội",
            algorithm_standard="TCVN-7142-GOV",
            commission_date="2025-01-10",
            status="ACTIVE_OPERATIONAL",
        )
        assert res["system_id"] == "SYS-GOV-01"
        assert res["branch_type"] == "PARTY_GOVERNMENT"
        assert res["security_level"] == "TUYET_MAT_TOP_SECRET"
        assert res["algorithm_standard"] == "TCVN-7142-GOV"
        assert res["status"] == "ACTIVE_OPERATIONAL"

    def test_register_system_duplicate(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        engine.register_system(
            system_id="SYS-DUP",
            system_name="Hệ thống Trùng",
            branch_type="MILITARY_DEFENSE",
            security_level="TOI_MAT_SECRET",
            deployment_location="Bộ Tổng Tham mưu",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_system(
                system_id="SYS-DUP",
                system_name="Hệ thống Trùng",
                branch_type="MILITARY_DEFENSE",
                security_level="TOI_MAT_SECRET",
                deployment_location="Bộ Tổng Tham mưu",
            )

    def test_register_system_invalid_inputs(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_system(
                system_id="",
                system_name="Tên",
                branch_type="PARTY_GOVERNMENT",
                security_level="TUYET_MAT_TOP_SECRET",
                deployment_location="",
            )

        with pytest.raises(ValueError, match="Invalid branch_type"):
            engine.register_system(
                system_id="SYS-INV-BRANCH",
                system_name="Tên",
                branch_type="COMMERCIAL_BANK",
                security_level="TUYET_MAT_TOP_SECRET",
                deployment_location="Hà Nội",
            )

        with pytest.raises(ValueError, match="Invalid security_level"):
            engine.register_system(
                system_id="SYS-INV-LEVEL",
                system_name="Tên",
                branch_type="PARTY_GOVERNMENT",
                security_level="PUBLIC_DOMAIN",
                deployment_location="Hà Nội",
            )

        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_system(
                system_id="SYS-INV-STAT",
                system_name="Tên",
                branch_type="PARTY_GOVERNMENT",
                security_level="TUYET_MAT_TOP_SECRET",
                deployment_location="Hà Nội",
                status="HACKED_COMPROMISED",
            )

    def test_issue_key_valid(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        res = engine.issue_key(
            key_id="KEY-2026-A1",
            system_id="SYS-GOV-01",
            key_type="MASTER_ROOT_KEY",
            custodian_officer="Đại tá Trần Văn Bình",
            key_length_bits=256,
            key_fingerprint="SHA256:e3b0c44298fc1c149afbf4c8996fb924",
            rotation_interval_days=90,
            status="ACTIVE_VALID",
        )
        assert res["key_id"] == "KEY-2026-A1"
        assert res["system_id"] == "SYS-GOV-01"
        assert res["key_type"] == "MASTER_ROOT_KEY"
        assert res["key_length_bits"] == 256
        assert res["rotation_interval_days"] == 90
        assert res["status"] == "ACTIVE_VALID"

    def test_issue_key_duplicate(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        engine.issue_key(
            key_id="KEY-DUP",
            system_id="SYS-01",
            key_type="DATA_ENCRYPTION_KEY",
            custodian_officer="Cán bộ Cơ yếu",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.issue_key(
                key_id="KEY-DUP",
                system_id="SYS-01",
                key_type="DATA_ENCRYPTION_KEY",
                custodian_officer="Cán bộ Cơ yếu",
            )

    def test_issue_key_invalid_inputs(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.issue_key(
                key_id="",
                system_id="",
                key_type="MASTER_ROOT_KEY",
                custodian_officer="",
            )

        with pytest.raises(ValueError, match="Invalid key_type"):
            engine.issue_key(
                key_id="KEY-INV",
                system_id="SYS-01",
                key_type="ROTCIPHER_KEY",
                custodian_officer="Cán bộ",
            )

        with pytest.raises(ValueError, match="at least 128 bits"):
            engine.issue_key(
                key_id="KEY-INV-BITS",
                system_id="SYS-01",
                key_type="MASTER_ROOT_KEY",
                custodian_officer="Cán bộ",
                key_length_bits=64,
            )

        with pytest.raises(ValueError, match="rotation_interval_days must be positive"):
            engine.issue_key(
                key_id="KEY-INV-DAYS",
                system_id="SYS-01",
                key_type="MASTER_ROOT_KEY",
                custodian_officer="Cán bộ",
                rotation_interval_days=0,
            )

        with pytest.raises(ValueError, match="Invalid status"):
            engine.issue_key(
                key_id="KEY-INV-STAT",
                system_id="SYS-01",
                key_type="MASTER_ROOT_KEY",
                custodian_officer="Cán bộ",
                status="LEAKED_WIKILEAKS",
            )

    def test_register_civil_license_valid(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        res = engine.register_civil_license(
            license_id="LIC-MMDS-2026-001",
            enterprise_name="Tập đoàn Công nghệ An ninh Mạng Quốc gia",
            enterprise_tax_id="0109988776",
            license_type="PRODUCT_TRADING",
            product_category="HARDWARE_HSM",
            issuing_authority="Ban Cơ yếu Chính phủ - Cục QLMMDS",
            valid_from="2026-01-01",
            valid_until="2036-01-01",
            status="VALID_ACTIVE",
        )
        assert res["license_id"] == "LIC-MMDS-2026-001"
        assert res["enterprise_name"] == "Tập đoàn Công nghệ An ninh Mạng Quốc gia"
        assert res["license_type"] == "PRODUCT_TRADING"
        assert res["product_category"] == "HARDWARE_HSM"
        assert res["status"] == "VALID_ACTIVE"

    def test_register_civil_license_duplicate(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        engine.register_civil_license(
            license_id="LIC-DUP",
            enterprise_name="Doanh nghiệp A",
            enterprise_tax_id="0101010101",
            license_type="SERVICE_PROVISION",
            product_category="SECURITY_IP_VPN",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_civil_license(
                license_id="LIC-DUP",
                enterprise_name="Doanh nghiệp A",
                enterprise_tax_id="0101010101",
                license_type="SERVICE_PROVISION",
                product_category="SECURITY_IP_VPN",
            )

    def test_register_civil_license_invalid_inputs(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_civil_license(
                license_id="",
                enterprise_name="",
                enterprise_tax_id="",
                license_type="PRODUCT_TRADING",
                product_category="HARDWARE_HSM",
            )

        with pytest.raises(ValueError, match="Invalid license_type"):
            engine.register_civil_license(
                license_id="LIC-INV-TYPE",
                enterprise_name="DN",
                enterprise_tax_id="0123456789",
                license_type="FREE_DISTRIBUTION",
                product_category="HARDWARE_HSM",
            )

        with pytest.raises(ValueError, match="Invalid product_category"):
            engine.register_civil_license(
                license_id="LIC-INV-CAT",
                enterprise_name="DN",
                enterprise_tax_id="0123456789",
                license_type="PRODUCT_TRADING",
                product_category="QUANTUM_TELEPORT",
            )

        with pytest.raises(ValueError, match="Invalid status"):
            engine.register_civil_license(
                license_id="LIC-INV-STAT",
                enterprise_name="DN",
                enterprise_tax_id="0123456789",
                license_type="PRODUCT_TRADING",
                product_category="HARDWARE_HSM",
                status="BLACKLISTED",
            )

    def test_register_equipment_valid(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        res = engine.register_equipment(
            equipment_id="EQ-HSM-2026-01",
            serial_number="VN-HSM-9988-X1",
            model_name="VNCIPHER-HSM-4000",
            equipment_type="HSM_APPLIANCE",
            tamper_resistance_level="PHYSICAL_ZEROIZE_SENSITIVE",
            assigned_unit="Cục Cơ yếu Đảng - Chính quyền",
            inspection_status="CERTIFIED_PASSED",
        )
        assert res["equipment_id"] == "EQ-HSM-2026-01"
        assert res["serial_number"] == "VN-HSM-9988-X1"
        assert res["model_name"] == "VNCIPHER-HSM-4000"
        assert res["tamper_resistance_level"] == "PHYSICAL_ZEROIZE_SENSITIVE"
        assert res["inspection_status"] == "CERTIFIED_PASSED"

    def test_register_equipment_duplicate(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        engine.register_equipment(
            equipment_id="EQ-DUP",
            serial_number="SN-1234",
            model_name="Model X",
            equipment_type="DEDICATED_ENCRYPTOR",
            tamper_resistance_level="TAMPER_EVIDENT",
            assigned_unit="Đơn vị A",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_equipment(
                equipment_id="EQ-DUP",
                serial_number="SN-1234",
                model_name="Model X",
                equipment_type="DEDICATED_ENCRYPTOR",
                tamper_resistance_level="TAMPER_EVIDENT",
                assigned_unit="Đơn vị A",
            )

    def test_register_equipment_invalid_inputs(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.register_equipment(
                equipment_id="",
                serial_number="",
                model_name="",
                equipment_type="HSM_APPLIANCE",
                tamper_resistance_level="TAMPER_EVIDENT",
                assigned_unit="",
            )

        with pytest.raises(ValueError, match="Invalid equipment_type"):
            engine.register_equipment(
                equipment_id="EQ-INV",
                serial_number="SN-1",
                model_name="Model 1",
                equipment_type="LASER_CANNON",
                tamper_resistance_level="TAMPER_EVIDENT",
                assigned_unit="Unit",
            )

        with pytest.raises(ValueError, match="Invalid tamper_resistance_level"):
            engine.register_equipment(
                equipment_id="EQ-INV-TAMPER",
                serial_number="SN-1",
                model_name="Model 1",
                equipment_type="HSM_APPLIANCE",
                tamper_resistance_level="PAPER_ENVELOPE",
                assigned_unit="Unit",
            )

        with pytest.raises(ValueError, match="Invalid inspection_status"):
            engine.register_equipment(
                equipment_id="EQ-INV-INSP",
                serial_number="SN-1",
                model_name="Model 1",
                equipment_type="HSM_APPLIANCE",
                tamper_resistance_level="TAMPER_EVIDENT",
                assigned_unit="Unit",
                inspection_status="DESTROYED_IN_COMBAT",
            )

    def test_report_incident_valid(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        res = engine.report_incident(
            incident_id="INC-CIPHER-2026-01",
            affected_system_or_key="KEY-2026-A1",
            severity_level="HIGH_TAMPER_DETECTED",
            incident_description="Phát hiện can thiệp cảm biến mở vỏ vật lý tại nút mạng dự phòng",
            containment_actions="Kích hoạt tự động Zeroize bộ nhớ khóa và thu hồi chứng thư khẩn cấp",
            reporting_officer="Thiếu tá Lê Hồng Quang",
            reported_date="2026-03-25",
            resolved=True,
        )
        assert res["incident_id"] == "INC-CIPHER-2026-01"
        assert res["affected_system_or_key"] == "KEY-2026-A1"
        assert res["severity_level"] == "HIGH_TAMPER_DETECTED"
        assert res["resolved"] is True

    def test_report_incident_duplicate(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        engine.report_incident(
            incident_id="INC-DUP",
            affected_system_or_key="SYS-01",
            severity_level="LOW_PROTOCOL_MISMATCH",
            incident_description="Cảnh báo",
            containment_actions="Xử lý",
            reporting_officer="Cán bộ",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.report_incident(
                incident_id="INC-DUP",
                affected_system_or_key="SYS-01",
                severity_level="LOW_PROTOCOL_MISMATCH",
                incident_description="Cảnh báo",
                containment_actions="Xử lý",
                reporting_officer="Cán bộ",
            )

    def test_report_incident_invalid_inputs(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="are required"):
            engine.report_incident(
                incident_id="",
                affected_system_or_key="",
                severity_level="LOW_PROTOCOL_MISMATCH",
                incident_description="",
                containment_actions="",
                reporting_officer="",
            )

        with pytest.raises(ValueError, match="Invalid severity_level"):
            engine.report_incident(
                incident_id="INC-INV",
                affected_system_or_key="SYS-1",
                severity_level="NUCLEAR_MELTDOWN",
                incident_description="Desc",
                containment_actions="Act",
                reporting_officer="Officer",
            )

    def test_list_records_categories(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        engine.register_system("S-1", "Hệ thống A", "PARTY_GOVERNMENT", "TUYET_MAT_TOP_SECRET", "Hà Nội")
        engine.issue_key("K-1", "S-1", "MASTER_ROOT_KEY", "Đại tá A")
        engine.register_civil_license("L-1", "DN 1", "01001", "PRODUCT_TRADING", "HARDWARE_HSM")
        engine.register_equipment("E-1", "SN-1", "Model 1", "HSM_APPLIANCE", "PHYSICAL_ZEROIZE_SENSITIVE", "Đơn vị 1")
        engine.report_incident("I-1", "S-1", "LOW_PROTOCOL_MISMATCH", "Lỗi nhẹ", "Khởi động lại", "Sĩ quan 1")

        all_records = engine.list_records(record_type="all")
        assert len(all_records["systems"]) == 1
        assert len(all_records["keys"]) == 1
        assert len(all_records["licenses"]) == 1
        assert len(all_records["equipment"]) == 1
        assert len(all_records["incidents"]) == 1

        systems_only = engine.list_records(record_type="systems")
        assert "systems" in systems_only
        assert "keys" not in systems_only

    def test_telemetry_status_calculations(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        engine.register_system("S-1", "Mạng Đảng", "PARTY_GOVERNMENT", "TUYET_MAT_TOP_SECRET", "Hà Nội", status="ACTIVE_OPERATIONAL")
        engine.register_system("S-2", "Mạng Quân sự", "MILITARY_DEFENSE", "TUYET_MAT_TOP_SECRET", "Bộ Quốc phòng", status="ACTIVE_OPERATIONAL")
        engine.register_system("S-3", "Mạng Dự phòng", "MILITARY_DEFENSE", "TOI_MAT_SECRET", "Hải Phòng", status="STANDBY_BACKUP")

        engine.issue_key("K-1", "S-1", "MASTER_ROOT_KEY", "Đại tá A", status="ACTIVE_VALID")
        engine.issue_key("K-2", "S-2", "SESSION_TRANSPORT_KEY", "Đại tá B", status="ACTIVE_VALID")
        engine.issue_key("K-3", "S-3", "DATA_ENCRYPTION_KEY", "Đại tá C", status="REVOKED")

        engine.register_civil_license("L-1", "DN 1", "01001", "PRODUCT_TRADING", "HARDWARE_HSM", status="VALID_ACTIVE")
        engine.register_civil_license("L-2", "DN 2", "01002", "SERVICE_PROVISION", "SECURITY_IP_VPN", status="EXPIRED")

        engine.register_equipment("E-1", "SN-1", "Model 1", "HSM_APPLIANCE", "PHYSICAL_ZEROIZE_SENSITIVE", "Cục A", inspection_status="CERTIFIED_PASSED")
        engine.register_equipment("E-2", "SN-2", "Model 2", "DEDICATED_ENCRYPTOR", "TAMPER_RESISTANT", "Cục B", inspection_status="INSPECTION_PENDING")

        engine.report_incident("I-1", "S-1", "HIGH_TAMPER_DETECTED", "Can thiệp", "Xử lý", "Cán bộ", resolved=True)
        engine.report_incident("I-2", "S-2", "CRITICAL_KEY_COMPROMISE", "Nghi lộ khóa", "Cách ly", "Cán bộ", resolved=False)

        telemetry = engine.get_telemetry_status()
        assert telemetry["active_operational_systems"] == 2
        assert telemetry["systems_by_branch"]["PARTY_GOVERNMENT"] == 1
        assert telemetry["systems_by_branch"]["MILITARY_DEFENSE"] == 2
        assert telemetry["active_valid_keys"] == 2
        assert telemetry["active_civil_licenses"] == 1
        assert telemetry["certified_equipment_count"] == 1
        assert telemetry["total_cryptographic_incidents"] == 2
        assert telemetry["unresolved_incidents"] == 1


class TestCipherCLI:
    def test_cli_default_dashboard_text(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(cipher_app, [])
        assert result.exit_code == 0
        assert "BAN CƠ YẾU CHÍNH PHỦ" in result.output

    def test_cli_default_dashboard_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(cipher_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "active_operational_systems" in data
        assert "active_valid_keys" in data

    def test_cli_status_text_and_json(self, temp_db: str) -> None:
        runner = CliRunner()
        res_text = runner.invoke(cipher_app, ["status"])
        assert res_text.exit_code == 0
        assert "Mật mã Quốc gia" in res_text.output

        res_json = runner.invoke(cipher_app, ["status", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "certified_equipment_count" in data

    def test_cli_system_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "system",
                "--id", "SYS-CLI-01",
                "--name", "Mạng Mật mã Ngoại giao Toàn cầu",
                "--branch", "DIPLOMATIC_FOREIGN",
                "--level", "TUYET_MAT_TOP_SECRET",
                "--location", "Bộ Ngoại giao, Hà Nội",
                "--algo", "TCVN-7142-GOV",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["system_id"] == "SYS-CLI-01"
        assert data["branch_type"] == "DIPLOMATIC_FOREIGN"

    def test_cli_system_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "system",
                "--id", "SYS-ERR",
                "--name", "Tên",
                "--branch", "INVALID_BRANCH",
                "--level", "TUYET_MAT_TOP_SECRET",
                "--location", "Loc",
            ],
        )
        assert result.exit_code != 0

    def test_cli_key_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "key",
                "--id", "KEY-CLI-01",
                "--system", "SYS-CLI-01",
                "--type", "SIGNING_AUTH_KEY",
                "--officer", "Thượng tá Đỗ Minh Tuấn",
                "--bits", "512",
                "--interval", "60",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["key_id"] == "KEY-CLI-01"
        assert data["key_length_bits"] == 512

    def test_cli_key_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "key",
                "--id", "KEY-ERR",
                "--system", "SYS-1",
                "--type", "INVALID_TYPE",
                "--officer", "Officer",
            ],
        )
        assert result.exit_code != 0

    def test_cli_license_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "license",
                "--id", "LIC-CLI-01",
                "--enterprise", "Công ty CP An ninh Mật mã Sao Vàng",
                "--tax-id", "0312456789",
                "--type", "SERVICE_PROVISION",
                "--category", "SECURITY_IP_VPN",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["license_id"] == "LIC-CLI-01"
        assert data["product_category"] == "SECURITY_IP_VPN"

    def test_cli_license_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "license",
                "--id", "LIC-ERR",
                "--enterprise", "DN",
                "--tax-id", "123",
                "--type", "INVALID_TYPE",
                "--category", "HARDWARE_HSM",
            ],
        )
        assert result.exit_code != 0

    def test_cli_equipment_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "equipment",
                "--id", "EQ-CLI-01",
                "--serial", "SN-98711-ROUTER",
                "--model", "VNCIPHER-VPN-9000",
                "--type", "SECURE_ROUTER_VPN",
                "--tamper", "COGNITIVE_SHIELDED",
                "--unit", "Bộ Tư lệnh Tác chiến Không gian mạng",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["equipment_id"] == "EQ-CLI-01"
        assert data["tamper_resistance_level"] == "COGNITIVE_SHIELDED"

    def test_cli_equipment_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "equipment",
                "--id", "EQ-ERR",
                "--serial", "SN",
                "--model", "M",
                "--type", "INVALID_EQUIPMENT",
                "--unit", "Unit",
            ],
        )
        assert result.exit_code != 0

    def test_cli_incident_command_success(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "incident",
                "--id", "INC-CLI-01",
                "--target", "EQ-CLI-01",
                "--severity", "MEDIUM_FIRMWARE_ANOMALY",
                "--desc", "Phát hiện sai lệch mã băm firmware trong đợt kiểm tra định kỳ",
                "--actions", "Flash lại firmware ký số gốc và cô lập nút mạng",
                "--officer", "Trung tá Phạm Văn Dũng",
                "--resolved",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["incident_id"] == "INC-CLI-01"
        assert data["resolved"] is True

    def test_cli_incident_command_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cipher_app,
            [
                "incident",
                "--id", "INC-ERR",
                "--target", "T",
                "--severity", "INVALID_SEV",
                "--desc", "D",
                "--actions", "A",
                "--officer", "O",
            ],
        )
        assert result.exit_code != 0

    def test_cli_list_command_text_and_json(self, temp_db: str) -> None:
        runner = CliRunner()
        res_text = runner.invoke(cipher_app, ["list", "--type", "all"])
        assert res_text.exit_code == 0

        res_json = runner.invoke(cipher_app, ["list", "--type", "all", "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "systems" in data
        assert "equipment" in data

    def test_cli_help_options(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cipher_app, ["--help"])
        assert result.exit_code == 0
        assert "system" in result.output
        assert "key" in result.output
        assert "license" in result.output
        assert "equipment" in result.output
        assert "incident" in result.output
        assert "list" in result.output
        assert "status" in result.output


class TestCipherMCP:
    def test_mcp_standalone_system(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_cipher_system

        res_str = handle_cipher_system({
            "system_id": "SYS-MCP-01",
            "system_name": "Mạng Cơ yếu Công an Nhân dân",
            "branch_type": "PUBLIC_SECURITY",
            "security_level": "TUYET_MAT_TOP_SECRET",
            "deployment_location": "Bộ Công an",
        })
        res = json.loads(res_str)
        assert res["system_id"] == "SYS-MCP-01"
        assert res["branch_type"] == "PUBLIC_SECURITY"

    def test_mcp_standalone_key(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_cipher_key

        res_str = handle_cipher_key({
            "key_id": "KEY-MCP-01",
            "system_id": "SYS-MCP-01",
            "custodian_officer": "Đại tá Vũ Nam",
            "key_type": "SESSION_TRANSPORT_KEY",
            "key_length_bits": 256,
        })
        res = json.loads(res_str)
        assert res["key_id"] == "KEY-MCP-01"
        assert res["key_type"] == "SESSION_TRANSPORT_KEY"

    def test_mcp_standalone_license(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_cipher_license

        res_str = handle_cipher_license({
            "license_id": "LIC-MCP-01",
            "enterprise_name": "Tập đoàn Viễn thông An ninh",
            "enterprise_tax_id": "0108877665",
            "license_type": "IMPORT_EXPORT_PERMIT",
            "product_category": "PKI_SMART_CARD",
        })
        res = json.loads(res_str)
        assert res["license_id"] == "LIC-MCP-01"
        assert res["license_type"] == "IMPORT_EXPORT_PERMIT"

    def test_mcp_standalone_equipment(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_cipher_equipment

        res_str = handle_cipher_equipment({
            "equipment_id": "EQ-MCP-01",
            "serial_number": "SN-CARD-001",
            "model_name": "VN-PKI-TOKEN",
            "equipment_type": "TOKEN_CARD",
            "tamper_resistance_level": "TAMPER_RESISTANT",
            "assigned_unit": "Ban Cơ yếu TW",
        })
        res = json.loads(res_str)
        assert res["equipment_id"] == "EQ-MCP-01"
        assert res["equipment_type"] == "TOKEN_CARD"

    def test_mcp_standalone_incident(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_cipher_incident

        res_str = handle_cipher_incident({
            "incident_id": "INC-MCP-01",
            "affected_system_or_key": "SYS-MCP-01",
            "severity_level": "LOW_PROTOCOL_MISMATCH",
            "incident_description": "Không đồng bộ giao thức bắt tay mã hóa",
            "containment_actions": "Khởi động lại tiến trình daemon",
            "reporting_officer": "Đại úy Hùng",
            "resolved": True,
        })
        res = json.loads(res_str)
        assert res["incident_id"] == "INC-MCP-01"
        assert res["resolved"] is True

    def test_mcp_standalone_list_and_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_cipher_list, handle_cipher_status

        list_str = handle_cipher_list({"category": "all", "limit": 10})
        lst = json.loads(list_str)
        assert "systems" in lst
        assert "equipment" in lst

        stat_str = handle_cipher_status({})
        stat = json.loads(stat_str)
        assert "active_operational_systems" in stat
        assert "active_valid_keys" in stat

    def test_mcp_standalone_error_handling(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_cipher_equipment,
            handle_cipher_incident,
            handle_cipher_key,
            handle_cipher_license,
            handle_cipher_system,
        )

        err_s = json.loads(handle_cipher_system({}))
        assert err_s["ok"] is False
        assert "error" in err_s

        err_k = json.loads(handle_cipher_key({}))
        assert err_k["ok"] is False

        err_l = json.loads(handle_cipher_license({}))
        assert err_l["ok"] is False

        err_e = json.loads(handle_cipher_equipment({}))
        assert err_e["ok"] is False

        err_i = json.loads(handle_cipher_incident({}))
        assert err_i["ok"] is False

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")
        s_str = server._handle_cipher_system(
            system_id="SYS-CORE-01",
            system_name="Mạng Core",
            branch_type="PARTY_GOVERNMENT",
            security_level="TUYET_MAT_TOP_SECRET",
            deployment_location="Căn cứ Core",
        )
        s_data = json.loads(s_str)
        assert s_data["system_id"] == "SYS-CORE-01"

        k_str = server._handle_cipher_key(
            key_id="KEY-CORE-01",
            system_id="SYS-CORE-01",
            custodian_officer="Cán bộ Core",
            key_type="MASTER_ROOT_KEY",
        )
        k_data = json.loads(k_str)
        assert k_data["key_id"] == "KEY-CORE-01"

        l_str = server._handle_cipher_license(
            license_id="LIC-CORE-01",
            enterprise_name="DN Core",
            enterprise_tax_id="0109999999",
            license_type="PRODUCT_TRADING",
            product_category="HARDWARE_HSM",
        )
        l_data = json.loads(l_str)
        assert l_data["license_id"] == "LIC-CORE-01"

        e_str = server._handle_cipher_equipment(
            equipment_id="EQ-CORE-01",
            serial_number="SN-CORE-01",
            model_name="Model Core",
            assigned_unit="Đơn vị Core",
        )
        e_data = json.loads(e_str)
        assert e_data["equipment_id"] == "EQ-CORE-01"

        i_str = server._handle_cipher_incident(
            incident_id="INC-CORE-01",
            affected_system_or_key="SYS-CORE-01",
            incident_description="Sự cố Core",
            containment_actions="Xử lý Core",
            reporting_officer="Sĩ quan Core",
        )
        i_data = json.loads(i_str)
        assert i_data["incident_id"] == "INC-CORE-01"

        lst_str = server._handle_cipher_list(category="all")
        lst_data = json.loads(lst_str)
        assert len(lst_data["systems"]) >= 1

        stat_str = server._handle_cipher_status()
        stat_data = json.loads(stat_str)
        assert stat_data["active_operational_systems"] >= 1

    def test_scripts_mcp_server_core_handlers_parity(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        expected_tools = [
            "mekong_cipher_system",
            "mekong_cipher_key",
            "mekong_cipher_license",
            "mekong_cipher_equipment",
            "mekong_cipher_incident",
            "mekong_cipher_list",
            "mekong_cipher_status",
            "cipher_system",
            "cipher_key",
            "cipher_license",
            "cipher_equipment",
            "cipher_incident",
            "cipher_list",
            "cipher_status",
        ]
        for tool in expected_tools:
            assert tool in CORE_HANDLERS, f"Missing {tool} in scripts.mcp_server.CORE_HANDLERS"
            assert callable(CORE_HANDLERS[tool]), f"{tool} handler is not callable"

    def test_scripts_mcp_server_tools_spec(self) -> None:
        from scripts.mcp_server import CORE_TOOLS_SPEC

        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected_spec_tools = [
            "mekong_cipher_system",
            "mekong_cipher_key",
            "mekong_cipher_license",
            "mekong_cipher_equipment",
            "mekong_cipher_incident",
            "mekong_cipher_list",
            "mekong_cipher_status",
        ]
        for tool in expected_spec_tools:
            assert tool in spec_names, f"Missing {tool} in scripts.mcp_server.CORE_TOOLS_SPEC"


class TestCipherEdgeCases:
    def test_all_branches_supported(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        for i, branch in enumerate(sorted(VALID_BRANCH_TYPES)):
            res = engine.register_system(
                system_id=f"SYS-BRANCH-{i}",
                system_name=f"Hệ thống Branch {i}",
                branch_type=branch,
                security_level="TUYET_MAT_TOP_SECRET",
                deployment_location="Căn cứ",
            )
            assert res["branch_type"] == branch

    def test_all_security_levels_supported(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        for i, level in enumerate(sorted(VALID_SECURITY_LEVELS)):
            res = engine.register_system(
                system_id=f"SYS-LEVEL-{i}",
                system_name=f"Hệ thống Level {i}",
                branch_type="PARTY_GOVERNMENT",
                security_level=level,
                deployment_location="Căn cứ",
            )
            assert res["security_level"] == level

    def test_all_key_types_supported(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        for i, ktype in enumerate(sorted(VALID_KEY_TYPES)):
            res = engine.issue_key(
                key_id=f"KEY-TYPE-{i}",
                system_id="SYS-01",
                key_type=ktype,
                custodian_officer="Cán bộ",
            )
            assert res["key_type"] == ktype

    def test_all_license_types_supported(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        for i, ltype in enumerate(sorted(VALID_LICENSE_TYPES)):
            res = engine.register_civil_license(
                license_id=f"LIC-TYPE-{i}",
                enterprise_name=f"DN {i}",
                enterprise_tax_id=f"01000{i}",
                license_type=ltype,
                product_category="HARDWARE_HSM",
            )
            assert res["license_type"] == ltype

    def test_all_product_categories_supported(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        for i, cat in enumerate(sorted(VALID_PRODUCT_CATEGORIES)):
            res = engine.register_civil_license(
                license_id=f"LIC-CAT-{i}",
                enterprise_name=f"DN Cat {i}",
                enterprise_tax_id=f"02000{i}",
                license_type="PRODUCT_TRADING",
                product_category=cat,
            )
            assert res["product_category"] == cat

    def test_all_equipment_types_supported(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        for i, eq_type in enumerate(sorted(VALID_EQUIPMENT_TYPES)):
            res = engine.register_equipment(
                equipment_id=f"EQ-TYPE-{i}",
                serial_number=f"SN-{i}",
                model_name=f"Model-{i}",
                equipment_type=eq_type,
                tamper_resistance_level="PHYSICAL_ZEROIZE_SENSITIVE",
                assigned_unit="Đơn vị",
            )
            assert res["equipment_type"] == eq_type

    def test_all_tamper_levels_supported(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        for i, tamper in enumerate(sorted(VALID_TAMPER_LEVELS)):
            res = engine.register_equipment(
                equipment_id=f"EQ-TAMPER-{i}",
                serial_number=f"SN-T-{i}",
                model_name=f"Model-T-{i}",
                equipment_type="HSM_APPLIANCE",
                tamper_resistance_level=tamper,
                assigned_unit="Đơn vị",
            )
            assert res["tamper_resistance_level"] == tamper

    def test_all_severity_levels_supported(self, temp_db: str) -> None:
        engine = CipherEngine(db_path=temp_db)
        for i, sev in enumerate(sorted(VALID_SEVERITY_LEVELS)):
            res = engine.report_incident(
                incident_id=f"INC-SEV-{i}",
                affected_system_or_key="SYS-01",
                severity_level=sev,
                incident_description="Mô tả",
                containment_actions="Hành động",
                reporting_officer="Cán bộ",
            )
            assert res["severity_level"] == sev
