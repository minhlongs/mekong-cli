# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Particle Balance, Aggregation, and Legacy Tenant Models."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from src.models.particle_models import CURRENCY_USD


@dataclass
class ParticleBalance:
    """Balance snapshot for a key_id at a point in time."""

    key_id: str
    balance: Decimal = field(default_factory=lambda: Decimal("0.0"))
    currency: str = CURRENCY_USD
    last_particle_id: Optional[str] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    particle_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "ParticleBalance":
        """Create ParticleBalance from database row dict."""
        balance = data.get("balance", Decimal("0.0"))
        return cls(
            key_id=data.get("key_id", ""),
            balance=Decimal(balance) if balance is not None else Decimal("0.0"),
            currency=data.get("currency", CURRENCY_USD),
            last_particle_id=data.get("last_particle_id"),
            last_updated=data.get("last_updated") or datetime.now(timezone.utc),
            particle_count=data.get("particle_count", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_id": self.key_id,
            "balance": str(self.balance),
            "currency": self.currency,
            "last_particle_id": self.last_particle_id,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "particle_count": self.particle_count,
        }


@dataclass
class ParticleAggregation:
    """Aggregated particle statistics for reporting."""

    key_id: str
    particle_type: str
    total_amount: Decimal = field(default_factory=lambda: Decimal("0.0"))
    particle_count: int = 0
    currency: str = CURRENCY_USD
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ParticleAggregation":
        """Create from database aggregation result."""
        total = data.get("total_amount", Decimal("0.0"))
        return cls(
            key_id=data.get("key_id", ""),
            particle_type=data.get("particle_type", ""),
            total_amount=Decimal(total) if total is not None else Decimal("0.0"),
            particle_count=data.get("particle_count", 0),
            currency=data.get("currency", CURRENCY_USD),
            period_start=data.get("period_start"),
            period_end=data.get("period_end"),
        )


@dataclass
class Tenant:
    """Legacy tenant record for RaaS multi-tenant isolation."""

    id: str
    name: str
    api_key: str
    created_at: str
    is_active: bool = True


def _hash_key(key: str) -> str:
    """Return the SHA-256 hex digest of *key*."""
    return hashlib.sha256(key.encode()).hexdigest()


def _row_to_tenant(row: dict, api_key: str = "") -> Tenant:
    """Convert a DB row to a Tenant instance."""
    return Tenant(
        id=row["id"],
        name=row["name"],
        api_key=api_key,
        created_at=row["created_at"].isoformat() if isinstance(row["created_at"], datetime) else row["created_at"],
        is_active=bool(row["is_active"]),
    )
