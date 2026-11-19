# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Composite handlers for the Vietnamese finance/tax/payment operations.

A composite handler is used only when one advertised promise needs several real
engine calls plus a persisted business fact (for example: record the incoming
bank transfer *and* write the reconciled revenue fact that the ``first-revenue``
gate is measured from). Every call is a real engine call against a
workspace-scoped database; nothing is simulated.
"""

from __future__ import annotations

import datetime
import pathlib
import typing

from src.core.promise.runtime import HandlerContext


def engine_db(context: HandlerContext, name: str) -> str:
    """Workspace-scoped database path so tenants never share a ledger file.

    The path must be identical to the one the runtime derived from the contract's
    declared ``WRITE:`` effect, otherwise the ``record_persisted`` postcondition
    would look in a different database than the handler wrote to.
    """
    declared = context.engine_db_path
    if declared and pathlib.Path(declared).stem == name:
        return declared
    folder = context.state_dir / "workspaces" / context.workspace_id
    folder.mkdir(parents=True, exist_ok=True)
    return str(folder / f"{name}.db")


def sibling_db(context: HandlerContext, name: str) -> str:
    """Path of another ledger inside the *same* workspace folder as this run's database."""
    if context.engine_db_path:
        return str(pathlib.Path(context.engine_db_path).parent / f"{name}.db")
    return engine_db(context, name)


def ke_toan_journal(
    context: HandlerContext,
    amount: float,
    buyer: str,
    vat_rate: int = 10,
    seller: str = "Doanh Nghiệp",
    seller_tax_code: str = "",
    description: str = "Hàng hóa/Dịch vụ",
) -> dict[str, typing.Any]:
    """Prepare a TT78-shaped draft invoice and post its Circular 200/133 journal.

    The invoice is a draft, not a legally issued e-invoice: issuance requires
    transmission through a TVAN licensed by the General Department of Taxation,
    which this engine does not integrate.
    """
    from src.core.ke_toan_engine import KeToanEngine

    engine = KeToanEngine(db_path=engine_db(context, "ke_toan"))
    invoice = engine.create_invoice(
        amount=amount, buyer=buyer, vat_rate=vat_rate, seller=seller,
        seller_tax_code=seller_tax_code, description=description,
    )
    journal = engine.create_vas_journal(invoice)
    stored_invoice = engine.get_invoice(invoice["invoice_id"])
    return {
        **journal,
        "invoice": invoice,
        "invoice_persisted": bool(stored_invoice),
        "vat_rate": vat_rate,
        "subtotal": invoice.get("subtotal"),
    }


def _validate_duplicate_bank_transaction(
    transaction: dict[str, typing.Any],
    *,
    bank_tx_id: str,
    amount_vnd: int,
    memo: str,
    bin_code: str,
    matched_order_id: str | None,
) -> None:
    """Reject a duplicate bank transaction whose persisted fields disagree with the retry payload."""
    mismatches: list[str] = []
    persisted_amount = transaction.get("amount_vnd")
    if persisted_amount is None or int(persisted_amount) != int(amount_vnd):
        mismatches.append(f"amount_vnd (persisted={persisted_amount}, incoming={amount_vnd})")
    persisted_memo = str(transaction.get("memo") or "")
    if persisted_memo != str(memo):
        mismatches.append(f"memo (persisted={persisted_memo!r}, incoming={memo!r})")
    persisted_bin = str(transaction.get("bin_code") or "")
    if persisted_bin != str(bin_code):
        mismatches.append(f"bin_code (persisted={persisted_bin!r}, incoming={bin_code!r})")
    persisted_order = transaction.get("matched_order_id") or None
    incoming_order = matched_order_id or None
    if persisted_order != incoming_order:
        mismatches.append(
            f"matched_order_id (persisted={persisted_order!r}, incoming={incoming_order!r})"
        )
    if mismatches:
        raise ValueError(
            f"Duplicate bank transaction '{bank_tx_id}' conflicts with persisted bank record: "
            + ", ".join(mismatches)
        )


