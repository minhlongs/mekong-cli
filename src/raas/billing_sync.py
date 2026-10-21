# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Billing Sync Service - Usage Records Synchronization

Synchronizes local usage records from SQLite store to RaaS Gateway.
"""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Any, Optional

import httpx

from src.config.logging_config import get_logger
from src.raas.billing_sync_models import SyncConfig, SyncResult, UsageRecord
from src.raas.billing_sync_storage import BillingSyncStorageMixin
from src.raas.billing_sync_transport import BillingSyncTransportMixin


class BillingSyncService(BillingSyncStorageMixin, BillingSyncTransportMixin):
    """
    Billing Sync Service for usage records synchronization.

    Syncs local SQLite usage records to RaaS Gateway v2/usage endpoint.
    Handles idempotency, retry logic, and error recovery.
    """

    def __init__(self, config: Optional[SyncConfig] = None) -> None:
        self.config = config or SyncConfig()
        self.api_key = (
            self.config.api_key
            or os.getenv("MEKONG_API_KEY")
            or os.getenv("RAAS_LICENSE_KEY")
        )
        self._conn: Optional[sqlite3.Connection] = None
        self._logger = get_logger(__name__)

    def get_sync_status(self) -> dict[str, Any]:
        """Get current sync status."""
        conn = self._get_connection()

        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM usage_records WHERE synced = 0"
        )
        unsynced_count = cursor.fetchone()["count"]

        cursor = conn.execute(
            "SELECT COUNT(*) as count FROM usage_records WHERE synced = 1"
        )
        synced_count = cursor.fetchone()["count"]

        cursor = conn.execute(
            "SELECT MAX(synced_at) as last_sync FROM usage_records WHERE synced = 1"
        )
        row = cursor.fetchone()
        last_sync = row["last_sync"] if row else None

        cursor = conn.execute(
            """
            SELECT idempotency_key, records_count, status, created_at
            FROM sync_history
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        recent_history = [dict(r) for r in cursor.fetchall()]

        return {
            "unsynced_records": unsynced_count,
            "synced_records": synced_count,
            "last_sync": last_sync,
            "recent_history": recent_history,
            "api_key_configured": bool(self.api_key),
            "gateway_url": self.config.gateway_url,
        }

    def force_resync(self, limit: Optional[int] = None) -> SyncResult:
        """Force resync of already synced records."""
        conn = self._get_connection()
        query = """
            UPDATE usage_records
            SET synced = 0,
                last_sync_error = NULL
            WHERE synced = 1
            ORDER BY created_at ASC
            LIMIT ?
        """
        conn.execute(query, (limit or self.config.batch_size,))
        conn.commit()
        return self.sync_to_gateway(limit)


# Global instance
_service: Optional[BillingSyncService] = None


def get_service() -> BillingSyncService:
    """Get global billing sync service instance."""
    global _service
    if _service is None:
        _service = BillingSyncService()
    return _service


def reset_service() -> None:
    """Reset global service instance (for testing)."""
    global _service
    _service = None


__all__ = [
    "BillingSyncService",
    "SyncConfig",
    "SyncResult",
    "UsageRecord",
    "get_service",
    "httpx",
    "reset_service",
    "time",
]
