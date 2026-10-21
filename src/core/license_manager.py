# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""License Manager — Local License Storage & Validation."""

from __future__ import annotations
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.auth.secure_storage import get_secure_storage

logger = logging.getLogger(__name__)


@dataclass
class LicenseData:
    license_key: str
    tenant_id: str
    tier: str
    features: List[str] = field(default_factory=list)
    rate_limit: int = 60
    max_payload_size: int = 1048576
    retention_days: int = 30
    expires_at: Optional[str] = None
    activated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_validated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            return datetime.now(timezone.utc) >= datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        except ValueError:
            return False

    @property
    def days_until_expiry(self) -> Optional[int]:
        if not self.expires_at:
            return None
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return max(0, (expiry - datetime.now(timezone.utc)).days)
        except ValueError:
            return None

    @property
    def is_premium(self) -> bool:
        return self.tier.lower() in ("pro", "enterprise", "unlimited")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LicenseData:
        now_iso = datetime.now(timezone.utc).isoformat()
        return cls(
            license_key=data.get("license_key", ""), tenant_id=data.get("tenant_id", ""),
            tier=data.get("tier", "free"), features=data.get("features", []),
            rate_limit=data.get("rate_limit", 60), max_payload_size=data.get("max_payload_size", 1048576),
            retention_days=data.get("retention_days", 30), expires_at=data.get("expires_at"),
            activated_at=data.get("activated_at", now_iso), last_validated=data.get("last_validated", now_iso),
        )


class LicenseManager:
    LICENSE_FILE = "license.json"

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".mekong"
        self.license_path = self.config_dir / self.LICENSE_FILE
        self._cache: Optional[LicenseData] = None
        self._storage = get_secure_storage()

    def _ensure_config_dir(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_license(self, license_data: LicenseData) -> bool:
        try:
            self._ensure_config_dir()
            data = license_data.to_dict()
            if license_data.license_key:
                data["license_key"] = self._storage.encrypt(license_data.license_key)
            with open(self.license_path, "w") as f:
                json.dump(data, f, indent=2)
            self._cache = license_data
            return True
        except Exception as e:
            logger.warning("Failed to save license data: %s", e)
            return False

    def get_license(self) -> Optional[LicenseData]:
        if self._cache or not self.license_path.exists():
            return self._cache
        try:
            with open(self.license_path, "r") as f:
                data = json.load(f)
            encrypted_key = data.get("license_key", "")
            try:
                data["license_key"] = self._storage.decrypt(encrypted_key)
            except Exception as e:
                logger.debug("License key decryption failed, using as-is: %s", e)
                data["license_key"] = encrypted_key
            self._cache = LicenseData.from_dict(data)
            return self._cache
        except Exception as e:
            logger.warning("Failed to load license data: %s", e)
            return None

    def is_valid(self) -> bool:
        lic = self.get_license()
        return bool(lic and not lic.is_expired)

    def get_tier(self) -> str:
        lic = self.get_license()
        return lic.tier.lower() if lic else "free"

    def get_features(self) -> List[str]:
        lic = self.get_license()
        return lic.features if lic else []

    def has_feature(self, feature: str) -> bool:
        features = self.get_features()
        return (feature in ["cli:basic", "cli:cook"]) if not features else (feature in features)

    def get_rate_limit(self) -> int:
        lic = self.get_license()
        return lic.rate_limit if lic else 60

    def clear_license(self) -> bool:
        try:
            if self.license_path.exists():
                self.license_path.unlink()
            self._cache = None
            return True
        except Exception as e:
            logger.warning("Failed to clear license: %s", e)
            return False

    def update_validation_timestamp(self) -> bool:
        lic = self.get_license()
        if not lic:
            return False
        lic.last_validated = datetime.now(timezone.utc).isoformat()
        return self.save_license(lic)


_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager


def get_license_tier() -> str:
    return get_license_manager().get_tier()


def is_license_valid() -> bool:
    return get_license_manager().is_valid()


def has_feature(feature: str) -> bool:
    return get_license_manager().has_feature(feature)
