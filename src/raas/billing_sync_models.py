# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and schema constants for RaaS Billing Sync Service."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

USAGE_RECORDS_DDL = """
    CREATE TABLE IF NOT EXISTS usage_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT UNIQUE NOT NULL,
        event_type TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        endpoint TEXT,
        model TEXT,
        input_tokens INTEGER DEFAULT 0,
        output_tokens INTEGER DEFAULT 0,
        duration_ms REAL DEFAULT 0,
        metadata TEXT,
        synced INTEGER DEFAULT 0,
        sync_attempts INTEGER DEFAULT 0,
        last_sync_error TEXT,
        synced_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""

SYNC_HISTORY_DDL = """
    CREATE TABLE IF NOT EXISTS sync_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idempotency_key TEXT UNIQUE NOT NULL,
        records_count INTEGER NOT NULL,
        payload_size INTEGER NOT NULL,
        status TEXT NOT NULL,
        gateway_response TEXT,
        error TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""

IDX_USAGE_SYNCED_DDL = """
    CREATE INDEX IF NOT EXISTS idx_usage_synced
    ON usage_records(synced, created_at)
"""


@dataclass
class SyncConfig:
    """Configuration for billing sync."""

    db_path: str = field(
        default_factory=lambda: str(Path.home() / ".mekong" / "usage.db")
    )
    gateway_url: str = "https://raas.mekongmind.com/v2/usage"
    api_key: Optional[str] = None
    batch_size: int = 100
    max_retries: int = 5
    base_backoff_seconds: float = 1.0
    max_backoff_seconds: float = 60.0
    request_timeout_seconds: float = 30.0


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    records_synced: int
    records_failed: int
    total_payload_size: int
    elapsed_ms: float
    error: Optional[str] = None
    gateway_response: Optional[dict] = None
    idempotency_key: Optional[str] = None
    retry_count: int = 0


@dataclass
class UsageRecord:
    """Single usage record from local store."""

    id: int
    event_id: str
    event_type: str
    tenant_id: str
    timestamp: str
    endpoint: Optional[str]
    model: Optional[str]
    input_tokens: int
    output_tokens: int
    duration_ms: float
    metadata: dict
    synced: bool
    created_at: str


__all__ = [
    "IDX_USAGE_SYNCED_DDL",
    "SYNC_HISTORY_DDL",
    "SyncConfig",
    "SyncResult",
    "USAGE_RECORDS_DDL",
    "UsageRecord",
]
