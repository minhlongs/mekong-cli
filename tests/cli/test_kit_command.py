"""Tests for AgentKit 4-Kit registry and mekong kit CLI commands."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from src.cli.commands.kit_command import kit_app
from src.core.kit_registry import SUPPORTED_TARGETS, KitRegistry
from src.core.kit_storage import OwnershipLedger

runner = CliRunner()


class TestKitCommand(unittest.TestCase):
    """Test mekong kit list, install, and export."""

    def test_list_kits_json(self) -> None:
        result = runner.invoke(kit_app, ["list", "--json"])
        self.assertEqual(result.exit_code, 0)
        data = json.loads(result.output)
        kit_ids = [k["id"] for k in data["kits"]]
        self.assertEqual(
            kit_ids,
            ["kit:re", "kit:engineer", "kit:business", "kit:marketing"],
        )
        self.assertEqual(len(data["targets"]), 8)

    def test_install_kit_tracks_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_ws, tempfile.TemporaryDirectory() as tmp_home:
            with patch("pathlib.Path.home", return_value=Path(tmp_home)):
                result = runner.invoke(
                    kit_app, ["install", "kit:re", "--workspace", tmp_ws]
                )
                self.assertEqual(result.exit_code, 0)
                ledger = OwnershipLedger(root_dir=Path(tmp_ws))
                self.assertTrue(ledger.check_integrity(".mekong/kits/re.json"))
                self.assertEqual(ledger.get_ownership(".mekong/kits/re.json"), "kit:re")

    def test_export_all_7_native_targets_plus_portable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_out:
            result = runner.invoke(
                kit_app, ["export", "kit:re", "--target", "all", "--out", tmp_out]
            )
            self.assertEqual(result.exit_code, 0)
            out_path = Path(tmp_out)
            for t in SUPPORTED_TARGETS:
                manifest_file = out_path / t / "kit-re.json"
                self.assertTrue(manifest_file.is_file(), f"Missing export for {t}")
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                self.assertEqual(manifest["kit_id"], "kit:re")
                self.assertEqual(manifest["target"], t)

    def test_registry_lookup_shorthand(self) -> None:
        reg = KitRegistry()
        self.assertIsNotNone(reg.get_kit("re"))
        self.assertIsNotNone(reg.get_kit("kit:engineer"))
        self.assertIsNone(reg.get_kit("unknown"))


if __name__ == "__main__":
    unittest.main()
