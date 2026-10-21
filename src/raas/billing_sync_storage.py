# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite storage and payload building helpers for RaaS Billing Sync Service."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, Optional

from src.raas.billing_sync_models import (
    IDX_USAGE_SYNCED_DDL,
    SYNC_HISTORY_DDL,
    USAGE_RECORDS_DDL,
    SyncConfig,
    UsageRecord,
)


class BillingSyncStorageMixin:
    """SQLite persistence and payload assembly methods for BillingSyncService."""

    config: SyncConfig
    api_key: Optional[str]
    _conn: Optional[sqlite3.Connection]
    _logger: Any

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            db_path = Path(self.config.db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(db_path))
            self._conn.row_factory = sqlite3.Row
            self._init_db()
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        conn.execute(USAGE_RECORDS_DDL)
        conn.execute(SYNC_HISTORY_DDL)
        conn.execute(IDX_USAGE_SYNCED_DDL)
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def generate_idempotency_key(self, records: list[UsageRecord]) -> str:
        content = "|".join(sorted([r.event_id for r in records]))
        return f"mk_idem_{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def fetch_unsynced_records(self, limit: Optional[int] = None) -> list[UsageRecord]:
        conn = self._get_connection()
        query = (
            "SELECT id, event_id, event_type, tenant_id, timestamp, endpoint, model, "
            "input_tokens, output_tokens, duration_ms, metadata, synced, created_at "
            "FROM usage_records WHERE synced = 0 ORDER BY created_at ASC LIMIT ?"
        )
        rows = conn.execute(query, (limit or self.config.batch_size,)).fetchall()
        return [
            UsageRecord(
                id=row["id"], event_id=row["event_id"], event_type=row["event_type"],
                tenant_id=row["tenant_id"], timestamp=row["timestamp"],
                endpoint=row["endpoint"], model=row["model"],
                input_tokens=row["input_tokens"] or 0, output_tokens=row["output_tokens"] or 0,
                duration_ms=row["duration_ms"] or 0.0,
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                synced=bool(row["synced"]), created_at=row["created_at"],
            )
            for row in rows
        ]

    def build_payload(self, records: list[UsageRecord]) -> dict[str, Any]:
        events = []
        total_input = 0
        total_output = 0
        total_duration = 0.0

        for record in records:
            events.append({
                "event_id": record.event_id, "event_type": record.event_type,
                "timestamp": record.timestamp, "endpoint": record.endpoint,
                "model": record.model, "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens, "duration_ms": record.duration_ms,
                "metadata": record.metadata,
            })
            total_input += record.input_tokens
            total_output += record.output_tokens
            total_duration += record.duration_ms

        return {
            "tenant_id": records[0].tenant_id if records else "",
            "license_key": self.api_key or "",
            "events": events,
            "summary": {
                "total_events": len(events),
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_duration_ms": total_duration,
            },
        }

    def mark_as_synced(self, record_ids: list[int]) -> None:
        if not record_ids:
            return
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        placeholders = ",".join("?" * len(record_ids))
        conn.execute(
            f"UPDATE usage_records SET synced = 1, sync_attempts = sync_attempts + 1, synced_at = ? WHERE id IN ({placeholders})",
            [now] + record_ids,
        )
        conn.commit()
        self._logger.info("billing_sync.marked_synced", record_count=len(record_ids))

    def mark_sync_failed(self, record_ids: list[int], error: str) -> None:
        if not record_ids:
            return
        conn = self._get_connection()
        for record_id in record_ids:
            conn.execute(
                "UPDATE usage_records SET sync_attempts = sync_attempts + 1, last_sync_error = ? WHERE id IN (?)",
                (error, record_id),
            )
        conn.commit()

    def record_sync_history(
        self,
        idempotency_key: str,
        records_count: int,
        payload_size: int,
        status: str,
        gateway_response: Optional[dict] = None,
        error: Optional[str] = None,
    ) -> None:
        conn = self._get_connection()
        conn.execute(
            "INSERT INTO sync_history (idempotency_key, records_count, payload_size, status, gateway_response, error) VALUES (?, ?, ?, ?, ?, ?)",
            (
                idempotency_key, records_count, payload_size, status,
                json.dumps(gateway_response) if gateway_response else None, error,
            ),
        )
        conn.commit()


__all__ = ["BillingSyncStorageMixin"]
