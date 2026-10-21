# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Secure Storage Abstraction for Mekong CLI (macOS Keychain, Windows Vault, Linux AES-256-GCM)."""

import hashlib
import json
import os
import platform
import subprocess  # noqa: F401
import sys
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.auth.secure_storage_backends import (
    MacOSKeychainBackend, SecureStorageBackend, SecureStorageError,
    WindowsVaultBackend, _sanitize_credential_name,
)


class LinuxEncryptedBackend(SecureStorageBackend):
    """Linux encrypted file backend using AES-256-GCM."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or (Path.home() / ".mekong")
        self.credentials_file = self.config_dir / "credentials.enc"

    def is_available(self) -> bool:
        return sys.platform.startswith("linux")

    def _get_machine_key(self) -> bytes:
        """Generate machine-specific encryption key."""
        try:
            for p in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
                if p.exists():
                    machine_id = p.read_text().strip()
                    break
            else:
                machine_id = platform.node() + platform.machine()
        except Exception:
            machine_id = platform.node() + platform.machine()
        return hashlib.sha256(f"{machine_id}:mekong-cli-secure-storage-v1".encode()).digest()

    def _encrypt_data(self, data: str, key: bytes) -> bytes:
        """Encrypt data using AES-256-GCM."""
        nonce = os.urandom(12)
        return nonce + AESGCM(key).encrypt(nonce, data.encode(), None)

    def _decrypt_data(self, encrypted: bytes, key: bytes) -> str:
        """Decrypt data using AES-256-GCM."""
        return AESGCM(key).decrypt(encrypted[:12], encrypted[12:], None).decode()

    def _read_credentials(self) -> dict:
        """Read and decrypt credentials file."""
        if not self.credentials_file.exists():
            return {}
        try:
            encrypted_data = self.credentials_file.read_bytes()
            return json.loads(self._decrypt_data(encrypted_data, self._get_machine_key()))
        except Exception:
            return {}

    def _write_credentials(self, credentials: dict) -> None:
        """Encrypt and write credentials file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        encrypted_data = self._encrypt_data(json.dumps(credentials), self._get_machine_key())
        self.credentials_file.write_bytes(encrypted_data)
        os.chmod(self.credentials_file, 0o600)

    def store_credential(self, key: str, value: str) -> None:
        credentials = self._read_credentials()
        credentials[key] = value
        self._write_credentials(credentials)

    def get_credential(self, key: str) -> Optional[str]:
        return self._read_credentials().get(key)

    def delete_credential(self, key: str) -> bool:
        credentials = self._read_credentials()
        if key not in credentials:
            return False
        del credentials[key]
        self._write_credentials(credentials)
        return True


class SecureStorage:
    """High-level secure storage interface."""

    def __init__(self):
        self.backends: list = []
        self._init_backends()

    def _init_backends(self) -> None:
        self.backends = [MacOSKeychainBackend(), WindowsVaultBackend(), LinuxEncryptedBackend()]

    def _get_available_backend(self) -> Optional[SecureStorageBackend]:
        return next((b for b in self.backends if b.is_available()), None)

    def store_license(self, license_key: str) -> None:
        backend = self._get_available_backend()
        if not backend:
            raise SecureStorageError("No secure storage backend available")
        backend.store_credential("raas_license_key", license_key)

    def get_license(self) -> Optional[str]:
        backend = self._get_available_backend()
        return backend.get_credential("raas_license_key") if backend else None

    def delete_license(self) -> bool:
        backend = self._get_available_backend()
        return backend.delete_credential("raas_license_key") if backend else False

    def is_configured(self) -> bool:
        return self.get_license() is not None


_secure_storage: Optional[SecureStorage] = None


def get_secure_storage() -> SecureStorage:
    global _secure_storage
    if _secure_storage is None:
        _secure_storage = SecureStorage()
    return _secure_storage


__all__ = [
    "LinuxEncryptedBackend", "MacOSKeychainBackend", "SecureStorage", "SecureStorageBackend",
    "SecureStorageError", "WindowsVaultBackend", "_sanitize_credential_name", "get_secure_storage",
]
