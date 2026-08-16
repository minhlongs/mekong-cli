# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Sync Client Models — Dataclasses for RaaS Sync Client

Defines SyncResult and UsageSummary data containers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SyncResult:
    """Result of metrics synchronization."""

    success: bool
    synced_count: int
    total_payload_size: int
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_in: Optional[int] = None
    error: Optional[str] = None
    gateway_response: Optional[dict] = None
    elapsed_ms: float = 0.0


@dataclass
class UsageSummary:
    """Summary of local usage metrics."""

    total_requests: int = 0
    total_payload_size: int = 0
    hours_active: int = 0
    peak_hour: Optional[str] = None
    peak_requests: int = 0
    endpoints: dict[str, int] = field(default_factory=dict)
    methods: dict[str, int] = field(default_factory=dict)
