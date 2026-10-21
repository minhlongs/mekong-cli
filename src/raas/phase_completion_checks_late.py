# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 5-6 checks and orchestration for PhaseCompletionDetector."""

from __future__ import annotations

import asyncio
import importlib.util
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from src.raas.phase_completion_models import (
    PhaseInfo,
    PhaseStatus,
    render_phase_summary_table,
)


class PhaseCompletionLateChecksMixin:
    """Checks for Phases 5-6 and aggregate completion orchestration."""

    console: Any
    _phases: Dict[str, PhaseInfo]
    _callbacks: List[Callable[[], Awaitable[None]]]
    _all_operational: bool
    _last_check: Optional[datetime]

    async def check_phase_1_license_gate(self) -> PhaseInfo: ...
    async def check_phase_2_license_ui(self) -> PhaseInfo: ...
    async def check_phase_3_payment_webhook(self) -> PhaseInfo: ...
    async def check_phase_4_usage_metering(self) -> PhaseInfo: ...

    async def check_phase_5_analytics_dashboard(self) -> PhaseInfo:
        """Check Phase 5: Analytics dashboard status."""
        phase = self._phases["phase_5_analytics_dashboard"]
        phase.last_checked = datetime.now(timezone.utc).isoformat()
        phase.status = PhaseStatus.INITIALIZING
        phase.errors = []

        try:
            try:
                from src.analytics import dashboard_service  # noqa: F401

                phase.details["dashboard_service_loaded"] = True
            except ImportError:
                phase.status = PhaseStatus.DEGRADED
                phase.errors.append("Dashboard service not available")
                phase.details["dashboard_service_loaded"] = False

            try:
                from src.db.queries import analytics_queries  # noqa: F401

                phase.details["analytics_queries_loaded"] = True
            except ImportError:
                phase.details["analytics_queries_loaded"] = False

            try:
                phase.details["dashboard_api_available"] = (
                    importlib.util.find_spec("src.api.dashboard.app") is not None
                )
            except Exception:
                phase.details["dashboard_api_available"] = False

            if phase.details.get("dashboard_service_loaded"):
                phase.status = PhaseStatus.OPERATIONAL
            else:
                phase.status = PhaseStatus.DEGRADED
                phase.errors.append("Dashboard service not available")

            self.console.print(f"[dim]✓ Phase 5 check complete: {phase.status.value}[/dim]")
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.errors.append(f"Phase 5 check failed: {e}")

        self._phases["phase_5_analytics_dashboard"] = phase
        return phase

    async def check_phase_6_terminal_validation(self) -> PhaseInfo:
        """Check Phase 6: Terminal Validation status."""
        phase = self._phases["phase_6_terminal_validation"]
        phase.last_checked = datetime.now(timezone.utc).isoformat()
        phase.status = PhaseStatus.INITIALIZING
        phase.errors = []

        try:
            from src.raas.completion_certificate import generate_certificate, save_certificate
            from src.raas.final_phase_validator import get_validator as get_phase6_validator

            res = await get_phase6_validator().validate_all()
            phase.details.update({
                "validation_passed": res.all_passed,
                "project_id": res.project_id,
                "license_key_hash": res.license_key_hash,
                "total_billed_usage": res.total_billed_usage,
                "gateway_issuer": res.gateway_issuer,
                "attestation_hash": res.attestation,
            })

            if res.all_passed:
                op = PhaseStatus.OPERATIONAL
                cert = generate_certificate(
                    res,
                    phases_status={
                        "Phase 1: License Gate": self._phases["phase_1_license_gate"].status == op,
                        "Phase 2: License UI": self._phases["phase_2_license_ui"].status == op,
                        "Phase 3: Payment Webhook": self._phases["phase_3_payment_webhook"].status == op,
                        "Phase 4: Usage Metering": self._phases["phase_4_usage_metering"].status == op,
                        "Phase 5: Analytics Dashboard": self._phases["phase_5_analytics_dashboard"].status == op,
                        "Phase 6: Terminal Validation": True,
                    },
                )
                phase.details["certificate_saved"] = save_certificate(cert)
                phase.details["certificate_id"] = cert.certificate_id
                phase.status = PhaseStatus.OPERATIONAL
                phase.errors.append(f"Certificate: {cert.certificate_id}")
            else:
                phase.status = PhaseStatus.DEGRADED
                phase.errors.extend(res.errors)

            self.console.print(f"[dim]✓ Phase 6 check complete: {phase.status.value}[/dim]")
        except ImportError as e:
            phase.status = PhaseStatus.DEGRADED
            phase.errors.append(f"Phase 6 validator not available: {e}")
            phase.details["validation_passed"] = False
        except Exception as e:
            phase.status = PhaseStatus.FAILED
            phase.errors.append(f"Phase 6 check failed: {e}")
            phase.details["validation_passed"] = False

        self._phases["phase_6_terminal_validation"] = phase
        return phase

    async def check_all_phases(self) -> bool:
        """Check all six phases and return True if all are operational."""
        self.console.print("\n[bold cyan]=== ROIaaS Phase Completion Check (6 Phases) ===[/bold cyan]")
        results = await asyncio.gather(
            self.check_phase_1_license_gate(),
            self.check_phase_2_license_ui(),
            self.check_phase_3_payment_webhook(),
            self.check_phase_4_usage_metering(),
            self.check_phase_5_analytics_dashboard(),
            self.check_phase_6_terminal_validation(),
            return_exceptions=False,
        )
        all_operational = all(phase.status == PhaseStatus.OPERATIONAL for phase in results)
        was_operational = self._all_operational
        self._all_operational = all_operational
        self._last_check = datetime.now(timezone.utc)

        self._display_phase_summary(results)
        if all_operational and not was_operational:
            self.console.print("\n[bold green]✓ All phases operational! Triggering shutdown sequence...[/bold green]")
            await self._trigger_callbacks()

        return all_operational

    def _display_phase_summary(self, phases: List[PhaseInfo]) -> None:
        render_phase_summary_table(self.console, phases)

    async def _trigger_callbacks(self) -> None:
        for callback in self._callbacks:
            try:
                await callback()
            except Exception as e:
                self.console.print(f"[yellow]⚠ Callback error: {e}[/yellow]")

