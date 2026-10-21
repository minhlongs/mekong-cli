# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Batch execution and status query mixin for IdempotencyManager."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.raas.billing_idempotency_models import BatchRecord, BatchResult, BatchStatus

logger = logging.getLogger(__name__)


class IdempotencyBatchProcessorMixin:
    """Batch processing orchestration for IdempotencyManager."""

    _repo: Any

    def generate_batch_id(
        self,
        license_key: str,
        events: List[Dict[str, Any]],
        timestamp: Optional[datetime] = None,
    ) -> str: ...

    async def check_or_create_batch(
        self,
        batch_id: str,
        license_key: str,
        key_id: str,
        events_count: int,
    ) -> tuple[Optional[BatchRecord], bool]: ...

    async def mark_processing(self, batch_id: str) -> bool: ...
    async def mark_completed(
        self,
        batch_id: str,
        billing_record_id: str,
        processed_count: Optional[int] = None,
    ) -> bool: ...
    async def mark_failed(self, batch_id: str, error_message: str) -> bool: ...

    async def process_batch(
        self,
        batch_id: str,
        license_key: str,
        key_id: str,
        events: List[Dict[str, Any]],
        process_fn: Any,
    ) -> BatchResult:
        """Process a batch with idempotency guarantees."""
        timestamp = datetime.now(timezone.utc)

        if not batch_id:
            batch_id = self.generate_batch_id(license_key, events, timestamp)

        batch_record, is_duplicate = await self.check_or_create_batch(
            batch_id=batch_id,
            license_key=license_key,
            key_id=key_id,
            events_count=len(events),
        )

        if is_duplicate:
            if batch_record:
                if batch_record.status == BatchStatus.COMPLETED:
                    return BatchResult(
                        batch_id=batch_id,
                        license_key=license_key,
                        status=batch_record.status,
                        is_duplicate=True,
                        billing_record_id=batch_record.billing_record_id,
                        created_at=batch_record.created_at,
                    )
                if batch_record.status == BatchStatus.PROCESSING:
                    logger.warning(f"Batch {batch_id} still processing")
                    return BatchResult(
                        batch_id=batch_id,
                        license_key=license_key,
                        status=BatchStatus.PROCESSING,
                        is_duplicate=True,
                        error_message="Batch still processing",
                        created_at=batch_record.created_at,
                    )
                if batch_record.status == BatchStatus.FAILED:
                    logger.info(f"Retrying failed batch {batch_id}")
                else:
                    return BatchResult(
                        batch_id=batch_id,
                        license_key=license_key,
                        status=batch_record.status,
                        is_duplicate=True,
                        created_at=batch_record.created_at,
                    )
            else:
                return BatchResult(
                    batch_id=batch_id,
                    license_key=license_key,
                    status=BatchStatus.PENDING,
                    is_duplicate=True,
                    error_message="Unknown batch state",
                )

        if not batch_record:
            await asyncio.sleep(0.1)
            existing = await self._repo.check_batch_idempotency(batch_id)
            if existing:
                return BatchResult(
                    batch_id=batch_id,
                    license_key=license_key,
                    status=BatchStatus(existing["status"]),
                    is_duplicate=True,
                    billing_record_id=existing.get("billing_record_id"),
                    created_at=existing["created_at"],
                )

        await self.mark_processing(batch_id)

        try:
            billing_record_id = await process_fn(events)
            await self.mark_completed(batch_id, billing_record_id)
            return BatchResult(
                batch_id=batch_id,
                license_key=license_key,
                status=BatchStatus.COMPLETED,
                is_duplicate=False,
                billing_record_id=billing_record_id,
                created_at=timestamp,
            )
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            await self.mark_failed(batch_id, str(e))
            return BatchResult(
                batch_id=batch_id,
                license_key=license_key,
                status=BatchStatus.FAILED,
                is_duplicate=False,
                error_message=str(e),
                created_at=timestamp,
            )

    async def get_batch_status(self, batch_id: str) -> Optional[BatchRecord]:
        """Get current batch status."""
        result = await self._repo.check_batch_idempotency(batch_id)
        if not result:
            return None

        return BatchRecord(
            batch_id=result["batch_id"],
            license_key=result["license_key"],
            key_id=result["key_id"],
            events_count=result["events_count"],
            status=BatchStatus(result["status"]),
            created_at=result["created_at"],
            processed_at=result.get("processed_at"),
            billing_record_id=result.get("billing_record_id"),
            error_message=result.get("error_message"),
        )

    async def cleanup_expired_batches(self, max_age_hours: int = 720) -> int:
        """Clean up expired batch records."""
        logger.info(f"Cleanup requested for batches older than {max_age_hours}h")
        return 0