def vietqr_record_reconciled_payment(
    context: HandlerContext,
    bank_tx_id: str,
    amount_vnd: int,
    memo: str,
    provider: str,
    provider_reference: str,
    invoice_ref: str | None = None,
    currency: str = "VND",
    matched_order_id: str | None = None,
    bin_code: str = "970422",
) -> dict[str, typing.Any]:
    """Record an incoming VietQR transfer and its write-once revenue fact.

    The complete finance intent is committed atomically with the bank transaction.
    A retry can repair missing evidence only when its payload matches that intent;
    old bank rows without the intent require separate reconciliation.
    """
    import json

    from src.core.ke_toan_engine import KeToanEngine
    from src.core.vietqr_engine import VietQrEngine

    currency = str(currency).strip().upper()
    if currency != "VND":
        raise ValueError("currency must be VND for VietQR revenue reconciliation")

    accounting_db = sibling_db(context, "ke_toan")
    accounting = KeToanEngine(db_path=accounting_db)
    proposed_intent: dict[str, typing.Any] = {
        "workspace_id": context.workspace_id,
        "bank_tx_id": bank_tx_id,
        "amount_vnd": int(amount_vnd),
        "memo": str(memo),
        "bin_code": str(bin_code),
        "matched_order_id": matched_order_id,
        "provider": str(provider).strip(),
        "provider_reference": str(provider_reference).strip(),
        "invoice_ref": str(invoice_ref or "").strip(),
        "currency": str(currency).strip().upper(),
    }
    invoice = accounting.get_invoice(proposed_intent["invoice_ref"])
    if invoice is None:
        raise ValueError(
            f"Không thể đối soát doanh thu: hóa đơn '{invoice_ref}' chưa được phát hành trong "
            f"workspace '{context.workspace_id}' — hãy lập hóa đơn trước "
            "(mekong ke-toan create_invoice)"
        )
    invoiced_total = float(invoice.get("total_amount") or 0.0)
    if float(amount_vnd) - invoiced_total > 0.5:
        raise ValueError(
            f"Số tiền đối soát {amount_vnd:,.0f} đ vượt tổng hóa đơn '{invoice_ref}' "
            f"({invoiced_total:,.0f} đ) — cần hóa đơn điều chỉnh/bổ sung trước khi ghi nhận doanh thu"
        )

    engine = VietQrEngine(db_path=engine_db(context, "vietqr"))
    transaction = engine.record_transaction(
        bank_tx_id=bank_tx_id,
        amount_vnd=amount_vnd,
        memo=memo,
        bin_code=bin_code,
        matched_order_id=matched_order_id,
        reconciliation_intent=proposed_intent,
    )
    if transaction.get("conflict") or not transaction.get("ok", True):
        raise ValueError(
            f"Order '{matched_order_id}' already settled by bank transaction "
            f"'{transaction.get('existing_bank_tx_id')}' — rejecting conflicting '{bank_tx_id}'"
        )

    _validate_duplicate_bank_transaction(
        transaction, bank_tx_id=bank_tx_id, amount_vnd=amount_vnd,
        memo=memo, bin_code=bin_code, matched_order_id=matched_order_id,
    )
    stored_intent_json = transaction.get("reconciliation_intent_json")
    if stored_intent_json is not None:
        try:
            stored_intent = json.loads(str(stored_intent_json))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Bank transaction '{bank_tx_id}' has an invalid reconciliation intent"
            ) from exc
        if not isinstance(stored_intent, dict):
            raise ValueError(f"Bank transaction '{bank_tx_id}' has an invalid reconciliation intent")
        mismatches = [
            field for field, value in proposed_intent.items()
            if field not in stored_intent or stored_intent[field] != value
        ]
        if mismatches:
            raise ValueError(
                f"Bank transaction '{bank_tx_id}' conflicts with persisted reconciliation intent: "
                + ", ".join(mismatches)
            )

    provider = proposed_intent["provider"]
    provider_reference = proposed_intent["provider_reference"]
    invoice_ref = proposed_intent["invoice_ref"]
    currency = proposed_intent["currency"]

    store = context.evidence_store()
    ensured = store.record_revenue_transaction_once(
        workspace_id=context.workspace_id,
        bank_tx_id=bank_tx_id,
        require_existing=stored_intent_json is None,
        run_id=context.run_id,
        provider=provider,
        method="vietqr_bank_transfer",
        amount=amount_vnd,
        currency=currency,
        invoice_ref=invoice_ref,
        status="RECONCILED",
        provider_confirmation={
            "provider": provider,
            "reference": provider_reference,
            "bank_tx_id": bank_tx_id,
            "amount_vnd": amount_vnd,
            "currency": currency,
            "memo": memo,
            "bin_code": bin_code,
            "matched_order_id": matched_order_id,
        },
        confirmed_at=datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        reconciled_by=context.principal_id,
    )
    record = ensured.get("record")
    if not isinstance(record, dict):
        rows = store.query("revenue_transactions", context.workspace_id,
                           "tx_id = ?", (ensured["tx_id"],))
        record = rows[0] if rows else None
    if not isinstance(record, dict):
        return {
            "status": "FAILED",
            "transaction": transaction,
            "revenue_record": None,
            "detail": f"revenue fact '{ensured['tx_id']}' was not readable back from the evidence store",
        }

    return {
        "status": "RECONCILED",
        "is_duplicate": not ensured["created"],
        "recovered": bool(transaction.get("is_duplicate") and ensured["created"]),
        "transaction": transaction,
        "invoice": {
            "invoice_id": invoice.get("invoice_id"),
            "invoice_date": invoice.get("invoice_date"),
            "buyer_name": invoice.get("buyer_name"),
            "total_amount": invoice.get("total_amount"),
        },
        "invoice_db": accounting_db,
        "evidence_db": str(store.db_path),
        "revenue_record": record,
        "existing_revenue_tx_id": ensured["tx_id"] if not ensured["created"] else None,
        "legacy_revenue_match": bool(ensured.get("legacy_match")),
        "reconciliation": {
            "provider": provider,
            "provider_reference": provider_reference,
            "reconciled_by": context.principal_id,
            "invoice_ref": invoice_ref,
            "amount_vnd": amount_vnd,
            "currency": currency,
        },
        "detail": (
            f"bank transaction '{bank_tx_id}' already has matching revenue fact '{ensured['tx_id']}'"
            if not ensured["created"] else "reconciled bank transaction and revenue fact"
        ),
    }


