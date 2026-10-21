# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Billing Event Emitter."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional

from src.core.auth_tenant import derive_tenant_id
from src.core.event_bus import EventType, get_event_bus
from src.core.protocols import SerializableBillingResult
from src.raas.billing_engine import BillingResult
from src.raas.billing_event_payloads import (
    build_batch_processed_payload,
    build_idempotency_conflict_payload,
    build_overage_payload,
    build_period_closed_payload,
    build_recorded_payload,
    build_reconciliation_payload,
)

logger = logging.getLogger(__name__)


class BillingEventEmitter:
    """Emit structured billing events for analytics sync."""

    def __init__(self) -> None:
        self._event_bus = get_event_bus()

    def emit_billing_recorded(
        self,
        billing_result: BillingResult,
        billing_record_id: str,
        billing_period_id: Optional[str] = None,
    ) -> None:
        """Emit event when billing record is created."""
        event_data = build_recorded_payload(
            billing_result, billing_record_id, billing_period_id
        )
        self._event_bus.emit(EventType.BILLING_RECORDED, event_data)
        logger.debug("Emitted billing:recorded for %s", derive_tenant_id(billing_result.license_key))

    def emit_billing_overage(
        self,
        license_key: str,
        key_id: str,
        overage_calculations: List[SerializableBillingResult],
        total_overage: Decimal,
        period_start: datetime,
        period_end: datetime,
    ) -> None:
        """Emit event when overage is detected."""
        event_data = build_overage_payload(
            license_key, key_id, overage_calculations, total_overage, period_start, period_end
        )
        self._event_bus.emit(EventType.BILLING_OVERAGE, event_data)
        logger.info("Emitted billing:overage for %s: %s", derive_tenant_id(license_key), total_overage)

    def emit_billing_period_closed(
        self,
        billing_period_id: str,
        license_key: str,
        key_id: str,
        total_amount: Decimal,
        final_usage: Dict[str, Any],
    ) -> None:
        """Emit event when billing period is closed."""
        event_data = build_period_closed_payload(
            billing_period_id, license_key, key_id, total_amount, final_usage
        )
        self._event_bus.emit(EventType.BILLING_PERIOD_CLOSED, event_data)
        logger.info("Emitted billing:period_closed for %s", derive_tenant_id(license_key))

    def emit_billing_reconciliation(
        self,
        audit_id: str,
        license_key: str,
        key_id: str,
        audit_date: str,
        expected_amount: Decimal,
        actual_amount: Decimal,
        variance: Decimal,
        variance_percent: float,
        status: str,
        discrepancies: Optional[List[Dict]] = None,
    ) -> None:
        """Emit event when reconciliation audit is completed."""
        event_data = build_reconciliation_payload(
            audit_id, license_key, key_id, audit_date, expected_amount,
            actual_amount, variance, variance_percent, status, discrepancies,
        )
        self._event_bus.emit(EventType.BILLING_RECONCILIATION, event_data)
        logger.debug("Emitted billing:reconciliation for %s: %s", derive_tenant_id(license_key), status)

    def emit_billing_batch_processed(
        self,
        batch_result: SerializableBillingResult,
        events_count: int,
        processing_duration_ms: int,
    ) -> None:
        """Emit event when batch processing is completed."""
        event_data = build_batch_processed_payload(
            batch_result, events_count, processing_duration_ms
        )
        self._event_bus.emit(EventType.BILLING_BATCH_PROCESSED, event_data)
        logger.debug("Emitted billing:batch_processed for %s", batch_result.batch_id)

    def emit_billing_idempotency_conflict(
        self,
        batch_id: str,
        license_key: str,
        original_billing_record_id: str,
        conflict_timestamp: datetime,
    ) -> None:
        """Emit event when idempotency conflict is detected."""
        event_data = build_idempotency_conflict_payload(
            batch_id, license_key, original_billing_record_id, conflict_timestamp
        )
        self._event_bus.emit(EventType.BILLING_IDEMPOTENCY_CONFLICT, event_data)
        logger.warning("Emitted billing:idempotency_conflict for %s", batch_id)

    def emit_billing_proration(
        self,
        proration_result: SerializableBillingResult,
        billing_period_id: str,
    ) -> None:
        """Emit event when proration is calculated."""
        event_data = proration_result.to_dict()
        event_data["billing_period_id"] = billing_period_id
        event_data["event_type"] = "proration_calculated"

        self._event_bus.emit(EventType.BILLING_RECORDED, event_data)
        logger.debug("Emitted proration event for %s: %s", proration_result.license_key, proration_result.new_plan)


_emitter: Optional[BillingEventEmitter] = None


def get_emitter() -> BillingEventEmitter:
    """Get or create the billing event emitter singleton."""
    global _emitter
    if _emitter is None:
        _emitter = BillingEventEmitter()
    return _emitter


def reset_emitter() -> None:
    """Reset singleton (for testing)."""
    global _emitter
    _emitter = None


__all__ = ["BillingEventEmitter", "get_emitter", "reset_emitter"]
