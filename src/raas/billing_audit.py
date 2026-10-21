# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - Reconciliation Service

Nightly audit service for variance detection and double-billing prevention.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import logging
from typing import List, Optional

from src.core.event_bus import EventType, get_event_bus
from src.db.repository import LicenseRepository, get_repository
from src.raas.billing_audit_models import (
    AuditResult,
    ReconciliationConfig,
    ReconciliationHelpersMixin,
)
from src.raas.billing_engine import BillingEngine, get_engine

logger = logging.getLogger(__name__)


class ReconciliationService(ReconciliationHelpersMixin):
    """
    Nightly reconciliation service for billing audit.

    Compares expected vs actual billing amounts, logs audit results,
    and alerts on variance above threshold.
    """

    def __init__(
        self,
        repository: Optional[LicenseRepository] = None,
        billing_engine: Optional[BillingEngine] = None,
        config: Optional[ReconciliationConfig] = None,
    ) -> None:
        self._repo = repository or get_repository()
        self._engine = billing_engine or get_engine()
        self._event_bus = get_event_bus()
        self._config = config or ReconciliationConfig()

    async def run_daily_reconciliation(
        self,
        audit_date: Optional[date] = None,
    ) -> List[AuditResult]:
        """Run daily reconciliation for all active licenses."""
        if audit_date is None:
            audit_date = date.today() - timedelta(days=1)

        logger.info(f"Starting daily reconciliation for {audit_date}")
        licenses = await self._get_active_licenses()
        results: List[AuditResult] = []

        for license_info in licenses:
            license_key = license_info["license_key"]
            key_id = license_info["key_id"]
            try:
                result = await self._reconcile_license(
                    license_key=license_key,
                    key_id=key_id,
                    audit_date=audit_date,
                )
                results.append(result)
                self._emit_reconciliation_event(result)

                if result.status != "matched":
                    logger.warning(
                        f"Reconciliation variance for {license_key}: "
                        f"{result.variance_percent:.2f}%"
                    )
            except Exception as e:
                logger.error(f"Reconciliation failed for {license_key}: {e}")
                results.append(
                    AuditResult(
                        audit_id=f"audit_{license_key}_{audit_date}_error",
                        license_key=license_key,
                        key_id=key_id,
                        audit_date=audit_date,
                        expected_amount=Decimal(0),
                        actual_amount=Decimal(0),
                        variance=Decimal(0),
                        variance_percent=0,
                        status="investigating",
                        discrepancies=[{"error": str(e)}],
                        details={"reconciliation_error": str(e)},
                    )
                )

        logger.info(
            f"Daily reconciliation complete: {len(results)} licenses audited"
        )
        return results

    async def _reconcile_license(
        self,
        license_key: str,
        key_id: str,
        audit_date: date,
    ) -> AuditResult:
        """Reconcile billing for a single license."""
        expected_amount = await self._calculate_expected_amount(
            license_key=license_key,
            audit_date=audit_date,
        )
        actual_amount = await self._get_actual_billed_amount(
            license_key=license_key,
            audit_date=audit_date,
        )

        variance = actual_amount - expected_amount
        variance_percent = 0.0
        if expected_amount > 0:
            variance_percent = float(abs(variance) / expected_amount * 100)
        elif actual_amount > 0:
            variance_percent = 100.0

        status, discrepancies = self._determine_status(
            expected_amount=expected_amount,
            actual_amount=actual_amount,
            variance=variance,
            variance_percent=variance_percent,
        )

        result = AuditResult(
            audit_id=f"audit_{license_key}_{audit_date}",
            license_key=license_key,
            key_id=key_id,
            audit_date=audit_date,
            expected_amount=round(expected_amount, 2),
            actual_amount=round(actual_amount, 2),
            variance=round(variance, 2),
            variance_percent=round(variance_percent, 2),
            status=status,
            discrepancies=discrepancies,
            details={
                "calculation_method": "usage_events_vs_billing_records",
                "auto_resolved": (
                    status == "matched"
                    and variance_percent < self._config.auto_resolve_threshold_percent
                ),
            },
        )
        await self._save_audit_result(result)
        return result


_service: Optional[ReconciliationService] = None


def get_reconciliation_service() -> ReconciliationService:
    """Get or create the reconciliation service singleton."""
    global _service
    if _service is None:
        _service = ReconciliationService()
    return _service


def reset_reconciliation_service() -> None:
    """Reset singleton (for testing)."""
    global _service
    _service = None


__all__ = [
    "AuditResult",
    "EventType",
    "ReconciliationConfig",
    "ReconciliationService",
    "get_reconciliation_service",
    "reset_reconciliation_service",
]
