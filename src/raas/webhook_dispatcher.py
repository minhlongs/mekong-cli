"""Webhook dispatcher with exponential backoff retry for RaaS events.

Delivers RaaSWebhookEvents to tenant-configured URLs with:
- Idempotency via event_id deduplication
- Exponential backoff (max 5 retries, cap 300s)
- HMAC-SHA256 signature header
"""
from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json

from src.raas.webhook_events import RaaSWebhookEvent

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"

_RETRY_DELAYS = (10, 30, 90, 180, 300)  # seconds between retries


class WebhookDispatcher:
    """Delivers webhook events to tenant endpoints with retry logic.

    Uses SQLite to track delivered events for idempotency.
    All HTTP calls are synchronous (intended for background thread usage).
    """

    def __init__(
        self,
        db_path: Path = _DB_PATH,
        signing_secret: str = "",
    ) -> None:
        self._db_path = db_path
        self._secret = signing_secret
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS webhook_deliveries (
                        event_id     TEXT NOT NULL,
                        tenant_id    TEXT NOT NULL,
                        delivered_at TEXT,
                        attempts     INTEGER NOT NULL DEFAULT 0,
                        last_status  INTEGER,
                        PRIMARY KEY (event_id, tenant_id)
                    )
                    """
                )
        except sqlite3.Error as exc:
            logger.warning("WebhookDispatcher: DB init failed: %s", exc)

    def _already_delivered(self, event_id: str, tenant_id: str) -> bool:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT delivered_at FROM webhook_deliveries "
                    "WHERE event_id=? AND tenant_id=? AND delivered_at IS NOT NULL",
                    (event_id, tenant_id),
                ).fetchone()
                return row is not None
        except sqlite3.Error:
            return False

    def _record_attempt(
        self,
        event_id: str,
        tenant_id: str,
        status_code: Optional[int],
        success: bool,
    ) -> None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat() if success else None
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO webhook_deliveries
                        (event_id, tenant_id, delivered_at, attempts, last_status)
                    VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(event_id, tenant_id) DO UPDATE SET
                        attempts    = attempts + 1,
                        last_status = excluded.last_status,
                        delivered_at = COALESCE(excluded.delivered_at, delivered_at)
                    """,
                    (event_id, tenant_id, now, status_code),
                )
        except sqlite3.Error as exc:
            logger.warning("WebhookDispatcher: record attempt failed: %s", exc)

    def deliver(
        self,
        event: RaaSWebhookEvent,
        url: str,
        timeout: int = 10,
    ) -> bool:
        """Deliver an event to a URL with exponential backoff.

        Args:
            event: The webhook event to deliver.
            url: Tenant webhook endpoint.
            timeout: Per-attempt HTTP timeout in seconds.

        Returns:
            True if delivered successfully, False after all retries exhausted.
        """
        if self._already_delivered(event.event_id, event.tenant_id):
            logger.debug("Webhook %s already delivered, skipping", event.event_id)
            return True

        body = json.dumps(event.to_dict()).encode()
        signature = event.sign(self._secret) if self._secret else ""

        headers = {
            "Content-Type": "application/json",
            "X-RaaS-Event": event.event_type.value,
            "X-RaaS-Event-ID": event.event_id,
            "X-RaaS-Signature": f"sha256={signature}",
        }

        for attempt, delay in enumerate([0] + list(_RETRY_DELAYS)):
            if delay:
                logger.info(
                    "Webhook retry %d/%d for %s in %ds",
                    attempt, len(_RETRY_DELAYS), event.event_id, delay,
                )
                time.sleep(delay)

            try:
                req = Request(url, data=body, headers=headers, method="POST")
                with urlopen(req, timeout=timeout) as resp:
                    status = resp.status
                if 200 <= status < 300:
                    self._record_attempt(event.event_id, event.tenant_id, status, True)
                    logger.info("Webhook delivered: %s -> %d", event.event_id, status)
                    return True
                self._record_attempt(event.event_id, event.tenant_id, status, False)
                logger.warning("Webhook %s got HTTP %d", event.event_id, status)
            except HTTPError as exc:
                self._record_attempt(event.event_id, event.tenant_id, exc.code, False)
                logger.warning("Webhook HTTP error %d: %s", exc.code, exc)
            except (URLError, OSError) as exc:
                self._record_attempt(event.event_id, event.tenant_id, None, False)
                logger.warning("Webhook network error: %s", exc)

        logger.error("Webhook %s exhausted all retries", event.event_id)
        return False
