"""
Unit and integration tests for Vietnamese National Identification, Electronic Identity (VNeID),
Biometrics & Population Database Suite.
Governed by:
- Law on Identification 2023 (Law No. 26/2023/QH15 — Luật Căn cước 2023)
- Decree No. 69/2024/NĐ-CP & Decree No. 70/2024/NĐ-CP
- Circular No. 16/2024/TT-BCA & Circular No. 17/2024/TT-BCA
"""

from __future__ import annotations

import datetime
import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.identity_command import app as identity_app
from src.core.identity_engine import (
    VALID_BIOMETRIC_TYPES,
    VALID_CARD_STATUS,
    VALID_COLLECTION_TYPES,
    VALID_GENDERS,
    VALID_VERIFY_METHODS,
    VALID_VNEID_LEVELS,
    VALID_VNEID_STATUS,
    IdentityEngine,
    calculate_identity_card_expiry,
)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_IDENTITY_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestIdentityEngine:
    def test_calculate_identity_card_expiry_underage(self) -> None:
        # Born in 2020 (age 4 in 2024) -> expires at age 14 (2034)
        exp = calculate_identity_card_expiry("2020-05-15", "2024-07-01")
        assert exp == "2034-05-15"

    def test_calculate_identity_card_expiry_youth(self) -> None:
        # Born in 2005 (age 19 in 2024) -> expires at age 25 (2030)
        exp = calculate_identity_card_expiry("2005-08-10", "2024-07-01")
        assert exp == "2030-08-10"

    def test_calculate_identity_card_expiry_near_milestone(self) -> None:
        # Born in 2001 (age 23 in 2024, within 2 years of 25) -> valid until next milestone (age 40: 2041)
        exp = calculate_identity_card_expiry("2001-05-10", "2024-07-01")
        assert exp == "2041-05-10"

    def test_calculate_identity_card_expiry_senior(self) -> None:
        # Born in 1960 (age 64 in 2024) -> lifetime (9999-12-31)
        exp = calculate_identity_card_expiry("1960-01-01", "2024-07-01")
        assert exp == "9999-12-31"

    def test_issue_identity_card_valid(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        res = engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Số 10 Tràng Thi, Hoàn Kiếm, Hà Nội",
            ethnicity="Kinh",
            nationality="VIETNAM",
            card_status="ACTIVE_VALID",
            issue_date="2024-07-01",
        )
        assert res["card_id"] == "001090012345"
        assert res["full_name"] == "Nguyễn Văn An"
        assert res["gender"] == "MALE"
        assert res["card_status"] == "ACTIVE_VALID"
        assert res["issuing_authority"] == "C06_BCA"
        # Age at issue was 34 -> expires at 40 (2030-06-15)
        assert res["expiry_date"] == "2030-06-15"

    def test_issue_identity_card_invalid_id_not_12_digits(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="12-digit"):
            engine.issue_identity_card(
                card_id="12345",
                full_name="Trần Văn Ba",
                date_of_birth="1995-01-01",
                gender="MALE",
                place_of_birth="Đà Nẵng",
                place_of_residence="Hải Châu, Đà Nẵng",
            )

    def test_issue_identity_card_missing_name(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="full_name is required"):
            engine.issue_identity_card(
                card_id="001090012346",
                full_name="",
                date_of_birth="1995-01-01",
                gender="MALE",
                place_of_birth="Đà Nẵng",
                place_of_residence="Hải Châu, Đà Nẵng",
            )

    def test_issue_identity_card_invalid_dob_format(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            engine.issue_identity_card(
                card_id="001090012346",
                full_name="Trần Văn Ba",
                date_of_birth="01-01-1995",
                gender="MALE",
                place_of_birth="Đà Nẵng",
                place_of_residence="Hải Châu, Đà Nẵng",
            )

    def test_issue_identity_card_invalid_gender(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid gender"):
            engine.issue_identity_card(
                card_id="001090012346",
                full_name="Trần Văn Ba",
                date_of_birth="1995-01-01",
                gender="UNKNOWN",
                place_of_birth="Đà Nẵng",
                place_of_residence="Hải Châu, Đà Nẵng",
            )

    def test_issue_identity_card_invalid_status(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid card_status"):
            engine.issue_identity_card(
                card_id="001090012346",
                full_name="Trần Văn Ba",
                date_of_birth="1995-01-01",
                gender="MALE",
                place_of_birth="Đà Nẵng",
                place_of_residence="Hải Châu, Đà Nẵng",
                card_status="NON_EXISTENT_STATUS",
            )

    def test_issue_identity_card_duplicate_error(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.issue_identity_card(
                card_id="001090012345",
                full_name="Nguyễn Văn An Khác",
                date_of_birth="1990-06-15",
                gender="MALE",
                place_of_birth="Hà Nội",
                place_of_residence="Hà Nội",
            )

    def test_provision_vneid_account_valid(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        res = engine.provision_vneid_account(
            card_id="001090012345",
            phone_number="0912345678",
            account_level="LEVEL_2",
            email="an.nguyen@gov.vn",
            integrated_docs=["GPLX", "BHYT", "BHXH", "MA_SO_THUE"],
            activation_status="ACTIVATED",
        )
        assert res["account_id"] == "VNEID-001090012345"
        assert res["card_id"] == "001090012345"
        assert res["account_level"] == "LEVEL_2"
        assert res["phone_number"] == "0912345678"
        assert "GPLX" in res["integrated_docs"]
        assert res["activation_status"] == "ACTIVATED"

    def test_provision_vneid_account_update_existing(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.provision_vneid_account(
            card_id="001090012345",
            phone_number="0912345678",
            account_level="LEVEL_1",
        )
        updated = engine.provision_vneid_account(
            card_id="001090012345",
            phone_number="0987654321",
            account_level="LEVEL_2",
            integrated_docs=["GPLX", "BHYT"],
        )
        assert updated["account_level"] == "LEVEL_2"
        assert updated["phone_number"] == "0987654321"
        assert updated["integrated_docs"] == ["GPLX", "BHYT"]

    def test_provision_vneid_invalid_level(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid account_level"):
            engine.provision_vneid_account(
                card_id="001090012345",
                phone_number="0912345678",
                account_level="LEVEL_99",
            )

    def test_provision_vneid_invalid_status(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid activation_status"):
            engine.provision_vneid_account(
                card_id="001090012345",
                phone_number="0912345678",
                activation_status="UNKNOWN_STATUS",
            )

    def test_enroll_biometrics_valid(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        res = engine.enroll_biometrics(
            card_id="001090012345",
            biometric_type="IRIS_SCAN",
            collection_type="MANDATORY_STATUTORY",
            raw_payload_or_template="IRIS_SAMPLE_VECTOR_XYZ",
            quality_score=98.5,
            collecting_officer_badge="BCA-C06-009",
        )
        assert res["biometric_id"] == "BIO-001090012345-IRIS_SCAN"
        assert res["biometric_type"] == "IRIS_SCAN"
        assert res["quality_score"] == 98.5
        assert len(res["data_hash"]) == 64

    def test_enroll_biometrics_invalid_type(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid biometric_type"):
            engine.enroll_biometrics(
                card_id="001090012345",
                biometric_type="RETINA_SCAN",
            )

    def test_enroll_biometrics_invalid_score(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="quality_score must be between 0.0 and 100.0"):
            engine.enroll_biometrics(
                card_id="001090012345",
                biometric_type="IRIS_SCAN",
                quality_score=150.0,
            )

    def test_issue_identity_certificate_valid(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        res = engine.issue_identity_certificate(
            full_name="Nguyễn Văn Bình",
            date_of_birth="1985-04-12",
            gender="MALE",
            place_of_origin="Campuchia (Gốc An Giang)",
            current_residence="Ấp An Lạc, Xã An Phú, Huyện An Phú, An Giang",
            cert_id="GCN-VN-2024-0001",
            validity_years=2,
            issuing_unit="CONG_AN_HUYEN_AN_PHU",
        )
        assert res["cert_id"] == "GCN-VN-2024-0001"
        assert res["full_name"] == "Nguyễn Văn Bình"
        assert res["status"] == "VALID_ACTIVE"
        assert res["issuing_unit"] == "CONG_AN_HUYEN_AN_PHU"

    def test_verify_identity_qr_valid_card(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
        )
        res = engine.verify_identity(
            card_or_cert_id="001090012345",
            verifier_agency="NGÂN HÀNG QUÂN ĐỘI (MBBANK)",
            verification_method="QR_CODE_SCAN",
        )
        assert res["is_verified"] is True
        assert res["verification_result"] == "MATCH_SUCCESS_VERIFIED"
        assert res["matched_score"] == 100.0
        assert res["document_details"]["full_name"] == "Nguyễn Văn An"

    def test_verify_identity_biometric_iris_success(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
        )
        sample = "IRIS_RAW_VECTOR_SAMPLE_999"
        engine.enroll_biometrics(
            card_id="001090012345",
            biometric_type="IRIS_SCAN",
            raw_payload_or_template=sample,
            quality_score=97.0,
        )
        res = engine.verify_identity(
            card_or_cert_id="001090012345",
            verifier_agency="SỞ GIAO DỊCH CHỨNG KHOÁN TP.HCM",
            verification_method="BIOMETRIC_MATCH_IRIS",
            biometric_sample=sample,
        )
        assert res["is_verified"] is True
        assert res["matched_score"] == 97.0

    def test_verify_identity_biometric_iris_mismatch(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
        )
        engine.enroll_biometrics(
            card_id="001090012345",
            biometric_type="IRIS_SCAN",
            raw_payload_or_template="CORRECT_IRIS_SAMPLE",
        )
        res = engine.verify_identity(
            card_or_cert_id="001090012345",
            verifier_agency="SỞ TƯ PHÁP HÀ NỘI",
            verification_method="BIOMETRIC_MATCH_IRIS",
            biometric_sample="WRONG_IRIS_SAMPLE",
        )
        assert res["is_verified"] is False
        assert res["verification_result"] == "MISMATCH_FAILED"

    def test_verify_identity_revoked_card(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
            card_status="REVOKED_INVALIDATED",
        )
        res = engine.verify_identity(
            card_or_cert_id="001090012345",
            verifier_agency="CẢNG HÀNG KHÔNG QUỐC TẾ NỘI BÀI",
            verification_method="NFC_CHIP_READ",
        )
        assert res["is_verified"] is False
        assert res["verification_result"] == "REVOKED_INVALID"

    def test_verify_identity_expired_card(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
            expiry_date="2020-01-01",
        )
        res = engine.verify_identity(
            card_or_cert_id="001090012345",
            verifier_agency="PHÒNG CÔNG CHỨNG SỐ 1 TP.HCM",
            verification_method="QR_CODE_SCAN",
        )
        assert res["is_verified"] is False
        assert res["verification_result"] == "EXPIRED_DOCUMENT"

    def test_verify_identity_nonexistent(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        res = engine.verify_identity(
            card_or_cert_id="999999999999",
            verifier_agency="CÔNG AN PHƯỜNG",
        )
        assert res["is_verified"] is False
        assert res["verification_result"] == "MISMATCH_FAILED"

    def test_list_records_and_telemetry(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
        )
        engine.provision_vneid_account(
            card_id="001090012345",
            phone_number="0912345678",
            account_level="LEVEL_2",
        )
        engine.enroll_biometrics(
            card_id="001090012345",
            biometric_type="IRIS_SCAN",
        )
        engine.issue_identity_certificate(
            full_name="Lê Văn Nam",
            date_of_birth="1980-01-01",
            gender="MALE",
            place_of_origin="Campuchia",
            current_residence="Tây Ninh",
        )
        engine.verify_identity(
            card_or_cert_id="001090012345",
            verifier_agency="TEST_BANK",
        )

        records = engine.list_records("all")
        assert len(records["cards"]) == 1
        assert len(records["vneid"]) == 1
        assert len(records["biometrics"]) == 1
        assert len(records["certificates"]) == 1
        assert len(records["audits"]) == 1

        telem = engine.get_telemetry_status()
        assert telem["total_identity_cards"] == 1
        assert telem["active_identity_cards"] == 1
        assert telem["total_vneid_accounts"] == 1
        assert telem["vneid_level2_active"] == 1
        assert telem["total_biometrics_enrolled"] == 1
        assert telem["iris_scans_enrolled"] == 1
        assert telem["total_origin_certificates"] == 1
        assert telem["total_verification_audits"] == 1
        assert telem["verification_success_rate_percent"] == 100.0


class TestIdentityCLI:
    def test_cli_default_dashboard(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(identity_app, [])
        assert result.exit_code == 0
        assert "BỘ CÔNG AN" in result.output

    def test_cli_default_dashboard_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(identity_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_identity_cards" in data

    def test_cli_card_issue(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "card",
                "--id", "001090012345",
                "--name", "Hoàng Văn Tuấn",
                "--dob", "1992-03-25",
                "--gender", "MALE",
                "--pob", "Hải Phòng",
                "--por", "Lê Chân, Hải Phòng",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully issued Identity Card" in result.output

    def test_cli_card_issue_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "card",
                "--id", "001090099999",
                "--name", "Phạm Thị Dung",
                "--dob", "1996-12-10",
                "--gender", "FEMALE",
                "--pob", "Nam Định",
                "--por", "Ý Yên, Nam Định",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["card_id"] == "001090099999"
        assert data["full_name"] == "Phạm Thị Dung"

    def test_cli_card_issue_error(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "card",
                "--id", "invalid-id",
                "--name", "Lỗi ID",
                "--dob", "1990-01-01",
                "--pob", "Pob",
                "--por", "Por",
            ],
        )
        assert result.exit_code == 1
        assert "Error issuing identity card" in result.output

    def test_cli_vneid_provision(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "vneid",
                "--id", "001090012345",
                "--phone", "0912345678",
                "--level", "LEVEL_2",
                "--docs", "GPLX,BHYT,BHXH",
            ],
        )
        assert result.exit_code == 0
        assert "VNeID Account VNEID-001090012345 configured successfully" in result.output

    def test_cli_vneid_provision_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "vneid",
                "--id", "001090012345",
                "--phone", "0912345678",
                "--level", "LEVEL_2",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["account_id"] == "VNEID-001090012345"

    def test_cli_biometric_enroll(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "biometric",
                "--id", "001090012345",
                "--type", "IRIS_SCAN",
                "--score", "99.0",
            ],
        )
        assert result.exit_code == 0
        assert "Enrolled IRIS_SCAN for Card 001090012345" in result.output

    def test_cli_biometric_enroll_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "biometric",
                "--id", "001090012345",
                "--type", "FACIAL_PORTRAIT",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["biometric_type"] == "FACIAL_PORTRAIT"

    def test_cli_cert_issue(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "cert",
                "--name", "Nguyễn Văn Kiên",
                "--dob", "1988-08-08",
                "--origin", "Campuchia",
                "--residence", "Đồng Tháp",
            ],
        )
        assert result.exit_code == 0
        assert "Issued Identity Certificate" in result.output

    def test_cli_cert_issue_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "cert",
                "--name", "Nguyễn Văn Kiên",
                "--dob", "1988-08-08",
                "--origin", "Campuchia",
                "--residence", "Đồng Tháp",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "cert_id" in data

    def test_cli_verify(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
        )
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "verify",
                "--id", "001090012345",
                "--agency", "VIETCOMBANK",
                "--method", "QR_CODE_SCAN",
            ],
        )
        assert result.exit_code == 0
        assert "MATCH_SUCCESS_VERIFIED" in result.output

    def test_cli_verify_json(self, temp_db: str) -> None:
        engine = IdentityEngine(db_path=temp_db)
        engine.issue_identity_card(
            card_id="001090012345",
            full_name="Nguyễn Văn An",
            date_of_birth="1990-06-15",
            gender="MALE",
            place_of_birth="Hà Nội",
            place_of_residence="Hà Nội",
        )
        runner = CliRunner()
        result = runner.invoke(
            identity_app,
            [
                "verify",
                "--id", "001090012345",
                "--agency", "VIETCOMBANK",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_verified"] is True

    def test_cli_list(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(identity_app, ["list"])
        assert result.exit_code == 0

    def test_cli_list_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(identity_app, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "cards" in data

    def test_cli_status(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(identity_app, ["status"])
        assert result.exit_code == 0
        assert "National Identity Telemetry" in result.output

    def test_cli_status_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(identity_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_identity_cards" in data


class TestIdentityCoreMCP:
    def test_core_mcp_handlers(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. Card
        raw_card = server._handle_identity_card(
            card_id="001090012345",
            full_name="Đặng Văn Lâm",
            date_of_birth="1993-08-13",
            gender="MALE",
            place_of_birth="Moscow, LB Nga",
            place_of_residence="Hà Nội",
        )
        res_card = json.loads(raw_card)
        assert res_card["card_id"] == "001090012345"

        # 2. VNeID
        raw_vneid = server._handle_identity_vneid(
            card_id="001090012345",
            phone_number="0912345678",
            account_level="LEVEL_2",
            integrated_docs=["GPLX", "BHYT"],
        )
        res_vneid = json.loads(raw_vneid)
        assert res_vneid["account_id"] == "VNEID-001090012345"

        # 3. Biometric
        raw_bio = server._handle_identity_biometric(
            card_id="001090012345",
            biometric_type="IRIS_SCAN",
            quality_score=96.0,
        )
        res_bio = json.loads(raw_bio)
        assert res_bio["biometric_type"] == "IRIS_SCAN"

        # 4. Certificate
        raw_cert = server._handle_identity_certificate(
            full_name="Nguyễn Văn Sơn",
            date_of_birth="1987-11-20",
            gender="MALE",
            place_of_origin="Lào",
            current_residence="Kon Tum",
        )
        res_cert = json.loads(raw_cert)
        assert "cert_id" in res_cert

        # 5. Verify
        raw_ver = server._handle_identity_verify(
            card_or_cert_id="001090012345",
            verifier_agency="VPBANK",
            verification_method="QR_CODE_SCAN",
        )
        res_ver = json.loads(raw_ver)
        assert res_ver["is_verified"] is True

        # 6. List
        raw_list = server._handle_identity_list(category="all", limit=10)
        res_list = json.loads(raw_list)
        assert "cards" in res_list

        # 7. Status
        raw_stat = server._handle_identity_status()
        res_stat = json.loads(raw_stat)
        assert res_stat["total_identity_cards"] == 1

    def test_core_mcp_aliases(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert server._handle_mekong_identity_card == server._handle_identity_card
        assert server._handle_mekong_identity_vneid == server._handle_identity_vneid
        assert server._handle_mekong_identity_biometric == server._handle_identity_biometric
        assert server._handle_mekong_identity_certificate == server._handle_identity_certificate
        assert server._handle_mekong_identity_verify == server._handle_identity_verify
        assert server._handle_mekong_identity_list == server._handle_identity_list
        assert server._handle_mekong_identity_status == server._handle_identity_status

    def test_core_mcp_error(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        raw = server._handle_identity_card(
            card_id="invalid",
            full_name="Test Error",
            date_of_birth="1990-01-01",
        )
        res = json.loads(raw)
        assert res["ok"] is False
        assert "Identity card error" in res["error"]


class TestIdentityScriptsMCP:
    def test_scripts_mcp_core_handlers_registered(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        expected = [
            "mekong_identity_card",
            "mekong_identity_vneid",
            "mekong_identity_biometric",
            "mekong_identity_certificate",
            "mekong_identity_verify",
            "mekong_identity_list",
            "mekong_identity_status",
            "identity_card",
            "identity_vneid",
            "identity_biometric",
            "identity_certificate",
            "identity_verify",
            "identity_list",
            "identity_status",
        ]
        for name in expected:
            assert name in CORE_HANDLERS, f"Missing {name} in CORE_HANDLERS"

    def test_scripts_mcp_core_tools_spec(self) -> None:
        from scripts.mcp_server import CORE_TOOLS_SPEC

        names = {tool["name"] for tool in CORE_TOOLS_SPEC}
        expected = [
            "mekong_identity_card",
            "mekong_identity_vneid",
            "mekong_identity_biometric",
            "mekong_identity_certificate",
            "mekong_identity_verify",
            "mekong_identity_list",
            "mekong_identity_status",
        ]
        for name in expected:
            assert name in names, f"Missing {name} in CORE_TOOLS_SPEC"

    def test_scripts_mcp_handle_card(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_identity_card

        raw = handle_identity_card({
            "card_id": "001090012345",
            "full_name": "Trần Văn Cường",
            "date_of_birth": "1994-05-18",
            "gender": "MALE",
            "place_of_birth": "Cần Thơ",
            "place_of_residence": "Ninh Kiều, Cần Thơ",
        })
        res = json.loads(raw)
        assert res["card_id"] == "001090012345"

    def test_scripts_mcp_handle_vneid(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_identity_vneid

        raw = handle_identity_vneid({
            "card_id": "001090012345",
            "phone_number": "0909090909",
            "account_level": "LEVEL_2",
            "integrated_docs": ["GPLX", "BHYT"],
        })
        res = json.loads(raw)
        assert res["account_id"] == "VNEID-001090012345"

    def test_scripts_mcp_handle_biometric(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_identity_biometric

        raw = handle_identity_biometric({
            "card_id": "001090012345",
            "biometric_type": "IRIS_SCAN",
            "quality_score": 95.0,
        })
        res = json.loads(raw)
        assert res["biometric_type"] == "IRIS_SCAN"

    def test_scripts_mcp_handle_certificate(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_identity_certificate

        raw = handle_identity_certificate({
            "full_name": "Lâm Văn Hải",
            "date_of_birth": "1989-10-10",
            "gender": "MALE",
            "place_of_origin": "Campuchia",
            "current_residence": "Kiên Giang",
        })
        res = json.loads(raw)
        assert "cert_id" in res

    def test_scripts_mcp_handle_verify(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_identity_card, handle_identity_verify

        handle_identity_card({
            "card_id": "001090012345",
            "full_name": "Trần Văn Cường",
            "date_of_birth": "1994-05-18",
            "place_of_birth": "Cần Thơ",
            "place_of_residence": "Cần Thơ",
        })
        raw = handle_identity_verify({
            "card_or_cert_id": "001090012345",
            "verifier_agency": "TECHCOMBANK",
            "verification_method": "QR_CODE_SCAN",
        })
        res = json.loads(raw)
        assert res["is_verified"] is True

    def test_scripts_mcp_handle_list(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_identity_list

        raw = handle_identity_list({"category": "all", "limit": 10})
        res = json.loads(raw)
        assert "cards" in res

    def test_scripts_mcp_handle_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_identity_status

        raw = handle_identity_status({})
        res = json.loads(raw)
        assert "total_identity_cards" in res

    def test_scripts_mcp_error_handling(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_identity_card

        raw = handle_identity_card({"card_id": ""})
        res = json.loads(raw)
        assert res["ok"] is False
        assert "Identity card error" in res["error"]
