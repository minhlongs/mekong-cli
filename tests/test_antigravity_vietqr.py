# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous VietQR / Napas 247 Instant Payment, Dynamic EMVCo QR Code & Banking Webhook Verification Engine (Phase 44)."""

from __future__ import annotations

import ast
import hashlib
import hmac
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    CORE_TOOLS_SPEC,
    handle_vietqr_banks,
    handle_vietqr_generate,
    handle_vietqr_record,
    handle_vietqr_status,
    handle_vietqr_transactions,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
from src.core.vietqr_engine import (
    VIETNAMESE_BANKS,
    VietQrEngine,
    _crc16_ccitt,
    build_emvco_payload,
)

runner = CliRunner()


class TestVietQrEngine:
    """Unit test battery for VietQrEngine core payment logic."""

    @pytest.fixture
    def engine(self, tmp_path: Path) -> VietQrEngine:
        db_file = tmp_path / "test_vietqr.db"
        return VietQrEngine(db_path=db_file)

    def test_engine_init_and_default_account(self, engine: VietQrEngine) -> None:
        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_bank_accounts"] >= 1
        assert status["default_account"]["account_number"] == "0988889999"
        assert "MBBank" in status["default_account"]["bank"]
        assert status["total_qr_generated"] == 0
        assert status["total_transactions_recorded"] == 0
        assert status["total_volume_received_vnd"] == 0
        assert status["supported_banks_count"] == len(VIETNAMESE_BANKS)

    def test_crc16_ccitt(self) -> None:
        crc = _crc16_ccitt("00020101021138240010A00000072701069704220210098888999953037045802VN6304")
        assert len(crc) == 4
        assert all(c in "0123456789ABCDEF" for c in crc)

    def test_emvco_payload_builder_static(self) -> None:
        payload = build_emvco_payload(
            bin_code="970422",
            account_number="0988889999",
            amount_vnd=0,
            memo="",
        )
        assert payload.startswith("000201")
        assert "010211" in payload  # Static QR flag
        assert "A000000727" in payload  # Napas GUID
        assert "970422" in payload  # MBBank BIN
        assert "0988889999" in payload
        assert "5303704" in payload  # Currency VND

    def test_emvco_payload_builder_dynamic(self) -> None:
        payload = build_emvco_payload(
            bin_code="970436",
            account_number="1234567890",
            amount_vnd=250000,
            memo="MK-ORDER-88",
        )
        assert payload.startswith("000201")
        assert "010212" in payload  # Dynamic QR flag
        assert "970436" in payload  # VCB BIN
        assert "5406250000" in payload  # Amount 250,000 VND
        assert "MK-ORDER-88" in payload

    def test_resolve_bank(self, engine: VietQrEngine) -> None:
        vcb = engine.resolve_bank("VCB")
        assert vcb["bin"] == "970436"

        mb = engine.resolve_bank("970422")
        assert mb["short_name"] == "MB"

        tcb = engine.resolve_bank("tcb")
        assert tcb["bin"] == "970407"

    def test_generate_qr_with_quicklink(self, engine: VietQrEngine) -> None:
        res = engine.generate_qr(
            bank="VCB",
            account_number="1012345678",
            account_name="NGUYEN VAN A",
            amount_vnd=500000,
            memo="BILL-001",
        )
        assert res["ok"] is True
        assert res["qr_id"].startswith("VQR-")
        assert res["bank_bin"] == "970436"
        assert res["bank_short"] == "VCB"
        assert res["amount_vnd"] == 500000
        assert res["memo"] == "BILL-001"
        assert res["quicklink_url"].startswith("https://img.vietqr.io/image/970436-1012345678-compact2.png")
        assert "amount=500000" in res["quicklink_url"]
        assert "BILL-001" in res["quicklink_url"]

        # Check DB persistence
        status = engine.get_status()
        assert status["total_qr_generated"] == 1
        assert len(status["recent_qr_codes"]) == 1

    def test_verify_webhook_signature(self, engine: VietQrEngine) -> None:
        body = b'{"gateway":"sepay","amount":500000,"memo":"MK-INV-101"}'
        secret = "super_secure_webhook_secret_key"
        expected_sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

        # Valid signature
        assert engine.verify_webhook_signature(body, expected_sig, secret) is True
        # Case insensitive hex check
        assert engine.verify_webhook_signature(body, expected_sig.upper(), secret) is True
        # Tampered body
        assert engine.verify_webhook_signature(b'tampered body', expected_sig, secret) is False
        # Wrong secret
        assert engine.verify_webhook_signature(body, expected_sig, "wrong_secret") is False

    def test_record_transaction_and_idempotency(self, engine: VietQrEngine) -> None:
        # First record
        tx1 = engine.record_transaction(
            bank_tx_id="FT2609001",
            amount_vnd=199000,
            memo="MEKONG-PRO",
            matched_order_id="ORD-101",
        )
        assert tx1["ok"] is True
        assert tx1["is_duplicate"] is False
        assert tx1["transaction_id"].startswith("VTX-")

        # Second record with same bank_tx_id -> idempotent duplicate detection
        tx2 = engine.record_transaction(
            bank_tx_id="FT2609001",
            amount_vnd=199000,
            memo="MEKONG-PRO",
        )
        assert tx2["ok"] is True
        assert tx2["is_duplicate"] is True
        assert tx2["transaction_id"] == tx1["transaction_id"]

        # Check telemetry
        status = engine.get_status()
        assert status["total_transactions_recorded"] == 1
        assert status["total_volume_received_vnd"] == 199000
        assert len(status["recent_transactions"]) == 1


