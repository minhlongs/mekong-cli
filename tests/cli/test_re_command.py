"""Tests for Mekong RE CLI commands and codebase audit."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from src.cli.commands.re_command import re_app
from src.commands.re.codebase_audit import scan_duplicate_cli_registrations
from src.core.adapters.re_mcp_bridge import ReMcpBridge
from src.core.capability import InMemoryCapabilityBus

runner = CliRunner()


class TestReCommand(unittest.TestCase):
    """Test mekong re subcommands."""

    def test_codebase_audit_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            p = Path(tmp_dir)
            (p / "sample.py").write_text("import os\nprint(os.name)\n", encoding="utf-8")
            result = runner.invoke(re_app, ["codebase-audit", "--path", str(p), "--json"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('"total_files": 1', result.output)

    def test_web_re_command(self) -> None:
        result = runner.invoke(re_app, ["web", "https://api.example.com/v1"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("api.example.com", result.output)

    def test_binary_re_command(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".bin") as tmp_bin:
            tmp_bin.write(b"\x7fELF\x02\x01\x01\x00")
            tmp_bin.flush()
            result = runner.invoke(re_app, ["binary", tmp_bin.name, "--decompile"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("MEDIUM_RISK", result.output)

    def test_apk_re_command(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".apk") as tmp_apk:
            tmp_apk.write(b"PK\x03\x04")
            tmp_apk.flush()
            result = runner.invoke(re_app, ["apk", tmp_apk.name])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("JADX-AI-MCP", result.output)

    def test_protocol_re_command(self) -> None:
        result = runner.invoke(re_app, ["protocol", "--interface", "en0", "--port", "443"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("en0", result.output)

    def test_mcp_sync_command(self) -> None:
        result = runner.invoke(re_app, ["mcp-sync"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("ghidra", result.output)
        self.assertIn("radare2", result.output)

    def test_duplicate_scanner_detects_duplicates(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8") as f:
            f.write('root.add_typer(a, name="competition")\n')
            f.write('root.add_typer(b, name="other")\n')
            f.write('root.add_typer(c, name="competition")\n')
            f.flush()
            dups = scan_duplicate_cli_registrations(Path(f.name))
            self.assertEqual(len(dups), 1)
            self.assertEqual(dups[0][0], "competition")

    def test_doctor_re_flag_and_check(self) -> None:
        from src.cli.commands.doctor_command import app as doctor_app
        res1 = runner.invoke(doctor_app, ["--re", "-v"])
        self.assertEqual(res1.exit_code, 0)
        self.assertIn("RE Core ready", res1.output)

        res2 = runner.invoke(doctor_app, ["--check", "re"])
        self.assertEqual(res2.exit_code, 0)
        self.assertIn("RE Core ready", res2.output)

    def test_re_mcp_bridge_registers_tools(self) -> None:
        bus = InMemoryCapabilityBus()
        bridge = ReMcpBridge(bus)
        mock_client = MagicMock()
        mock_client.list_tools.return_value = [
            {"name": "decompile_func", "description": "Decompile function", "inputSchema": {}}
        ]
        mock_client.call_tool.return_value = {"content": ["int main() { return 0; }"], "is_error": False, "text": "int main() { return 0; }"}

        with patch("src.core.adapters.re_mcp_bridge.from_config", return_value=mock_client):
            ids = bridge.connect_server("ghidra", {"command": "ghidra-mcp"}, risk_level="MEDIUM_RISK")
            self.assertEqual(ids, ["re:mcp:ghidra:decompile_func"])
            res = bus.execute("re:mcp:ghidra:decompile_func", {"addr": "0x401000"})
            self.assertEqual(res.get("text"), "int main() { return 0; }")


if __name__ == "__main__":
    unittest.main()
