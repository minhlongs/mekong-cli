# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Secure Storage Backends — macOS Keychain and Windows Credential Vault."""

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _facade():
    return sys.modules["src.auth.secure_storage"]


class SecureStorageError(Exception):
    """Base exception for secure storage operations."""


class SecureStorageBackend(ABC):
    """Abstract base class for platform-specific secure storage backends."""

    SERVICE_NAME = "mekong-cli"

    @abstractmethod
    def store_credential(self, key: str, value: str) -> None:
        """Store a credential securely."""

    @abstractmethod
    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve a credential. Returns None if not found."""

    @abstractmethod
    def delete_credential(self, key: str) -> bool:
        """Delete a credential. Returns True if deleted."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available on current system."""


class MacOSKeychainBackend(SecureStorageBackend):
    """macOS Keychain backend using security CLI."""

    def __init__(self, account: Optional[str] = None):
        self.account = account or os.environ.get("USER", "mekong-user")

    def is_available(self) -> bool:
        return sys.platform == "darwin"

    def _run_security(self, args: list) -> Tuple[int, str, str]:
        """Run security CLI command."""
        try:
            res = subprocess.run(["security"] + args, capture_output=True, text=True, timeout=10)
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            raise SecureStorageError("Keychain operation timed out")
        except FileNotFoundError:
            raise SecureStorageError("security command not found")

    def store_credential(self, key: str, value: str) -> None:
        code, _out, err = self._run_security(["add-generic-password", "-s", self.SERVICE_NAME, "-a", self.account, "-l", key, "-w", value])
        if code != 0:
            raise SecureStorageError(f"Failed to store credential: {err.strip()}")

    def get_credential(self, key: str) -> Optional[str]:
        code, out, err = self._run_security(["find-generic-password", "-s", self.SERVICE_NAME, "-a", self.account, "-l", key, "-w"])
        if code == 44:
            return None
        if code != 0:
            raise SecureStorageError(f"Failed to retrieve credential: {err.strip()}")
        return out.strip()

    def delete_credential(self, key: str) -> bool:
        code, _out, err = self._run_security(["delete-generic-password", "-s", self.SERVICE_NAME, "-a", self.account, "-l", key])
        if code == 44:
            return False
        if code != 0:
            raise SecureStorageError(f"Failed to delete credential: {err.strip()}")
        return True


def _sanitize_credential_name(value: str) -> str:
    """Sanitize a credential name/key for safe embedding in PowerShell cmdkey args."""
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "", value)
    if not sanitized:
        raise ValueError(f"Credential name '{value}' is empty after sanitization")
    if sanitized != value:
        raise ValueError(f"Credential name '{value}' contains disallowed characters — only alphanumeric, '.', '_', '-' are permitted")
    return sanitized


class WindowsVaultBackend(SecureStorageBackend):
    """Windows Credential Vault backend using PowerShell."""

    def __init__(self, account: Optional[str] = None):
        self.account = account or os.environ.get("USERNAME", "mekong-user")

    def is_available(self) -> bool:
        return sys.platform == "win32"

    def _run_powershell(self, command: str) -> Tuple[int, str, str]:
        """Run PowerShell command."""
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            raise SecureStorageError("PowerShell operation timed out")

    def store_credential(self, key: str, value: str) -> None:
        """Store license key in Windows Credential Vault."""
        try:
            safe_key, safe_acc = _sanitize_credential_name(key), _sanitize_credential_name(self.account)
        except ValueError as exc:
            raise SecureStorageError(f"Invalid credential identifier: {exc}") from exc
        generic = f"{self.SERVICE_NAME}:{safe_key}:{safe_acc}"
        res = subprocess.run(
            ["cmdkey", f"/generic:{generic}", f"/user:{safe_acc}", f"/pass:{value}"],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode != 0:
            raise SecureStorageError(f"Failed to store credential: {res.stderr.strip()}")

    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve license key from Windows Credential Vault fallback."""
        return self._get_from_fallback(key)

    def _get_from_fallback(self, key: str) -> Optional[str]:
        """Fallback to encrypted file for Windows."""
        fallback_path = getattr(_facade(), "Path", Path).home() / ".mekong" / "credentials.enc"
        if not fallback_path.exists():
            return None
        try:
            decrypted = self._decrypt_data(fallback_path.read_bytes(), self._get_machine_key())
            return json.loads(decrypted).get(key)
        except Exception:
            return None

    def _get_machine_key(self) -> bytes:
        return hashlib.sha256((platform.machine() + platform.processor()).encode()).digest()

    def _decrypt_data(self, encrypted: bytes, key: bytes) -> str:
        return AESGCM(key).decrypt(encrypted[:12], encrypted[12:], None).decode()

    def delete_credential(self, key: str) -> bool:
        """Delete credential from Windows Credential Vault."""
        try:
            safe_key, safe_acc = _sanitize_credential_name(key), _sanitize_credential_name(self.account)
        except ValueError as exc:
            raise SecureStorageError(f"Invalid credential identifier: {exc}") from exc
        code, _out, _err = self._run_powershell(f'cmdkey /delete:"{self.SERVICE_NAME}:{safe_key}:{safe_acc}"')
        return code == 0
