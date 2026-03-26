"""NOWPayments IPN webhook handler — verify + process crypto payment callbacks.

Verifies HMAC signature, updates credit balance on successful payment.
Mirrors polar_webhook_handler.py pattern for consistency.

Env vars:
    NOWPAYMENTS_IPN_SECRET — IPN secret for HMAC verification
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.raas.credit_account_repository import CreditAccountRepository

logger = logging.getLogger(__name__)

IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "")

# Payment status constants from NOWPayments docs
STATUS_FINISHED = "finished"
STATUS_CONFIRMED = "confirmed"
STATUS_SENDING = "sending"
STATUS_WAITING = "waiting"
STATUS_EXPIRED = "expired"
STATUS_FAILED = "failed"
STATUS_REFUNDED = "refunded"

# Tier detection from order_description or order_id
TIER_CREDITS: dict[str, int] = {
    "starter": 200,
    "pro": 1000,
    "growth": 3000,
    "enterprise": 10000,
}

# Ledger path for audit trail
LEDGER_DIR = Path.home() / ".mekong" / "raas" / "payments"


def verify_ipn_signature(payload_json: str, received_sig: str) -> bool:
    """Verify NOWPayments IPN HMAC-SHA512 signature."""
    if not IPN_SECRET:
        logger.warning("NOWPAYMENTS_IPN_SECRET not set — skipping verification")
        return True

    # NOWPayments sorts keys before hashing
    sorted_payload = json.dumps(json.loads(payload_json), sort_keys=True)
    expected = hmac.new(
        IPN_SECRET.encode(),
        sorted_payload.encode(),
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(expected, received_sig)


def _extract_tier(data: dict) -> str:
    """Extract tier name from order_id or order_description."""
    order_id = data.get("order_id", "").lower()
    description = data.get("order_description", "").lower()

    for tier in TIER_CREDITS:
        if tier in order_id or tier in description:
            return tier
    return "starter"  # fallback


def _log_payment(data: dict, tier: str, credits: int) -> None:
    """Append payment to audit ledger."""
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    ledger_file = LEDGER_DIR / "nowpayments-ledger.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payment_id": data.get("payment_id"),
        "order_id": data.get("order_id"),
        "status": data.get("payment_status"),
        "pay_amount": data.get("pay_amount"),
        "pay_currency": data.get("pay_currency"),
        "price_amount": data.get("price_amount"),
        "price_currency": data.get("price_currency"),
        "tier": tier,
        "credits_granted": credits,
    }

    with ledger_file.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    logger.info(f"[NP] Logged payment {data.get('payment_id')} → {tier} ({credits} credits)")


def handle_ipn(payload_json: str, signature: str = "") -> dict[str, Any]:
    """Process a NOWPayments IPN callback.

    Args:
        payload_json: Raw JSON body from webhook
        signature: x-nowpayments-sig header value

    Returns:
        dict with status, action taken, and any error
    """
    # Verify signature
    if signature and not verify_ipn_signature(payload_json, signature):
        logger.warning("[NP] IPN signature mismatch — rejecting")
        return {"ok": False, "error": "signature_mismatch"}

    data = json.loads(payload_json)
    payment_status = data.get("payment_status", "")
    payment_id = data.get("payment_id", "unknown")

    logger.info(f"[NP] IPN received: payment={payment_id} status={payment_status}")

    # Only process completed payments
    if payment_status not in (STATUS_FINISHED, STATUS_CONFIRMED):
        _log_payment(data, _extract_tier(data), 0)
        return {
            "ok": True,
            "action": "ignored",
            "reason": f"status={payment_status} (not finished/confirmed)",
        }

    # Extract tier and grant credits
    tier = _extract_tier(data)
    credits = TIER_CREDITS.get(tier, 200)

    # Grant credits via CreditAccountRepository
    order_id = data.get("order_id", "")
    workspace_id = order_id.split("-")[0] if "-" in order_id else "default"

    try:
        repo = CreditAccountRepository()
        repo.add_credits(workspace_id, credits, f"nowpayments:{payment_id}")
        _log_payment(data, tier, credits)
        return {
            "ok": True,
            "action": "credits_granted",
            "tier": tier,
            "credits": credits,
            "workspace_id": workspace_id,
            "payment_id": payment_id,
        }
    except Exception as e:
        logger.error(f"[NP] Failed to grant credits: {e}")
        _log_payment(data, tier, 0)
        return {"ok": False, "error": str(e)}
