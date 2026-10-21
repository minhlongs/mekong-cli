# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data structures and protocols for x402 payment settlement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from src.core.governance import GovernanceDecision


PROVIDER_NAME = "x402"
ATOMIC_DECIMALS = 6
_REQUIRED_FIELDS = ("endpoint", "asset", "network", "recipient")


class X402ConfigError(ValueError):
    """Raised when explicit x402 settlement config is missing or invalid."""


class X402ReplayError(ValueError):
    """Raised when a replayed idempotency key is rejected (fail-closed)."""


class X402SettlementError(ValueError):
    """Raised when settlement fails closed (approval, transport, response)."""


class X402Transport(Protocol):
    """Injected transport — the ONLY network seam this provider uses."""

    def __call__(
        self, endpoint: str, headers: Dict[str, str], body: Dict[str, Any]
    ) -> Dict[str, Any]: ...


class ApprovalGate(Protocol):
    """Governance seam — mirrors Governance.request_approval."""

    def request_approval(self, goal: str, decision: GovernanceDecision) -> bool: ...


@dataclass(frozen=True)
class X402QuotaStatus:
    """Concrete QuotaStatus-shaped carrier (satisfies the Protocol structurally)."""

    remaining_mcu: int
    total_mcu: int
    tier: str
    reset_at: str


@dataclass(frozen=True)
class X402PaymentResult:
    """Concrete PaymentResult-shaped carrier (satisfies the Protocol structurally)."""

    success: bool
    transaction_id: Optional[str] = None
    pending: bool = False
    note: Optional[str] = None
    error: Optional[str] = None


__all__ = [
    "PROVIDER_NAME",
    "ATOMIC_DECIMALS",
    "_REQUIRED_FIELDS",
    "X402ConfigError",
    "X402ReplayError",
    "X402SettlementError",
    "X402Transport",
    "ApprovalGate",
    "X402QuotaStatus",
    "X402PaymentResult",
]
