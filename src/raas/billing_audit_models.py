# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and helper methods for RaaS Billing Audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple

from src.core.event_bus import EventType

logger = logging.getLogger(__name__)


@dataclass
class AuditResult:
    """Result of reconciliation audit."""

    audit_id: str
    license_key: str
    key_id: str
    audit_date: date
    expected_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    variance_percent: float
    status: str  # 'matched', 'variance', 'investigating', 'resolved'
    discrepancies: List[Dict[str, Any]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "license_key": self.license_key,
            "key_id": self.key_id,
            "audit_date": self.audit_date.isoformat(),
            "expected_amount": str(self.expected_amount),
            "actual_amount": str(self.actual_amount),
            "variance": str(self.variance),
            "variance_percent": self.variance_percent,
            "status": self.status,
            "discrepancies": self.discrepancies,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
        }


@dataclass
class ReconciliationConfig:
    variance_threshold_percent: float = 5.0
    auto_resolve_threshold_percent: float = 0.5
    max_discrepancies: int = 100
    retention_days: int = 90


class ReconciliationHelpersMixin:
    """Helper methods for ReconciliationService."""

    _repo: Any
    _engine: Any
    _event_bus: Any
    _config: ReconciliationConfig

    async def _calculate_expected_amount(self, license_key: str, audit_date: date) -> Decimal:
        start_dt = datetime.combine(audit_date, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)
        events = await self._repo.get_usage_events(
            license_key=license_key, start_date=start_dt, end_date=end_dt
        )
        if not events:
            return Decimal(0)

        from src.core.usage_metering import UsageEvent

        usage_events = [
            UsageEvent(
                event_type=e.get("event_type", "usage:api_call"),
                category="usage",
                metric=e.get("metric", "requests"),
                value=e.get("value", 0),
                timestamp=(
                    e["timestamp"].timestamp()
                    if isinstance(e["timestamp"], datetime)
                    else e["timestamp"]
                ),
                metadata=e.get("metadata", {}),
            )
            for e in events
        ]
        billing_result = await self._engine.calculate_charges(
            license_key=license_key, usage_events=usage_events,
            period_start=start_dt, period_end=end_dt,
        )
        return billing_result.total

    async def _get_actual_billed_amount(self, license_key: str, audit_date: date) -> Decimal:
        return Decimal(0)

    def _determine_status(
        self,
        expected_amount: Decimal,
        actual_amount: Decimal,
        variance: Decimal,
        variance_percent: float,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        if (
            variance_percent < self._config.auto_resolve_threshold_percent
            or variance_percent <= self._config.variance_threshold_percent
        ):
            return "matched", []

        entry = (
            {
                "type": "over_billing",
                "description": f"Actual (${actual_amount}) exceeds expected (${expected_amount})",
                "variance": str(variance),
                "variance_percent": variance_percent,
            }
            if variance > 0
            else {
                "type": "under_billing",
                "description": f"Expected (${expected_amount}) exceeds actual (${actual_amount})",
                "variance": str(variance),
                "variance_percent": variance_percent,
            }
        )
        discrepancies = [entry][: self._config.max_discrepancies]
        return "variance", discrepancies

    async def _save_audit_result(self, result: AuditResult) -> None:
        await self._repo.create_reconciliation_audit(
            audit_date=result.audit_date, license_key=result.license_key, key_id=result.key_id,
            expected_amount=result.expected_amount, actual_amount=result.actual_amount,
            variance=result.variance, discrepancies=result.discrepancies,
            status=result.status, notes=f"Variance: {result.variance_percent:.2f}%",
        )

    def _emit_reconciliation_event(self, result: AuditResult) -> None:
        self._event_bus.emit(EventType.BILLING_RECONCILIATION, result.to_dict())

    async def get_audit_history(
        self, license_key: str, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        return []

    async def resolve_audit(self, audit_id: str, resolved_by: str, notes: str) -> bool:
        logger.info(f"Audit {audit_id} resolved by {resolved_by}: {notes}")
        return True
