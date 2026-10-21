# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

# DEPRECATED: logic lives here; import via the backward-compat shim
# src.billing.idempotency instead. New code should import from
# src.raas.billing_adapter (BillingAdapter) — the canonical billing entry
# point. See Phase 9 billing consolidation.

"""
Mekong CLI - Idempotency Layer

Prevent double-billing on batch processing with batch ID tracking
and concurrent submission safety.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.db.repository import LicenseRepository, get_repository
from src.raas.billing_idempotency_models import BatchRecord, BatchResult, BatchStatus
from src.raas.billing_idempotency_processor import IdempotencyBatchProcessorMixin

logger = logging.getLogger(__name__)


class IdempotencyManager(IdempotencyBatchProcessorMixin):
    """
    Manage batch idempotency for billing processing.

    Features:
    - Batch ID generation from usage events
    - Duplicate detection via database lookup
    - Concurrent submission handling with row-level locking
    - Retry support for failed batches
    """

    def __init__(self, repository: Optional[LicenseRepository] = None) -> None:
        self._repo = repository or get_repository()
        self._lock_timeout = 5000  # 5 seconds
        self._batch_ttl_hours = 720  # 30 days

    def generate_batch_id(
        self,
        license_key: str,
        events: List[Dict[str, Any]],
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Generate deterministic batch ID from usage events."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        event_sigs = [
            f"{event.get('event_type', '')}:{event.get('value', 0)}:{event.get('metric', '')}"
            for event in events
        ]
        event_sigs.sort()

        content = f"{license_key}:{timestamp.date()}:{'|'.join(event_sigs)}"
        batch_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        return f"batch_{license_key}_{timestamp.strftime('%Y%m%d')}_{batch_hash}"

    async def check_or_create_batch(
        self,
        batch_id: str,
        license_key: str,
        key_id: str,
        events_count: int,
    ) -> tuple[Optional[BatchRecord], bool]:
        """Check if batch exists, create if not."""
        existing = await self._repo.check_batch_idempotency(batch_id)
        if existing:
            return BatchRecord(
                batch_id=existing["batch_id"],
                license_key=existing["license_key"],
                key_id=existing["key_id"],
                events_count=existing["events_count"],
                status=BatchStatus(existing["status"]),
                created_at=existing["created_at"],
                processed_at=existing.get("processed_at"),
                billing_record_id=existing.get("billing_record_id"),
                error_message=existing.get("error_message"),
            ), True

        try:
            result = await self._repo.create_batch_idempotency(
                batch_id=batch_id,
                license_key=license_key,
                key_id=key_id,
                events_count=events_count,
            )

            if result:
                new_record = BatchRecord(
                    batch_id=result["batch_id"],
                    license_key=result["license_key"],
                    key_id=result["key_id"],
                    events_count=result["events_count"],
                    status=BatchStatus.PENDING,
                    created_at=result["created_at"],
                )
                return new_record, False

            logger.warning(f"Batch creation failed for {batch_id}")
            return None, False

        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                logger.info(f"Concurrent batch creation detected: {batch_id}")
                return None, True
            raise

    async def mark_processing(self, batch_id: str) -> bool:
        """Mark batch as processing."""
        return await self._repo.update_batch_idempotency(
            batch_id=batch_id,
            status="processing",
        )

    async def mark_completed(
        self,
        batch_id: str,
        billing_record_id: str,
        processed_count: Optional[int] = None,
    ) -> bool:
        """Mark batch as completed."""
        return await self._repo.update_batch_idempotency(
            batch_id=batch_id,
            status="completed",
            billing_record_id=billing_record_id,
        )

    async def mark_failed(
        self,
        batch_id: str,
        error_message: str,
    ) -> bool:
        """Mark batch as failed."""
        return await self._repo.update_batch_idempotency(
            batch_id=batch_id,
            status="failed",
            error_message=error_message,
        )


# Module-level singleton
_manager: Optional[IdempotencyManager] = None


def get_idempotency_manager() -> IdempotencyManager:
    """Get or create the idempotency manager singleton."""
    global _manager
    if _manager is None:
        _manager = IdempotencyManager()
    return _manager


def reset_idempotency_manager() -> None:
    """Reset singleton (for testing)."""
    global _manager
    _manager = None


__all__ = [
    "BatchStatus",
    "BatchRecord",
    "BatchResult",
    "IdempotencyManager",
    "get_idempotency_manager",
    "reset_idempotency_manager",
]
