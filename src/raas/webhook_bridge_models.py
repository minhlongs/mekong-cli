# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and configuration for RaaS Webhook Bridge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .usage_event_schema import WebhookEvent


class BillingProvider(str, Enum):
    """Supported billing providers."""

    STRIPE = "stripe"
    POLAR = "polar"


@dataclass
class WebhookResult:
    """Result of webhook push attempt."""

    success: bool
    provider: BillingProvider
    event_id: str
    status_code: Optional[int] = None
    error: Optional[str] = None
    retries: int = 0
    elapsed_ms: float = 0.0


@dataclass
class WebhookConfig:
    """Configuration for webhook bridge."""

    stripe_api_key: Optional[str] = None
    stripe_api_base: str = "https://api.stripe.com/v1"
    polar_api_key: Optional[str] = None
    polar_api_base: str = "https://api.polar.sh/v1"
    max_retries: int = 3
    retry_delay_ms: int = 1000
    timeout_seconds: int = 30


__all__ = [
    "BillingProvider",
    "WebhookConfig",
    "WebhookEvent",
    "WebhookResult",
]