class TestVietQrCliCommands:
    """CLI test battery for mekong vietqr subcommands."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_vietqr_overview_console(self, app) -> None:
        res = runner.invoke(app, ["vietqr"])
        assert res.exit_code == 0
        assert "VIETQR" in res.output or "Napas" in res.output

    def test_vietqr_overview_json(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert "VietQR" in data["gateway"]
        assert "default_account" in data

    def test_vietqr_generate_console(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "generate", "250000", "--memo", "DEMO-PAY", "--bank", "MB"])
        assert res.exit_code == 0
        assert "MÃ THANH TOÁN VIETQR" in res.output or "DEMO-PAY" in res.output

    def test_vietqr_generate_json(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "generate", "350000", "--memo", "INV-99", "--bank", "VCB", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["amount_vnd"] == 350000
        assert data["memo"] == "INV-99"
        assert data["bank_short"] == "VCB"
        assert "quicklink_url" in data
        assert "emvco_payload" in data

    def test_vietqr_banks_console(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "banks"])
        assert res.exit_code == 0
        assert "MB" in res.output
        assert "Vietcombank" in res.output

    def test_vietqr_banks_json(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "banks", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["total"] >= 10
        assert any(b["short_name"] == "MB" for b in data["banks"])

    def test_vietqr_record_console(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "record", "CLI-TX-101", "500000", "--memo", "SUB-RENEW"])
        assert res.exit_code == 0
        assert "GHI NHẬN ĐỐI SOÁT GIAO DỊCH" in res.output or "CLI-TX-101" in res.output

    def test_vietqr_record_json(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "record", "CLI-TX-102", "1200000", "--memo", "YEARLY-PLAN", "--order", "ORD-2026", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert data["bank_tx_id"] == "CLI-TX-102"
        assert data["amount_vnd"] == 1200000
        assert data["matched_order_id"] == "ORD-2026"

    def test_vietqr_transactions_json(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "transactions", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "transactions" in data
        assert isinstance(data["transactions"], list)

    def test_vietqr_status_json(self, app) -> None:
        res = runner.invoke(app, ["vietqr", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert data["supported_banks_count"] >= 10


class TestVietQrMcpParity:
    """Test suite ensuring parity across FastMCP and pure-Python JSON-RPC 2.0 stdio engines."""

    def test_mcp_spec_registration(self) -> None:
        names = {tool["name"] for tool in CORE_TOOLS_SPEC}
        assert "mekong_vietqr_generate" in names
        assert "mekong_vietqr_banks" in names
        assert "mekong_vietqr_transactions" in names
        assert "mekong_vietqr_record" in names
        assert "mekong_vietqr_status" in names

    def test_script_mcp_handlers(self) -> None:
        # Status
        status_raw = handle_vietqr_status({})
        status = json.loads(status_raw)
        assert status["status"] == "operational"

        # Generate
        gen_raw = handle_vietqr_generate({"amount": 100000, "memo": "MCP-TEST", "bank": "MB"})
        gen = json.loads(gen_raw)
        assert gen["ok"] is True
        assert gen["amount_vnd"] == 100000
        assert "quicklink_url" in gen

        # Banks
        banks_raw = handle_vietqr_banks({})
        banks = json.loads(banks_raw)
        assert banks["ok"] is True
        assert banks["total"] >= 10

        # Record
        rec_raw = handle_vietqr_record({"tx_id": "MCP-TX-001", "amount": 250000, "memo": "PAID"})
        rec = json.loads(rec_raw)
        assert rec["ok"] is True
        assert rec["bank_tx_id"] == "MCP-TX-001"

        # Transactions
        txs_raw = handle_vietqr_transactions({"limit": 5})
        txs = json.loads(txs_raw)
        assert txs["ok"] is True
        assert txs["total"] >= 1

    def test_core_mcp_server_handlers_and_aliases(self) -> None:
        server = MekongMcpServer(name="test-server")

        # Handlers
        status_res = json.loads(server._handle_vietqr_status())
        assert status_res["status"] == "operational"

        gen_res = json.loads(server._handle_vietqr_generate(amount=200000, memo="CORE-MCP", bank="VCB"))
        assert gen_res["ok"] is True
        assert gen_res["bank_short"] == "VCB"

        banks_res = json.loads(server._handle_vietqr_banks())
        assert banks_res["total"] >= 10

        rec_res = json.loads(server._handle_vietqr_record(bank_tx_id="CORE-TX-999", amount_vnd=750000))
        assert rec_res["ok"] is True

        txs_res = json.loads(server._handle_vietqr_transactions(limit=10))
        assert txs_res["total"] >= 1

        # Aliases
        assert server._handle_mekong_vietqr_generate == server._handle_vietqr_generate
        assert server._handle_mekong_vietqr_banks == server._handle_vietqr_banks
        assert server._handle_mekong_vietqr_transactions == server._handle_vietqr_transactions
        assert server._handle_mekong_vietqr_record == server._handle_vietqr_record
        assert server._handle_mekong_vietqr_status == server._handle_vietqr_status


class TestVietQrCoreBoundary:
    """Ensure src/core/vietqr_engine.py is pure Python standard library with zero external HTTP or vendor SDK imports."""

    def test_core_ast_imports(self) -> None:
        engine_path = Path("src/core/vietqr_engine.py")
        assert engine_path.exists()

        tree = ast.parse(engine_path.read_text(encoding="utf-8"))
        disallowed_prefixes = (
            "requests",
            "urllib3",
            "httpx",
            "aiohttp",
            "flask",
            "fastapi",
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for disallowed in disallowed_prefixes:
                        assert not alias.name.startswith(disallowed), (
                            f"Disallowed import '{alias.name}' in pure core engine {engine_path}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for disallowed in disallowed_prefixes:
                    assert not module.startswith(disallowed), (
                        f"Disallowed from-import '{module}' in pure core engine {engine_path}"
                    )
