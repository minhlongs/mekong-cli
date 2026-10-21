# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models for RaaS Billing Idempotency Layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional


class BatchStatus(str, Enum):
    """Batch processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BatchRecord:
    """Batch processing record."""

    batch_id: str
    license_key: str
    key_id: str
    events_count: int
    status: BatchStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    billing_record_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "batch_id": self.batch_id,
            "license_key": self.license_key,
            "key_id": self.key_id,
            "events_count": self.events_count,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "billing_record_id": self.billing_record_id,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchRecord":
        """Deserialize from dictionary."""
        return cls(
            batch_id=data["batch_id"],
            license_key=data["license_key"],
            key_id=data["key_id"],
            events_count=data["events_count"],
            status=BatchStatus(data["status"]),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now(timezone.utc)
            ),
            processed_at=(
                datetime.fromisoformat(data["processed_at"])
                if data.get("processed_at")
                else None
            ),
            billing_record_id=data.get("billing_record_id"),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class BatchResult:
    """Result of batch processing."""

    batch_id: str
    license_key: str
    status: BatchStatus
    is_duplicate: bool
    billing_record_id: Optional[str] = None
    error_message: Optional[str] = None
    processed_count: int = 0
    total_charge: Decimal = Decimal(0)
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "batch_id": self.batch_id,
            "license_key": self.license_key,
            "status": self.status.value,
            "is_duplicate": self.is_duplicate,
            "billing_record_id": self.billing_record_id,
            "error_message": self.error_message,
            "processed_count": self.processed_count,
            "total_charge": str(self.total_charge),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


__all__ = [
    "BatchRecord",
    "BatchResult",
    "BatchStatus",
]
