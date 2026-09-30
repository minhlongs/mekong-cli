"""
Comprehensive test battery for Vietnamese Electronic Transactions, Digital Signatures,
Trust Services & Data Messages Suite (Phase 117).
Validates statutory adherence to:
- Law on Electronic Transactions 2023 (Law No. 20/2023/QH15)
- Decree No. 130/2018/ND-CP (Digital Signatures & CA Certification)
- Decree No. 52/2024/ND-CP (CeCA Certified E-Contract Authority)
"""

import json
import uuid
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.core.etransaction_engine import ETransactionEngine
from src.cli.commands.etransaction_command import etransaction_app
from scripts.mcp_server import (
    handle_etransaction_message,
    handle_etransaction_sign,
    handle_etransaction_trust,
    handle_etransaction_contract,
    handle_etransaction_list,
    handle_etransaction_status,
)
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path: Path) -> ETransactionEngine:
    db_file = tmp_path / "test_etransaction.db"
    return ETransactionEngine(db_path=str(db_file))


# =============================================================================
# 1. Core Engine Tests
# =============================================================================

class TestETransactionEngine:
    def test_create_data_message_valid(self, temp_engine: ETransactionEngine) -> None:
        res = temp_engine.create_data_message(
            title="Biên bản Bàn giao Hạ tầng Cloud",
            content='{"server_cluster": "HCM-01", "vcpus": 128}',
            originator="Công ty Cổ phần Hạ tầng Đám mây Mekong",
            recipient="Tập đoàn Bán lẻ Alpha",
            format_type="json",
            is_original=True,
            retention_years=10,
        )
        assert res["message_id"].startswith("MSG-")
        assert res["title"] == "Biên bản Bàn giao Hạ tầng Cloud"
        assert res["originator"] == "Công ty Cổ phần Hạ tầng Đám mây Mekong"
        assert res["recipient"] == "Tập đoàn Bán lẻ Alpha"
        assert res["is_original"] is True
        assert res["is_paper_converted"] is False
        assert res["legal_validity"]["written_document_validity"] is True
        assert res["legal_validity"]["original_validity"] is True
        assert res["legal_validity"]["evidence_admissibility"] is True
        assert len(res["content_hash"]) == 64

    def test_create_data_message_invalid_inputs(self, temp_engine: ETransactionEngine) -> None:
        with pytest.raises(ValueError, match="title cannot be empty"):
            temp_engine.create_data_message(
                title="",
                content="test content",
                originator="A",
                recipient="B",
            )

        with pytest.raises(ValueError, match="content cannot be empty"):
            temp_engine.create_data_message(
                title="Title",
                content="",
                originator="A",
                recipient="B",
            )

        with pytest.raises(ValueError, match="Originator cannot be empty"):
            temp_engine.create_data_message(
                title="Title",
                content="content",
                originator="   ",
                recipient="B",
            )

        with pytest.raises(ValueError, match="Recipient cannot be empty"):
            temp_engine.create_data_message(
                title="Title",
                content="content",
                originator="A",
                recipient="",
            )

        with pytest.raises(ValueError, match="Retention period must be greater than zero"):
            temp_engine.create_data_message(
                title="Title",
                content="content",
                originator="A",
                recipient="B",
                retention_years=0,
            )

    def test_verify_data_message_integrity_intact(self, temp_engine: ETransactionEngine) -> None:
        content = "Thỏa thuận bảo mật thông tin NDA 2026"
        msg = temp_engine.create_data_message(
            title="NDA 2026",
            content=content,
            originator="Party 1",
            recipient="Party 2",
        )
        ver = temp_engine.verify_data_message(message_id=msg["message_id"])
        assert ver["integrity_verified"] is True
        assert ver["legal_assessment"]["article_9_written_validity"] is True
        assert ver["legal_assessment"]["article_10_original_validity"] is True
        assert ver["legal_assessment"]["tamper_detected"] is False

    def test_verify_data_message_tampered(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message(
            title="Hợp đồng Nguyên tắc",
            content="Điều khoản thanh toán: 30 ngày",
            originator="Party 1",
            recipient="Party 2",
        )
        # Verify against altered content
        ver = temp_engine.verify_data_message(
            message_id=msg["message_id"],
            presented_content="Điều khoản thanh toán: 90 ngày (bị sửa đổi trái phép)",
        )
        assert ver["integrity_verified"] is False
        assert ver["legal_assessment"]["tamper_detected"] is True
        assert ver["legal_assessment"]["article_9_written_validity"] is False

    def test_verify_data_message_nonexistent(self, temp_engine: ETransactionEngine) -> None:
        with pytest.raises(KeyError, match="not found"):
            temp_engine.verify_data_message("MSG-NONEXISTENT")

    def test_convert_paper_to_electronic(self, temp_engine: ETransactionEngine) -> None:
        res = temp_engine.convert_paper_to_electronic(
            paper_ref="Số 45/2026/GCN-QSDĐ ngày 10/01/2026",
            converted_by="Văn phòng Đăng ký Đất đai",
            content="Bản số hóa giấy chứng nhận quyền sử dụng đất thửa số 88 tờ bản đồ số 12",
            title="Bản số hóa GCN QSDĐ",
            recipient="Ngân hàng Vietcombank",
        )
        assert res["is_paper_converted"] is True
        assert res["is_original"] is False  # Derived electronic copy under Art 12
        assert res["originator"] == "Văn phòng Đăng ký Đất đai"

    def test_create_electronic_signature_ordinary(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Thông báo", "Nội dung", "A", "B")
        sig = temp_engine.create_electronic_signature(
            message_id=msg["message_id"],
            signer_identity="Nguyễn Văn A (OTP Xác nhận)",
            signer_role="individual_customer",
            signature_type="ORDINARY",
        )
        assert sig["signature_id"].startswith("SIG-")
        assert sig["signature_type"] == "ORDINARY"
        assert sig["is_valid"] is True

    def test_create_electronic_signature_specialized(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Quyết định Nội bộ", "Nội dung", "A", "B")
        sig = temp_engine.create_electronic_signature(
            message_id=msg["message_id"],
            signer_identity="Trần Thị B - Trưởng phòng Pháp chế",
            signer_role="department_head",
            signature_type="SPECIALIZED",
        )
        assert sig["signature_type"] == "SPECIALIZED"
        assert sig["is_valid"] is True

    def test_create_electronic_signature_qualified_valid(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Hóa đơn", "Nội dung hóa đơn", "A", "B")
        sig = temp_engine.create_electronic_signature(
            message_id=msg["message_id"],
            signer_identity="Lê Văn C - Tổng Giám đốc",
            signer_role="legal_representative",
            signature_type="QUALIFIED",
            ca_provider="VNPT-CA",
            cert_serial="5404BFA6C723810E",
            cert_valid_until="2029-12-31T23:59:59Z",
        )
        assert sig["signature_type"] == "QUALIFIED"
        assert sig["ca_provider"] == "VNPT-CA"
        assert sig["is_valid"] is True
        assert len(sig["signature_value"]) == 64

    def test_create_electronic_signature_qualified_expired(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Văn bản", "Nội dung", "A", "B")
        sig = temp_engine.create_electronic_signature(
            message_id=msg["message_id"],
            signer_identity="Người ký",
            signer_role="legal_rep",
            signature_type="QUALIFIED",
            ca_provider="Viettel-CA",
            cert_serial="123456789",
            cert_valid_until="2020-01-01T00:00:00Z",  # Past date
        )
        assert sig["is_valid"] is False
        assert "expired" in sig["verification_log"]["notes"][0].lower()

    def test_create_electronic_signature_qualified_missing_fields(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Văn bản", "Nội dung", "A", "B")
        with pytest.raises(ValueError, match="requires a licensed CA provider"):
            temp_engine.create_electronic_signature(
                message_id=msg["message_id"],
                signer_identity="Signer",
                signer_role="Role",
                signature_type="QUALIFIED",
                ca_provider="",
                cert_serial="123",
                cert_valid_until="2028-12-31T23:59:59Z",
            )

        with pytest.raises(ValueError, match="requires a digital certificate serial"):
            temp_engine.create_electronic_signature(
                message_id=msg["message_id"],
                signer_identity="Signer",
                signer_role="Role",
                signature_type="QUALIFIED",
                ca_provider="VNPT-CA",
                cert_serial="",
                cert_valid_until="2028-12-31T23:59:59Z",
            )

    def test_create_electronic_signature_invalid_type(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Văn bản", "Nội dung", "A", "B")
        with pytest.raises(ValueError, match="Invalid signature type"):
            temp_engine.create_electronic_signature(
                message_id=msg["message_id"],
                signer_identity="Signer",
                signer_role="Role",
                signature_type="UNKNOWN_SIG",
            )

    def test_verify_electronic_signature(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Biên bản", "Nội dung thỏa thuận", "A", "B")
        sig = temp_engine.create_electronic_signature(
            message_id=msg["message_id"],
            signer_identity="Signer X",
            signer_role="Director",
            signature_type="QUALIFIED",
            ca_provider="VNPT-CA",
            cert_serial="ABC-123",
            cert_valid_until="2030-01-01T00:00:00Z",
        )
        res = temp_engine.verify_electronic_signature(signature_id=sig["signature_id"])
        assert res["is_valid"] is True
        assert res["verification_breakdown"]["message_integrity_intact"] is True
        assert res["verification_breakdown"]["certificate_unexpired"] is True

    def test_issue_trust_token_timestamp(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Tài liệu số", "Payload", "A", "B")
        token = temp_engine.issue_trust_token(
            target_id=msg["message_id"],
            service_type="TIMESTAMP",
            authority_name="Vietnam National Timestamp Authority",
            license_number="BTTTT-TRUST-088/GP",
        )
        assert token["token_id"].startswith("TRU-")
        assert token["service_type"] == "TIMESTAMP"
        assert token["authority_name"] == "Vietnam National Timestamp Authority"
        assert len(token["token_signature"]) == 64

    def test_issue_trust_token_invalid_service(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Tài liệu số", "Payload", "A", "B")
        with pytest.raises(ValueError, match="Invalid trust service type"):
            temp_engine.issue_trust_token(
                target_id=msg["message_id"],
                service_type="INVALID_TYPE",
            )

    def test_create_electronic_contract_valid(self, temp_engine: ETransactionEngine) -> None:
        parties = [
            {"name": "Công ty A", "tax_id": "0100109106", "role": "Bên cung cấp"},
            {"name": "Công ty B", "tax_id": "0300123456", "role": "Bên sử dụng"},
        ]
        ctr = temp_engine.create_electronic_contract(
            contract_number="HD-2026-CLOUD-01",
            title="Hợp đồng Thuê Dịch vụ Điện toán Đám mây",
            content="Điều 1: Cung cấp hạ tầng...",
            parties=parties,
            contract_value=500000000,
            currency="VND",
        )
        assert ctr["contract_id"].startswith("CTR-")
        assert ctr["contract_number"] == "HD-2026-CLOUD-01"
        assert ctr["status"] == "PENDING_SIGNATURES"
        assert ctr["ceca_verified"] is False
        assert ctr["contract_value"] == 500000000

    def test_create_electronic_contract_invalid(self, temp_engine: ETransactionEngine) -> None:
        with pytest.raises(ValueError, match="requires at least 2 parties"):
            temp_engine.create_electronic_contract(
                contract_number="HD-01",
                title="HD",
                content="Nội dung",
                parties=[{"name": "Chỉ có 1 bên", "tax_id": "01001"}],
            )

        with pytest.raises(ValueError, match="Contract value cannot be negative"):
            temp_engine.create_electronic_contract(
                contract_number="HD-02",
                title="HD",
                content="Nội dung",
                parties=[
                    {"name": "A", "tax_id": "01"},
                    {"name": "B", "tax_id": "02"},
                ],
                contract_value=-1000,
            )

    def test_sign_electronic_contract_lifecycle(self, temp_engine: ETransactionEngine) -> None:
        parties = [
            {"name": "Công ty A", "tax_id": "0100109106", "role": "Bên A"},
            {"name": "Công ty B", "tax_id": "0300123456", "role": "Bên B"},
        ]
        ctr = temp_engine.create_electronic_contract(
            contract_number="HD-LIFECYCLE-01",
            title="Hợp đồng Thử nghiệm",
            content="Điều khoản thỏa thuận...",
            parties=parties,
        )

        # First party signs
        res1 = temp_engine.sign_electronic_contract(
            contract_id=ctr["contract_id"],
            party_name="Công ty A",
            signer_role="legal_representative",
            signature_type="QUALIFIED",
            ca_provider="VNPT-CA",
        )
        assert res1["status"] == "PENDING_SIGNATURES"
        assert res1["all_parties_signed"] is False
        assert len(res1["signed_parties"]) == 1

        # Second party signs
        res2 = temp_engine.sign_electronic_contract(
            contract_id=ctr["contract_id"],
            party_name="Công ty B",
            signer_role="legal_representative",
            signature_type="QUALIFIED",
            ca_provider="Viettel-CA",
        )
        assert res2["status"] == "FULLY_EXECUTED"
        assert res2["all_parties_signed"] is True
        assert len(res2["signed_parties"]) == 2

    def test_sign_electronic_contract_unauthorized_party(self, temp_engine: ETransactionEngine) -> None:
        parties = [
            {"name": "Công ty A", "tax_id": "01"},
            {"name": "Bên B", "tax_id": "02"},
        ]
        ctr = temp_engine.create_electronic_contract("HD-ERR", "Title", "Content", parties)
        with pytest.raises(ValueError, match="not a designated party"):
            temp_engine.sign_electronic_contract(
                contract_id=ctr["contract_id"],
                party_name="Kẻ mạo danh X",
                signer_role="hacker",
            )

    def test_certify_ceca_contract_success(self, temp_engine: ETransactionEngine) -> None:
        parties = [
            {"name": "Bên A", "tax_id": "01"},
            {"name": "Bên B", "tax_id": "02"},
        ]
        ctr = temp_engine.create_electronic_contract("HD-CECA", "Title", "Content", parties)
        temp_engine.sign_electronic_contract(ctr["contract_id"], "Bên A", "Director")
        temp_engine.sign_electronic_contract(ctr["contract_id"], "Bên B", "Director")

        ceca = temp_engine.certify_ceca_contract(
            contract_id=ctr["contract_id"],
            ceca_authority="CeCA-Vietnam-Post",
            license_number="BCT-CeCA-008/GP",
        )
        assert ceca["ceca_verified"] is True
        assert ceca["ceca_token_id"].startswith("TRU-")
        assert ceca["authority_name"] == "CeCA-Vietnam-Post"

    def test_certify_ceca_contract_not_fully_executed(self, temp_engine: ETransactionEngine) -> None:
        parties = [
            {"name": "Bên A", "tax_id": "01"},
            {"name": "Bên B", "tax_id": "02"},
        ]
        ctr = temp_engine.create_electronic_contract("HD-CECA-FAIL", "Title", "Content", parties)
        # Not signed yet
        with pytest.raises(ValueError, match="Only FULLY_EXECUTED contracts can be certified"):
            temp_engine.certify_ceca_contract(contract_id=ctr["contract_id"])

    def test_list_records_and_telemetry(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("T1", "C1", "O1", "R1")
        temp_engine.create_electronic_signature(
            msg["message_id"],
            "Signer 1",
            "Rep",
            signature_type="QUALIFIED",
            ca_provider="VNPT-CA",
            cert_serial="5404BFA6C723810E",
            cert_valid_until="2029-12-31T23:59:59Z",
        )
        temp_engine.issue_trust_token(msg["message_id"])

        records = temp_engine.list_records(record_type="all")
        assert len(records["messages"]) >= 1
        assert len(records["signatures"]) >= 1
        assert len(records["trust_tokens"]) >= 1

        status = temp_engine.get_telemetry_status()
        assert status["status"] == "HEALTHY"
        assert status["data_messages"]["total"] >= 1
        assert status["signatures"]["total"] >= 1
        assert status["signatures"]["compliance_rate_pct"] == 100.0

    def test_verify_tampered_signature_payload(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Văn bản bảo mật", "Nội dung gốc", "A", "B")
        sig = temp_engine.create_electronic_signature(
            message_id=msg["message_id"],
            signer_identity="Signer Integrity",
            signer_role="Officer",
            signature_type="QUALIFIED",
            ca_provider="VNPT-CA",
            cert_serial="CERT-999",
            cert_valid_until="2029-01-01T00:00:00Z",
        )
        # Tamper payload in DB directly
        with temp_engine._get_connection() as conn:
            conn.execute(
                "UPDATE data_messages SET content_payload = ? WHERE message_id = ?",
                ("Nội dung đã bị can thiệp sau khi ký", msg["message_id"]),
            )
        ver = temp_engine.verify_electronic_signature(sig["signature_id"])
        assert ver["is_valid"] is False
        assert ver["verification_breakdown"]["message_integrity_intact"] is False
        assert "Non-compliant / Tampered" in ver["verification_breakdown"]["law_compliance"]

    def test_convert_paper_empty_fields(self, temp_engine: ETransactionEngine) -> None:
        with pytest.raises(ValueError, match="Source paper reference cannot be empty"):
            temp_engine.convert_paper_to_electronic(
                paper_ref="",
                converted_by="UBND",
                content="Data",
                title="Title",
                recipient="Recipient",
            )
        with pytest.raises(ValueError, match="Converting agency/agent identity cannot be empty"):
            temp_engine.convert_paper_to_electronic(
                paper_ref="Ref 123",
                converted_by="",
                content="Data",
                title="Title",
                recipient="Recipient",
            )

    def test_issue_trust_token_ceca_contract(self, temp_engine: ETransactionEngine) -> None:
        parties = [{"name": "A", "tax_id": "01"}, {"name": "B", "tax_id": "02"}]
        ctr = temp_engine.create_electronic_contract("CTR-TRUST-01", "Title", "Content", parties)
        token = temp_engine.issue_trust_token(
            target_id=ctr["contract_id"],
            service_type="CECA_CONTRACT",
            authority_name="CeCA-VNPT",
            license_number="BCT-CeCA-001/GP",
        )
        assert token["token_id"].startswith("TRU-")
        assert token["service_type"] == "CECA_CONTRACT"
        assert token["authority_name"] == "CeCA-VNPT"

    def test_sign_contract_after_fully_executed(self, temp_engine: ETransactionEngine) -> None:
        parties = [{"name": "A", "tax_id": "01"}, {"name": "B", "tax_id": "02"}]
        ctr = temp_engine.create_electronic_contract("CTR-EXEC", "Title", "Content", parties)
        temp_engine.sign_electronic_contract(ctr["contract_id"], "A", "Rep")
        temp_engine.sign_electronic_contract(ctr["contract_id"], "B", "Rep")
        with pytest.raises(ValueError, match="cannot be signed in state 'FULLY_EXECUTED'"):
            temp_engine.sign_electronic_contract(ctr["contract_id"], "A", "Rep")

    def test_list_records_filtered(self, temp_engine: ETransactionEngine) -> None:
        msg = temp_engine.create_data_message("Title Filter", "Content", "A", "B")
        temp_engine.create_electronic_signature(
            msg["message_id"],
            "Signer",
            "Role",
            signature_type="SPECIALIZED",
        )
        msg_only = temp_engine.list_records(record_type="messages")
        assert "messages" in msg_only
        assert "signatures" not in msg_only

        sig_only = temp_engine.list_records(record_type="signatures")
        assert "signatures" in sig_only
        assert "messages" not in sig_only


# =============================================================================
# 2. CLI Command Tests
# =============================================================================

class TestETransactionCli:
    def test_cli_main_dashboard(self) -> None:
        res = runner.invoke(etransaction_app, [])
        assert res.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ GIAO DỊCH ĐIỆN TỬ" in res.output

    def test_cli_main_dashboard_json(self) -> None:
        res = runner.invoke(etransaction_app, ["--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"
        assert "data_messages" in data

    def test_cli_message(self) -> None:
        res = runner.invoke(
            etransaction_app,
            [
                "message",
                "Chứng từ Kế toán Số",
                "--content",
                '{"invoice_no": "INV-001", "amount": 1000000}',
                "--originator",
                "Kế toán Alpha",
                "--recipient",
                "Khách hàng Beta",
            ],
        )
        assert res.exit_code == 0
        assert "KHỞI TẠO THÔNG ĐIỆP DỮ LIỆU PHÁP LÝ THÀNH CÔNG" in res.output

    def test_cli_message_json(self) -> None:
        res = runner.invoke(
            etransaction_app,
            [
                "message",
                "Chứng từ JSON",
                "--content",
                "Nội dung payload",
                "--originator",
                "A",
                "--recipient",
                "B",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "message_id" in data
        assert data["legal_validity"]["written_document_validity"] is True

    def test_cli_verify_msg(self) -> None:
        # Create msg first via JSON
        c_res = runner.invoke(
            etransaction_app,
            ["message", "Test Msg", "--content", "Content 123", "--originator", "A", "--recipient", "B", "--json"],
        )
        msg_id = json.loads(c_res.output)["message_id"]

        v_res = runner.invoke(etransaction_app, ["verify-msg", msg_id])
        assert v_res.exit_code == 0
        assert "TOÀN VẸN (KHÔNG BỊ THAY ĐỔI)" in v_res.output

    def test_cli_verify_msg_json(self) -> None:
        c_res = runner.invoke(
            etransaction_app,
            ["message", "Test Msg", "--content", "Content 123", "--originator", "A", "--recipient", "B", "--json"],
        )
        msg_id = json.loads(c_res.output)["message_id"]

        v_res = runner.invoke(etransaction_app, ["verify-msg", msg_id, "--json"])
        assert v_res.exit_code == 0
        data = json.loads(v_res.output)
        assert data["integrity_verified"] is True

    def test_cli_convert(self) -> None:
        res = runner.invoke(
            etransaction_app,
            [
                "convert",
                "--paper-ref",
                "Số 99/GCN-2026",
                "--converted-by",
                "UBND Quận 1",
                "--content",
                "Nội dung số hóa từ giấy chứng nhận...",
                "--title",
                "Bản số hóa giấy phép kinh doanh",
                "--recipient",
                "Cục Thuế",
            ],
        )
        assert res.exit_code == 0
        assert "CHUYỂN ĐỔI VĂN BẢN GIẤY SANG ĐIỆN TỬ THÀNH CÔNG" in res.output

    def test_cli_convert_json(self) -> None:
        res = runner.invoke(
            etransaction_app,
            [
                "convert",
                "--paper-ref",
                "Số 100/GCN-2026",
                "--converted-by",
                "UBND",
                "--content",
                "Nội dung số hóa...",
                "--title",
                "Bản số hóa",
                "--recipient",
                "Sở KHĐT",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_paper_converted"] is True

    def test_cli_sign_and_verify_sig(self) -> None:
        c_res = runner.invoke(
            etransaction_app,
            ["message", "Hợp đồng lao động", "--content", "Nội dung HĐLĐ", "--originator", "HR", "--recipient", "Worker", "--json"],
        )
        msg_id = json.loads(c_res.output)["message_id"]

        s_res = runner.invoke(
            etransaction_app,
            ["sign", msg_id, "--signer", "Nguyễn Văn Giám Đốc", "--role", "CEO", "--type", "QUALIFIED", "--json"],
        )
        assert s_res.exit_code == 0
        sig_id = json.loads(s_res.output)["signature_id"]

        v_res = runner.invoke(etransaction_app, ["verify-sig", sig_id])
        assert v_res.exit_code == 0
        assert "KẾT QUẢ KIỂM TRA CHỮ KÝ SỐ" in v_res.output

    def test_cli_trust(self) -> None:
        c_res = runner.invoke(
            etransaction_app,
            ["message", "Thông điệp thời gian", "--content", "Nội dung", "--originator", "A", "--recipient", "B", "--json"],
        )
        msg_id = json.loads(c_res.output)["message_id"]

        res = runner.invoke(etransaction_app, ["trust", msg_id, "--type", "TIMESTAMP"])
        assert res.exit_code == 0
        assert "CẤP DẤU TIN CẬY / DẤU THỜI GIAN ĐIỆN TỬ THÀNH CÔNG" in res.output

    def test_cli_contract_flow(self) -> None:
        # Create contract
        c_res = runner.invoke(
            etransaction_app,
            [
                "contract",
                "--number",
                f"HD-CLI-{uuid.uuid4().hex[:6].upper()}",
                "--title",
                "Hợp đồng Mua bán Hàng hóa",
                "--content",
                "Điều khoản giao hàng và nghiệm thu...",
                "--party-a",
                "Công ty X",
                "--party-b",
                "Công ty Y",
                "--value",
                "250000000",
                "--json",
            ],
        )
        assert c_res.exit_code == 0
        ctr_id = json.loads(c_res.output)["contract_id"]

        # Sign party A
        s_a = runner.invoke(
            etransaction_app,
            ["sign-contract", ctr_id, "--party", "Công ty X", "--json"],
        )
        assert s_a.exit_code == 0
        assert json.loads(s_a.output)["all_parties_signed"] is False

        # Sign party B
        s_b = runner.invoke(
            etransaction_app,
            ["sign-contract", ctr_id, "--party", "Công ty Y", "--json"],
        )
        assert s_b.exit_code == 0
        assert json.loads(s_b.output)["all_parties_signed"] is True

        # CeCA certification
        ceca_res = runner.invoke(etransaction_app, ["ceca", ctr_id])
        assert ceca_res.exit_code == 0
        assert "CHỨNG THỰC HỢP ĐỒNG ĐIỆN TỬ CeCA THÀNH CÔNG" in ceca_res.output

    def test_cli_list_and_status(self) -> None:
        res_list = runner.invoke(etransaction_app, ["list", "--type", "all"])
        assert res_list.exit_code == 0

        res_status = runner.invoke(etransaction_app, ["status"])
        assert res_status.exit_code == 0
        assert "E-Transaction Subsystem Status:" in res_status.output


# =============================================================================
# 3. Dual MCP Parity Tests
# =============================================================================

class TestETransactionMcp:
    def test_scripts_mcp_message(self) -> None:
        payload = {
            "title": "MCP Message",
            "content": "MCP Content Payload",
            "originator": "MCP Sender",
            "recipient": "MCP Receiver",
            "format_type": "json",
            "is_original": True,
        }
        res_raw = handle_etransaction_message(payload)
        res = json.loads(res_raw)
        assert "message_id" in res
        assert res["title"] == "MCP Message"

        # Test paper conversion
        conv_payload = {
            "paper_ref": "Doc-Paper-01",
            "title": "Converted Paper",
            "content": "Paper Content",
            "originator": "Notary Office",
            "recipient": "Client",
        }
        conv_raw = handle_etransaction_message(conv_payload)
        conv = json.loads(conv_raw)
        assert conv["is_paper_converted"] is True

    def test_scripts_mcp_sign(self) -> None:
        # Create message first
        msg_raw = handle_etransaction_message({
            "title": "Msg For Sign",
            "content": "Content For Sign",
            "originator": "A",
            "recipient": "B",
        })
        msg_id = json.loads(msg_raw)["message_id"]

        sig_raw = handle_etransaction_sign({
            "message_id": msg_id,
            "signer_identity": "Signer MCP",
            "signer_role": "Director",
            "signature_type": "QUALIFIED",
            "ca_provider": "VNPT-CA",
        })
        sig = json.loads(sig_raw)
        assert sig["signature_id"].startswith("SIG-")
        assert sig["is_valid"] is True

    def test_scripts_mcp_trust(self) -> None:
        msg_raw = handle_etransaction_message({
            "title": "Msg For Trust",
            "content": "Content For Trust",
            "originator": "A",
            "recipient": "B",
        })
        msg_id = json.loads(msg_raw)["message_id"]

        trust_raw = handle_etransaction_trust({
            "target_id": msg_id,
            "service_type": "TIMESTAMP",
        })
        trust = json.loads(trust_raw)
        assert trust["token_id"].startswith("TRU-")
        assert trust["service_type"] == "TIMESTAMP"

    def test_scripts_mcp_contract(self) -> None:
        # Create
        c_raw = handle_etransaction_contract({
            "action": "create",
            "title": "MCP Contract",
            "party_a": "MCP Party A",
            "party_b": "MCP Party B",
            "contract_value": 100000000,
        })
        ctr = json.loads(c_raw)
        ctr_id = ctr["contract_id"]
        assert ctr["status"] == "PENDING_SIGNATURES"

        # Sign party A
        s_raw_a = handle_etransaction_contract({
            "action": "sign",
            "contract_id": ctr_id,
            "party_name": "MCP Party A",
        })
        assert json.loads(s_raw_a)["all_parties_signed"] is False

        # Sign party B
        s_raw_b = handle_etransaction_contract({
            "action": "sign",
            "contract_id": ctr_id,
            "party_name": "MCP Party B",
        })
        assert json.loads(s_raw_b)["all_parties_signed"] is True

        # CeCA
        ceca_raw = handle_etransaction_contract({
            "action": "ceca",
            "contract_id": ctr_id,
        })
        assert json.loads(ceca_raw)["ceca_verified"] is True

    def test_scripts_mcp_list(self) -> None:
        res_raw = handle_etransaction_list({"category": "all", "limit": 10})
        res = json.loads(res_raw)
        assert "messages" in res

    def test_scripts_mcp_status(self) -> None:
        res_raw = handle_etransaction_status({})
        res = json.loads(res_raw)
        assert res["status"] == "HEALTHY"
        assert "data_messages" in res

    def test_core_mcp_server_handlers(self) -> None:
        server = MekongMcpServer()

        # Test message handler
        msg_raw = server._handle_etransaction_message(
            title="Core MCP Msg",
            content="Content",
            originator="A",
            recipient="B",
        )
        msg = json.loads(msg_raw)
        assert msg["message_id"].startswith("MSG-")

        # Test sign handler
        sig_raw = server._handle_etransaction_sign(
            message_id=msg["message_id"],
            signer_identity="Core Signer",
        )
        sig = json.loads(sig_raw)
        assert sig["is_valid"] is True

        # Test trust handler
        trust_raw = server._handle_etransaction_trust(target_id=msg["message_id"])
        trust = json.loads(trust_raw)
        assert trust["token_id"].startswith("TRU-")

        # Test contract handler
        ctr_raw = server._handle_etransaction_contract(
            action="create",
            title="Core Contract",
            party_a="A",
            party_b="B",
        )
        ctr = json.loads(ctr_raw)
        assert ctr["status"] == "PENDING_SIGNATURES"

        # Test list handler
        list_raw = server._handle_etransaction_list(category="all", limit=5)
        assert "messages" in json.loads(list_raw)

        # Test status handler
        status_raw = server._handle_etransaction_status()
        assert json.loads(status_raw)["status"] == "HEALTHY"

        # Check aliases
        assert server._handle_mekong_etransaction_message == server._handle_etransaction_message
        assert server._handle_mekong_etransaction_sign == server._handle_etransaction_sign
        assert server._handle_mekong_etransaction_trust == server._handle_etransaction_trust
        assert server._handle_mekong_etransaction_contract == server._handle_etransaction_contract
        assert server._handle_mekong_etransaction_list == server._handle_etransaction_list
        assert server._handle_mekong_etransaction_status == server._handle_etransaction_status
