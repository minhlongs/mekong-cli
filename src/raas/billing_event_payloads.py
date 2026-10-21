# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Payload builders for BillingEventEmitter."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.protocols import SerializableBillingResult
from src.raas.billing_engine import BillingResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_recorded_payload(
    billing_result: BillingResult,
    billing_record_id: str,
    billing_period_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "billing_record_id": billing_record_id,
        "billing_period_id": billing_period_id,
        "license_key": billing_result.license_key,
        "key_id": billing_result.key_id,
        "period_start": billing_result.period_start.isoformat(),
        "period_end": billing_result.period_end.isoformat(),
        "total_amount": str(billing_result.total),
        "currency": billing_result.currency,
        "line_items_count": len(billing_result.line_items),
        "line_items": [item.to_dict() for item in billing_result.line_items],
        "subtotal": str(billing_result.subtotal),
        "discount": str(billing_result.discount),
        "metadata": billing_result.metadata,
        "timestamp": _now_iso(),
    }


def build_overage_payload(
    license_key: str,
    key_id: str,
    overage_calculations: List[SerializableBillingResult],
    total_overage: Decimal,
    period_start: datetime,
    period_end: datetime,
) -> Dict[str, Any]:
    return {
        "license_key": license_key,
        "key_id": key_id,
        "total_overage": str(total_overage),
        "overage_count": len(overage_calculations),
        "breakdown": [calc.to_dict() for calc in overage_calculations],
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "timestamp": _now_iso(),
    }


def build_period_closed_payload(
    billing_period_id: str,
    license_key: str,
    key_id: str,
    total_amount: Decimal,
    final_usage: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "billing_period_id": billing_period_id,
        "license_key": license_key,
        "key_id": key_id,
        "total_amount": str(total_amount),
        "final_usage": final_usage,
        "status": "closed",
        "timestamp": _now_iso(),
    }


def build_reconciliation_payload(
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
) -> Dict[str, Any]:
    return {
        "audit_id": audit_id,
        "license_key": license_key,
        "key_id": key_id,
        "audit_date": audit_date,
        "expected_amount": str(expected_amount),
        "actual_amount": str(actual_amount),
        "variance": str(variance),
        "variance_percent": variance_percent,
        "status": status,
        "discrepancies": discrepancies or [],
        "timestamp": _now_iso(),
    }


def build_batch_processed_payload(
    batch_result: SerializableBillingResult,
    events_count: int,
    processing_duration_ms: int,
) -> Dict[str, Any]:
    return {
        "batch_id": batch_result.batch_id,
        "license_key": batch_result.license_key,
        "status": batch_result.status.value,
        "is_duplicate": batch_result.is_duplicate,
        "billing_record_id": batch_result.billing_record_id,
        "events_count": events_count,
        "total_charge": str(batch_result.total_charge),
        "processing_duration_ms": processing_duration_ms,
        "error_message": batch_result.error_message,
        "timestamp": _now_iso(),
    }


def build_idempotency_conflict_payload(
    batch_id: str,
    license_key: str,
    original_billing_record_id: str,
    conflict_timestamp: datetime,
) -> Dict[str, Any]:
    return {
        "batch_id": batch_id,
        "license_key": license_key,
        "original_billing_record_id": original_billing_record_id,
        "conflict_timestamp": conflict_timestamp.isoformat(),
        "action": "rejected_duplicate",
        "timestamp": _now_iso(),
    }
