"""Signed VietQR webhook reconciliation and pre-accounting MISA/Sapo draft export.

Compliance boundary (Decree 123/2020/NĐ-CP & Circular 78/2021/TT-BTC):
- Exports pre-accounting drafts ONLY with status 'DRAFT_PENDING_TVAN'.
- Never self-certifies tax authority codes or legal e-invoice issuance ('ISSUED' is forbidden).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Final, Sequence

from src.core.vietqr_engine import VietQrEngine
from src.opc.privacy_guard import verify_confidence_and_math

DRAFT_STATUS_PENDING_TVAN: Final[str] = "DRAFT_PENDING_TVAN"
ALLOWED_ACCOUNTING_TARGETS: Final[frozenset[str]] = frozenset({"misa_meinvoice", "sapo_invoice"})
_RUN_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"\brun_[A-Za-z0-9_-]+\b")


class VietQrWebhookError(PermissionError):
    """Raised when a VietQR banking webhook fails HMAC verification, type safety, or order binding."""


@dataclass(frozen=True)
class AccountingDraftExport:
    """Verified pre-accounting e-invoice draft ready for MISA/Sapo TVAN digital signature."""
    draft_id: str
    run_id: str
    target_provider: str
    invoice_status: str
    requires_tvan_signature: bool
    legal_certified: bool
    buyer_name: str
    currency: str
    subtotal_vnd: int
    vat_rate_pct: int
    vat_amount_vnd: int
    total_amount_vnd: int
    bank_tx_id: str | None
    line_items: tuple[dict[str, Any], ...]
    payload_sha256: str


def _memo_binds_exclusively_to_run(memo: str, matched_order_id: object, expected_run_id: str) -> bool:
    clean_expected = expected_run_id.strip()
    if not clean_expected:
        return False
    if matched_order_id is not None and str(matched_order_id).strip() != clean_expected:
        return False
    run_tokens = {m.group(0) for m in _RUN_TOKEN_RE.finditer(memo)}
    if run_tokens and run_tokens != {clean_expected}:
        return False
    token_match = re.search(rf"(?<![A-Za-z0-9_-]){re.escape(clean_expected)}(?![A-Za-z0-9_-])", memo)
    return bool(token_match or (matched_order_id is not None and str(matched_order_id).strip() == clean_expected))


def reconcile_signed_vietqr_webhook(
    vietqr: VietQrEngine,
    raw_body: bytes,
    received_signature: str,
    webhook_secret: str,
    expected_run_id: str,
    expected_amount_vnd: int,
) -> dict[str, Any]:
    """Verify HMAC-SHA256 bank webhook signature, match exact order/amount, and prevent cross-order replay."""
    if not vietqr.verify_webhook_signature(raw_body, received_signature, webhook_secret):
        raise VietQrWebhookError("Invalid VietQR webhook HMAC-SHA256 signature (fail-closed).")

    try:
        body = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VietQrWebhookError("Malformed JSON in VietQR webhook body.") from exc
    if not isinstance(body, dict):
        raise VietQrWebhookError("VietQR webhook payload must be a JSON object.")

    bank_tx_id = str(body.get("bank_tx_id", "")).strip()
    memo = str(body.get("memo", "")).strip()
    bin_code = str(body.get("bin_code", "970422")).strip()
    raw_amt = body.get("amount_vnd")
    if isinstance(raw_amt, (bool, float)) or raw_amt is None:
        raise VietQrWebhookError("Invalid amount_vnd type in VietQR webhook payload.")
    try:
        amount_vnd = int(raw_amt)
    except (TypeError, ValueError) as exc:
        raise VietQrWebhookError("Non-integer amount_vnd in VietQR webhook payload.") from exc

    if not bank_tx_id:
        raise VietQrWebhookError("Missing bank_tx_id in VietQR webhook payload.")
    if amount_vnd <= 0 or amount_vnd != int(expected_amount_vnd):
        raise VietQrWebhookError(f"VietQR webhook amount mismatch: {amount_vnd} != {expected_amount_vnd} VND.")
    if not _memo_binds_exclusively_to_run(memo, body.get("matched_order_id"), expected_run_id):
        raise VietQrWebhookError(f"VietQR webhook memo '{memo}' does not bind exclusively to '{expected_run_id}'.")

    tx_record = vietqr.record_transaction(
        bank_tx_id=bank_tx_id, amount_vnd=amount_vnd, memo=memo,
        bin_code=bin_code, matched_order_id=expected_run_id, save=True,
    )
    if tx_record.get("matched_order_id") != expected_run_id or int(tx_record.get("amount_vnd", -1)) != int(expected_amount_vnd):
        raise VietQrWebhookError(
            f"Cross-order bank_tx_id replay blocked: '{bank_tx_id}' already bound to '{tx_record.get('matched_order_id')}'."
        )

    idem_lock = f"act_{hashlib.sha256(bank_tx_id.encode('utf-8')).hexdigest()}"
    return {
        "reconciled": True,
        "is_duplicate": bool(tx_record.get("is_duplicate", False)),
        "idempotency_lock": idem_lock,
        "transaction_id": tx_record["transaction_id"],
        "bank_tx_id": bank_tx_id,
        "amount_vnd": amount_vnd,
        "matched_order_id": expected_run_id,
    }


def build_accounting_draft_export(
    run_id: str, buyer_name: str, line_items: Sequence[dict[str, Any]],
    declared_subtotal_vnd: int, vat_rate_pct: int = 8,
    target_provider: str = "misa_meinvoice", bank_tx_id: str | None = None,
) -> AccountingDraftExport:
    """Create a mathematically verified pre-accounting draft (never legally self-certified)."""
    provider = target_provider.strip().lower()
    if provider not in ALLOWED_ACCOUNTING_TARGETS:
        raise ValueError(f"Unsupported accounting draft provider '{target_provider}'.")
    if vat_rate_pct not in (0, 5, 8, 10):
        raise ValueError(f"Unsupported Vietnamese VAT rate '{vat_rate_pct}%' (expected 0, 5, 8, or 10).")

    verified_sub = verify_confidence_and_math(line_items, Decimal(int(declared_subtotal_vnd)), confidence=1.0)
    subtotal_int = int(verified_sub)
    vat_int = int((verified_sub * Decimal(vat_rate_pct)) / Decimal(100))
    total_int = subtotal_int + vat_int
    normalized_items = tuple(
        {
            "item_name": str(it.get("service", it.get("item_name", "item"))),
            "quantity": int(Decimal(str(it.get("hours", it.get("quantity", 1))))),
            "unit_price_vnd": int(Decimal(str(it.get("rate", it.get("unit_price", 0))))),
            "line_subtotal_vnd": int(Decimal(str(it.get("subtotal", 0)))),
        }
        for it in line_items
    )
    canonical = json.dumps(
        {
            "run_id": run_id, "provider": provider, "status": DRAFT_STATUS_PENDING_TVAN,
            "buyer_name": buyer_name, "subtotal_vnd": subtotal_int, "vat_rate_pct": vat_rate_pct,
            "vat_amount_vnd": vat_int, "total_amount_vnd": total_int, "bank_tx_id": bank_tx_id,
            "line_items": normalized_items,
        },
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return AccountingDraftExport(
        draft_id=f"drf_{digest[:12]}", run_id=run_id, target_provider=provider,
        invoice_status=DRAFT_STATUS_PENDING_TVAN, requires_tvan_signature=True, legal_certified=False,
        buyer_name=buyer_name, currency="VND", subtotal_vnd=subtotal_int, vat_rate_pct=vat_rate_pct,
        vat_amount_vnd=vat_int, total_amount_vnd=total_int, bank_tx_id=bank_tx_id,
        line_items=normalized_items, payload_sha256=digest,
    )
