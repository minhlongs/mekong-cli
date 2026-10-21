# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Economic Particle Constants and Core Dataclass."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

PARTICLE_TYPE_USAGE = "usage"
PARTICLE_TYPE_CREDIT = "credit"
PARTICLE_TYPE_ADJUSTMENT = "adjustment"
PARTICLE_TYPE_ADJUSTMENT_POSITIVE = "adjustment_positive"
PARTICLE_TYPE_ADJUSTMENT_NEGATIVE = "adjustment_negative"
PARTICLE_TYPE_PAYMENT = "payment"
PARTICLE_TYPE_REFUND = "refund"
PARTICLE_TYPE_FEE = "fee"
PARTICLE_TYPE_SUBSCRIPTION = "subscription"

SOURCE_API = "api"
SOURCE_MANUAL = "manual"
SOURCE_WEBHOOK = "webhook"
SOURCE_CRON = "cron"
SOURCE_ADMIN = "admin"
SOURCE_MIGRATION = "migration"
SOURCE_RECONCILIATION = "reconciliation"

CURRENCY_USD = "USD"
CURRENCY_VND = "VND"
CURRENCY_EUR = "EUR"

VALID_PARTICLE_TYPES = {
    PARTICLE_TYPE_USAGE, PARTICLE_TYPE_CREDIT, PARTICLE_TYPE_ADJUSTMENT,
    PARTICLE_TYPE_ADJUSTMENT_POSITIVE, PARTICLE_TYPE_ADJUSTMENT_NEGATIVE,
    PARTICLE_TYPE_PAYMENT, PARTICLE_TYPE_REFUND, PARTICLE_TYPE_FEE, PARTICLE_TYPE_SUBSCRIPTION,
}

VALID_SOURCES = {
    SOURCE_API, SOURCE_MANUAL, SOURCE_WEBHOOK, SOURCE_CRON,
    SOURCE_ADMIN, SOURCE_MIGRATION, SOURCE_RECONCILIATION,
}

VALID_CURRENCIES = {CURRENCY_USD, CURRENCY_VND, CURRENCY_EUR}


@dataclass
class EconomicParticle:
    """Immutable snapshot of an economic particle (atomic financial event)."""

    id: Optional[str] = None
    tenant_id: Optional[str] = None
    key_id: str = ""
    particle_type: str = PARTICLE_TYPE_USAGE
    amount: Decimal = field(default_factory=lambda: Decimal("0.0"))
    currency: str = CURRENCY_USD
    balance_after: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = SOURCE_API
    reference_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_reference_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.particle_type not in VALID_PARTICLE_TYPES:
            raise ValueError(
                f"Invalid particle_type: {self.particle_type}. "
                f"Valid types: {', '.join(VALID_PARTICLE_TYPES)}"
            )
        if self.source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid source: {self.source}. "
                f"Valid sources: {', '.join(VALID_SOURCES)}"
            )
        if self.currency not in VALID_CURRENCIES:
            raise ValueError(
                f"Invalid currency: {self.currency}. "
                f"Valid currencies: {', '.join(VALID_CURRENCIES)}"
            )
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))
        if self.balance_after is not None and not isinstance(self.balance_after, Decimal):
            self.balance_after = Decimal(str(self.balance_after))
        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)
        if self.updated_at.tzinfo is None:
            self.updated_at = self.updated_at.replace(tzinfo=timezone.utc)

    @classmethod
    def from_dict(cls, data: dict) -> "EconomicParticle":
        """Create EconomicParticle from database row dict."""
        amount = data.get("amount", Decimal("0.0"))
        balance_after = data.get("balance_after")
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        elif updated_at is None:
            updated_at = datetime.now(timezone.utc)

        return cls(
            id=str(data.get("id", uuid.uuid4())),
            tenant_id=data.get("tenant_id"),
            key_id=data.get("key_id", ""),
            particle_type=data.get("particle_type", PARTICLE_TYPE_USAGE),
            amount=Decimal(amount) if amount is not None else Decimal("0.0"),
            currency=data.get("currency", CURRENCY_USD),
            balance_after=Decimal(balance_after) if balance_after is not None else None,
            metadata=data.get("metadata", {}),
            source=data.get("source", SOURCE_API),
            reference_id=data.get("reference_id"),
            created_at=created_at,
            updated_at=updated_at,
            tenant_reference_id=data.get("tenant_reference_id"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert EconomicParticle to dict for database insertion/update."""
        return {
            "id": self.id, "tenant_id": self.tenant_id, "key_id": self.key_id,
            "particle_type": self.particle_type, "amount": str(self.amount),
            "currency": self.currency,
            "balance_after": str(self.balance_after) if self.balance_after is not None else None,
            "metadata": self.metadata, "source": self.source, "reference_id": self.reference_id,
            "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat(),
            "tenant_reference_id": self.tenant_reference_id,
        }

    def to_insert_sql(self) -> tuple[str, List[Any]]:
        """Generate SQL insert statement and parameters."""
        query = """
            INSERT INTO economic_particles (
                id, tenant_id, key_id, particle_type, amount, currency,
                balance_after, metadata, source, reference_id, created_at, updated_at,
                tenant_reference_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
        """
        params = [
            self.id, self.tenant_id, self.key_id, self.particle_type,
            self.amount, self.currency, self.balance_after, self.metadata,
            self.source, self.reference_id, self.created_at, self.updated_at,
            self.tenant_reference_id,
        ]
        return query, params

    def is_credit(self) -> bool:
        return self.amount > Decimal("0")

    def is_debit(self) -> bool:
        return self.amount < Decimal("0")

    def is_usage(self) -> bool:
        return self.particle_type == PARTICLE_TYPE_USAGE

    def get_effective_amount(self) -> Decimal:
        return self.amount
