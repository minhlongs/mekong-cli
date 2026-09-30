"""
Test Suite for Vietnamese Notary, Legal Practice & Judicial Authentication Suite (Phase 89).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- NotaryEngine domain logic (Luật Công chứng, blocked asset registry, Luật Luật sư, Nghị định 23/2015).
- CLI commands with Rich tables and headless --json mode.
- Dual MCP server handlers (FastMCP and fallback JSON-RPC 2.0).
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.notary_engine import NotaryEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestNotaryBoundary:
    """Verifies that notary_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "notary_engine.py")
        with open(engine_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=engine_path)

        forbidden_prefixes = ("requests", "httpx", "aiohttp", "boto3", "openai", "anthropic", "google")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith(forbidden_prefixes), f"Forbidden from-import: {node.module}"


class TestNotaryEngine:
    """Tests core business logic of NotaryEngine."""

    def test_notarize_contract_compliant(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        res = engine.notarize_contract(
            contract_title="Hợp đồng chuyển nhượng QSDĐ Thảo Điền",
            notary_office="Văn phòng Công chứng Sài Gòn",
            notary_public_name="Nguyễn Văn Bình (CCV)",
            party_a="Trần Minh Tuấn",
            party_b="Lê Hoàng Oanh",
            contract_type="REAL_ESTATE_TRANSFER",
            transaction_value_vnd=3_500_000_000.0,
            asset_id="GCN-QSDD-HCM-2026-001",
        )
        assert res["status"] == "NOTARIZED_APPROVED"
        assert res["is_approved"] is True
        assert res["is_mandatory_notarization"] is True
        assert res["statutory_notary_fee_vnd"] > 0
        assert res["notary_book_number"].startswith("CC-")
        assert len(res["deficiencies"]) == 0

    def test_notarize_contract_blocked_asset(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        # First block the asset in the prevention DB
        engine.manage_blocked_asset(
            asset_id="GCN-QSDD-BLOCKED-999",
            asset_description="Căn hộ Vinhomes Central Park",
            block_reason="Kê biên theo quyết định thi hành án dân sự",
            blocking_authority="Cục THADS TP.HCM",
            is_blocked=True,
        )

        # Attempt to notarize the blocked asset
        res = engine.notarize_contract(
            contract_title="Chuyển nhượng căn hộ Vinhomes",
            notary_office="Văn phòng Công chứng Bến Nghé",
            notary_public_name="Lê Minh Tâm (CCV)",
            party_a="Nguyễn Văn A",
            party_b="Trần Thị B",
            contract_type="REAL_ESTATE_TRANSFER",
            transaction_value_vnd=5_000_000_000.0,
            asset_id="GCN-QSDD-BLOCKED-999",
        )
        assert res["status"] == "NOTARIZATION_BLOCKED"
        assert res["is_approved"] is False
        assert any("cơ sở dữ liệu ngăn chặn" in d for d in res["deficiencies"])

    def test_manage_blocked_asset_unblock(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        # Block
        res_block = engine.manage_blocked_asset(
            asset_id="ASSET-TEST-01",
            asset_description="Nhà đất Q3",
            block_reason="Tạm ngừng giao dịch",
            is_blocked=True,
        )
        assert res_block["action"] == "BLOCKED"
        assert len(engine.list_records("blocked")) == 1

        # Unblock
        res_unblock = engine.manage_blocked_asset(
            asset_id="ASSET-TEST-01",
            asset_description="Nhà đất Q3",
            block_reason="",
            is_blocked=False,
        )
        assert res_unblock["action"] == "UNBLOCKED"
        assert len(engine.list_records("blocked")) == 0

    def test_audit_legal_practice_agreement_compliant(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        res = engine.audit_legal_practice_agreement(
            law_firm_name="Công ty Luật Mekong & Cộng sự",
            attorney_name="LS. Phạm Quốc Toàn",
            bar_card_number="LS-HN-2024-8899",
            client_name="Tập đoàn Công nghệ Alpha",
            legal_matter="Tư vấn sáp nhập doanh nghiệp (M&A)",
            fee_vnd=150_000_000.0,
            has_conflict_of_interest=False,
            has_professional_insurance=True,
        )
        assert res["status"] == "COMPLIANT_RETAINER"
        assert res["is_compliant"] is True
        assert len(res["deficiencies"]) == 0
        assert res["agreement_code"].startswith("HDPL-")

    def test_audit_legal_practice_agreement_conflict_of_interest(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        res = engine.audit_legal_practice_agreement(
            law_firm_name="Văn phòng Luật sư Tranh tụng",
            attorney_name="LS. Hoàng Đức",
            bar_card_number="LS-HCM-1122",
            client_name="Bên Bị đơn",
            legal_matter="Tranh chấp tài sản",
            has_conflict_of_interest=True,
            has_professional_insurance=True,
        )
        assert res["status"] == "NON_COMPLIANT_RETAINER"
        assert res["is_compliant"] is False
        assert any("Xung đột lợi ích thân chủ" in d for d in res["deficiencies"])

    def test_audit_legal_practice_agreement_no_insurance(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        res = engine.audit_legal_practice_agreement(
            law_firm_name="Công ty Luật Chưa Mua Bảo Hiểm",
            attorney_name="LS. Vũ Nam",
            bar_card_number="LS-DN-3344",
            client_name="Khách hàng A",
            legal_matter="Tư vấn hợp đồng",
            has_conflict_of_interest=False,
            has_professional_insurance=False,
        )
        assert res["is_compliant"] is False
        assert any("chưa mua bảo hiểm trách nhiệm nghề nghiệp" in d for d in res["deficiencies"])

    def test_authenticate_document_copy_valid(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        res = engine.authenticate_document(
            document_title="Bằng Tốt nghiệp Đại học",
            auth_type="COPY_AUTHENTICATION",
            authenticating_body="UBND Phường Bến Nghé, Quận 1",
            number_of_copies=5,
            is_original_valid=True,
        )
        assert res["status"] == "AUTHENTICATED_COMPLIANT"
        assert res["statutory_fee_vnd"] == 10_000.0  # 5 copies * 2,000 VND
        assert res["auth_code"].startswith("CT-")

    def test_authenticate_document_signature_valid(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        res = engine.authenticate_document(
            document_title="Giấy ủy quyền giải quyết hồ sơ",
            auth_type="SIGNATURE_AUTHENTICATION",
            authenticating_body="Phòng Tư pháp Quận 3",
            number_of_copies=2,
            is_original_valid=True,
        )
        assert res["status"] == "AUTHENTICATED_COMPLIANT"
        assert res["statutory_fee_vnd"] == 20_000.0  # 2 signatures * 10,000 VND

    def test_authenticate_document_invalid_original(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        res = engine.authenticate_document(
            document_title="Hóa đơn có dấu hiệu cạo sửa",
            auth_type="COPY_AUTHENTICATION",
            authenticating_body="UBND Xã Tam Phước",
            number_of_copies=3,
            is_original_valid=False,
        )
        assert res["status"] == "AUTHENTICATION_REFUSED"
        assert res["statutory_fee_vnd"] == 0.0
        assert "TỪ CHỐI CHỨNG THỰC" in res["legal_conclusion"]

    def test_list_records_and_status(self, temp_db):
        engine = NotaryEngine(db_path=temp_db)
        engine.notarize_contract(
            contract_title="Hợp đồng Test List",
            notary_office="VPCC Sài Gòn",
            notary_public_name="Nguyễn Văn Bình",
            party_a="A",
            party_b="B",
        )
        engine.manage_blocked_asset(
            asset_id="ASSET-LIST-01",
            asset_description="Đất Q9",
            block_reason="Phong tỏa tài khoản",
        )
        engine.audit_legal_practice_agreement(
            law_firm_name="Firm List",
            attorney_name="Atty X",
            bar_card_number="LS-01",
            client_name="Client Y",
            legal_matter="Advisory",
        )
        engine.authenticate_document(
            document_title="Doc List",
        )

        contracts = engine.list_records("contracts")
        assert len(contracts) >= 1
        blocked = engine.list_records("blocked")
        assert len(blocked) >= 1
        agreements = engine.list_records("agreements")
        assert len(agreements) >= 1
        auths = engine.list_records("authentications")
        assert len(auths) >= 1

        status = engine.get_status()
        assert status["status"] == "HEALTHY"
        assert status["total_notarial_contracts_executed"] >= 1
        assert status["active_blocked_assets_in_registry"] >= 1
        assert status["total_legal_agreements_audited"] >= 1
        assert status["total_document_authentications"] >= 1


class TestNotaryCLI:
    """Tests CLI commands using Typer's CliRunner."""

    def test_cli_status_and_main(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["notary", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "HEALTHY"

        res_main = runner.invoke(app, ["notary"])
        assert res_main.exit_code == 0
        assert "CÔNG CHỨNG" in res_main.output

    def test_cli_contract_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "notary",
                "contract",
                "Hợp đồng Chuyển nhượng Đất CLI",
                "--office",
                "VPCC Thủ Thiêm",
                "--notary",
                "Trần Văn Công",
                "--value",
                "4000000000",
                "--asset-id",
                "GCN-CLI-TEST-001",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_approved"] is True
        assert data["status"] == "NOTARIZED_APPROVED"

    def test_cli_block_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "notary",
                "block",
                "GCN-BLOCKED-CLI-88",
                "--desc",
                "Biệt thự ven sông",
                "--reason",
                "Tạm ngừng giao dịch do tranh chấp",
                "--authority",
                "Tòa án ND TP.HCM",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["action"] == "BLOCKED"

    def test_cli_lawyer_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "notary",
                "lawyer",
                "Công ty Luật CLI Partners",
                "--attorney",
                "LS. Đỗ Hùng",
                "--client",
                "Công ty FinTech",
                "--matter",
                "Tư vấn đăng ký sở hữu trí tuệ",
                "--fee",
                "60000000",
                "--insurance",
                "--no-conflict",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_compliant"] is True
        assert data["status"] == "COMPLIANT_RETAINER"

    def test_cli_auth_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(
            app,
            [
                "notary",
                "auth",
                "Bản sao Giấy phép kinh doanh",
                "--copies",
                "10",
                "--valid",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "AUTHENTICATED_COMPLIANT"
        assert data["statutory_fee_vnd"] == 20_000.0

    def test_cli_list_cmd(self):
        app = build_app()
        runner = CliRunner()
        res = runner.invoke(app, ["notary", "list", "contracts", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestNotaryMCP:
    """Tests dual FastMCP and fallback handlers for Notary suite."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # Contract
        res_contract = json.loads(
            server._handle_notary_contract(
                contract_title="MCP Contract Test",
                transaction_value_vnd=2_000_000_000.0,
            )
        )
        assert res_contract["is_approved"] is True

        # Block
        res_block = json.loads(
            server._handle_notary_block(
                asset_id="GCN-MCP-01",
                asset_description="Đất vườn",
                block_reason="Kê biên",
                is_blocked=True,
            )
        )
        assert res_block["action"] == "BLOCKED"

        # Lawyer
        res_lawyer = json.loads(
            server._handle_notary_lawyer(
                law_firm_name="Mekong MCP Law Firm",
                client_name="Client MCP",
            )
        )
        assert res_lawyer["is_compliant"] is True

        # Auth
        res_auth = json.loads(
            server._handle_notary_auth(
                document_title="Căn cước công dân",
                number_of_copies=2,
            )
        )
        assert res_auth["status"] == "AUTHENTICATED_COMPLIANT"

        # List
        res_list = json.loads(server._handle_notary_list(category="contracts"))
        assert isinstance(res_list, list)

        # Status
        res_status = json.loads(server._handle_notary_status())
        assert res_status["status"] == "HEALTHY"

    def test_scripts_mcp_server_handlers(self):
        import scripts.mcp_server as script_mcp

        # Test dictionary registration
        assert "mekong_notary_contract" in script_mcp.CORE_HANDLERS
        assert "mekong_notary_block" in script_mcp.CORE_HANDLERS
        assert "mekong_notary_lawyer" in script_mcp.CORE_HANDLERS
        assert "mekong_notary_auth" in script_mcp.CORE_HANDLERS
        assert "mekong_notary_list" in script_mcp.CORE_HANDLERS
        assert "mekong_notary_status" in script_mcp.CORE_HANDLERS

        # Invocations
        h_contract = script_mcp.CORE_HANDLERS["mekong_notary_contract"]
        res_contract = json.loads(h_contract({"contract_title": "Script MCP Notary Test"}))
        assert "notary_book_number" in res_contract

        h_status = script_mcp.CORE_HANDLERS["mekong_notary_status"]
        res_status = json.loads(h_status({}))
        assert res_status["status"] == "HEALTHY"
