# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 1-4 checks for PhaseCompletionDetector."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any, Dict

from src.raas.phase_completion_models import PhaseInfo, PhaseStatus


class PhaseCompletionEarlyChecksMixin:
    """Checks for ROIaaS Phases 1 through 4."""

    console: Any
    _phases: Dict[str, PhaseInfo]

    async def check_phase_1_license_gate(self) -> PhaseInfo:
        """Check Phase 1: RAAS_LICENSE_KEY gate status."""
        phase = self._phases["phase_1_license_gate"]
        phase.last_checked = datetime.now(timezone.utc).isoformat()
        phase.status = PhaseStatus.INITIALIZING
        phase.errors = []
        try:
            license_key = os.getenv("RAAS_LICENSE_KEY")
            if not license_key:
                phase.status = PhaseStatus.DEGRADED
                phase.errors.append("RAAS_LICENSE_KEY not set")
                phase.details["license_present"] = False
            else:
                phase.details["license_present"] = True
                from src.lib.raas_gate_validator import RaasGateValidator

                is_valid, error = RaasGateValidator().validate()
                phase.details["license_valid"] = is_valid
                phase.status = (
                    PhaseStatus.OPERATIONAL if is_valid else PhaseStatus.DEGRADED
                )
                if not is_valid:
                    phase.errors.append(f"License validation failed: {error}")
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.errors.append(f"Phase 1 check failed: {e}")

        self._phases["phase_1_license_gate"] = phase
        return phase

    async def check_phase_2_license_ui(self) -> PhaseInfo:
        """Check Phase 2: License Management UI status."""
        phase = self._phases["phase_2_license_ui"]
        phase.last_checked = datetime.now(timezone.utc).isoformat()
        phase.status = PhaseStatus.INITIALIZING
        phase.errors = []
        try:
            try:
                from src.commands import license_admin  # noqa: F401

                phase.details["admin_commands_loaded"] = True
            except ImportError:
                phase.details["admin_commands_loaded"] = False

            try:
                from src.raas import dashboard  # noqa: F401

                phase.details["dashboard_loaded"] = True
            except ImportError:
                phase.details["dashboard_loaded"] = False

            if phase.details.get("admin_commands_loaded") or phase.details.get(
                "dashboard_loaded"
            ):
                phase.status = PhaseStatus.OPERATIONAL
            else:
                phase.status = PhaseStatus.DEGRADED
                phase.errors.append("License admin / dashboard not available")
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.errors.append(f"Phase 2 check failed: {e}")

        self._phases["phase_2_license_ui"] = phase
        return phase

    async def check_phase_3_payment_webhook(self) -> PhaseInfo:
        """Check Phase 3: Stripe/Polar webhook status."""
        phase = self._phases["phase_3_payment_webhook"]
        phase.last_checked = datetime.now(timezone.utc).isoformat()
        phase.status = PhaseStatus.INITIALIZING
        phase.errors = []
        try:
            try:
                from src.api import raas_billing_middleware  # noqa: F401

                phase.details["billing_middleware_loaded"] = True
                phase.status = PhaseStatus.OPERATIONAL
            except ImportError:
                phase.details["billing_middleware_loaded"] = False
                phase.status = PhaseStatus.DEGRADED
                phase.errors.append("Billing middleware not available")
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.errors.append(f"Phase 3 check failed: {e}")

        self._phases["phase_3_payment_webhook"] = phase
        return phase

    async def check_phase_4_usage_metering(self) -> PhaseInfo:
        """Check Phase 4: Usage metering status."""
        phase = self._phases["phase_4_usage_metering"]
        phase.last_checked = datetime.now(timezone.utc).isoformat()
        phase.status = PhaseStatus.INITIALIZING
        phase.errors = []
        try:
            loaded = 0
            for mod_path, name in [
                ("src.lib.usage_meter", "usage_meter_loaded"),
                ("src.lib.usage_metering_service", "metering_service_loaded"),
                ("src.raas.credit_rate_limiter", "rate_limiter_loaded"),
            ]:
                try:
                    __import__(mod_path)
                    phase.details[name] = True
                    loaded += 1
                except ImportError:
                    phase.details[name] = False

            if loaded >= 2:
                phase.status = PhaseStatus.OPERATIONAL
            elif loaded >= 1:
                phase.status = PhaseStatus.DEGRADED
                phase.errors.append("Some usage metering components missing")
            else:
                phase.status = PhaseStatus.FAILED
                phase.errors.append("No usage metering components available")
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.errors.append(f"Phase 4 check failed: {e}")

        self._phases["phase_4_usage_metering"] = phase
        return phase
