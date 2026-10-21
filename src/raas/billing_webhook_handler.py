# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Polar.sh webhook handler class and product map for RaaS credit provisioning."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
import sqlite3
from typing import Optional

from src.raas.credits import CreditStore

DB_PATH = Path.home() / ".mekong" / "raas" / "tenants.db"

POLAR_PRODUCT_MAP: dict[str, int] = {
    "starter_monthly": 300,
    "growth_monthly": 1200,
    "scale_monthly": 3500,
    "pro_monthly": 7000,
    "enterprise_monthly": 20000,
    "credits_10": 10,
    "credits_50": 50,
    "credits_100": 100,
}


class PolarWebhookHandler:
    """Handles incoming Polar.sh webhook events."""

    def __init__(
        self,
        credit_store: Optional[CreditStore] = None,
        db_path: Path = DB_PATH,
    ) -> None:
        self.credit_store = credit_store or CreditStore(db_path)
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS processed_events (
                        event_id     TEXT PRIMARY KEY,
                        processed_at TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as exc:
            raise RuntimeError(
                f"PolarWebhookHandler: failed to initialize DB: {exc}"
            ) from exc

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _is_duplicate(self, event_id: str) -> bool:
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT event_id FROM processed_events WHERE event_id = ?",
                    (event_id,),
                ).fetchone()
                return row is not None
        except sqlite3.Error as exc:
            raise RuntimeError(f"Idempotency check failed: {exc}") from exc

    def _mark_processed(self, event_id: str) -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO processed_events (event_id, processed_at) "
                    "VALUES (?, ?)",
                    (event_id, self._now_iso()),
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed to mark event processed: {exc}") from exc

    def verify_signature(
        self, payload: bytes, signature: str, secret: str
    ) -> bool:
        """Verify a Polar webhook HMAC-SHA256 signature."""
        expected = hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        sig = signature.removeprefix("sha256=")
        return hmac.compare_digest(expected, sig)

    def provision_credits(self, tenant_id: str, product_id: str) -> int:
        """Map a Polar product to a credit amount and add to tenant account."""
        amount = POLAR_PRODUCT_MAP.get(product_id)
        if amount is None:
            raise ValueError(
                f"Unknown product_id '{product_id}'. "
                f"Known products: {list(POLAR_PRODUCT_MAP)}"
            )
        reason = f"Polar purchase: {product_id}"
        return self.credit_store.add(tenant_id, amount, reason)

    def handle_event(self, event_data: dict) -> dict:
        """Route an incoming Polar event to the appropriate handler."""
        event_type = event_data.get("type", "")
        event_id = event_data.get("id", "")

        if not event_id:
            return {"status": "ignored", "reason": "missing event id"}

        if self._is_duplicate(event_id):
            return {"status": "duplicate", "event_id": event_id}

        result: dict = {"status": "ok", "event_id": event_id, "type": event_type}

        try:
            if event_type in ("order.created", "subscription.created"):
                data = event_data.get("data", {})
                tenant_id = (
                    data.get("customer", {}).get("external_id")
                    or data.get("metadata", {}).get("tenant_id")
                    or data.get("customer_id", "")
                )
                product_id = (
                    data.get("product", {}).get("id")
                    or data.get("product_id", "")
                )
                if not tenant_id or not product_id:
                    result["status"] = "error"
                    result["reason"] = "missing tenant_id or product_id"
                else:
                    new_balance = self.provision_credits(tenant_id, product_id)
                    result["tenant_id"] = tenant_id
                    result["product_id"] = product_id
                    result["new_balance"] = new_balance
            else:
                result["status"] = "acknowledged"
        except (ValueError, RuntimeError) as exc:
            result["status"] = "error"
            result["reason"] = str(exc)
        else:
            self._mark_processed(event_id)

        return result
