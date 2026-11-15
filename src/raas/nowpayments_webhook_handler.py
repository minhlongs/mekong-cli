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
import math
import os
from pathlib import Path
import re
from typing import Any

from src.core.raas_license_verifier import sign_license_key
from src.core.vietqr_engine import VietQrEngine
from src.raas.credit_account_repository import CreditAccountRepository
from src.raas.nowpayments_checkout import TIERS
from src.raas.tenant import TenantStore

logger = logging.getLogger(__name__)

_INIT_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET", "")
IPN_SECRET = _INIT_IPN_SECRET

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


def _unsigned_ipn_allowed() -> bool:
    """Explicit operator opt-out for unsigned IPNs; never the default."""
    return os.getenv("MEKONG_ALLOW_UNSIGNED_IPN", "").strip().lower() in ("1", "true", "yes")


def _effective_ipn_secret() -> str:
    if IPN_SECRET != _INIT_IPN_SECRET:
        return IPN_SECRET
    return os.getenv("NOWPAYMENTS_IPN_SECRET", "")


def verify_ipn_signature(payload_json: str, received_sig: str) -> bool:
    """Verify NOWPayments IPN HMAC-SHA512 signature."""
    secret = _effective_ipn_secret()
    if not secret:
        logger.error("NOWPAYMENTS_IPN_SECRET not set — rejecting webhook")
        return False

    # NOWPayments sorts keys before hashing
    sorted_payload = json.dumps(json.loads(payload_json), sort_keys=True)
    expected = hmac.new(
        secret.encode(),
        sorted_payload.encode(),
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(expected, received_sig)


def _extract_tier(data: dict) -> str:
    """Extract tier name from order_id or order_description."""
    order_id = data.get("order_id", "").lower()
    description = data.get("order_description", "").lower()

    for tier in ("free", "trial", "basic", "starter", "growth", "premium", "pro", "enterprise", "master"):
        if tier in order_id or tier in description:
            return tier
    return "starter"  # fallback


def _resolve_ipn_tenant_and_vn_flag(
    data: dict[str, Any], order_id: str, workspace_id: str
) -> tuple[bool, str | None]:
    """Resolve (is_vn_jurisdiction, matched_non_vn_tenant_key) for a NOWPayments IPN."""
    for key in ("jurisdiction", "country"):
        val = str(data.get(key) or "").strip().upper()
        if val.startswith("VN"):
            return (True, None)

    for curr_key in ("price_currency", "pay_currency"):
        if str(data.get(curr_key) or "").strip().lower() == "vnd":
            return (True, None)

    explicit_ws = str(data.get("workspace_id") or data.get("org_id") or data.get("tenant_id") or "").strip()
    for ident in (order_id, workspace_id, explicit_ws):
        low = ident.strip().lower()
        if low == "vn" or low.startswith(("vn-", "vn_")):
            return (True, None)

    order_low = order_id.lower()
    desc_low = str(data.get("order_description") or "").lower()
    tier_low = str(data.get("tier") or "").strip().lower()
    if tier_low in _VN_ONLY_TIER_TOKENS:
        return (True, None)
    if any(tok in order_low or tok in desc_low for tok in _VN_ONLY_TIER_TOKENS):
        return (True, None)

    persisted_order: dict[str, Any] | None = None
    if order_id:
        try:
            persisted_order = VietQrEngine().get_checkout_order(order_id)
        except Exception:
            persisted_order = None

    if persisted_order is not None:
        p_tier = str(persisted_order.get("display_tier") or "").strip().lower()
        p_rail = str(persisted_order.get("rail") or "").strip().lower()
        p_curr = str(persisted_order.get("currency") or "").strip().lower()
        if p_tier in _VN_ONLY_TIER_TOKENS or p_rail == "vietqr" or p_curr == "vnd":
            return (True, None)

    candidates: list[str] = []
    if explicit_ws:
        candidates.append(explicit_ws)
    if workspace_id and workspace_id != "default":
        candidates.append(workspace_id)
    if order_id:
        candidates.append(order_id)
        candidates.extend(_UUID_RE.findall(order_id))
        parts = order_id.split("-")
        for idx in range(1, len(parts)):
            candidates.append("-".join(parts[:idx]))
    customer_email = str(data.get("customer_email") or "").strip()
    if customer_email:
        candidates.append(customer_email)
        if customer_email.lower() != customer_email:
            candidates.append(customer_email.lower())
    if persisted_order is not None:
        p_org = str(persisted_order.get("org_id") or "").strip()
        p_email = str(persisted_order.get("customer_email") or "").strip()
        if p_org:
            candidates.append(p_org)
        if p_email:
            candidates.append(p_email)

    if not candidates:
        return (True, None)

    resolved_non_vn = False
    matched_tenant_key: str | None = None
    env_db = os.environ.get("MEKONG_RAAS_DB")
    try:
        store = TenantStore(Path(env_db)) if env_db else TenantStore()
        with closing(store._connect()) as conn:
            for candidate in dict.fromkeys(candidates):
                row = conn.execute(
                    "SELECT id, name, jurisdiction FROM tenants WHERE id = ? OR name = ?",
                    (candidate, candidate),
                ).fetchone()
                if row is not None:
                    jur = str(row["jurisdiction"] or "").strip().upper()
                    if not jur or jur.startswith("VN"):
                        return (True, None)
                    resolved_non_vn = True
                    if matched_tenant_key is None:
                        row_id = str(row["id"])
                        row_name = str(row["name"])
                        if explicit_ws and explicit_ws in (row_id, row_name):
                            matched_tenant_key = explicit_ws
                        elif order_low.startswith("mk-"):
                            matched_tenant_key = row_id
                        elif customer_email and (
                            customer_email == row_name
                            or customer_email.lower() == row_name.lower()
                            or customer_email == row_id
                        ):
                            matched_tenant_key = row_id
                        elif "@" not in row_name and candidate == row_name:
                            matched_tenant_key = row_name
                        else:
                            matched_tenant_key = row_id
    except Exception as exc:
        logger.error("[NP] TenantStore lookup error during jurisdiction check (failing closed): %s", exc)
        return (True, None)

    if order_low.startswith("mk-") and not resolved_non_vn:
        return (True, None)

    return (False, matched_tenant_key)


def _is_vn_jurisdiction_ipn(data: dict[str, Any], order_id: str, workspace_id: str) -> bool:
    """Return True when any Decree 52/2024 Vietnamese jurisdiction signal is present."""
    is_vn, _ = _resolve_ipn_tenant_and_vn_flag(data, order_id=order_id, workspace_id=workspace_id)
    return is_vn


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
    # Fail-closed: an IPN whose HMAC cannot be verified must never credit a
    # customer. Unsigned IPNs are only tolerated when an operator explicitly
    # opts out via MEKONG_ALLOW_UNSIGNED_IPN (local harnesses only).
    effective_secret = _effective_ipn_secret()
    if not effective_secret:
        if not _unsigned_ipn_allowed():
            logger.error("[NP] NOWPAYMENTS_IPN_SECRET unset — refusing unsigned IPNs")
            return {"ok": False, "error": "ipn_secret_unconfigured"}
        if signature:
            logger.warning("[NP] IPN signature provided while secret unset — rejecting")
            return {"ok": False, "error": "signature_mismatch"}
    elif not verify_ipn_signature(payload_json, signature):
        logger.warning("[NP] IPN signature mismatch or missing — rejecting")
        return {"ok": False, "error": "signature_mismatch"}

    data = json.loads(payload_json)
    payment_status = _clean_log_val(data.get("payment_status", ""))
    raw_payment_id = data.get("payment_id")
    payment_id = _clean_log_val(raw_payment_id if raw_payment_id is not None else "unknown")
    order_id = str(data.get("order_id") or "")
    lead_uuid = _UUID_RE.match(order_id)
    explicit_ws = str(data.get("workspace_id") or data.get("org_id") or data.get("tenant_id") or "").strip()
    if order_id.lower().startswith("mk-") and explicit_ws:
        workspace_id = explicit_ws
    else:
        workspace_id = lead_uuid.group(0) if lead_uuid else (order_id.split("-")[0] if "-" in order_id else "default")

    logger.info("[NP] IPN received: payment=%s status=%s", payment_id, payment_status)

    # Decree 52/2024/ND-CP fourth-door guard: domestic VN entities settle exclusively via VietQR
    is_vn, matched_tenant_key = _resolve_ipn_tenant_and_vn_flag(
        data, order_id=order_id, workspace_id=workspace_id
    )
    if is_vn:
        logger.warning("[NP] Blocked VN jurisdiction crypto IPN: order_id=%s", _clean_log_val(order_id))
        return {
            "ok": False,
            "error": "rail_not_permitted_for_jurisdiction",
            "jurisdiction": "VN",
            "allowed_rails": ["vietqr"],
        }
    if matched_tenant_key:
        workspace_id = matched_tenant_key

    # Only process completed payments
    if payment_status not in (STATUS_FINISHED, STATUS_CONFIRMED):
        _log_payment(data, _extract_tier(data), 0)
        return {
            "ok": True,
            "action": "ignored",
            "reason": f"status={payment_status} (not finished/confirmed)",
        }

    clean_pid = "" if isinstance(raw_payment_id, bool) else str(raw_payment_id or "").strip()
    if not clean_pid or clean_pid.lower() == "unknown":
        logger.warning("[NP] Missing or unknown payment_id on completed IPN — rejecting")
        return {"ok": False, "error": "missing_payment_id"}

    persisted_order: dict[str, Any] | None = None
    if order_id:
        try:
            persisted_order = VietQrEngine().get_checkout_order(order_id)
        except Exception:
            persisted_order = None

    if persisted_order is not None:
        expected_usd = int(persisted_order.get("expected_amount_usd") or 0)
        raw_price = data.get("price_amount")
        if expected_usd > 0:
            if raw_price is None or raw_price == "":
                return {"ok": False, "error": "missing_price_amount"}
            if isinstance(raw_price, bool):
                return {"ok": False, "error": "invalid_price_amount"}
            price_currency = str(data.get("price_currency") or "").strip().lower()
            if price_currency != "usd":
                return {"ok": False, "error": "invalid_price_currency"}
            try:
                paid_usd = float(raw_price)
            except (TypeError, ValueError):
                return {"ok": False, "error": "invalid_price_amount"}
            if not math.isfinite(paid_usd):
                return {"ok": False, "error": "invalid_price_amount"}
            if paid_usd < float(expected_usd):
                logger.warning(
                    "[NP] Rejected underpaid IPN for order=%s: paid=%s expected=%s",
                    _clean_log_val(order_id),
                    paid_usd,
                    expected_usd,
                )
                _log_payment(data, _extract_tier(data), 0)
                return {
                    "ok": False,
                    "error": "underpaid_invoice",
                    "expected_amount_usd": expected_usd,
                    "received_amount_usd": paid_usd,
                }

    # Extract tier and grant credits — persisted checkout_orders are authoritative over IPN metadata
    tier = _extract_tier(data)
    if persisted_order is not None:
        persisted_canon = str(persisted_order.get("canonical_tier") or "").strip().lower()
        if persisted_canon in TIERS:
            tier = persisted_canon
    credits = TIERS.get(tier, {}).get("credits", 0)

    try:
        repo = CreditAccountRepository()
        if hasattr(repo, "grant_event_credits_once"):
            granted, _ = repo.grant_event_credits_once(
                f"np:{clean_pid}",
                "nowpayments_ipn",
                workspace_id,
                credits,
                f"nowpayments:{payment_id}",
            )
        else:
            repo.add_credits(workspace_id, credits, f"nowpayments:{payment_id}")
            granted = True

        if not granted:
            logger.info("[NP] Replay for payment=%s — credits already granted, re-attempting settlement", payment_id)

        # Settle the checkout order (mint license). This MUST succeed or the
        # entire IPN must fail so that NOWPayments retries. Never swallow the
        # exception — if credits were granted but settlement fails, a retry
        # will see granted=False, skip the credit grant, and re-attempt
        # settlement via this same path.
        if persisted_order is not None:
            VietQrEngine().settle_external_order_atomic(
                order_id=order_id,
                external_tx_id=f"NP-{clean_pid}",
                license_signer=lambda org_id, c_tier: sign_license_key(
                    tenant_id=org_id, tier=c_tier
                ),
            )

        if not granted:
            _log_payment(data, tier, 0)
            return {
                "ok": True,
                "action": "duplicate_ignored",
                "tier": tier,
                "credits": 0,
                "workspace_id": workspace_id,
                "payment_id": payment_id,
            }

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
        return {"ok": False, "error": str(e), "retryable": True}
