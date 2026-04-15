"""
Auth Credentials Mixin — Credential storage and migration for RaaSAuthClient

Handles:
- Saving/loading credentials (SecureStorage or plaintext file fallback)
- Migrating plaintext credentials to secure storage
- Ensuring credentials directory exists
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AuthCredentialsMixin:
    """Mixin for credential persistence operations."""

    def _ensure_credentials_dir(self) -> None:
        """Ensure credentials directory exists with secure permissions."""
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.credentials_path.parent, 0o700)

    def _save_credentials(self, credentials: Dict[str, Any]) -> None:
        """Save credentials to secure storage or fallback file."""
        token = credentials.get("token")
        if not token:
            return

        if self.use_secure_storage and self._secure_storage:
            try:
                self._secure_storage.store_license(token)
                return
            except Exception as e:
                logger.debug("Secure storage store_license failed, falling back to file: %s", e)

        self._ensure_credentials_dir()
        with open(self.credentials_path, "w") as f:
            json.dump(credentials, f, indent=2)
        os.chmod(self.credentials_path, 0o600)

    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from secure storage or fallback file."""
        if self.use_secure_storage and self._secure_storage:
            try:
                token = self._secure_storage.get_license()
                if token:
                    return {"token": token, "uses_secure_storage": True}
            except Exception as e:
                logger.debug("Secure storage get_license failed, falling back to file: %s", e)

        if not self.credentials_path.exists():
            return {}
        try:
            with open(self.credentials_path, "r") as f:
                data = json.load(f)
                if "token" in data:
                    data["uses_secure_storage"] = False
                return data
        except (json.JSONDecodeError, IOError):
            return {}

    def _migrate_to_secure_storage(self) -> bool:
        """
        Migrate plaintext credentials to secure storage.

        Returns:
            True if migration successful, False otherwise
        """
        if not self.use_secure_storage or not self._secure_storage:
            return False

        if self.credentials_path.exists():
            try:
                with open(self.credentials_path, "r") as f:
                    data = json.load(f)
                token = data.get("token")
                if token:
                    self._secure_storage.store_license(token)
                    os.remove(self.credentials_path)
                    return True
            except Exception as e:
                logger.debug("Credential migration to secure storage failed: %s", e)
        return False
