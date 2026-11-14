# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""NOWPayments IPN webhook handler — verify + process crypto payment callbacks.

Verifies HMAC signature, enforces Decree 52/2024/ND-CP domestic rail restrictions
against Vietnamese jurisdictions, and updates credit balance on valid overseas payments.

Env vars:
    NOWPAYMENTS_IPN_SECRET — IPN secret for HMAC verification
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import re
from typing import Any

from src.raas.credit_account_repository import CreditAccountRepository
from src.raas.nowpayments_checkout import TIERS
from src.raas.tenant import TenantStore

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

# Ledger path for audit trail
LEDGER_DIR = Path.home() / ".mekong" / "raas" / "payments"

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_VN_ONLY_TIER_TOKENS = ("pilot_a", "pilot-a", "agency", "agency_vn", "starter_vn", "growth_vn", "pro_vn")


def _clean_log_val(val: object) -> str:
    return str(val or "").replace("\r", " ").replace("\n", " ")[:160]


def verify_ipn_signature(payload_json: str, received_sig: str) -> bool:
    """Verify NOWPayments IPN HMAC-SHA512 signature."""
    if not IPN_SECRET:
        logger.error("NOWPAYMENTS_IPN_SECRET not set — rejecting webhook")
        return False

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

    for tier in ("free", "trial", "starter", "growth", "pro", "enterprise"):
        if tier in order_id or tier in description:
            return tier
    return "starter"  # fallback


def _is_vn_jurisdiction_ipn(data: dict[str, Any], order_id: str, workspace_id: str) -> bool:
    """Return True when any Decree 52/2024 Vietnamese jurisdiction signal is present."""
    for key in ("jurisdiction", "country"):
        val = str(data.get(key) or "").strip().upper()
        if val.startswith("VN"):
            return True

    for curr_key in ("price_currency", "pay_currency"):
        if str(data.get(curr_key) or "").strip().lower() == "vnd":
            return True

    explicit_ws = str(data.get("workspace_id") or data.get("org_id") or data.get("tenant_id") or "").strip()
    for ident in (order_id, workspace_id, explicit_ws):
        low = ident.strip().lower()
        if low == "vn" or low.startswith(("vn-", "vn_")):
            return True

    order_low = order_id.lower()
    desc_low = str(data.get("order_description") or "").lower()
    tier_low = str(data.get("tier") or "").strip().lower()
    if tier_low in _VN_ONLY_TIER_TOKENS:
        return True
    if any(tok in order_low or tok in desc_low for tok in _VN_ONLY_TIER_TOKENS):
        return True

    candidates: list[str] = []
    if explicit_ws:
        candidates.append(explicit_ws)
    if workspace_id and workspace_id != "default":
        candidates.append(workspace_id)
    if order_id:
        candidates.append(order_id)
        candidates.extend(_UUID_RE.findall(order_id))
    customer_email = str(data.get("customer_email") or "").strip()
    if customer_email:
        candidates.append(customer_email)

    if not candidates:
        return True

    env_db = os.environ.get("MEKONG_RAAS_DB")
    try:
        store = TenantStore(Path(env_db)) if env_db else TenantStore()
        with closing(store._connect()) as conn:
            for candidate in dict.fromkeys(candidates):
                row = conn.execute(
                    "SELECT jurisdiction FROM tenants WHERE id = ? OR name = ?",
                    (candidate, candidate),
                ).fetchone()
                if row is not None:
                    jur = str(row["jurisdiction"] or "").strip().upper()
                    if not jur or jur.startswith("VN"):
                        return True
    except Exception as exc:
        logger.error("[NP] TenantStore lookup error during jurisdiction check (failing closed): %s", exc)
        return True

    return False


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
    # Verify signature (mandatory whenever IPN_SECRET is configured)
    if (IPN_SECRET or signature) and not verify_ipn_signature(payload_json, signature):
        logger.warning("[NP] IPN signature mismatch or missing — rejecting")
        return {"ok": False, "error": "signature_mismatch"}

    data = json.loads(payload_json)
    payment_status = _clean_log_val(data.get("payment_status", ""))
    payment_id = _clean_log_val(data.get("payment_id", "unknown"))
    order_id = str(data.get("order_id") or "")
    lead_uuid = _UUID_RE.match(order_id)
    workspace_id = lead_uuid.group(0) if lead_uuid else (order_id.split("-")[0] if "-" in order_id else "default")

    logger.info("[NP] IPN received: payment=%s status=%s", payment_id, payment_status)

    # Decree 52/2024/ND-CP fourth-door guard: domestic VN entities settle exclusively via VietQR
    if _is_vn_jurisdiction_ipn(data, order_id=order_id, workspace_id=workspace_id):
        logger.warning("[NP] Blocked VN jurisdiction crypto IPN: order_id=%s", _clean_log_val(order_id))
        return {
            "ok": False,
            "error": "rail_not_permitted_for_jurisdiction",
            "jurisdiction": "VN",
            "allowed_rails": ["vietqr"],
        }

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
    credits = TIERS.get(tier, {}).get("credits", 0)

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
