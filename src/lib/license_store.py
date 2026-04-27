"""License store: wrapper around ~/.mekong/licenses.json.

Provides lookup, status, and tier resolution for license-gating middleware.
The Polar webhook (`src/api/polar_webhook.py`) writes records to the same file.

Schema (per license_key):
    {
      "subscription_id": "sub_xxx",
      "customer_id": "cus_xxx",
      "customer_email": "user@example.com",
      "tier": "starter|growth|pro",
      "product_name": "...",
      "created_at": "2026-04-27T...",
      "status": "active|cancelled"
    }
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _default_path() -> Path:
    override = os.environ.get("LICENSE_STORE_PATH")
    if override:
        return Path(override)
    return Path.home() / ".mekong" / "licenses.json"


class LicenseStore:
    """Read-only-ish accessor for the licenses.json store."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or _default_path()

    def _load(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("license_store.load_failed", extra={"error": str(exc)})
            return {}

    def get(self, license_key: str) -> Optional[dict]:
        """Return full record for a license key, or None if not found."""
        return self._load().get(license_key)

    def is_active(self, license_key: str) -> bool:
        """True only when license exists and status == 'active'."""
        record = self.get(license_key)
        return bool(record and record.get("status") == "active")

    def tenant_id(self, license_key: str) -> Optional[str]:
        """Customer ID acts as tenant ID for credit/MCU accounting."""
        record = self.get(license_key)
        return record.get("customer_id") if record else None

    def tier(self, license_key: str) -> Optional[str]:
        record = self.get(license_key)
        return record.get("tier") if record else None


_default_store: Optional[LicenseStore] = None


def get_license_store() -> LicenseStore:
    """Module-level singleton accessor."""
    global _default_store
    if _default_store is None:
        _default_store = LicenseStore()
    return _default_store