def payroll_payslip_document(
    context: HandlerContext,
    employee_name: str,
    gross: float,
    month: str | None = None,
    dependents: int = 0,
    region: int = 1,
    bonus: float = 0.0,
    lunch_allowance: float = 730_000.0,
) -> dict[str, typing.Any]:
    """Produce the payslip *and* a written artifact the employee can be given."""
    from src.core.payroll_engine import PayrollEngine

    engine = PayrollEngine(db_path=engine_db(context, "payroll"))
    payslip = engine.generate_payslip(
        employee_name=employee_name, gross=gross, month=month, dependents=dependents,
        region=region, lunch_allowance=lunch_allowance, bonus=bonus,
    )
    period = payslip.get("month") or month or datetime.date.today().strftime("%Y-%m")
    folder = pathlib.Path(engine_db(context, "artifacts")).parent / "artifacts" / "payslips"
    folder.mkdir(parents=True, exist_ok=True)
    artifact = folder / f"{payslip.get('payslip_id', 'payslip')}.md"
    tax = payslip.get("tax_calculation", {})
    insurance = payslip.get("employee_deductions", {})
    artifact.write_text(
        "\n".join([
            f"# Phiếu lương {period} — {employee_name}",
            "",
            f"- Mã nhân viên: {payslip.get('employee_id')}",
            f"- Lương gross: {payslip.get('gross'):,.0f} đ",
            f"- Phụ cấp ăn trưa miễn thuế: {payslip.get('exempt_lunch_allowance'):,.0f} đ",
            f"- BHXH (8%): {insurance.get('bhxh_8_pct', 0):,.0f} đ",
            f"- BHYT (1,5%): {insurance.get('bhyt_1_5_pct', 0):,.0f} đ",
            f"- BHTN (1%): {insurance.get('bhtn_1_pct', 0):,.0f} đ",
            f"- Thu nhập chịu thuế: {tax.get('taxable_income', 0):,.0f} đ",
            f"- Thuế TNCN: {tax.get('pit_tax', 0):,.0f} đ",
            f"- Thực nhận (net): {payslip.get('net', 0):,.0f} đ",
            "",
            f"Căn cứ: {payslip.get('rule_citation', '')}",
            (f"Phiên bản quy tắc: {payslip.get('rule_version', '')} "
             f"(bảo hiểm: {payslip.get('insurance_rule_version', '')})"),
            f"Kỳ lương: {payslip.get('payroll_period', period)}",
            "",
        ]),
        encoding="utf-8",
    )
    return {**payslip, "artifact_path": str(artifact), "artifact_bytes": artifact.stat().st_size}





def taxadmin_validate_mst(context: HandlerContext, tax_code: str) -> dict[str, typing.Any]:
    """Validate an MST with the engine's format rule *and* the modulus-11 check digit.

    ``TaxAdminEngine.validate_tax_code`` only matches the 10/13-digit shape, so a
    plausible-looking fake tax code passes it. A code that fails the independent
    check-digit computation is rejected here rather than reported as valid.
    """
    from src.core.taxadmin_engine import TaxAdminEngine
    from src.core.vn_statutory_rules import mst_checksum

    format_valid = bool(TaxAdminEngine.validate_tax_code(tax_code))
    verdict = mst_checksum(tax_code)
    if not format_valid:
        raise ValueError(
            f"Mã số thuế '{tax_code}' không đúng định dạng 10 hoặc 13 số "
            "(Điều 30 Luật Quản lý thuế 38/2019/QH14)"
        )
    if not verdict["valid"]:
        raise ValueError(
            f"Mã số thuế '{tax_code}' không hợp lệ: {verdict['reason']} — "
            f"số kiểm tra mong đợi {verdict['expected_check_digit']} "
            f"(Điều 5 Thông tư 105/2020/TT-BTC)"
        )
    return {
        "tax_code": tax_code,
        "format_valid": format_valid,
        "checksum_valid": bool(verdict["valid"]),
        "is_valid": True,
        "check_digit_rule": "modulus-11, trọng số [31,29,23,19,17,13,7,5,3] trên 9 số đầu",
        "expected_check_digit": verdict["expected_check_digit"],
        "actual_check_digit": verdict["actual_check_digit"],
        "legal_basis": "Điều 30 Luật Quản lý thuế 38/2019/QH14; Điều 5 TT 105/2020/TT-BTC",
        "citation": verdict.get("citation", ""),
        "note": "Từ 01/07/2025 MST cá nhân 10 số được thay bằng số định danh cá nhân 12 số (TT 86/2024/TT-BTC)",
    }


__all__ = [
    "engine_db",
    "ke_toan_journal",
    "payroll_payslip_document",
    "taxadmin_validate_mst",
    "vietqr_record_reconciled_payment",
]
