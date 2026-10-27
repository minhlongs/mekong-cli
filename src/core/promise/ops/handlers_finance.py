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
    """Issue a TT78 e-invoice and post its Circular 200/133 double-entry journal."""
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
    """Record an incoming VietQR transfer and the reconciled revenue fact.

    The revenue fact is what the ``first-revenue`` (L3) gate measures: it needs
    a provider confirmation payload and a named reconciler, not a string typed
    into a browser form.
    """
    from src.core.ke_toan_engine import KeToanEngine
    from src.core.vietqr_engine import VietQrEngine

    accounting_db = sibling_db(context, "ke_toan")
    accounting = KeToanEngine(db_path=accounting_db)
    invoice = accounting.get_invoice(invoice_ref or "")
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
        bank_tx_id=bank_tx_id, amount_vnd=amount_vnd, memo=memo,
        bin_code=bin_code, matched_order_id=matched_order_id,
    )
    if transaction.get("is_duplicate"):
        return {
            "status": "DUPLICATE",
            "transaction": transaction,
            "invoice_db": accounting_db,
            "revenue_record": None,
            "detail": f"bank transaction '{bank_tx_id}' was already recorded — no second revenue fact written",
        }
    store = context.evidence_store()
    inserted = store.record_revenue_transaction(
        workspace_id=context.workspace_id,
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
            "matched_order_id": matched_order_id,
        },
        confirmed_at=datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        reconciled_by=context.principal_id,
    )
    rows = store.query("revenue_transactions", context.workspace_id,
                       "tx_id = ?", (inserted["tx_id"],))
    record = rows[0] if rows else None
    if record is None:
        return {
            "status": "FAILED",
            "transaction": transaction,
            "revenue_record": None,
            "detail": f"revenue fact '{inserted['tx_id']}' was not readable back from the evidence store",
        }
    return {
        "status": "RECONCILED",
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
        "reconciliation": {
            "provider": provider,
            "provider_reference": provider_reference,
            "reconciled_by": context.principal_id,
            "invoice_ref": invoice_ref,
            "amount_vnd": amount_vnd,
            "currency": currency,
        },
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
