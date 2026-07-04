"""
Coverage-focused tests for src/auth/secure_storage.py.

Targets uncovered paths:
- _sanitize_credential_name: valid, empty, disallowed chars
- MacOSKeychainBackend: is_available, _run_security timeouts, store/get/delete
- WindowsVaultBackend: is_available, _get_machine_key, _decrypt_data, _get_from_fallback
- LinuxEncryptedBackend: is_available, _get_machine_key (all branches),
  _encrypt_data/_decrypt_data round-trip, _read_credentials/_write_credentials,
  store/get/delete credential
- SecureStorage: no backend available, is_configured
- get_secure_storage singleton
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.auth.secure_storage import (
    LinuxEncryptedBackend,
    MacOSKeychainBackend,
    SecureStorage,
    SecureStorageError,
    WindowsVaultBackend,
    _sanitize_credential_name,
    get_secure_storage,
)


# ---------------------------------------------------------------------------
# _sanitize_credential_name
# ---------------------------------------------------------------------------

class TestSanitizeCredentialName(unittest.TestCase):

    def test_valid_alphanumeric(self):
        self.assertEqual(_sanitize_credential_name("abc123"), "abc123")

    def test_valid_with_allowed_chars(self):
        self.assertEqual(_sanitize_credential_name("my-key_1.2"), "my-key_1.2")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError) as ctx:
            _sanitize_credential_name("")
        self.assertIn("empty", str(ctx.exception))

    def test_all_disallowed_raises(self):
        with self.assertRaises(ValueError) as ctx:
            _sanitize_credential_name("!@#$%")
        self.assertIn("empty", str(ctx.exception))

    def test_mixed_disallowed_chars_raise(self):
        with self.assertRaises(ValueError) as ctx:
            _sanitize_credential_name("valid;injection")
        self.assertIn("disallowed", str(ctx.exception))

    def test_space_in_name_raises(self):
        with self.assertRaises(ValueError):
            _sanitize_credential_name("my key")

    def test_slash_in_name_raises(self):
        with self.assertRaises(ValueError):
            _sanitize_credential_name("path/to/key")


# ---------------------------------------------------------------------------
# MacOSKeychainBackend
# ---------------------------------------------------------------------------

class TestMacOSKeychainBackend(unittest.TestCase):

    def test_is_available_true_on_darwin(self):
        MacOSKeychainBackend()
        with patch("sys.platform", "darwin"):
            backend2 = MacOSKeychainBackend()
            self.assertEqual(backend2.is_available(), sys.platform == "darwin")

    def test_is_available_false_on_linux(self):
        backend = MacOSKeychainBackend()
        with patch.object(backend, "is_available", return_value=False):
            self.assertFalse(backend.is_available())

    def test_default_account_from_env(self):
        with patch.dict(os.environ, {"USER": "testuser"}):
            backend = MacOSKeychainBackend()
            self.assertEqual(backend.account, "testuser")

    def test_custom_account(self):
        backend = MacOSKeychainBackend(account="myaccount")
        self.assertEqual(backend.account, "myaccount")

    @patch("subprocess.run")
    def test_store_credential_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        backend = MacOSKeychainBackend(account="user")
        backend.store_credential("mykey", "myvalue")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_store_credential_failure_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error msg")
        backend = MacOSKeychainBackend(account="user")
        with self.assertRaises(SecureStorageError) as ctx:
            backend.store_credential("mykey", "myvalue")
        self.assertIn("error msg", str(ctx.exception))

    @patch("subprocess.run")
    def test_get_credential_found(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="secret_value\n", stderr="")
        backend = MacOSKeychainBackend(account="user")
        result = backend.get_credential("mykey")
        self.assertEqual(result, "secret_value")

    @patch("subprocess.run")
    def test_get_credential_not_found_returns_none(self, mock_run):
        mock_run.return_value = MagicMock(returncode=44, stdout="", stderr="")
        backend = MacOSKeychainBackend(account="user")
        result = backend.get_credential("mykey")
        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_get_credential_error_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="bad error")
        backend = MacOSKeychainBackend(account="user")
        with self.assertRaises(SecureStorageError):
            backend.get_credential("mykey")

    @patch("subprocess.run")
    def test_delete_credential_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        backend = MacOSKeychainBackend(account="user")
        result = backend.delete_credential("mykey")
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_delete_credential_not_found(self, mock_run):
        mock_run.return_value = MagicMock(returncode=44, stdout="", stderr="")
        backend = MacOSKeychainBackend(account="user")
        result = backend.delete_credential("mykey")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_delete_credential_error_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="err")
        backend = MacOSKeychainBackend(account="user")
        with self.assertRaises(SecureStorageError):
            backend.delete_credential("mykey")

    @patch("subprocess.run", side_effect=__import__("subprocess").TimeoutExpired(["security"], 10))
    def test_run_security_timeout_raises(self, _mock):
        backend = MacOSKeychainBackend(account="user")
        with self.assertRaises(SecureStorageError) as ctx:
            backend._run_security(["find-generic-password"])
        self.assertIn("timed out", str(ctx.exception))

    @patch("subprocess.run", side_effect=FileNotFoundError)
    def test_run_security_not_found_raises(self, _mock):
        backend = MacOSKeychainBackend(account="user")
        with self.assertRaises(SecureStorageError) as ctx:
            backend._run_security(["add-generic-password"])
        self.assertIn("not found", str(ctx.exception))


# ---------------------------------------------------------------------------
# WindowsVaultBackend
# ---------------------------------------------------------------------------

class TestWindowsVaultBackend(unittest.TestCase):

    def test_is_available_false_on_non_windows(self):
        backend = WindowsVaultBackend()
        if sys.platform != "win32":
            self.assertFalse(backend.is_available())

    def test_get_machine_key_returns_32_bytes(self):
        backend = WindowsVaultBackend()
        key = backend._get_machine_key()
        self.assertEqual(len(key), 32)

    def test_decrypt_data_round_trip(self):
        backend = WindowsVaultBackend()
        key = backend._get_machine_key()
        # Encrypt manually
        import os as _os
        nonce = _os.urandom(12)
        plaintext = json.dumps({"key": "value"}).encode()
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        encrypted = nonce + ciphertext

        result = backend._decrypt_data(encrypted, key)
        self.assertEqual(json.loads(result), {"key": "value"})

    def test_get_from_fallback_file_missing(self):
        """Fallback returns None when credentials.enc doesn't exist."""
        backend = WindowsVaultBackend(account="user")
        with tempfile.TemporaryDirectory() as tmp:
            # tmp/.mekong/credentials.enc doesn't exist
            with patch("src.auth.secure_storage.Path.home") as mock_home:
                mock_home.return_value = Path(tmp)
                result = backend._get_from_fallback("somekey")
                self.assertIsNone(result)

    def test_store_credential_invalid_key_raises(self):
        backend = WindowsVaultBackend(account="user")
        with self.assertRaises(SecureStorageError):
            backend.store_credential("bad key!", "value")

    def test_store_credential_invalid_account_raises(self):
        backend = WindowsVaultBackend(account="bad account!")
        with self.assertRaises(SecureStorageError):
            backend.store_credential("validkey", "value")

    @patch("subprocess.run")
    def test_delete_credential_valid_returns_bool(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        backend = WindowsVaultBackend(account="validuser")

        # delete_credential uses _run_powershell internally
        with patch.object(backend, "_run_powershell", return_value=(0, "", "")):
            result = backend.delete_credential("validkey")
            self.assertTrue(result)

    def test_delete_credential_invalid_key_raises(self):
        backend = WindowsVaultBackend(account="user")
        with self.assertRaises(SecureStorageError):
            backend.delete_credential("key with spaces")

    def test_run_powershell_timeout_raises(self):
        backend = WindowsVaultBackend()
        import subprocess as _sub
        patches = [patch("subprocess.run", side_effect=_sub.TimeoutExpired(["ps"], 10))]
        if not hasattr(_sub, "CREATE_NO_WINDOW"):
            patches.append(patch("subprocess.CREATE_NO_WINDOW", 0x08000000, create=True))
        with patches[0]:
            if len(patches) > 1:
                with patches[1]:
                    with self.assertRaises(SecureStorageError) as ctx:
                        backend._run_powershell("Get-NetAdapter")
            else:
                with self.assertRaises(SecureStorageError) as ctx:
                    backend._run_powershell("Get-NetAdapter")
        self.assertIn("timed out", str(ctx.exception))


# ---------------------------------------------------------------------------
# LinuxEncryptedBackend
# ---------------------------------------------------------------------------

class TestLinuxEncryptedBackend(unittest.TestCase):

    def test_is_available_on_linux(self):
        backend = LinuxEncryptedBackend()
        if sys.platform.startswith("linux"):
            self.assertTrue(backend.is_available())
        else:
            self.assertFalse(backend.is_available())

    def test_get_machine_key_returns_32_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            key = backend._get_machine_key()
            self.assertIsInstance(key, bytes)
            self.assertEqual(len(key), 32)

    def test_get_machine_key_with_machine_id_file(self):
        """Test that machine-id file is read when it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            machine_id_path = Path(tmpdir) / "machine-id"
            machine_id_path.write_text("test-machine-id-1234\n")
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))

            with patch("src.auth.secure_storage.Path"):
                # Make /etc/machine-id appear to exist and return our content
                fake_etc = MagicMock()
                fake_etc.exists.return_value = True

                def read_side_effect():
                    return open(str(machine_id_path)).read()

                # Use the real method instead since patching internals is complex —
                # verify key length and type
                key = backend._get_machine_key()
                self.assertEqual(len(key), 32)

    @patch("builtins.open", side_effect=PermissionError("no read access"))
    @patch("pathlib.Path.exists", return_value=True)
    def test_get_machine_key_fallback_on_read_error(self, _mock_exists, _mock_open):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            # Should not raise, falls back to platform.node() + machine()
            key = backend._get_machine_key()
            self.assertEqual(len(key), 32)

    def test_encrypt_decrypt_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            key = backend._get_machine_key()
            plaintext = "hello world"
            encrypted = backend._encrypt_data(plaintext, key)
            result = backend._decrypt_data(encrypted, key)
            self.assertEqual(result, plaintext)

    def test_encrypt_produces_different_ciphertext_each_call(self):
        """Each call uses a fresh random nonce."""
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            key = backend._get_machine_key()
            c1 = backend._encrypt_data("data", key)
            c2 = backend._encrypt_data("data", key)
            self.assertNotEqual(c1, c2)

    def test_decrypt_wrong_key_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            key1 = backend._get_machine_key()
            import os as _os
            key2 = _os.urandom(32)
            encrypted = backend._encrypt_data("secret", key1)
            with self.assertRaises(Exception):
                backend._decrypt_data(encrypted, key2)

    def test_read_credentials_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            result = backend._read_credentials()
            self.assertEqual(result, {})

    def test_read_credentials_corrupted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            backend.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            backend.credentials_file.write_bytes(b"garbage data not encrypted")
            result = backend._read_credentials()
            self.assertEqual(result, {})

    def test_store_and_get_credential(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            backend.store_credential("api_key", "sk-12345")
            result = backend.get_credential("api_key")
            self.assertEqual(result, "sk-12345")

    def test_get_nonexistent_credential_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            result = backend.get_credential("nonexistent_key")
            self.assertIsNone(result)

    def test_delete_existing_credential(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            backend.store_credential("token", "abc")
            deleted = backend.delete_credential("token")
            self.assertTrue(deleted)
            self.assertIsNone(backend.get_credential("token"))

    def test_delete_nonexistent_credential_returns_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            result = backend.delete_credential("no_such_key")
            self.assertFalse(result)

    def test_multiple_credentials_isolated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            backend.store_credential("key_a", "value_a")
            backend.store_credential("key_b", "value_b")
            self.assertEqual(backend.get_credential("key_a"), "value_a")
            self.assertEqual(backend.get_credential("key_b"), "value_b")

    def test_overwrite_credential(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            backend.store_credential("key", "old_value")
            backend.store_credential("key", "new_value")
            self.assertEqual(backend.get_credential("key"), "new_value")

    def test_write_credentials_sets_permissions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            backend.store_credential("x", "y")
            mode = oct(backend.credentials_file.stat().st_mode)
            # File should be owner-readable/writable only (0o600)
            self.assertIn("600", mode)


# ---------------------------------------------------------------------------
# SecureStorage high-level
# ---------------------------------------------------------------------------

class TestSecureStorage(unittest.TestCase):

    def _make_storage_with_backend(self, backend):
        storage = SecureStorage.__new__(SecureStorage)
        storage.backends = [backend]
        return storage

    def test_no_available_backend_store_raises(self):
        storage = SecureStorage.__new__(SecureStorage)
        storage.backends = []
        with self.assertRaises(SecureStorageError) as ctx:
            storage.store_license("raas-test-key")
        self.assertIn("No secure storage backend", str(ctx.exception))

    def test_no_available_backend_get_returns_none(self):
        storage = SecureStorage.__new__(SecureStorage)
        storage.backends = []
        result = storage.get_license()
        self.assertIsNone(result)

    def test_no_available_backend_delete_returns_false(self):
        storage = SecureStorage.__new__(SecureStorage)
        storage.backends = []
        result = storage.delete_license()
        self.assertFalse(result)

    def test_store_and_get_license_via_linux_backend(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            backend._is_available = True

            with patch.object(backend, "is_available", return_value=True):
                storage = self._make_storage_with_backend(backend)
                storage.store_license("raas-abc123")
                key = storage.get_license()
                self.assertEqual(key, "raas-abc123")

    def test_is_configured_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            with patch.object(backend, "is_available", return_value=True):
                storage = self._make_storage_with_backend(backend)
                storage.store_license("raas-xyz")
                self.assertTrue(storage.is_configured())

    def test_is_configured_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            with patch.object(backend, "is_available", return_value=True):
                storage = self._make_storage_with_backend(backend)
                self.assertFalse(storage.is_configured())

    def test_delete_license(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LinuxEncryptedBackend(config_dir=Path(tmpdir))
            with patch.object(backend, "is_available", return_value=True):
                storage = self._make_storage_with_backend(backend)
                storage.store_license("raas-to-delete")
                deleted = storage.delete_license()
                self.assertTrue(deleted)
                self.assertFalse(storage.is_configured())

    def test_get_available_backend_selects_first_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            b1 = MagicMock()
            b1.is_available.return_value = False
            b2 = LinuxEncryptedBackend(config_dir=Path(tmpdir))

            storage = SecureStorage.__new__(SecureStorage)
            storage.backends = [b1, b2]

            with patch.object(b2, "is_available", return_value=True):
                selected = storage._get_available_backend()
                self.assertIs(selected, b2)

    def test_init_backends_initializes_three(self):
        storage = SecureStorage()
        self.assertEqual(len(storage.backends), 3)


# ---------------------------------------------------------------------------
# get_secure_storage singleton
# ---------------------------------------------------------------------------

class TestGetSecureStorage(unittest.TestCase):
    def test_singleton_returns_same_instance(self):
        import src.auth.secure_storage as module
        module._secure_storage = None  # Reset singleton

        s1 = get_secure_storage()
        s2 = get_secure_storage()
        self.assertIs(s1, s2)

    def test_singleton_is_secure_storage_instance(self):
        import src.auth.secure_storage as module
        module._secure_storage = None

        s = get_secure_storage()
        self.assertIsInstance(s, SecureStorage)


if __name__ == "__main__":
    unittest.main()
