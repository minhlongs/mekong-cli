# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS License Gate — ROIaaS Phase 2."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional, Tuple

import requests

from engine.license.license_generator import validate_license
from src.lib.raas_gate_utils import get_upgrade_message
from src.lib.raas_gate_validator import RaasGateValidator

logger = logging.getLogger(__name__)


class LicenseTier:
    FREE = "free"
    TRIAL = "trial"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseService:
    pass


PREMIUM_FEATURES: list[str] = [
    "cook", "gateway", "binh-phap", "swarm",
    "schedule", "telegram", "autonomous", "agi",
]

FREE_COMMANDS: list[str] = [
    "init", "version", "list", "search", "status",
    "config", "doctor", "help", "dash",
]


class RaasLicenseGate:
    """License gate for RaaS premium features."""

    _REMOTE_URL = "https://api.cashclaw.cc"
    _COMMAND_COSTS: dict[str, int] = {
        "init": 1, "version": 1, "list": 1, "search": 1,
        "status": 1, "config": 1, "doctor": 1, "help": 1, "dash": 1,
        "cook": 3, "gateway": 3, "binh-phap": 3,
        "swarm": 5, "schedule": 5, "telegram": 5, "autonomous": 5, "agi": 5,
    }

    def __init__(self, enable_remote: bool = True) -> None:
        self._enable_remote = enable_remote
        self._remote_url = self._REMOTE_URL
        self._license_key: Optional[str] = os.environ.get("RAAS_LICENSE_KEY")
        self._validator = RaasGateValidator()
        self._validated: bool = False

    @property
    def license_key(self) -> Optional[str]:
        return self._license_key

    @property
    def has_license(self) -> bool:
        return bool(self._license_key)

    def is_free_command(self, command: str) -> bool:
        return command.lower() in FREE_COMMANDS

    def is_premium_command(self, command: str) -> bool:
        return command.lower() in PREMIUM_FEATURES

    def get_command_cost(self, command: str) -> int:
        return self._COMMAND_COSTS.get(command.lower(), 3)

    def validate_license_format(self, license_key: Optional[str] = None) -> Tuple[bool, str]:
        key = license_key or self._license_key
        if not key:
            return False, "License key not set"
        if not key.startswith("raas-"):
            return False, "License key must start with 'raas-'"
        parts = key.split("-")
        if len(parts) < 4:
            return False, "expected raas-[tier]-[id]-[signature]"
        valid_tiers = {"free", "trial", "pro", "enterprise"}
        if parts[1] not in valid_tiers:
            return False, f"Invalid tier '{parts[1]}'. Valid: {sorted(valid_tiers)}"
        return True, ""

    def validate_remote(self, license_key: Optional[str] = None) -> Tuple[bool, Optional[dict], str]:
        key = license_key or self._license_key
        if not key:
            return False, None, "No license key"
        if not self._enable_remote:
            res = validate_license(key)
            info = res[1] if len(res) > 1 and isinstance(res[1], dict) else {}
            return (True, info, "") if res[0] else (False, None, res[1] if len(res) > 1 else "Local validation failed")
        try:
            r = requests.post(f"{self._remote_url}/validate", json={"license_key": key}, timeout=10)
            if r.status_code == 200:
                return True, r.json(), ""
            if r.status_code == 401:
                return False, None, "Invalid or revoked license"
            if r.status_code == 403:
                reason = r.json().get("reason", "") if r.content else ""
                return False, None, reason.capitalize() if reason else "License access denied"
            return False, None, "Rate limit exceeded" if r.status_code == 429 else f"Gateway error: {r.status_code}"
        except Exception as exc:
            logger.warning("Remote validation failed, falling back to local: %s", exc)
            res = validate_license(key)
            info = res[1] if len(res) > 1 and isinstance(res[1], dict) else {}
            return (True, info, "") if res[0] else (False, None, res[1] if len(res) > 1 else str(exc))

    def check(self, command: str) -> Tuple[bool, Optional[str]]:
        if self.is_free_command(command):
            return True, None
        if not self.has_license:
            return False, get_upgrade_message(command)
        valid, err = self.validate_license_format()
        if not valid:
            return False, f"Invalid license: {err}"
        is_valid, _, err = self.validate_remote()
        if not is_valid:
            return False, f"License validation failed: {err}"
        self._validated = True
        return True, None

    def get_license_info(self) -> dict[str, Any]:
        if not self.has_license:
            return {"status": "no_license", "upgrade_url": "https://raas.mekong.dev/pricing"}
        valid, _ = self.validate_license_format()
        if not valid:
            return {"status": "invalid"}
        tier = self._license_key.split("-")[1] if self._license_key else "unknown"
        preview = f"{self._license_key[:8]}...{self._license_key[-4:]}" if self._license_key else ""
        return {"status": "valid", "tier": tier, "key_preview": preview}


_gate_instance: Optional[RaasLicenseGate] = None


def get_license_gate(enable_remote: bool = False) -> RaasLicenseGate:
    global _gate_instance
    if _gate_instance is None:
        _gate_instance = RaasLicenseGate(enable_remote=enable_remote)
    return _gate_instance


def require_license(command: str) -> None:
    allowed, error = get_license_gate().check(command)
    if not allowed:
        print(error or "License required")
        raise SystemExit(1)


def check_license(command: str) -> bool:
    allowed, _ = get_license_gate().check(command)
    return allowed


async def record_usage(license_key: str, tier: str) -> Tuple[bool, str]:
    try:
        from engine.payments.usage_meter import UsageMeter
        return await UsageMeter().record_usage(license_key, tier)
    except ImportError:
        return True, ""


__all__ = [
    "RaasLicenseGate", "LicenseService", "LicenseTier", "PREMIUM_FEATURES",
    "FREE_COMMANDS", "get_license_gate", "require_license", "check_license",
    "record_usage", "validate_license",
]
