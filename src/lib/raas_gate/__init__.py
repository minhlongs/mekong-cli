# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS License Gate — ROIaaS Phase 2

Provides license validation, command gating (free vs premium),
and usage metering for Mekong CLI.

Exports:
- RaasLicenseGate: main gate class
- get_license_gate: singleton accessor
- require_license: raise on invalid license
- check_license: boolean check wrapper
- LicenseService, LicenseTier, PREMIUM_FEATURES: legacy compat
- record_usage: async usage recording stub
- validate_license: gateway validation re-export
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional, Tuple

import requests

from engine.license.license_generator import validate_license
from src.lib.raas_gate_validator import RaasGateValidator
from src.lib.raas_gate_utils import get_upgrade_message

logger = logging.getLogger(__name__)


# ─── Legacy enums (backward compat) ────────────────────────────────────────────

class LicenseTier:
    """License tier enumeration."""
    FREE = "free"
    TRIAL = "trial"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseService:
    """License service descriptor (legacy compat)."""
    pass


# Commands that require a premium license
PREMIUM_FEATURES: list[str] = [
    "cook", "gateway", "binh-phap", "swarm",
    "schedule", "telegram", "autonomous", "agi",
]

# Commands available on free tier
FREE_COMMANDS: list[str] = [
    "init", "version", "list", "search", "status",
    "config", "doctor", "help", "dash",
]


# ─── Main gate class ───────────────────────────────────────────────────────────

