# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Individual validation steps for FinalPhaseValidator."""

from __future__ import annotations

import sys
from typing import Any, Optional

import requests

from src.raas.final_phase_validator_models import ValidationResult


def _requests_mod() -> Any:
    mod = sys.modules.get("src.raas.final_phase_validator")
    return getattr(mod, "requests", requests) if mod else requests


class FinalPhaseValidatorChecksMixin:
    """Validation check methods for FinalPhaseValidator."""

    gateway_url: str

    def _get_auth_client(self) -> Any: ...
    def _get_license_key(self) -> Optional[str]: ...
    def _hash_license_key(self, license_key: str) -> str: ...

    async def validate_license_authentication(self) -> ValidationResult:
        """Validate end-to-end license authentication."""
        result = ValidationResult(
            name="License Authentication",
            passed=False,
            message="Validating license...",
        )
        license_key = self._get_license_key()
        if not license_key:
            result.errors.append("RAAS_LICENSE_KEY not set and no stored credentials")
            result.message = "No license key found"
            return result

        result.details["license_key_present"] = True
        result.details["license_key_hash"] = self._hash_license_key(license_key)
        auth = self._get_auth_client().validate_credentials(license_key)
        if auth.valid and auth.tenant:
            result.passed = True
            result.message = "License authenticated successfully"
            result.details["tenant_id"] = auth.tenant.tenant_id
            result.details["tier"] = auth.tenant.tier
            result.details["features"] = auth.tenant.features
        else:
            result.message = f"License validation failed: {auth.error}"
            result.errors.append(auth.error or "Unknown error")
        return result

    async def validate_usage_reporting(self) -> ValidationResult:
        """Validate usage reporting integration."""
        req = _requests_mod()
        result = ValidationResult(
            name="Usage Reporting",
            passed=False,
            message="Checking usage reporting...",
        )
        try:
            from src.core import usage_metering  # noqa: F401

            result.details["usage_meter_loaded"] = True
        except ImportError:
            result.details["usage_meter_loaded"] = False
            result.errors.append("Usage meter module not available")

        license_key = self._get_license_key()
        if license_key:
            try:
                resp = req.get(
                    f"{self.gateway_url}/v1/usage",
                    headers={"Authorization": f"Bearer {license_key}"},
                    timeout=10,
                )
                result.details["usage_endpoint_reachable"] = resp.status_code in (
                    200,
                    404,
                )
            except req.RequestException as e:
                result.details["usage_endpoint_reachable"] = False
                result.errors.append(f"Usage endpoint unreachable: {e}")

        result.passed = bool(result.details.get("usage_meter_loaded"))
        result.message = (
            "Usage reporting operational"
            if result.passed
            else "Usage reporting not available"
        )
        return result

    async def validate_billing_sync(self) -> ValidationResult:
        """Validate billing sync with RaaS backend."""
        req = _requests_mod()
        result = ValidationResult(
            name="Billing Sync",
            passed=False,
            message="Checking billing sync...",
        )
        try:
            from src.api import raas_billing_middleware  # noqa: F401

            result.details["billing_middleware_loaded"] = True
        except ImportError:
            result.details["billing_middleware_loaded"] = False
            result.errors.append("Billing middleware not available")

        license_key = self._get_license_key()
        if license_key:
            try:
                resp = req.get(
                    f"{self.gateway_url}/v1/usage",
                    headers={"Authorization": f"Bearer {license_key}"},
                    timeout=10,
                )
                result.details["usage_data_available"] = resp.status_code == 200
            except req.RequestException as e:
                result.errors.append(f"Failed to fetch usage: {e}")

        result.passed = bool(result.details.get("billing_middleware_loaded"))
        result.message = (
            "Billing sync operational"
            if result.passed
            else "Billing sync not available"
        )
        return result

    async def validate_gateway_attestation(self) -> ValidationResult:
        """Validate RaaS Gateway JWT attestation."""
        req = _requests_mod()
        result = ValidationResult(
            name="Gateway Attestation",
            passed=False,
            message="Requesting gateway attestation...",
        )
        license_key = self._get_license_key()
        if not license_key:
            result.message = "No license key for attestation"
            result.errors.append("Cannot request attestation without license")
            return result

        try:
            resp = req.post(
                f"{self.gateway_url}/v1/auth/validate",
                headers={"Authorization": f"Bearer {license_key}"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                result.passed = True
                result.message = "Gateway attestation successful"
                result.details["tenant_id"] = data.get("tenant_id")
                result.details["tier"] = data.get("tier")
                result.details["features"] = data.get("features", [])
                result.details["attestation_data"] = data
            else:
                result.message = f"Gateway returned {resp.status_code}"
                result.errors.append(f"Attestation request failed: {resp.status_code}")
        except req.RequestException as e:
            result.message = f"Gateway unreachable: {e}"
            result.errors.append(f"Attestation request failed: {e}")

        return result
