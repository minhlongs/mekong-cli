"""CashClaw billing — Polar.sh subscription management for 3 tiers.

Products:
  CashClaw Starter — $49/month  (5 signals/day, no dark edge)
  CashClaw Pro     — $149/month (20 signals/day, ensemble N=3)
  CashClaw Elite   — $499/month (unlimited, ensemble N=5, custom strategies)

Webhook handler for:
  subscription.created   → provision API key, set tier
  subscription.updated   → update tier
  subscription.cancelled → revoke API key (7-day grace)
  payment.failed         → notify, 3-day retry window
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/polar", tags=["CashClaw Billing"])

POLAR_WEBHOOK_SECRET = os.getenv("POLAR_WEBHOOK_SECRET", "")
DB_PATH = os.getenv("DATABASE_PATH", "data/algo-trade.db")

# Product ID → tier mapping
PRODUCT_TIERS: dict[str, str] = {
    os.getenv("POLAR_STARTER_PRODUCT_ID", "prod_starter"): "starter",
    os.getenv("POLAR_PRO_PRODUCT_ID", "prod_pro"): "pro",
    os.getenv("POLAR_ENTERPRISE_PRODUCT_ID", "prod_enterprise"): "elite",
}


@dataclass
class Subscription:
    """A customer subscription record."""
    subscription_id: str
    user_id: str
    email: str
    tier: str
    api_key: str
    active: bool
    created_at: str
    expires_at: Optional[str] = None
    grace_until: Optional[str] = None


class BillingDB:
    """SQLite-backed subscription store."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create billing tables if not exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'starter',
                    api_key TEXT UNIQUE NOT NULL,
                    active INTEGER DEFAULT 1,
                    created_at TEXT,
                    expires_at TEXT,
                    grace_until TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS billing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    subscription_id TEXT,
                    payload TEXT,
                    processed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def provision_subscription(
        self,
        subscription_id: str,
        user_id: str,
        email: str,
        tier: str,
    ) -> Subscription:
        """Create new subscription and generate API key."""
        api_key = f"ck_{uuid.uuid4().hex}"

        sub = Subscription(
            subscription_id=subscription_id,
            user_id=user_id,
            email=email,
            tier=tier,
            api_key=api_key,
            active=True,
            created_at=datetime.utcnow().isoformat(),
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO subscriptions
                   (subscription_id, user_id, email, tier, api_key, active, created_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?)""",
                (sub.subscription_id, sub.user_id, sub.email,
                 sub.tier, sub.api_key, sub.created_at),
            )

        logger.info(
            "Provisioned subscription %s tier=%s email=%s",
            subscription_id, tier, email,
        )
        return sub

    def update_tier(self, subscription_id: str, new_tier: str) -> bool:
        """Update subscription tier."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE subscriptions SET tier = ? WHERE subscription_id = ?",
                (new_tier, subscription_id),
            )
            return cursor.rowcount > 0

    def cancel_subscription(self, subscription_id: str, grace_days: int = 7) -> bool:
        """Cancel subscription with grace period."""
        grace_until = (datetime.utcnow() + timedelta(days=grace_days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """UPDATE subscriptions
                   SET active = 0, grace_until = ?
                   WHERE subscription_id = ?""",
                (grace_until, subscription_id),
            )
            return cursor.rowcount > 0

    def get_by_api_key(self, api_key: str) -> Optional[Subscription]:
        """Look up subscription by API key."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM subscriptions WHERE api_key = ?",
                (api_key,),
            ).fetchone()

        if row is None:
            return None

        return Subscription(
            subscription_id=row["subscription_id"],
            user_id=row["user_id"],
            email=row["email"],
            tier=row["tier"],
            api_key=row["api_key"],
            active=bool(row["active"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            grace_until=row["grace_until"],
        )

    def get_by_subscription_id(self, subscription_id: str) -> Optional[Subscription]:
        """Look up subscription by Polar subscription ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM subscriptions WHERE subscription_id = ?",
                (subscription_id,),
            ).fetchone()

        if row is None:
            return None

        return Subscription(
            subscription_id=row["subscription_id"],
            user_id=row["user_id"],
            email=row["email"],
            tier=row["tier"],
            api_key=row["api_key"],
            active=bool(row["active"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            grace_until=row["grace_until"],
        )

    def log_event(self, event_type: str, subscription_id: str, payload: str) -> None:
        """Log a billing event for audit."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO billing_events (event_type, subscription_id, payload)
                   VALUES (?, ?, ?)""",
                (event_type, subscription_id, payload),
            )

    def count_active(self) -> dict[str, int]:
        """Count active subscriptions by tier."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT tier, COUNT(*) FROM subscriptions WHERE active = 1 GROUP BY tier"
            ).fetchall()
        return {tier: count for tier, count in rows}


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------

def verify_polar_signature(payload: bytes, signature: str) -> bool:
    """Verify Polar.sh webhook HMAC-SHA256 signature."""
    if not POLAR_WEBHOOK_SECRET:
        logger.warning("POLAR_WEBHOOK_SECRET not set — skipping verification")
        return True  # Allow in dev

    expected = hmac.new(
        POLAR_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    provided = signature.replace("sha256=", "")
    return hmac.compare_digest(expected, provided)


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@router.post("")
async def handle_polar_webhook(request: Request) -> dict:
    """Handle Polar.sh subscription webhooks."""
    # Verify signature
    body = await request.body()
    signature = request.headers.get("X-Polar-Signature", "")

    if not verify_polar_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get("type", "")
    data = payload.get("data", {}).get("object", {})

    db = BillingDB()

    # Log event
    subscription_id = data.get("id", "unknown")
    db.log_event(event_type, subscription_id, body.decode())

    # Route event
    if event_type == "subscription.created":
        return _handle_subscription_created(db, data)
    elif event_type == "subscription.updated":
        return _handle_subscription_updated(db, data)
    elif event_type == "subscription.cancelled":
        return _handle_subscription_cancelled(db, data)
    elif event_type == "payment.failed":
        return _handle_payment_failed(db, data)
    else:
        logger.info("Unhandled webhook event: %s", event_type)
        return {"status": "ignored", "event": event_type}


def _handle_subscription_created(db: BillingDB, data: dict) -> dict:
    """Provision new subscription."""
    product_id = data.get("product_id", "")
    tier = PRODUCT_TIERS.get(product_id, "starter")

    sub = db.provision_subscription(
        subscription_id=data.get("id", ""),
        user_id=data.get("customer_id", ""),
        email=data.get("customer_email", ""),
        tier=tier,
    )

    return {
        "status": "provisioned",
        "tier": tier,
        "api_key": sub.api_key,
        "subscription_id": sub.subscription_id,
    }


def _handle_subscription_updated(db: BillingDB, data: dict) -> dict:
    """Update subscription tier."""
    product_id = data.get("product_id", "")
    new_tier = PRODUCT_TIERS.get(product_id, "starter")
    subscription_id = data.get("id", "")

    db.update_tier(subscription_id, new_tier)
    return {"status": "updated", "tier": new_tier}


def _handle_subscription_cancelled(db: BillingDB, data: dict) -> dict:
    """Cancel subscription with 7-day grace period."""
    subscription_id = data.get("id", "")
    db.cancel_subscription(subscription_id, grace_days=7)
    return {"status": "cancelled", "grace_days": 7}


def _handle_payment_failed(db: BillingDB, data: dict) -> dict:
    """Handle failed payment — 3-day retry window."""
    subscription_id = data.get("subscription_id", "")
    logger.warning("Payment failed for subscription %s", subscription_id)
    return {"status": "payment_failed", "retry_days": 3}
