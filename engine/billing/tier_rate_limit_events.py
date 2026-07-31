"""Structured event logging for tier rate-limit middleware."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from src.lib.time_utils import utc_iso_now
from src.services.license_enforcement import LicenseStatus

logger = logging.getLogger("mekong.rate_limits")


def log_rate_limit_event(
    event_type: str,
    tenant_id: str,
    tier: str,
    endpoint: str,
    preset: str,
    quota_limit: Optional[int] = None,
    quota_remaining: Optional[int] = None,
    quota_utilization_pct: Optional[float] = None,
    response_status: Optional[int] = None,
    retry_after: Optional[int] = None,
    request_context: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
    event_logger: logging.Logger = logger,
) -> None:
    """Log one structured rate-limit event."""
    log_entry: dict[str, Any] = {
        "timestamp": utc_iso_now(),
        "level": "INFO" if event_type != "rate_limited" else "WARNING",
        "event": "rate_limit_event",
        "tenant_id": tenant_id,
        "tier": tier,
        "endpoint": endpoint,
        "preset": preset,
        "event_type": event_type,
        "quota": {
            "requests_per_minute": quota_limit,
            "quota_remaining": quota_remaining,
            "quota_utilization_pct": quota_utilization_pct,
        },
        "response": {"status": response_status, "retry_after": retry_after},
    }
    if request_context:
        log_entry["request"] = request_context
    if metadata:
        log_entry["metadata"] = metadata
    event_logger.info(json.dumps(log_entry))


def log_license_enforcement(
    tenant_id: str,
    status: LicenseStatus,
    endpoint: str,
    action: str,
    event_logger: logging.Logger = logger,
) -> None:
    """Log one structured license enforcement event."""
    log_entry = {
        "timestamp": utc_iso_now(),
        "level": "INFO" if action == "allowed" else "WARNING",
        "event": "license_enforcement_event",
        "tenant_id": tenant_id,
        "license_status": status.value,
        "enforcement_action": action,
        "endpoint": endpoint,
    }
    event_logger.info(json.dumps(log_entry))


__all__ = ["log_license_enforcement", "log_rate_limit_event", "logger"]
