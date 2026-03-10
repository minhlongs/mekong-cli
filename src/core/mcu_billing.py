"""Mekong MCU Billing — Mission Credit Unit accounting system.

Condition C4: Credit store with MCU deduction per task complexity.
Pricing: simple=1 MCU, standard=3 MCU, complex=5 MCU.

Usage:
    from src.core.mcu_billing import MCUBilling, MCU_COSTS
    billing = MCUBilling()
    billing.add_credits("tenant-123", 100)
    result = billing.deduct("tenant-123", "standard")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Literal, Optional


# MCU cost per task complexity
MCU_COSTS: dict[str, int] = {
    "simple": 1,
    "standard": 3,
    "complex": 5,
}

# Tier credit bundles (for Polar.sh checkout)
TIER_CREDITS: dict[str, int] = {
    "starter": 50,
    "growth": 200,
    "premium": 1000,
}

# Low balance threshold
LOW_BALANCE_THRESHOLD = 10


@dataclass
class MCUTransaction:
    """Single MCU transaction record."""

    tenant_id: str
    amount: int  # positive = credit, negative = debit
    balance_after: int
    transaction_type: Literal["credit", "debit", "refund"]
    description: str = ""
    mission_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "tenant_id": self.tenant_id,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "transaction_type": self.transaction_type,
            "description": self.description,
            "mission_id": self.mission_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TenantBalance:
    """Tenant MCU balance and transaction history."""

    tenant_id: str
    balance: int = 0
    total_credited: int = 0
    total_debited: int = 0
    total_refunded: int = 0
    transactions: list[MCUTransaction] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "tenant_id": self.tenant_id,
            "balance": self.balance,
            "total_credited": self.total_credited,
            "total_debited": self.total_debited,
            "total_refunded": self.total_refunded,
            "transaction_count": len(self.transactions),
        }


@dataclass
class DeductionResult:
    """Result of an MCU deduction attempt."""

    success: bool
    balance_before: int
    balance_after: int
    amount_deducted: int
    low_balance: bool = False
    error: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "success": self.success,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "amount_deducted": self.amount_deducted,
            "low_balance": self.low_balance,
            "error": self.error,
        }


class MCUBilling:
    """MCU billing engine for tenant credit management.

    In-memory store for development. Production would use database.
    """

    def __init__(
        self,
        low_threshold: int = LOW_BALANCE_THRESHOLD,
        webhook_handler: Optional[Callable[[str, dict], None]] = None,
    ) -> None:
        self._tenants: dict[str, TenantBalance] = {}
        self.low_threshold = low_threshold
        self._webhook_handler = webhook_handler
        self._notified_tenants: set[str] = set()

    def _get_or_create(self, tenant_id: str) -> TenantBalance:
        """Get tenant balance, creating if not exists."""
        if tenant_id not in self._tenants:
            self._tenants[tenant_id] = TenantBalance(tenant_id=tenant_id)
        return self._tenants[tenant_id]

    def add_credits(
        self, tenant_id: str, amount: int, description: str = ""
    ) -> TenantBalance:
        """Add MCU credits to a tenant's balance.

        Args:
            tenant_id: Tenant identifier
            amount: Number of credits to add (must be positive)
            description: Transaction description

        Returns:
            Updated TenantBalance

        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        tenant = self._get_or_create(tenant_id)
        tenant.balance += amount
        tenant.total_credited += amount

        tx = MCUTransaction(
            tenant_id=tenant_id,
            amount=amount,
            balance_after=tenant.balance,
            transaction_type="credit",
            description=description or f"Added {amount} MCU",
        )
        tenant.transactions.append(tx)
        return tenant

    def deduct(
        self,
        tenant_id: str,
        complexity: str = "simple",
        mission_id: str = "",
    ) -> DeductionResult:
        """Deduct MCU credits for a mission.

        Args:
            tenant_id: Tenant identifier
            complexity: Task complexity (simple=1, standard=3, complex=5)
            mission_id: Associated mission ID

        Returns:
            DeductionResult with success/failure details
        """
        cost = MCU_COSTS.get(complexity, MCU_COSTS["simple"])
        tenant = self._get_or_create(tenant_id)
        balance_before = tenant.balance

        if tenant.balance < cost:
            return DeductionResult(
                success=False,
                balance_before=balance_before,
                balance_after=tenant.balance,
                amount_deducted=0,
                error=f"Insufficient MCU: need {cost}, have {tenant.balance}",
            )

        tenant.balance -= cost
        tenant.total_debited += cost

        tx = MCUTransaction(
            tenant_id=tenant_id,
            amount=-cost,
            balance_after=tenant.balance,
            transaction_type="debit",
            description=f"Mission {complexity} ({cost} MCU)",
            mission_id=mission_id,
        )
        tenant.transactions.append(tx)

        result = DeductionResult(
            success=True,
            balance_before=balance_before,
            balance_after=tenant.balance,
            amount_deducted=cost,
            low_balance=tenant.balance < self.low_threshold,
        )

        # Trigger webhook if low balance and not yet notified
        if result.low_balance and tenant_id not in self._notified_tenants:
            self._trigger_low_balance_webhook(tenant_id, tenant.balance)
            self._notified_tenants.add(tenant_id)

        return result

    def refund(
        self,
        tenant_id: str,
        amount: int,
        mission_id: str = "",
    ) -> TenantBalance | None:
        """Refund MCU credits to a tenant.

        Args:
            tenant_id: Tenant identifier
            amount: Credits to refund (must be positive)
            mission_id: Associated mission ID

        Returns:
            Updated TenantBalance, or None if tenant not found

        Raises:
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Refund amount must be positive")

        if tenant_id not in self._tenants:
            return None

        tenant = self._tenants[tenant_id]
        tenant.balance += amount
        tenant.total_refunded += amount

        tx = MCUTransaction(
            tenant_id=tenant_id,
            amount=amount,
            balance_after=tenant.balance,
            transaction_type="refund",
            description=f"Refund {amount} MCU",
            mission_id=mission_id,
        )
        tenant.transactions.append(tx)
        return tenant

    def get_balance(self, tenant_id: str) -> int:
        """Get current MCU balance for a tenant."""
        tenant = self._tenants.get(tenant_id)
        return tenant.balance if tenant else 0

    def get_tenant(self, tenant_id: str) -> TenantBalance | None:
        """Get full tenant balance info."""
        return self._tenants.get(tenant_id)

    def is_low_balance(self, tenant_id: str) -> bool:
        """Check if tenant has low balance."""
        return self.get_balance(tenant_id) < self.low_threshold

    def _trigger_low_balance_webhook(self, tenant_id: str, balance: int) -> None:
        """Trigger credits.low webhook event.

        Args:
            tenant_id: Tenant identifier
            balance: Current credit balance
        """
        if not self._webhook_handler:
            return

        payload = {
            "event_type": "credits.low",
            "tenant_id": tenant_id,
            "current_balance": balance,
            "threshold": self.low_threshold,
            "currency": "MCU",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self._webhook_handler("credits.low", payload)
        except Exception:
            pass  # Log error in production

    def reset_low_balance_notification(self, tenant_id: str) -> None:
        """Reset low balance notification for a tenant (allow re-trigger)."""
        if tenant_id in self._notified_tenants:
            self._notified_tenants.discard(tenant_id)

    @property
    def tenant_count(self) -> int:
        """Number of tenants in the system."""
        return len(self._tenants)


__all__ = [
    "MCUBilling",
    "MCUTransaction",
    "TenantBalance",
    "DeductionResult",
    "MCU_COSTS",
    "TIER_CREDITS",
    "LOW_BALANCE_THRESHOLD",
]
