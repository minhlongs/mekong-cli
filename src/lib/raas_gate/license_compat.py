# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
License Compat — Backward-compatible aliases for raas_gate

Provides:
- LicenseTier: Tier constant class
- LicenseService: Compatibility shim wrapping RaasLicenseGate
- PREMIUM_FEATURES: Feature catalogue keyed by tier
- _ValidationResult: Structured validation result dataclass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class _ValidationResult:
    valid: bool
    tier: str
    features: List[str] = field(default_factory=list)


# Feature catalogue keyed by tier
PREMIUM_FEATURES: Dict[str, List[str]] = {
    "free": [
        "init", "version", "list", "search", "status", "config", "doctor", "help", "dash",
    ],
    "pro": [
        "init", "version", "list", "search", "status", "config", "doctor", "help", "dash",
        "cook", "gateway", "binh-phap", "telegram", "agi",
        "recipe_library", "llm_routing", "usage_analytics",
    ],
    "enterprise": [
        "init", "version", "list", "search", "status", "config", "doctor", "help", "dash",
        "cook", "gateway", "binh-phap", "telegram", "agi",
        "swarm", "schedule", "autonomous",
        "recipe_library", "llm_routing", "usage_analytics",
        "multi_tenant", "sso", "audit_logs", "priority_support",
    ],
}


class LicenseTier(str):
    """License tier constants."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseService:
    """Compatibility shim — thin wrapper around RaasLicenseGate with singleton."""

    _instance: Optional["LicenseService"] = None

    @classmethod
    def getInstance(cls) -> "LicenseService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        from src.lib.raas_gate import get_license_gate
        self._gate = get_license_gate()

    def validateSync(self, key: Optional[str] = None) -> _ValidationResult:
        """Validate a license key synchronously and return structured result."""
        import os

        check_key = key or os.getenv("RAAS_LICENSE_KEY", "")
        if not check_key:
            return _ValidationResult(valid=False, tier="free", features=PREMIUM_FEATURES["free"])

        valid, _msg = self._gate.validate_license_format(check_key)
        if not valid:
            return _ValidationResult(valid=False, tier="free", features=PREMIUM_FEATURES["free"])

        parts = check_key.split("-")
        tier = parts[1].lower() if len(parts) >= 2 else "free"
        if tier not in PREMIUM_FEATURES:
            tier = "free"
        return _ValidationResult(valid=True, tier=tier, features=PREMIUM_FEATURES[tier])
