# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Telemetry Reporter — Usage Metering & Analytics."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class UsageRecord:
    """Single usage record."""

    endpoint: str
    method: str
    status_code: int
    payload_size: int
    timestamp: float
    error: Optional[str] = None
    tenant_id: Optional[str] = None


class TelemetryReporter:
    """Telemetry Reporter with local SQLite buffering."""

    DB_PATH = "~/.mekong/telemetry/usage.db"
    BATCH_SIZE = 10
    FLUSH_INTERVAL = 60

    def __init__(self, gateway_url: Optional[str] = None):
        self.gateway_url = gateway_url or os.getenv("RAAS_GATEWAY_URL", "https://api.cashclaw.cc")
        self.db_path = Path(self.DB_PATH).expanduser()
        self._buffer: list[UsageRecord] = []
        self._last_flush = time.time()
        self._ensure_db()

    def _ensure_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS usage_records ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, endpoint TEXT NOT NULL, method TEXT NOT NULL, "
                "status_code INTEGER NOT NULL, payload_size INTEGER NOT NULL, timestamp REAL NOT NULL, "
                "error TEXT, tenant_id TEXT)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_records(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant ON usage_records(tenant_id)")
            try:
                conn.execute("ALTER TABLE usage_records ADD COLUMN tenant_id TEXT")
            except sqlite3.OperationalError:
                pass

    def record_call(
        self, endpoint: str, method: str, status_code: int, payload_size: int,
        error: Optional[str] = None, tenant_id: Optional[str] = None, gateway_url: Optional[str] = None,
    ) -> None:
        self._buffer.append(
            UsageRecord(endpoint, method, status_code, payload_size, time.time(), error, tenant_id)
        )
        if len(self._buffer) >= self.BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT INTO usage_records (endpoint, method, status_code, payload_size, timestamp, error) VALUES (?, ?, ?, ?, ?, ?)",
                [(r.endpoint, r.method, r.status_code, r.payload_size, r.timestamp, r.error) for r in self._buffer],
            )
            conn.commit()
        self._flush_to_gateway()
        self._buffer.clear()
        self._last_flush = time.time()

    def _flush_to_gateway(self) -> None:
        import requests

        try:
            records = self._get_unsent_records()
            if not records:
                return
            token = self._get_auth_token()
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}" if token else ""}
            response = requests.post(
                f"{self.gateway_url}/v1/usage/report", headers=headers, json={"records": records}, timeout=10
            )
            if response.status_code == 200:
                self._mark_sent(records)
        except Exception as e:
            logging.debug(f"Failed to flush telemetry: {e}")

    def _get_auth_token(self) -> Optional[str]:
        creds_path = Path("~/.mekong/raas/credentials.json").expanduser()
        if creds_path.exists():
            try:
                with open(creds_path) as f:
                    return json.load(f).get("token")
            except (json.JSONDecodeError, OSError) as e:
                logging.debug(f"Failed to load credentials: {e}")
        return os.getenv("RAAS_LICENSE_KEY")

    def _get_unsent_records(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM usage_records WHERE timestamp > ? ORDER BY timestamp ASC LIMIT 100",
                (self._last_flush,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _mark_sent(self, records: list[dict[str, Any]]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM usage_records WHERE timestamp < ?", (time.time() - 86400,))
            conn.commit()

    def get_current_usage(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*), SUM(payload_size), AVG(status_code), MIN(timestamp), MAX(timestamp) "
                "FROM usage_records WHERE timestamp > ?",
                (time.time() - 3600,),
            )
            row = cursor.fetchone()
            return {
                "total_requests": row[0] or 0,
                "total_payload_bytes": row[1] or 0,
                "avg_status_code": row[2] or 0,
                "first_request": datetime.fromtimestamp(row[3], tz=timezone.utc).isoformat() if row[3] else None,
                "last_request": datetime.fromtimestamp(row[4], tz=timezone.utc).isoformat() if row[4] else None,
            }

    def get_metrics(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM usage_records ORDER BY timestamp ASC LIMIT 1000")
            return [dict(row) for row in cursor.fetchall()]

    def get_hourly_metrics(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT strftime('%Y-%m-%d-%H', datetime(timestamp, 'unixepoch')) as hour_bucket, "
                "COUNT(*), SUM(payload_size), endpoint, method "
                "FROM usage_records GROUP BY hour_bucket, endpoint, method ORDER BY hour_bucket ASC"
            )
            return [
                {"hour_bucket": r[0], "request_count": r[1], "payload_size": r[2], "endpoint": r[3], "method": r[4]}
                for r in cursor.fetchall()
            ]


_telemetry_reporter: Optional[TelemetryReporter] = None


def get_telemetry_reporter() -> TelemetryReporter:
    global _telemetry_reporter
    if _telemetry_reporter is None:
        _telemetry_reporter = TelemetryReporter()
    return _telemetry_reporter
