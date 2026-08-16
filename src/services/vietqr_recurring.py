# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VietQR recurring billing — monthly subscription tracking + auto-renewal.

Handles:
- Record initial pilot→paid conversion as a subscription
- Track renewal dates (30-day cycle)
- Detect overdue/expired subscriptions
- Auto-topup MCU credits on confirmed payment
- Idempotent renewals (same bank_tx_ref → skip)

Storage: delegates to StorageBackend (JSONL or SQLite via _backend()).
Tier config: imported from factory/contracts/pricing.json (single source of truth).
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ---------- Tier config (from factory/contracts/pricing.json — single source) ----------
# Accurate on 2026-07-14. Re-import from contracts update to stay in sync.

_TIER_CREDITS: dict[str, int] = {
    "starter_vnd": 300,  # 199K VND / month
    "growth_vnd": 1200,  # 299K VND / month
    "pro_vnd": 3500,  # 499K VND / month
}

_TIER_PRICES_VND: dict[int, str] = {
    199_000: "starter_vnd",
    299_000: "growth_vnd",
    499_000: "pro_vnd",
}

# ---------- Backend delegation ----------


def _ensure_dir() -> None:
    import src.api.vn_pilot_state as _state
    _state.CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_subscriptions() -> list[dict]:
    from src.services.storage_backend import _backend
    return _backend().load_subscriptions() if hasattr(_backend(), "load_subscriptions") else []


def _append_subscription(record: dict) -> None:
    _ensure_dir()
    from src.services.storage_backend import _backend
    _backend().append_subscription(record)


def _subscriptions_path():
    """Legacy path helper (kept for backwards compat). Writes go via backend."""
    import src.api.vn_pilot_state as _state
    return _state.CONFIG_DIR / "subscriptions.jsonl"


# ---------- Business logic ----------


def create_subscription(
    user_id: str,
    org_id: str,
    tier: str,
    monthly_vnd: int,
    bank_tx_ref: str,
    started_at: Optional[str] = None,
    credits: Optional[int] = None,
) -> dict:
    """Record a new subscription after pilot→paid conversion.

    Idempotent on (user_id, bank_tx_ref) — returns existing if duplicate.
    Idempotent on user_id alone — returns existing subscription without
    overriding renewal_count, last_paid_at, next_due_at, or credits.
    """
    started = started_at or datetime.now(timezone.utc).date().isoformat()
    subs = _load_subs()

    # Full idempotency: same user_id + bank_tx_ref
    for s in subs:
        if s.get("user_id") == user_id and s.get("bank_tx_ref") == bank_tx_ref:
            logger.info("Subscription already exists for %s tx=%s", user_id, bank_tx_ref)
            return s

    # User-level idempotency: return existing, don't replace
    for s in subs:
        if s.get("user_id") == user_id:
            logger.info("Subscription already exists for %s (no replace)", user_id)
            return s

    credits_to_assign = credits or _TIER_CREDITS.get(tier, 300)
    started_date = date.fromisoformat(started)
    next_due = (started_date + timedelta(days=30)).isoformat()

    record = {
        "user_id": user_id,
        "org_id": org_id,
        "tier": tier,
        "monthly_vnd": monthly_vnd,
        "credits": credits_to_assign,
        "status": "active",
        "started_at": started,
        "last_paid_at": started,
        "next_due_at": next_due,
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
    """Process a renewal payment — topup credits + bump next_due_at + 30 days.

    Idempotent on bank_tx_ref — same ref returns last record.
    Also idempotent on user_id + paid_at (same-day duplicate).
    Uses LAST record (most recent state) for idempotency checks.
    """
    paid_at = paid_at or datetime.now(timezone.utc).date().isoformat()
    subs = _load_subs()

    sub = _latest_subscription(subs, user_id)
    if not sub:
        raise ValueError(f"No subscription found for user_id={user_id}")

    # Idempotency: same bank_tx_ref against the LATEST record
    if sub.get("bank_tx_ref") == bank_tx_ref:
        logger.info("Renewal already recorded for %s tx=%s", user_id, bank_tx_ref)
        return sub

    # Idempotency: same paid date
    if sub.get("last_paid_at") == paid_at:
        logger.info("Renewal already recorded for %s on %s", user_id, paid_at)
        return sub

    paid_date = date.fromisoformat(paid_at)
    # next_due_at: 30 days from paid_at (could be late — reset from actual payment)
    next_due = (paid_date + timedelta(days=30)).isoformat()
    renewal_count = sub.get("renewal_count", 0) + 1
    new_credits = _TIER_CREDITS.get(sub.get("tier", "starter_vnd"), 300)

    updated = {
        **sub,
        "status": "active",
        "last_paid_at": paid_at,
        "next_due_at": next_due,
        "renewal_count": renewal_count,
        "bank_tx_ref": bank_tx_ref,
        "credits": new_credits,
    }
    _append_subscription(updated)
    return updated


def get_subscription(user_id: str) -> Optional[dict]:
    """Return current (latest) subscription for a user_id, or None."""
    subs = _load_subs()
    sub = _latest_subscription(subs, user_id)
    if not sub:
        return None
    _refresh_subscription_status(sub)
    return sub


def get_subscription_status(user_id: str) -> str:
    """Return status string: active | overdue | expired | cancelled | none.

    Rules:
    - no subscription → "none"
    - status == "cancelled" → "cancelled"
    - _effective_status == "overdue" → "overdue"
    - _effective_status == "expired" → "expired"
    - otherwise → "active"
    """
    sub = get_subscription(user_id)
    if not sub:
        return "none"
    if sub.get("status") == "cancelled":
        return "cancelled"
    effective = sub.get("_effective_status", sub.get("status", "active"))
    if effective in ("overdue", "expired"):
        return effective
    return "active"


def get_credit_status(user_id: str) -> dict:
    """Return credit + subscription info for paywall decisions.

    Used by API endpoint GET /v1/pilot/credit-status.
    """
    sub = get_subscription(user_id)
    if not sub:
        return {
            "user_id": user_id,
            "status": "none",
            "credits": 0,
            "suggested_tier": "starter_vnd",
            "suggested_price_vnd": 199_000,
        }

    # stale check: next_due in the past
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
        if sub.get("status") in ("cancelled",):
            continue
        next_due = sub.get("next_due_at", "")
        if next_due and next_due < today and sub.get("status") != "expired":
            expired += 1
            record = {
                **sub,
                "status": "expired",
                "expired_at": today,
            }
            _append_subscription(record)
    return {"expired": expired, "scanned": len(subs)}


# ---------- Internal helpers ----------


def _load_subs() -> list[dict]:
    """Load all subscription records for a user. Uses storage backend."""
    from src.services.storage_backend import _backend
    backend = _backend()
    if hasattr(backend, "load_subscriptions"):
        return backend.load_subscriptions()
    # Fallback: read JSONL directly (for legacy/debug)
    path = _subscriptions_path()
    if not path.exists():
        return []
    out: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _latest_subscription(subs: list[dict], user_id: str) -> Optional[dict]:
    """Return the LAST subscription record for a user (most recent state).
    Returns None if user has no subscription.
    """
    matching = [s for s in subs if s.get("user_id") == user_id]
    return matching[-1] if matching else None


def _refresh_subscription_status(sub: dict) -> None:
    """Mutate sub in-place with effective status — no append (read-only)."""
    today = datetime.now(timezone.utc).date().isoformat()
    next_due = sub.get("next_due_at", "")
    if next_due and next_due < today and sub.get("status") not in ("cancelled", "expired"):
        sub["_effective_status"] = "overdue"
    else:
        sub["_effective_status"] = sub.get("status", "active")
