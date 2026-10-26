"""Tests for AgentKit storage standardization and file ownership."""

import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.kit_storage import (
    OwnershipLedger,
    SCHEMA_VERSION,
    get_global_mekong_dir,
    load_auth_session,
    save_auth_session,
)


class TestKitStorage(unittest.TestCase):
    """Test global ~/.mekong and auth session storage."""

    def test_global_mekong_dir_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_home:
            with patch("pathlib.Path.home", return_value=Path(tmp_home)):
                mekong_dir = get_global_mekong_dir()
                self.assertTrue(mekong_dir.is_dir())
                mode = stat.S_IMODE(mekong_dir.stat().st_mode)
                self.assertEqual(mode, 0o700)

    def test_save_and_load_auth_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_home:
            with patch("pathlib.Path.home", return_value=Path(tmp_home)):
                session_path = save_auth_session(
                    {"token": "test-sec-token", "tier": "ENTERPRISE"},
                    principal="agentkit-user",
                )
                self.assertTrue(session_path.is_file())
                mode = stat.S_IMODE(session_path.stat().st_mode)
                self.assertEqual(mode, 0o600)

                loaded = load_auth_session()
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded.get("version"), SCHEMA_VERSION)
                self.assertEqual(loaded.get("principal"), "agentkit-user")
                self.assertEqual(loaded.get("session", {}).get("tier"), "ENTERPRISE")

    def test_ownership_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_proj:
            proj_root = Path(tmp_proj)
            sample_file = proj_root / "config.json"
            sample_file.write_text('{"key": "value"}', encoding="utf-8")

            ledger = OwnershipLedger(root_dir=proj_root)
            ledger.register_file("config.json", owner="kit:re")

            self.assertEqual(ledger.get_ownership("config.json"), "kit:re")
            self.assertTrue(ledger.check_integrity("config.json"))

            # Tamper with file
            sample_file.write_text('{"key": "tampered"}', encoding="utf-8")
            self.assertFalse(ledger.check_integrity("config.json"))


if __name__ == "__main__":
    unittest.main()
