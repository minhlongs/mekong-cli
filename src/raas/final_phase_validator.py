# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Final Phase Validator — ROIaaS Phase 6 Terminal Validation

Validates end-to-end RaaS integration and generates completion certificate.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from datetime import datetime, timezone
from typing import Optional

import requests
from rich.console import Console

from src.core.raas_auth import RaaSAuthClient
from src.raas.final_phase_validator_checks import FinalPhaseValidatorChecksMixin
from src.raas.final_phase_validator_models import (
    Phase6ValidationResult,
    ValidationResult,
    render_validation_summary,
)


class FinalPhaseValidator(FinalPhaseValidatorChecksMixin):
    """Terminal-phase validation for ROIaaS Phase 6."""

    DEFAULT_GATEWAY_URL = "https://raas.mekongmind.com"

    def __init__(self, gateway_url: Optional[str] = None) -> None:
        self.console = Console()
        self.gateway_url = gateway_url or os.getenv(
            "RAAS_GATEWAY_URL", self.DEFAULT_GATEWAY_URL
        )
        self._auth_client: Optional[RaaSAuthClient] = None

    def _get_auth_client(self) -> RaaSAuthClient:
        """Get or create RaaS auth client."""
        if self._auth_client is None:
            self._auth_client = RaaSAuthClient(gateway_url=self.gateway_url)
        return self._auth_client

    def _get_project_id(self) -> str:
        """Get unique project ID for mekong-cli."""
        project_id = os.getenv("MEKONG_PROJECT_ID")
        if project_id:
            return project_id

        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                repo_url = result.stdout.strip()
                return hashlib.sha256(repo_url.encode()).hexdigest()[:16]
        except Exception:
            pass

        return hashlib.sha256(b"mekong-cli-raas-project").hexdigest()[:16]

    def _hash_license_key(self, license_key: str) -> str:
        """Create secure hash of license key for certificate."""
        if not license_key:
            return "none"
        return hashlib.sha256(license_key.encode()).hexdigest()[:16]

    def _get_license_key(self) -> Optional[str]:
        """Get license key from env or stored credentials."""
        license_key = os.getenv("RAAS_LICENSE_KEY")
        if license_key:
            return license_key

        try:
            creds = self._get_auth_client()._load_credentials()
            return creds.get("token")
        except Exception:
            return None

    async def validate_all(self) -> Phase6ValidationResult:
        """Run all Phase 6 validations and generate completion certificate."""
        self.console.print("\n[bold cyan]=== ROIaaS Phase 6: Terminal Validation ===[/bold cyan]\n")

        self.console.print("[dim]Step 1: Validating license authentication...[/dim]")
        license_result = await self.validate_license_authentication()

        self.console.print("[dim]Step 2: Validating usage reporting...[/dim]")
        usage_result = await self.validate_usage_reporting()

        self.console.print("[dim]Step 3: Validating billing sync...[/dim]")
        billing_result = await self.validate_billing_sync()

        self.console.print("[dim]Step 4: Requesting gateway attestation...[/dim]")
        attestation_result = await self.validate_gateway_attestation()

        results = [license_result, usage_result, billing_result, attestation_result]
        all_passed = license_result.passed and attestation_result.passed

        license_key = self._get_license_key() or ""
        project_id = self._get_project_id()

        total_billed_usage = 0
        for result in results:
            if "total_requests" in result.details:
                total_billed_usage = result.details["total_requests"]

        attestation = None
        gateway_issuer = None
        if attestation_result.passed:
            attestation_data = attestation_result.details.get("attestation_data", {})
            gateway_issuer = attestation_data.get("gateway", {}).get("url", self.gateway_url)
            attestation_payload = (
                f"{project_id}:{self._hash_license_key(license_key)}:{int(time.time())}"
            )
            attestation = hashlib.sha256(attestation_payload.encode()).hexdigest()

        phase6_result = Phase6ValidationResult(
            all_passed=all_passed,
            project_id=project_id,
            license_key_hash=self._hash_license_key(license_key),
            total_billed_usage=total_billed_usage,
            attestation=attestation,
            gateway_issuer=gateway_issuer,
            validation_timestamp=datetime.now(timezone.utc).isoformat(),
            results=results,
            errors=[e for r in results for e in r.errors],
        )

        self._display_validation_summary(phase6_result)
        return phase6_result

    def _display_validation_summary(self, result: Phase6ValidationResult) -> None:
        """Display validation summary table."""
        render_validation_summary(self.console, result)


# Singleton instance
_validator: Optional[FinalPhaseValidator] = None


def get_validator(gateway_url: Optional[str] = None) -> FinalPhaseValidator:
    """Get global FinalPhaseValidator instance."""
    global _validator
    if _validator is None or gateway_url:
        _validator = FinalPhaseValidator(gateway_url=gateway_url)
    return _validator


def reset_validator() -> None:
    """Reset global validator instance (for testing)."""
    global _validator
    _validator = None


__all__ = [
    "ValidationResult",
    "Phase6ValidationResult",
    "FinalPhaseValidator",
    "RaaSAuthClient",
    "get_validator",
    "requests",
    "reset_validator",
]
