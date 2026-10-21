# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VietQR recurring billing — monthly subscription tracking + auto-renewal."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from src.services.vietqr_recurring_store import (
    _TIER_CREDITS,
    _TIER_PRICES_VND,
    _append_subscription,
    _ensure_dir,
    _latest_subscription,
    _load_subs,
    _load_subscriptions,
    _refresh_subscription_status,
    _subscriptions_path,
)

logger = logging.getLogger(__name__)


def create_subscription(
    user_id: str,
    org_id: str,
    tier: str,
    monthly_vnd: int,
    bank_tx_ref: str,
    started_at: Optional[str] = None,
    credits: Optional[int] = None,
) -> dict:
    """Record a new subscription after pilot→paid conversion."""
    started = started_at or datetime.now(timezone.utc).date().isoformat()
    subs = _load_subs()

    for s in subs:
        if s.get("user_id") == user_id and s.get("bank_tx_ref") == bank_tx_ref:
            logger.info("Subscription already exists for %s tx=%s", user_id, bank_tx_ref)
            return s
    for s in subs:
        if s.get("user_id") == user_id:
            logger.info("Subscription already exists for %s (no replace)", user_id)
            return s

    record = {
        "user_id": user_id,
        "org_id": org_id,
        "tier": tier,
        "monthly_vnd": monthly_vnd,
        "credits": credits or _TIER_CREDITS.get(tier, 300),
        "status": "active",
        "started_at": started,
        "last_paid_at": started,
        "next_due_at": (date.fromisoformat(started) + timedelta(days=30)).isoformat(),
        "bank_tx_ref": bank_tx_ref,
        "renewal_count": 0,
    }
    _append_subscription(record)
    return record


def renew_subscription(
    user_id: str,
    bank_tx_ref: str,
    paid_at: Optional[str] = None,
) -> dict:
    """Process a renewal payment — topup credits + bump next_due_at + 30 days."""
    paid_at = paid_at or datetime.now(timezone.utc).date().isoformat()
    sub = _latest_subscription(_load_subs(), user_id)
    if not sub:
        raise ValueError(f"No subscription found for user_id={user_id}")
    if sub.get("bank_tx_ref") == bank_tx_ref:
        logger.info("Renewal already recorded for %s tx=%s", user_id, bank_tx_ref)
        return sub
    if sub.get("last_paid_at") == paid_at:
        logger.info("Renewal already recorded for %s on %s", user_id, paid_at)
        return sub

    updated = {
        **sub,
        "status": "active",
        "last_paid_at": paid_at,
        "next_due_at": (date.fromisoformat(paid_at) + timedelta(days=30)).isoformat(),
        "renewal_count": sub.get("renewal_count", 0) + 1,
        "bank_tx_ref": bank_tx_ref,
        "credits": _TIER_CREDITS.get(sub.get("tier", "starter_vnd"), 300),
    }
    _append_subscription(updated)
    return updated


def get_subscription(user_id: str) -> Optional[dict]:
    """Return current (latest) subscription for a user_id, or None."""
    sub = _latest_subscription(_load_subs(), user_id)
    if not sub:
        return None
    _refresh_subscription_status(sub)
    return sub


def get_subscription_status(user_id: str) -> str:
    """Return status string: active | overdue | expired | cancelled | none."""
    sub = get_subscription(user_id)
    if not sub:
        return "none"
    if sub.get("status") == "cancelled":
        return "cancelled"
    effective = sub.get("_effective_status", sub.get("status", "active"))
    return effective if effective in ("overdue", "expired") else "active"


def get_credit_status(user_id: str) -> dict:
    """Return credit + subscription info for paywall decisions."""
    sub = get_subscription(user_id)
    if not sub:
        return {
            "user_id": user_id,
            "status": "none",
            "credits": 0,
            "suggested_tier": "starter_vnd",
            "suggested_price_vnd": 199_000,
        }
    today = datetime.now(timezone.utc).date().isoformat()
    overdue = sub.get("next_due_at", "") < today if sub.get("next_due_at") else False
    return {
        "user_id": user_id,
        "status": "overdue" if overdue else sub.get("status", "active"),
        "credits": sub.get("credits", 0),
        "tier": sub.get("tier"),
        "monthly_vnd": sub.get("monthly_vnd"),
        "next_due_at": sub.get("next_due_at"),
        "renewal_count": sub.get("renewal_count", 0),
        "suggested_tier": sub.get("tier", "starter_vnd"),
        "suggested_price_vnd": sub.get("monthly_vnd", 199_000),
    }


def expire_overdue_subscriptions() -> dict:
    """Mark overdue subscriptions as expired. Returns stats dict."""
    subs = _load_subs()
    today = datetime.now(timezone.utc).date().isoformat()
    expired = 0
    for sub in subs:
        if sub.get("status") == "cancelled":
            continue
        next_due = sub.get("next_due_at", "")
        if next_due and next_due < today and sub.get("status") != "expired":
            expired += 1
            _append_subscription({**sub, "status": "expired", "expired_at": today})
    return {"expired": expired, "scanned": len(subs)}


__all__ = [
    "_TIER_CREDITS",
    "_TIER_PRICES_VND",
    "_ensure_dir",
    "_load_subscriptions",
    "_append_subscription",
    "_subscriptions_path",
    "create_subscription",
    "renew_subscription",
    "get_subscription",
    "get_subscription_status",
    "get_credit_status",
    "expire_overdue_subscriptions",
    "_load_subs",
    "_latest_subscription",
    "_refresh_subscription_status",
]
