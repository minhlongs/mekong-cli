# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate limit event dataclass and telemetry models — ROIaaS Phase 6."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class RateLimitEvent:
    """Rate limit event data structure."""

    tenant_id: str
    tier: str
    endpoint: str
    preset: str
    event_type: str  # 'override_applied', 'request_allowed', 'rate_limited'

    # Quota information
    quota_limit: Optional[int] = None
    quota_remaining: Optional[int] = None
    quota_utilization_pct: Optional[float] = None

    # Request details
    client_ip: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    user_agent: Optional[str] = None

    # Response details
    response_status: Optional[int] = None
    retry_after: Optional[int] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


__all__ = ["RateLimitEvent"]