class RaasLicenseGate:
    """License gate for RaaS premium features.

    Validates license keys against the RaaS Gateway and gates
    premium commands behind valid licenses.
    """

    _REMOTE_URL = "https://api.cashclaw.cc"

    def __init__(self, enable_remote: bool = True) -> None:
        self._enable_remote = enable_remote
        self._remote_url = self._REMOTE_URL
        self._license_key: Optional[str] = os.environ.get("RAAS_LICENSE_KEY")
        self._validator = RaasGateValidator()
        self._validated: bool = False

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def license_key(self) -> Optional[str]:
        return self._license_key

    @property
    def has_license(self) -> bool:
        return bool(self._license_key)

    # ── Command categorization ───────────────────────────────────────────────

    def is_free_command(self, command: str) -> bool:
        """Check if command is free-tier."""
        return command.lower() in FREE_COMMANDS

    def is_premium_command(self, command: str) -> bool:
        """Check if command requires premium license."""
        return command.lower() in PREMIUM_FEATURES

    # ── Command cost tiers ─────────────────────────────────────────────────

    _COMMAND_COSTS: dict[str, int] = {
        # 1 credit
        "init": 1, "version": 1, "list": 1, "search": 1,
        "status": 1, "config": 1, "doctor": 1, "help": 1, "dash": 1,
        # 3 credits
        "cook": 3, "gateway": 3, "binh-phap": 3,
        # 5 credits
        "swarm": 5, "schedule": 5, "telegram": 5, "autonomous": 5, "agi": 5,
    }

    def get_command_cost(self, command: str) -> int:
        """Return credit cost for a command (default 3 for unknown)."""
        return self._COMMAND_COSTS.get(command.lower(), 3)

    # ── Format validation ────────────────────────────────────────────────────

    def validate_license_format(self, license_key: Optional[str] = None) -> Tuple[bool, str]:
        """Validate license key format: raas-[tier]-[id]-[signature]."""
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

    # ── Remote validation ────────────────────────────────────────────────────

    def validate_remote(self, license_key: Optional[str] = None) -> Tuple[bool, Optional[dict], str]:
        """Validate license against RaaS Gateway.

        Falls back to local validation on network errors.
        """
        key = license_key or self._license_key
        if not key:
            return False, None, "No license key"

        if not self._enable_remote:
            # Local validation fallback — handle both 2-tuple (valid, error) and 3-tuple
            result = validate_license(key)
            if result[0]:
                info = result[1] if len(result) > 1 and isinstance(result[1], dict) else {}
                return True, info, ""
            err = result[1] if len(result) > 1 else "Local validation failed"
            return False, None, err

        try:
            response = requests.post(
                f"{self._remote_url}/validate",
                json={"license_key": key},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return True, data, ""
            if response.status_code == 401:
                return False, None, "Invalid or revoked license"
            if response.status_code == 403:
                reason = ""
                try:
                    reason = response.json().get("reason", "")
                except Exception:
                    pass
                if reason:
                    return False, None, reason.capitalize()
                return False, None, "License access denied"
            if response.status_code == 429:
                return False, None, "Rate limit exceeded"
            return False, None, f"Gateway error: {response.status_code}"
        except Exception as exc:
            logger.warning("Remote validation failed, falling back to local: %s", exc)
            result = validate_license(key)
            if result[0]:
                info = result[1] if len(result) > 1 and isinstance(result[1], dict) else {}
                return True, info, ""
            err = result[1] if len(result) > 1 else str(exc)
            return False, None, err

    # ── Full check ───────────────────────────────────────────────────────────

    def check(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check if a command is allowed under current license.

        Returns (allowed: bool, error: str|None).
        """
        # Free commands always pass
        if self.is_free_command(command):
            return True, None

        # Premium commands need valid license
        if not self.has_license:
            return False, get_upgrade_message(command)

        # Validate format
        valid, err = self.validate_license_format()
        if not valid:
            return False, f"Invalid license: {err}"

        # Validate with gateway
        is_valid, info, err = self.validate_remote()
        if not is_valid:
            return False, f"License validation failed: {err}"

        self._validated = True
        return True, None

    # ── License info ─────────────────────────────────────────────────────────

    def get_license_info(self) -> dict[str, Any]:
        """Get current license status info."""
        if not self.has_license:
            return {"status": "no_license", "upgrade_url": "https://raas.mekong.dev/pricing"}

        valid, err = self.validate_license_format()
        if not valid:
            return {"status": "invalid"}

        # Extract tier from key
        tier = self._license_key.split("-")[1] if self._license_key else "unknown"
        return {
            "status": "valid",
            "tier": tier,
            "key_preview": f"{self._license_key[:8]}...{self._license_key[-4:]}" if self._license_key else "",
        }


# ─── Singleton accessor ────────────────────────────────────────────────────────

_gate_instance: Optional[RaasLicenseGate] = None


def get_license_gate(enable_remote: bool = False) -> RaasLicenseGate:
    """Return singleton license gate instance."""
    global _gate_instance
    if _gate_instance is None:
        _gate_instance = RaasLicenseGate(enable_remote=enable_remote)
    return _gate_instance


# ─── Helper functions ──────────────────────────────────────────────────────────

def require_license(command: str) -> None:
    """Raise SystemExit if command requires a license and none is valid."""
    gate = get_license_gate()
    allowed, error = gate.check(command)
    if not allowed:
        print(error or "License required")
        raise SystemExit(1)


def check_license(command: str) -> bool:
    """Return True if command is allowed under current license."""
    gate = get_license_gate()
    allowed, _ = gate.check(command)
    return allowed


# ─── Async usage recording stub ───────────────────────────────────────────────

async def record_usage(license_key: str, tier: str) -> Tuple[bool, str]:
    """Record usage for metering (stub — delegates to usage_meter)."""
    try:
        from engine.payments.usage_meter import UsageMeter
        meter = UsageMeter()
        return await meter.record_usage(license_key, tier)
    except ImportError:
        return True, ""


# ─── Public API ────────────────────────────────────────────────────────────────

__all__ = [
    "RaasLicenseGate",
    "LicenseService",
    "LicenseTier",
    "PREMIUM_FEATURES",
    "FREE_COMMANDS",
    "get_license_gate",
    "require_license",
    "check_license",
    "record_usage",
    "validate_license",
]
