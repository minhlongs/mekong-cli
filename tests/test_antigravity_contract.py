# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Commercial Contract, E-Sign & Legal Risk Assessment Engine (Phase 51)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.contract_engine import (
    CONTRACT_TEMPLATES,
    ContractEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestContractCoreBoundary:
    """Ensure ContractEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/contract_engine.py")
        assert source_path.exists(), "contract_engine.py must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import: {pkg}"


# ---------------------------------------------------------------------------
# Engine Unit Tests
# ---------------------------------------------------------------------------


class TestContractEngine:
    """Test ContractEngine business logic, drafting, risk audit, and e-signatures."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> ContractEngine:
        db_file = tmp_path / "test_contracts.db"
        return ContractEngine(db_path=db_file)

    def test_templates_constants(self) -> None:
        assert "SOFTWARE_DEV" in CONTRACT_TEMPLATES
        assert "COMMERCIAL_SALE" in CONTRACT_TEMPLATES
        assert "NDA" in CONTRACT_TEMPLATES
        assert "DISTRIBUTION" in CONTRACT_TEMPLATES
        assert CONTRACT_TEMPLATES["SOFTWARE_DEV"]["default_penalty_pct"] == 8.0

    def test_draft_contract_software_dev(self, engine: ContractEngine) -> None:
        res = engine.draft_contract(
            template_type="SOFTWARE_DEV",
            party_a_name="Công Ty Công Nghệ Alpha",
            party_b_name="Mekong AI Solutions",
            contract_value_vnd=500_000_000.0,
            scope_summary="Phát triển hệ thống Autonomous Agent Platform",
            penalty_rate_pct=8.0,
        )
        assert res["ok"] is True
        assert res["contract_id"].startswith("CT-")
        assert "SOFTWARE_DEV" in res["contract_number"]
        assert res["party_a_name"] == "Công Ty Công Nghệ Alpha"
        assert res["contract_value_vnd"] == 500_000_000.0
        assert res["penalty_rate_pct"] == 8.0
        assert res["status"] == "DRAFTED"
        assert len(res["content_sha256"]) == 64

        # Verify persisted
        contracts = engine.list_contracts()
        assert len(contracts) == 1
        assert contracts[0]["contract_id"] == res["contract_id"]

    def test_draft_contract_invalid_template(self, engine: ContractEngine) -> None:
        res = engine.draft_contract(
            template_type="NON_EXISTENT_TEMPLATE",
            party_a_name="Bên A",
            party_b_name="Bên B",
        )
        assert res["ok"] is False
        assert "Mẫu hợp đồng không hợp lệ" in res["error"]

    def test_assess_contract_risk_penalty_breach(self, engine: ContractEngine) -> None:
        # Penalty clause exceeding 8% statutory cap
        text = "Hai bên thỏa thuận mức phạt vi phạm là 15% tổng giá trị hợp đồng nếu chậm tiến độ giao hàng."
        res = engine.assess_contract_risk(contract_text=text, penalty_pct=15.0)
        assert res["ok"] is True
        assert res["risk_level"] in ("HIGH", "MEDIUM")
        assert res["risk_score"] >= 40
        assert any(rf["clause"] == "Điều khoản Phạt vi phạm" for rf in res["red_flags"])
        assert any("vượt quá trần luật định 8%" in rf["issue"] for rf in res["red_flags"])

    def test_assess_contract_risk_missing_force_majeure(self, engine: ContractEngine) -> None:
        text = "Hợp đồng mua bán hàng hóa tiêu chuẩn. Không bao gồm các điều khoản sự kiện đặc biệt."
        res = engine.assess_contract_risk(contract_text=text, penalty_pct=8.0)
        assert res["ok"] is True
        assert any(rf["clause"] == "Điều khoản Bất khả kháng" for rf in res["red_flags"])

    def test_sign_contract_and_verify(self, engine: ContractEngine) -> None:
        # First draft a contract
        draft = engine.draft_contract(
            template_type="NDA",
            party_a_name="Tập Đoàn Mekong",
            party_b_name="Đối Tác Chiến Lược",
        )
        contract_id = draft["contract_id"]

        # Sign contract electronically
        sig_res = engine.sign_contract(
            contract_id=contract_id,
            signer_name="Nguyễn Văn A",
            signer_title="Tổng Giám Đốc",
            signer_tax_id="0101234567",
            organization_name="Tập Đoàn Mekong",
        )
        assert sig_res["ok"] is True
        assert sig_res["signature_id"].startswith("SIG-")
        assert len(sig_res["signature_hash"]) == 64
        assert sig_res["legal_status"] == "VALID_ELECTRONIC_SIGNATURE"

        # Verify contract status updated to SIGNED
        contracts = engine.list_contracts(status="SIGNED")
        assert len(contracts) == 1
        assert contracts[0]["status"] == "SIGNED"

        # Verify electronic signature
        verify_res = engine.verify_signature(signature_id=sig_res["signature_id"])
        assert verify_res["ok"] is True
        assert verify_res["is_valid"] is True
        assert verify_res["integrity_verified"] is True
        assert "CHỮ KÝ ĐIỆN TỬ HỢP LỆ" in verify_res["statutory_validity"]

    def test_verify_nonexistent_signature(self, engine: ContractEngine) -> None:
        res = engine.verify_signature(signature_id="SIG-NONEXISTENT")
        assert res["ok"] is False
        assert res["is_valid"] is False

    def test_get_status(self, engine: ContractEngine) -> None:
        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "ContractEngine"
        assert "metrics" in status
        assert "SOFTWARE_DEV" in status["available_templates"]


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestContractCLI:
    """Test Typer CLI surface for mekong contract."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_overview(self, app) -> None:
        result = runner.invoke(app, ["contract"])
        assert result.exit_code == 0
        assert "HỢP ĐỒNG THƯƠNG MẠI" in result.output

    def test_cli_overview_json(self, app) -> None:
        result = runner.invoke(app, ["contract", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["engine"] == "ContractEngine"

    def test_cli_draft(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "contract",
                "draft",
                "SOFTWARE_DEV",
                "Công Ty Alpha",
                "Công Ty Beta",
                "--value",
                "250000000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "contract_id" in data
        assert data["template_type"] == "SOFTWARE_DEV"

    def test_cli_risk_check(self, app) -> None:
        result = runner.invoke(
            app,
            [
                "contract",
                "risk-check",
                "Phạt vi phạm 12% giá trị hợp đồng và không chịu trách nhiệm trong mọi tình huống.",
                "--penalty",
                "12.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["risk_score"] > 0
        assert data["risk_level"] in ("HIGH", "MEDIUM")

    def test_cli_sign_and_verify(self, app) -> None:
        # Draft first
        draft_out = runner.invoke(
            app,
            [
                "contract",
                "draft",
                "NDA",
                "Công Ty A",
                "Công Ty B",
                "--json",
            ],
        )
        assert draft_out.exit_code == 0
        c_id = json.loads(draft_out.output)["contract_id"]

        # Sign
        sign_out = runner.invoke(
            app,
            [
                "contract",
                "sign",
                c_id,
                "Trần Văn Giám Đốc",
                "--title",
                "Giám Đốc",
                "--json",
            ],
        )
        assert sign_out.exit_code == 0
        sig_data = json.loads(sign_out.output)
        assert sig_data["ok"] is True
        sig_id = sig_data["signature_id"]

        # Verify
        verify_out = runner.invoke(
            app,
            [
                "contract",
                "verify",
                sig_id,
                "--json",
            ],
        )
        assert verify_out.exit_code == 0
        verify_data = json.loads(verify_out.output)
        assert verify_data["ok"] is True
        assert verify_data["is_valid"] is True

    def test_cli_list(self, app) -> None:
        result = runner.invoke(app, ["contract", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "contracts" in data

    def test_cli_status(self, app) -> None:
        result = runner.invoke(app, ["contract", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# MCP Server Integration Tests
# ---------------------------------------------------------------------------


class TestContractMCP:
    """Test contract tools in pure-Python and FastMCP servers."""

    def test_pure_mcp_handlers(self) -> None:
        from scripts.mcp_server import (
            CORE_HANDLERS,
            CORE_TOOLS_SPEC,
            handle_contract_draft,
            handle_contract_list,
            handle_contract_risk_check,
            handle_contract_sign,
            handle_contract_status,
            handle_contract_verify,
        )

        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_contract_draft" in tool_names
        assert "mekong_contract_risk_check" in tool_names
        assert "mekong_contract_sign" in tool_names
        assert "mekong_contract_verify" in tool_names
        assert "mekong_contract_list" in tool_names
        assert "mekong_contract_status" in tool_names

        assert "mekong_contract_draft" in CORE_HANDLERS
        assert "contract_draft" in CORE_HANDLERS

        # Draft handler
        draft_res = json.loads(
            handle_contract_draft({
                "template_type": "SOFTWARE_DEV",
                "party_a_name": "Công Ty X",
                "party_b_name": "Công Ty Y",
                "contract_value_vnd": 100000000,
            })
        )
        assert draft_res["ok"] is True
        assert "contract_id" in draft_res
        c_id = draft_res["contract_id"]

        # Risk check handler
        rk_res = json.loads(
            handle_contract_risk_check({
                "contract_text": "Phạt vi phạm 15% tổng giá trị nghĩa vụ.",
                "penalty_pct": 15.0,
            })
        )
        assert rk_res["ok"] is True
        assert rk_res["risk_score"] > 0

        # Sign handler
        sign_res = json.loads(
            handle_contract_sign({
                "contract_id": c_id,
                "signer_name": "Lê Văn Ký",
            })
        )
        assert sign_res["ok"] is True
        sig_id = sign_res["signature_id"]

        # Verify handler
        ver_res = json.loads(handle_contract_verify({"signature_id": sig_id}))
        assert ver_res["ok"] is True
        assert ver_res["is_valid"] is True

        # List handler
        list_res = json.loads(handle_contract_list({"status": "ALL"}))
        assert list_res["ok"] is True
        assert len(list_res["contracts"]) >= 1

        # Status handler
        stat_res = json.loads(handle_contract_status({}))
        assert stat_res["ok"] is True
        assert "metrics" in stat_res

    def test_core_mcp_server_handlers(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res = json.loads(
            server._handle_contract_draft(
                template_type="NDA",
                party_a_name="Bên A",
                party_b_name="Bên B",
            )
        )
        assert res["ok"] is True
        assert "contract_id" in res

        stat = json.loads(server._handle_contract_status())
        assert stat["ok"] is True
        assert "metrics" in stat
