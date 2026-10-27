# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Domain postconditions for Vietnamese finance, tax, insurance and payments.

Each check recomputes the answer *independently* from
:mod:`src.core.vn_statutory_rules` (dual-path verification) or re-measures a
structural/legal invariant of the produced artifact. They never read the
handler's own ``ok``/``status`` field as proof.
"""

from __future__ import annotations

import datetime
import decimal
import typing

from src.core.promise.checks import CheckContext, CheckResult, resolve_path
from src.core.vn_statutory_rules import (
    compute_bhxh,
    compute_cit,
    compute_deductions,
    compute_pit,
    mst_checksum,
    validate_vat_rate,
    vat_amount,
)

D = decimal.Decimal
TOLERANCE_VND = 1.0


def _num(value: typing.Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _close(left: typing.Any, right: typing.Any, tolerance: float = TOLERANCE_VND) -> bool:
    a, b = _num(left), _num(right)
    return a is not None and b is not None and abs(a - b) <= tolerance


def _period(ctx: CheckContext, args: dict[str, typing.Any]) -> typing.Any:
    return (
        args.get("period_param")
        and ctx.params.get(str(args["period_param"]))
        or ctx.params.get("tax_period")
        or ctx.params.get("as_of")
        or None
    )


def pit_dual_path(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """Recompute PIT (deductions + progressive schedule) from statute."""
    period = _period(ctx, args)
    income = _num(ctx.params.get(args.get("income_param", "monthly_income")))
    dependents = int(ctx.params.get(args.get("dependents_param", "dependents"), 0) or 0)
    if income is None:
        return CheckResult("pit_dual_path", "FAILED", "no monthly income supplied")
    deductions = compute_deductions(dependents, period)
    taxable = max(0.0, income - deductions["total_deductions"])
    recomputed = compute_pit(taxable, period)

    reported_tax = resolve_path(ctx.result, args.get("tax_path", "tax_amount"))
    reported_taxable = resolve_path(ctx.result, args.get("taxable_path", "taxable_income"))
    reported_personal = resolve_path(ctx.result, args.get("personal_path", "personal_deduction"))
    problems: list[str] = []
    if not _close(reported_taxable, taxable):
        problems.append(f"taxable income {reported_taxable} != statutory {taxable}")
    if not _close(reported_tax, recomputed["tax"]):
        problems.append(
            f"PIT {reported_tax} != statutory {recomputed['tax']} for period "
            f"{recomputed['rule_version']}"
        )
    if not _close(reported_personal, deductions["personal_deduction"]):
        problems.append(
            f"personal deduction {reported_personal} != {deductions['personal_deduction']} "
            f"({recomputed['citation']})"
        )
    if problems:
        return CheckResult("pit_dual_path", "FAILED", "; ".join(problems),
                           {"statutory_tax": recomputed["tax"], "rule_version": recomputed["rule_version"]})
    return CheckResult(
        "pit_dual_path", "PASSED",
        f"PIT recomputed from {recomputed['rule_version']} matches ({recomputed['tax']} VND)",
        {"statutory_tax": recomputed["tax"], "taxable": taxable,
         "rule_version": recomputed["rule_version"], "citation": recomputed["citation"]},
    )


def cit_dual_path(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    period = _period(ctx, args)
    revenue = _num(ctx.params.get("annual_revenue", ctx.params.get("revenue")))
    profit = _num(ctx.params.get("profit"))
    is_sme = bool(ctx.params.get("is_sme", True))
    if revenue is None:
        return CheckResult("cit_dual_path", "FAILED", "no annual revenue supplied")
    taxable_profit = profit if profit is not None else round(revenue * 0.15)
    recomputed = compute_cit(taxable_profit, revenue, period, is_sme=is_sme)
    reported_rate = resolve_path(ctx.result, args.get("rate_path", "applied_rate_pct"))
    reported_tax = resolve_path(ctx.result, args.get("tax_path", "tax_amount"))
    problems: list[str] = []
    if not _close(reported_rate, recomputed["rate_pct"], 0.001):
        problems.append(
            f"CIT rate {reported_rate}% != statutory {recomputed['rate_pct']}% "
            f"({recomputed['rate_tier']})"
        )
    if not _close(reported_tax, recomputed["tax"]):
        problems.append(f"CIT {reported_tax} != statutory {recomputed['tax']}")
    if problems:
        return CheckResult("cit_dual_path", "FAILED", "; ".join(problems),
                           {"rule_version": recomputed["rule_version"]})
    return CheckResult(
        "cit_dual_path", "PASSED",
        f"CIT recomputed under {recomputed['rule_version']} ({recomputed['rate_tier']}) matches",
        {"statutory_tax": recomputed["tax"], "rate_tier": recomputed["rate_tier"],
         "rule_version": recomputed["rule_version"], "citation": recomputed["citation"]},
    )


def vat_dual_path(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    period = _period(ctx, args)
    subtotal = _num(resolve_path(ctx.result, args.get("subtotal_path", "subtotal")))
    if subtotal is None:
        subtotal = _num(ctx.params.get("amount", ctx.params.get("subtotal")))
    rate = resolve_path(ctx.result, args.get("rate_path", "vat_rate_pct"))
    if rate is None:
        rate = ctx.params.get("rate", ctx.params.get("vat_rate"))
    sector = ctx.params.get("sector")
    legality = validate_vat_rate(rate, period, sector=sector)
    if not legality["valid"]:
        return CheckResult("vat_dual_path", "FAILED", legality["reason"], {"legality": legality})
    recomputed = vat_amount(subtotal, rate, period, sector=sector)
    reported_vat = resolve_path(ctx.result, args.get("vat_path", "vat_amount"))
    reported_total = resolve_path(ctx.result, args.get("total_path", "total_inclusive"))
    if reported_total is None:
        reported_total = resolve_path(ctx.result, "total_amount")
    problems: list[str] = []
    if not _close(reported_vat, recomputed["vat"]):
        problems.append(f"VAT {reported_vat} != statutory {recomputed['vat']}")
    if not _close(reported_total, recomputed["total_inclusive"]):
        problems.append(f"VAT-inclusive total {reported_total} != {recomputed['total_inclusive']}")
    if problems:
        return CheckResult("vat_dual_path", "FAILED", "; ".join(problems), {"legality": legality})
    return CheckResult(
        "vat_dual_path", "PASSED",
        f"VAT {rate}% verified for period under {legality['rule_version']}",
        {"vat": recomputed["vat"], "total": recomputed["total_inclusive"],
         "rule_version": legality["rule_version"], "citation": legality["citation"]},
    )


def bhxh_dual_path(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    period = _period(ctx, args) or ctx.params.get("period")
    salary = _num(ctx.params.get("salary"))
    region = int(ctx.params.get("region", 1) or 1)
    include_kpcd = bool(ctx.params.get("include_kpcd", False))
    if salary is None:
        return CheckResult("bhxh_dual_path", "FAILED", "no salary supplied")
    recomputed = compute_bhxh(salary, region, period, include_kpcd=include_kpcd)
    reported_employee = resolve_path(ctx.result, args.get("employee_total_path", "employee.total"))
    reported_employer = resolve_path(ctx.result, args.get("employer_total_path", "employer.total"))
    reported_ceiling = resolve_path(ctx.result, args.get("ceiling_path", "ceiling_bhxh_bhyt"))
    problems: list[str] = []
    if not _close(reported_employee, recomputed["employee_total"]):
        problems.append(
            f"employee contribution {reported_employee} != statutory {recomputed['employee_total']}"
        )
    if not _close(reported_employer, recomputed["employer_total"]):
        problems.append(
            f"employer contribution {reported_employer} != statutory {recomputed['employer_total']}"
        )
    if reported_ceiling is not None and not _close(reported_ceiling, recomputed["ceiling_bhxh_bhyt"]):
        problems.append(
            f"ceiling {reported_ceiling} != {recomputed['ceiling_bhxh_bhyt']} "
            f"(20 x reference salary, {recomputed['rule_version']})"
        )
    if problems:
        return CheckResult("bhxh_dual_path", "FAILED", "; ".join(problems),
                           {"rule_version": recomputed["rule_version"]})
    return CheckResult(
        "bhxh_dual_path", "PASSED",
        f"contributions recomputed under {recomputed['rule_version']} match "
        f"(ceiling {recomputed['ceiling_bhxh_bhyt']:.0f}đ)",
        {"employee_total": recomputed["employee_total"], "employer_total": recomputed["employer_total"],
         "rule_version": recomputed["rule_version"], "citation": recomputed["citation"]},
    )


#: PIT-exempt ceiling for a mid-shift meal allowance (Thông tư 26/2016/TT-BLĐTBXH).
LUNCH_EXEMPT_CAP = 730_000.0


def payroll_dual_path(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """Gross-to-net: insurance base, PIT reliefs, tax and net pay must tie out for the period.

    Statutory model re-derived here (independently of ``PayrollEngine``):

    * a meal allowance is excluded from the *compulsory insurance base*
      (Thông tư 10/2020/TT-BLĐTBXH) but capped at 730,000đ when exempted from PIT;
    * employee insurance is 10.5% of the capped base (8% BHXH + 1.5% BHYT + 1% BHTN);
    * taxable income = gross - employee insurance - family reliefs - exempt allowances;
    * net = gross - employee insurance - PIT.
    """
    period = _period(ctx, args) or ctx.params.get("month")
    gross = _num(ctx.params.get("gross"))
    if gross is None:
        return CheckResult("payroll_dual_path", "FAILED", "no gross salary supplied")
    bonus = _num(ctx.params.get("bonus")) or 0.0
    total_gross = gross + bonus
    dependents = int(_num(ctx.params.get("dependents")) or 0)
    region = int(_num(ctx.params.get("region")) or 1)
    lunch = _num(ctx.params.get("lunch_allowance"))
    if lunch is None:
        lunch = LUNCH_EXEMPT_CAP  # engine default
    other_exempt = _num(ctx.params.get("other_exempt_allowances")) or 0.0
    exempt_lunch = min(max(lunch, 0.0), LUNCH_EXEMPT_CAP)
    insurable = max(0.0, total_gross - lunch) if lunch > 0 else total_gross

    insurance_reported = _num(resolve_path(ctx.result, "employee_deductions.total_insurance"))
    taxable_reported = _num(resolve_path(ctx.result, "tax_calculation.taxable_income"))
    pit_reported = _num(resolve_path(ctx.result, "tax_calculation.pit_tax"))
    net_reported = (_num(resolve_path(ctx.result, "net_take_home"))
                    if _num(resolve_path(ctx.result, "net_take_home")) is not None
                    else _num(resolve_path(ctx.result, "net")))
    if insurance_reported is None or taxable_reported is None or pit_reported is None:
        return CheckResult("payroll_dual_path", "FAILED",
                           "payslip is missing insurance/taxable/PIT fields")

    statutory = compute_bhxh(insurable, region, period)
    reliefs = compute_deductions(dependents, period)
    expected_insurance = statutory["employee_total"]
    expected_taxable = max(
        0.0,
        total_gross - expected_insurance
        - float(reliefs["personal_deduction"]) - float(reliefs["dependent_deduction"])
        - exempt_lunch - other_exempt,
    )
    expected_pit = compute_pit(expected_taxable, period)
    expected_net = total_gross - expected_insurance - expected_pit["tax"]

    problems: list[str] = []
    if abs(insurance_reported - expected_insurance) > 2.0:
        problems.append(
            f"employee insurance {insurance_reported:,.0f}đ != 10.5% of the capped base "
            f"{insurable:,.0f}đ = {expected_insurance:,.0f}đ ({statutory['rule_version']})"
        )
    ceiling_reported = _num(resolve_path(ctx.result, "insurance_base.ceiling_bhxh_bhyt"))
    if ceiling_reported is not None and not _close(ceiling_reported, statutory["ceiling_bhxh_bhyt"]):
        problems.append(
            f"BHXH/BHYT ceiling {ceiling_reported:,.0f}đ != {statutory['ceiling_bhxh_bhyt']:,.0f}đ "
            f"(20 x lương tham chiếu, {statutory['rule_version']})"
        )
    if abs(taxable_reported - expected_taxable) > 2.0:
        problems.append(
            f"taxable income {taxable_reported:,.0f}đ != gross {total_gross:,.0f}đ "
            f"- insurance {expected_insurance:,.0f}đ - reliefs "
            f"{float(reliefs['personal_deduction']) + float(reliefs['dependent_deduction']):,.0f}đ "
            f"- exempt allowances {exempt_lunch + other_exempt:,.0f}đ = {expected_taxable:,.0f}đ "
            f"({expected_pit['rule_version']})"
        )
    if abs(pit_reported - expected_pit["tax"]) > 2.0:
        problems.append(
            f"PIT {pit_reported:,.0f}đ != statutory {expected_pit['tax']:,.0f}đ "
            f"({expected_pit['rule_version']})"
        )
    if net_reported is not None and abs(net_reported - expected_net) > 2.0:
        problems.append(f"net pay {net_reported:,.0f}đ != gross - insurance - PIT = {expected_net:,.0f}đ")
    if problems:
        return CheckResult("payroll_dual_path", "FAILED", "; ".join(problems),
                           {"rule_version": expected_pit["rule_version"],
                            "insurance_rule_version": statutory["rule_version"]})
    return CheckResult(
        "payroll_dual_path", "PASSED",
        f"gross-to-net ties out: insurance {expected_insurance:,.0f}đ, taxable "
        f"{expected_taxable:,.0f}đ, PIT {expected_pit['tax']:,.0f}đ, net {expected_net:,.0f}đ "
        f"under {expected_pit['rule_version']}",
        {"insurance": expected_insurance, "taxable": expected_taxable, "pit": expected_pit["tax"],
         "net": expected_net, "rule_version": expected_pit["rule_version"],
         "insurance_rule_version": statutory["rule_version"],
         "citation": f"{expected_pit['citation']}; {statutory['citation']}"},
    )


def vas_double_entry(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """Circular 200/133 double-entry invariants for a sales journal."""
    debit = _num(resolve_path(ctx.result, "total_debit"))
    credit = _num(resolve_path(ctx.result, "total_credit"))
    entries = resolve_path(ctx.result, "entries") or []
    if debit is None or credit is None:
        return CheckResult("vas_double_entry", "FAILED", "journal is missing debit/credit totals")
    if abs(debit - credit) > 0.5:
        return CheckResult("vas_double_entry", "FAILED",
                           f"journal does not balance: debit {debit} != credit {credit}")
    by_account: dict[str, dict[str, float]] = {}
    for row in entries:
        code = str(row.get("account"))
        by_account[code] = {"debit": _num(row.get("debit")) or 0.0, "credit": _num(row.get("credit")) or 0.0}
    required = args.get("required_accounts") or ["131", "511", "3331"]
    missing = [code for code in required if code not in by_account]
    if missing:
        return CheckResult("vas_double_entry", "FAILED",
                           f"journal is missing required VAS accounts {missing}")
    revenue = by_account["511"]["credit"] if "511" in by_account else 0.0
    output_vat = by_account["3331"]["credit"] if "3331" in by_account else 0.0
    receivable = by_account["131"]["debit"] if "131" in by_account else 0.0
    if abs(receivable - (revenue + output_vat)) > 0.5:
        return CheckResult("vas_double_entry", "FAILED",
                           f"Nợ 131 ({receivable}) != Có 511 ({revenue}) + Có 3331 ({output_vat})")
    rate = ctx.params.get("vat_rate", 10)
    expected_vat = round(revenue * float(rate) / 100.0)
    if abs(output_vat - expected_vat) > 1.0:
        return CheckResult("vas_double_entry", "FAILED",
                           f"Có 3331 ({output_vat}) != {rate}% of revenue ({expected_vat})")
    return CheckResult(
        "vas_double_entry", "PASSED",
        f"balanced journal, Nợ 131 = Có 511 + Có 3331 ({receivable:.0f}đ), VAT {rate}% ties out",
        {"debit": debit, "credit": credit, "accounts": sorted(by_account)},
    )


def vietqr_emvco(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """Recompute the EMVCo CRC-16/CCITT-FALSE trailer of a VietQR payload."""
    payload = str(resolve_path(ctx.result, args.get("payload_path", "emvco_payload")) or "")
    if len(payload) < 20:
        return CheckResult("vietqr_emvco", "FAILED", "no EMVCo payload was produced")
    if payload[-8:-4] != "6304":
        return CheckResult("vietqr_emvco", "FAILED", "payload is missing the CRC tag 6304")
    body, crc = payload[:-4], payload[-4:]
    register = 0xFFFF
    for char in body.encode("ascii"):
        register ^= char << 8
        for _ in range(8):
            register = ((register << 1) ^ 0x1021) & 0xFFFF if register & 0x8000 else (register << 1) & 0xFFFF
    expected = f"{register:04X}"
    problems: list[str] = []
    if expected != crc.upper():
        problems.append(f"CRC trailer {crc} != recomputed {expected}")
    amount = ctx.params.get("amount_vnd", ctx.params.get("amount"))
    if amount is not None:
        tag = f"54{len(str(int(amount))):02d}{int(amount)}"
        if tag not in payload:
            problems.append(f"amount tag '{tag}' not present in payload")
    if "5303704" not in payload:
        problems.append("currency tag 53 (704 = VND) not present")
    if "5802VN" not in payload:
        problems.append("country tag 58 (VN) not present")
    account = str(ctx.params.get("account_number", "") or "")
    if account and account not in payload:
        problems.append(f"beneficiary account '{account}' not embedded in payload")
    if problems:
        return CheckResult("vietqr_emvco", "FAILED", "; ".join(problems), {"payload_length": len(payload)})
    return CheckResult(
        "vietqr_emvco", "PASSED",
        f"EMVCo CRC-16/CCITT-FALSE {crc} verified; amount/currency/country/account tags present",
        {"crc": crc, "payload_length": len(payload),
         "citation": "TCVN EMVCo QR (Napas QuickLink); tiêu chuẩn VietQR 2.0"},
    )


def adminsanction_fine_bounds(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """Luật XLVPHC 2012/2020 Art. 23-24 + NĐ 118/2021 fine bounds and direction."""
    entity = str(ctx.params.get("entity_type", "INDIVIDUAL")).upper()
    fine = _num(resolve_path(ctx.result, args.get("fine_path", "final_payable_fine_vnd")))
    if fine is None:
        fine = _num(resolve_path(ctx.result, "final_fine"))
    if fine is None:
        return CheckResult("adminsanction_fine_bounds", "FAILED", "no final fine was produced")
    # The engine rounds VND fines to the nearest thousand, so the frame and the
    # factor-direction checks carry that rounding granularity as tolerance.
    rounding = 500.0
    applied_min = None
    applied_max = None
    for prefix in ("applied_bracket", "applied"):
        lo = _num(resolve_path(ctx.result, f"{prefix}.min"))
        hi = _num(resolve_path(ctx.result, f"{prefix}.max"))
        if lo is None or hi is None:
            lo = _num(resolve_path(ctx.result, f"{prefix}_min_fine_vnd"))
            hi = _num(resolve_path(ctx.result, f"{prefix}_max_fine_vnd"))
        if lo is None or hi is None:
            lo = _num(resolve_path(ctx.result, f"{prefix}_min_fine"))
            hi = _num(resolve_path(ctx.result, f"{prefix}_max_fine"))
        if lo is not None and hi is not None:
            applied_min, applied_max = lo, hi
            break
    if applied_min is None or applied_max is None:
        return CheckResult("adminsanction_fine_bounds", "FAILED",
                           "engine did not report the applied statutory fine frame")
    problems: list[str] = []
    if not (applied_min - rounding <= fine <= applied_max + rounding):
        problems.append(f"fine {fine} outside the statutory frame [{applied_min}, {applied_max}]")
    mitigating = int(_num(ctx.params.get("mitigating_count", 0)) or 0) or len(
        ctx.params.get("mitigating_factors") or []
    )
    aggravating = int(_num(ctx.params.get("aggravating_count", 0)) or 0) or len(
        ctx.params.get("aggravating_factors") or []
    )
    average = (applied_min + applied_max) / 2
    if mitigating and not aggravating and fine > average + rounding:
        problems.append(f"{mitigating} mitigating factor(s) must pull the fine to/below the average {average}")
    if aggravating and not mitigating and fine < average - rounding:
        problems.append(f"{aggravating} aggravating factor(s) must push the fine to/above the average {average}")
    base_min = _num(ctx.params.get("min_fine"))
    if base_min is None:
        base_min = _num(ctx.params.get("statutory_min_fine_individual"))
    if entity == "ORGANIZATION" and base_min is not None and not _close(applied_min, 2 * base_min, rounding):
        problems.append(
            "organisations are fined at twice the individual frame (Art. 24 Luật XLVPHC): "
            f"applied_min {applied_min} vs 2 x {ctx.params.get('min_fine')}"
        )
    if problems:
        return CheckResult("adminsanction_fine_bounds", "FAILED", "; ".join(problems),
                           {"fine": fine, "frame": [applied_min, applied_max]})
    return CheckResult(
        "adminsanction_fine_bounds", "PASSED",
        f"fine {fine:.0f}đ inside statutory frame and consistent with "
        f"{mitigating} mitigating / {aggravating} aggravating factor(s)",
        {"fine": fine, "frame": [applied_min, applied_max], "entity_type": entity,
         "citation": "Điều 23-24 Luật XLVPHC 2012 (sửa đổi 2020); Nghị định 118/2021/NĐ-CP"},
    )


def mst_checksum_check(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """Modulus-11 check digit of a Vietnamese tax code (independent of the engine)."""
    raw = ctx.params.get(args.get("param", "tax_code")) or resolve_path(
        ctx.result, args.get("result_path", "tax_code")
    )
    verdict = mst_checksum(str(raw or ""))
    if not verdict["valid"]:
        return CheckResult("mst_checksum", "FAILED",
                           f"MST '{raw}' rejected: {verdict['reason']}", {"verdict": verdict})
    return CheckResult("mst_checksum", "PASSED", f"MST '{raw}' passes the modulus-11 check digit",
                       {"verdict": verdict})


def invoice_tt78_structure(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """A TT78 e-invoice artifact must carry the legally required elements."""
    required = args.get("required_fields") or [
        "invoice_id", "invoice_series", "invoice_number", "invoice_date", "seller_name",
        "seller_tax_code", "buyer_name", "subtotal", "vat_rate", "vat_amount", "total_amount",
    ]
    missing = [f for f in required if resolve_path(ctx.result, f) in (None, "")]
    xml = str(resolve_path(ctx.result, "xml_content") or "")
    problems: list[str] = []
    if missing:
        problems.append(f"invoice is missing required TT78 fields {missing}")
    if args.get("require_xml", True) and len(xml) < 80:
        problems.append("invoice has no XML representation (TT78 requires the e-invoice data file)")
    invoice_date = str(resolve_path(ctx.result, "invoice_date") or "")
    if invoice_date:
        try:
            datetime.date.fromisoformat(invoice_date)
        except ValueError:
            problems.append(f"invoice_date '{invoice_date}' is not a valid date")
    if problems:
        return CheckResult("invoice_tt78_structure", "FAILED", "; ".join(problems))
    return CheckResult(
        "invoice_tt78_structure", "PASSED",
        "e-invoice carries the TT78 mandatory elements and an XML data file",
        {"fields": required, "xml_bytes": len(xml),
         "citation": "Nghị định 123/2020/NĐ-CP; Thông tư 78/2021/TT-BTC"},
    )


def late_payment_interest(ctx: CheckContext, args: dict[str, typing.Any]) -> CheckResult:
    """0.03%/day late-payment interest (Điều 59 Luật Quản lý thuế 38/2019/QH14)."""
    declared = _num(ctx.params.get("declared_amount_vnd"))
    assessed = _num(ctx.params.get("assessed_amount_vnd"))
    if declared is None or assessed is None:
        return CheckResult("late_payment_interest", "FAILED", "declared/assessed amounts are required")
    # Điều 59: interest accrues on the *unpaid* tax — the higher of the declared
    # and assessed liability, less whatever has actually been paid.
    paid = _num(ctx.params.get("paid_amount_vnd"))
    if paid is None:
        paid = _num(resolve_path(ctx.result, "paid_amount_vnd"))
    outstanding = max(0.0, max(declared, assessed) - (paid or 0.0))
    reported = _num(resolve_path(ctx.result, "outstanding_tax_vnd"))
    interest = _num(resolve_path(ctx.result, args.get("interest_path", "late_payment_interest_vnd")))
    days = _num(resolve_path(ctx.result, args.get("days_path", "days_overdue")))
    if interest is None or days is None:
        return CheckResult("late_payment_interest", "FAILED",
                           "engine did not report days overdue / interest")
    problems: list[str] = []
    if reported is not None and not _close(reported, outstanding, 1.0):
        problems.append(
            f"outstanding tax {reported} != max(declared {declared}, assessed {assessed}) - paid {paid or 0}"
            f" = {outstanding}"
        )
    expected = round(outstanding * 0.0003 * days, 2)
    if abs(interest - expected) > max(2.0, expected * 0.01):
        problems.append(
            f"interest {interest} != 0.03%/day x {days:.0f} days x outstanding {outstanding} = {expected}"
        )
    if outstanding == 0.0 and days not in (0, None):
        problems.append("a fully paid liability must accrue zero days overdue")
    if problems:
        return CheckResult("late_payment_interest", "FAILED", "; ".join(problems),
                           {"expected": expected, "outstanding": outstanding})
    return CheckResult(
        "late_payment_interest", "PASSED",
        f"0.03%/day interest over {days:.0f} days on the outstanding {outstanding:.0f}đ = {interest:.0f}đ",
        {"days": days, "outstanding": outstanding, "interest": interest,
         "citation": "Điều 59 Luật Quản lý thuế 2019 (38/2019/QH14)"},
    )


FINANCE_CHECKS: dict[str, typing.Callable[[CheckContext, dict[str, typing.Any]], CheckResult]] = {
    "pit_dual_path": pit_dual_path,
    "cit_dual_path": cit_dual_path,
    "vat_dual_path": vat_dual_path,
    "bhxh_dual_path": bhxh_dual_path,
    "payroll_dual_path": payroll_dual_path,
    "vas_double_entry": vas_double_entry,
    "vietqr_emvco": vietqr_emvco,
    "adminsanction_fine_bounds": adminsanction_fine_bounds,
    "mst_checksum": mst_checksum_check,
    "invoice_tt78_structure": invoice_tt78_structure,
    "late_payment_interest": late_payment_interest,
}


def register() -> None:
    """Expose the finance checks to the generic postcondition evaluator."""
    from src.core.promise.checks import CHECKS

    for name, fn in FINANCE_CHECKS.items():
        CHECKS[name] = fn  # type: ignore[assignment]


register()

__all__ = ["FINANCE_CHECKS", "register"]
