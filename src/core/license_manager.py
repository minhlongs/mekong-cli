# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License Manager — Local License Storage & Cryptographic RAAS_LICENSE_KEY Validation."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.auth.secure_storage import get_secure_storage
from src.core.raas_license_verifier import verify_license_key

logger = logging.getLogger(__name__)


@dataclass
class LicenseData:
    """License data structure."""

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
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) >= expiry
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
        return self.tier.lower() in ("basic", "premium", "pro", "enterprise", "master", "unlimited")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LicenseData:
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            license_key=data.get("license_key", ""),
            tenant_id=data.get("tenant_id", ""),
            tier=data.get("tier", "free"),
            features=data.get("features", []),
            rate_limit=data.get("rate_limit", 60),
            max_payload_size=data.get("max_payload_size", 1048576),
            retention_days=data.get("retention_days", 30),
            expires_at=data.get("expires_at"),
            activated_at=data.get("activated_at", now),
            last_validated=data.get("last_validated", now),
        )


class LicenseManager:
    """Manager for local license storage and validation (~/.mekong/license.json)."""

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
                enc_fn = getattr(self._storage, "encrypt", None)
                if callable(enc_fn):
                    data["license_key"] = str(enc_fn(license_data.license_key))
            with open(self.license_path, "w") as f:
                json.dump(data, f, indent=2)
            self._cache = license_data
            return True
        except Exception as e:
            logger.warning("Failed to save license data: %s", e)
            return False

    def get_license(self) -> Optional[LicenseData]:
        if self._cache:
            return self._cache
        env_key = os.getenv("RAAS_LICENSE_KEY", "").strip()
        if env_key.startswith(("MEKONG-RAAS-v1.", "SOPHIA-RAAS-v1.")):
            res = verify_license_key(env_key)
            if res.valid and res.tier:
                exp_iso = (
                    datetime.fromtimestamp(res.expires_at, tz=timezone.utc).isoformat()
                    if res.expires_at
                    else None
                )
                self._cache = LicenseData(
                    license_key=env_key,
                    tenant_id=res.tenant_id or "default",
                    tier=res.tier.value,
                    features=list(res.features),
                    expires_at=exp_iso,
                )
                return self._cache
        if not self.license_path.exists():
            return None
        try:
            with open(self.license_path, "r") as f:
                data = json.load(f)
            encrypted_key = data.get("license_key", "")
            dec_fn = getattr(self._storage, "decrypt", None)
            if callable(dec_fn):
                try:
                    data["license_key"] = str(dec_fn(encrypted_key))
                except Exception:
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
        return (feature in features) if features else (feature in ("cli:basic", "cli:cook"))

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
