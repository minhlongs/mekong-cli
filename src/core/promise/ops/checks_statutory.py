# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Statute-specific postconditions that a generic checker cannot express.

Each check re-measures a legal fact from an independent source (the statutory
rule module or the engine's own database) instead of trusting the handler's
self-reported status.
"""

from __future__ import annotations

import datetime
import pathlib
import sqlite3
import typing

from src.core.promise.checks import CheckContext, CheckResult, resolve_path

PLACEHOLDER_NAMES = ("Nhân viên mới", "New Employee", "N/A", "Unknown", "unknown")


def declaration_names_roster_employee(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """A D02-LT filing must name the real roster employee it was prepared for."""
    name = str(resolve_path(ctx.result, "full_name") or "")
    employee_id = str(resolve_path(ctx.result, "employee_id") or ctx.params.get("employee_id") or "")
    if not name or name in PLACEHOLDER_NAMES:
        return CheckResult(
            "declaration_names_roster_employee", "FAILED",
            f"D02-LT for '{employee_id}' carries placeholder name '{name}' — the filing is not submittable",
        )
    if not ctx.engine_db_path:
        return CheckResult("declaration_names_roster_employee", "FAILED",
                           "no engine database available to confirm the roster row")
    try:
        conn = sqlite3.connect(f"file:{ctx.engine_db_path}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT full_name FROM employees WHERE employee_id = ?", (employee_id,)
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return CheckResult("declaration_names_roster_employee", "FAILED", f"roster lookup failed: {exc}")
    if row is None:
        return CheckResult(
            "declaration_names_roster_employee", "FAILED",
            f"employee '{employee_id}' is not on the BHXH roster, so no D02-LT may be issued for it",
        )
    if str(row[0]).strip() != name.strip():
        return CheckResult(
            "declaration_names_roster_employee", "FAILED",
            f"filing name '{name}' != roster name '{row[0]}'",
            {"roster_name": row[0], "filing_name": name},
        )
    return CheckResult(
        "declaration_names_roster_employee", "PASSED",
        f"D02-LT names roster employee '{name}' ({employee_id})",
        {"employee_id": employee_id, "full_name": name,
         "citation": "Quyết định 595/QĐ-BHXH — biểu mẫu D02-LT"},
    )


def revenue_fact_is_verifiable(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """The first-revenue fact must be provider-confirmed, workspace-scoped and amount-true."""
    status = str(resolve_path(ctx.result, "status") or "")
    if status == "DUPLICATE":
        record = resolve_path(ctx.result, "revenue_record")
        if record:
            return CheckResult("revenue_fact_is_verifiable", "FAILED",
                               "a duplicate bank transaction wrote a second revenue fact")
        return CheckResult("revenue_fact_is_verifiable", "PASSED",
                           "duplicate bank transaction was rejected without writing revenue",
                           {"status": "DUPLICATE"})
    if status != "RECONCILED":
        return CheckResult("revenue_fact_is_verifiable", "FAILED",
                           f"reconciliation status '{status}' is not RECONCILED")
    record = resolve_path(ctx.result, "revenue_record")
    if not isinstance(record, dict):
        return CheckResult("revenue_fact_is_verifiable", "FAILED", "no revenue record was persisted")
    amount = ctx.params.get("amount_vnd")
    problems: list[str] = []
    if record.get("status") != "RECONCILED":
        problems.append(f"revenue record status '{record.get('status')}' is not RECONCILED")
    confirmation = record.get("provider_confirmation")
    if isinstance(confirmation, str):
        import json

        try:
            confirmation = json.loads(confirmation)
        except ValueError:
            confirmation = {}
    if not confirmation:
        raw = record.get("provider_confirmation_json")
        if isinstance(raw, str) and raw:
            import json

            try:
                confirmation = json.loads(raw)
            except ValueError:
                confirmation = {}
    if not isinstance(confirmation, dict):
        confirmation = {}
    if not confirmation.get("reference"):
        problems.append("revenue record has no provider confirmation reference — the fact is unverifiable")
    if confirmation.get("provider") != ctx.params.get("provider"):
        problems.append("provider in the confirmation payload differs from the submitted provider")
    if str(record.get("workspace_id") or "") != str(ctx.workspace_id):
        problems.append(f"revenue record is scoped to workspace '{record.get('workspace_id')}', "
                        f"not '{ctx.workspace_id}'")
    if amount is not None and abs(float(record.get("amount") or 0) - float(amount)) > 0.5:
        problems.append(f"recorded amount {record.get('amount')} != submitted {amount}")
    if str(record.get("currency") or "").upper() != "VND":
        problems.append(f"currency '{record.get('currency')}' is not VND")
    if problems:
        return CheckResult("revenue_fact_is_verifiable", "FAILED", "; ".join(problems),
                           {"record_status": record.get("status")})
    return CheckResult(
        "revenue_fact_is_verifiable", "PASSED",
        f"revenue fact of {amount} VND is provider-confirmed "
        f"({ctx.params.get('provider')} / {confirmation.get('reference')}) and workspace-scoped",
        {"provider": ctx.params.get("provider"), "reference": confirmation.get("reference"),
         "amount_vnd": amount, "workspace_id": ctx.workspace_id,
         "citation": "Đối soát ngân hàng + hóa đơn TT78 (NĐ 123/2020/NĐ-CP)"},
    )


def limitation_period_recomputed(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """Recompute the Article 6 expiry date from the base date and the statutory years."""
    prefix = str(args.get("path") or "")
    node = resolve_path(ctx.result, prefix) if prefix else ctx.result
    if prefix and not isinstance(node, dict):
        return CheckResult("limitation_period_recomputed", "FAILED",
                           f"'{prefix}' is not a limitation assessment object")
    years = resolve_path(node, "statute_limit_years")
    base = str(resolve_path(node, "base_calculation_date") or "")
    expiry = str(resolve_path(node, "expiry_date") or "")
    assessment = str(resolve_path(node, "assessment_date") or "")
    if not base or not expiry or years is None:
        return CheckResult("limitation_period_recomputed", "FAILED",
                           "engine did not report base date / statutory years / expiry date")
    try:
        base_date = datetime.date.fromisoformat(base)
        expiry_date = datetime.date.fromisoformat(expiry)
        assessment_date = datetime.date.fromisoformat(assessment) if assessment else datetime.date.today()
    except ValueError as exc:
        return CheckResult("limitation_period_recomputed", "FAILED", f"unparseable date: {exc}")
    try:
        expected = base_date.replace(year=base_date.year + int(years))
    except ValueError:  # 29 February
        expected = base_date.replace(year=base_date.year + int(years), day=28)
    problems: list[str] = []
    if expected != expiry_date:
        problems.append(f"expiry {expiry_date} != base {base_date} + {years} year(s) = {expected}")
    expected_barred = assessment_date >= expiry_date
    if bool(resolve_path(node, "is_time_barred")) != expected_barred:
        problems.append(
            f"is_time_barred={resolve_path(node, 'is_time_barred')} but assessment "
            f"{assessment_date} vs expiry {expiry_date} implies {expected_barred}"
        )
    remaining = resolve_path(node, "days_remaining")
    if remaining is not None and int(remaining) > max(0, (expiry_date - assessment_date).days):
        problems.append(f"days_remaining {remaining} exceeds the actual {(expiry_date - assessment_date).days}")
    if problems:
        return CheckResult("limitation_period_recomputed", "FAILED", "; ".join(problems),
                           {"expected_expiry": expected.isoformat()})
    return CheckResult(
        "limitation_period_recomputed", "PASSED",
        f"limitation period of {years} year(s) from {base} expires {expiry} "
        f"(time-barred={resolve_path(node, 'is_time_barred')})",
        {"expiry": expiry, "years": years,
         "citation": "Điều 6 Luật Xử lý vi phạm hành chính 2012 (sửa đổi 2020)"},
    )


def tax_code_verdict_agrees(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """The engine's verdict must agree with the independent modulus-11 checksum."""
    from src.core.vn_statutory_rules import mst_checksum

    tax_code = str(ctx.params.get(args.get("param", "tax_code"))
                   or resolve_path(ctx.result, "tax_code") or "")
    format_valid = resolve_path(ctx.result, "format_valid")
    engine_valid = resolve_path(ctx.result, "is_valid")
    verdict = mst_checksum(tax_code)
    if format_valid is not None and engine_valid is not None and bool(format_valid) != bool(engine_valid):
        return CheckResult("tax_code_verdict_agrees", "FAILED",
                           f"format verdict {format_valid} disagrees with the checksum verdict {engine_valid}")
    if engine_valid is not None and bool(engine_valid) != bool(verdict["valid"]):
        return CheckResult(
            "tax_code_verdict_agrees", "FAILED",
            f"engine says '{tax_code}' valid={engine_valid} but the independent modulus-11 check says "
            f"{verdict['valid']} ({verdict['reason']})",
            {"verdict": verdict},
        )
    return CheckResult(
        "tax_code_verdict_agrees", "PASSED",
        f"MST '{tax_code}' verdict agrees with the independent modulus-11 computation "
        f"(check digit {verdict['actual_check_digit']})",
        {"verdict": verdict, "citation": verdict.get("citation", "")},
    )

def invoice_ref_is_issued(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """Revenue may only be reconciled against an e-invoice that was really issued.

    Re-reads the accounting ledger the handler reported instead of trusting the
    handler's own copy of the invoice.
    """
    invoice_ref = str(ctx.params.get("invoice_ref") or "")
    if not invoice_ref:
        return CheckResult("invoice_ref_is_issued", "FAILED",
                           "no invoice reference was supplied for the reconciled revenue")
    db = str(resolve_path(ctx.result, "invoice_db") or "")
    if not db or not pathlib.Path(db).exists():
        return CheckResult("invoice_ref_is_issued", "FAILED",
                           f"accounting ledger '{db}' does not exist — the invoice cannot be confirmed")
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT invoice_id, invoice_date, buyer_name, total_amount FROM invoices "
                "WHERE invoice_id = ?", (invoice_ref,)
            ).fetchone()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return CheckResult("invoice_ref_is_issued", "FAILED", f"invoice lookup failed: {exc}")
    if row is None:
        return CheckResult(
            "invoice_ref_is_issued", "FAILED",
            f"invoice '{invoice_ref}' is not in the workspace accounting ledger — revenue cannot be "
            "reconciled against an invoice that was never issued",
            {"invoice_ref": invoice_ref},
        )
    invoiced_total = float(row[3] or 0.0)
    reconciled = float(ctx.params.get("amount_vnd") or 0.0)
    problems: list[str] = []
    if reconciled - invoiced_total > 0.5:
        problems.append(
            f"reconciled {reconciled:,.0f}đ exceeds the invoiced total {invoiced_total:,.0f}đ — "
            "an adjustment invoice is required before this can count as revenue"
        )
    reported = resolve_path(ctx.result, "invoice") or {}
    if isinstance(reported, dict):
        if str(reported.get("invoice_id") or "") != str(row[0]):
            problems.append(f"handler reported invoice '{reported.get('invoice_id')}' but the ledger has '{row[0]}'")
        if abs(float(reported.get("total_amount") or 0.0) - invoiced_total) > 0.5:
            problems.append("handler-reported invoice total differs from the ledger row")
    if problems:
        return CheckResult("invoice_ref_is_issued", "FAILED", "; ".join(problems),
                           {"invoiced_total": invoiced_total, "reconciled": reconciled})
    return CheckResult(
        "invoice_ref_is_issued", "PASSED",
        f"invoice '{invoice_ref}' ({row[1]}, buyer '{row[2]}') is issued for {invoiced_total:,.0f}đ "
        f"and covers the reconciled {reconciled:,.0f}đ",
        {"invoice_ref": invoice_ref, "invoiced_total": invoiced_total, "reconciled": reconciled,
         "citation": "Nghị định 123/2020/NĐ-CP; Thông tư 78/2021/TT-BTC"},
    )


STATUTORY_CHECKS: dict[str, typing.Callable[[CheckContext, dict[str, typing.Any]], CheckResult]] = {
    "declaration_names_roster_employee": declaration_names_roster_employee,
    "invoice_ref_is_issued": invoice_ref_is_issued,
    "limitation_period_recomputed": limitation_period_recomputed,
    "revenue_fact_is_verifiable": revenue_fact_is_verifiable,
    "tax_code_verdict_agrees": tax_code_verdict_agrees,
}

__all__ = ["STATUTORY_CHECKS", "declaration_names_roster_employee", "invoice_ref_is_issued",
           "limitation_period_recomputed", "revenue_fact_is_verifiable", "tax_code_verdict_agrees"]
