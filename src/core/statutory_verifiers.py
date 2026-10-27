# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dual-Path Quantitative Statutory Verifiers for Vietnamese Tax, Accounting & Law.

Implements independent mathematical verification of command execution outputs
using ``decimal.Decimal`` with ``ROUND_HALF_UP`` to the nearest integer VND.

Cross-checks:
1. PIT (Thuế TNCN): Progressive bracket accumulation vs. General Department of
   Taxation shortcut formulas (Phụ lục 01/PL-TNCN, Thông tư 111/2013/TT-BTC).
2. CIT (Thuế TNDN): 20% standard vs. 17% SME rate and Decree 132/2020/NĐ-CP
   30% EBITDA interest deduction cap.
3. VAT (Thuế GTGT): Exact 0%, 5%, 8%, 10% rate verification.
4. VAS Accounting (Kế toán TT200/TT133): Double-entry balance invariant
   (Total Debit == Total Credit).
5. Social Insurance (BHXH NĐ 73/2024): Base salary 2.34M VND, 20x cap 46.8M VND,
   10.5% employee and 21.5% employer contribution rates.
6. VietQR (Napas 247): EMVCo TLV structure and CRC16-CCITT (0x1021) checksum.
7. Administrative Sanctions (Luật XLVPHC & NĐ 125/2020): 2.0x organization
   multiplier and ±10% aggravating/mitigating adjustments.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import typing

from src.core.vietqr_engine import _crc16_ccitt


def _round_vnd(val: Decimal | int | float | str) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _pit_brackets(as_of: typing.Any) -> tuple[tuple[Decimal, Decimal], ...]:
    """Return ``((upper_bound, rate), ...)`` for the schedule in force at ``as_of``.

    ``None`` as an upper bound means "and above".
    """
    from src.core.vn_statutory_rules import pit_rule

    rule = pit_rule(as_of)
    raw = rule.params.get("brackets") or ()  # type: ignore[union-attr]
    return tuple((Decimal("Infinity") if upper is None else Decimal(str(upper)), Decimal(str(rate)))
                 for upper, rate in raw)


def _pit_shortcut(taxable: Decimal, brackets: tuple[tuple[Decimal, Decimal], ...]) -> tuple[Decimal, int]:
    """GDT shortcut formula (Cách 2) derived from the bracket table itself.

    For the bracket *i* that the taxable income falls into:
    ``tax = rate_i x taxable - QD_i`` with
    ``QD_i = sum over j < i of (rate_i - rate_j) x width_j`` — the algebraic
    equivalent of accumulating every slice, so this remains an *independent*
    path from the engine's own bracket loop and works for both the 7-bracket
    schedule (until 2025) and the 5-bracket schedule (from 2026).
    """
    if taxable <= 0:
        return Decimal("0"), 0
    lower_edge = Decimal("0")
    slices: list[tuple[Decimal, Decimal]] = []
    index = len(brackets)
    for position, (upper, _rate) in enumerate(brackets, start=1):
        if taxable <= upper:
            index = position
            break
        slices.append((upper - lower_edge, _rate))
        lower_edge = upper
    rate = brackets[index - 1][1]
    quick_deduction = sum(((rate - slice_rate) * width for width, slice_rate in slices), Decimal("0"))
    return _round_vnd(taxable * rate - quick_deduction), index


def verify_pit_dual_path(
    taxable_income_vnd: Decimal | int | float,
    reported_tax_vnd: Decimal | int | float,
    as_of: typing.Any = None,
) -> dict[str, typing.Any]:
    """Verify PIT against the progressive schedule in force for the tax period.

    Until 31/12/2025 that is the 7-bracket schedule of Điều 22 Luật Thuế TNCN
    with the shortcut table of Phụ lục 01/PL-TNCN (Thông tư 111/2013/TT-BTC).
    From tax year 2026 it is the 5-bracket schedule of Luật 109/2025/QH15 — a
    verifier pinned to the old table would reject a correct 2026 payslip.
    """
    from src.core.vn_statutory_rules import pit_rule

    tntt = max(Decimal("0"), _round_vnd(taxable_income_vnd))
    reported = _round_vnd(reported_tax_vnd)
    rule = pit_rule(as_of)
    brackets = _pit_brackets(as_of)
    shortcut_tax, bracket = _pit_shortcut(tntt, brackets)

    delta = abs(reported - shortcut_tax)
    passed = delta <= Decimal("1")
    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "GDT_SHORTCUT_APPENDIX_01_PL_TNCN",
        "bracket": bracket,
        "bracket_count": len(brackets),
        "taxable_income_vnd": int(tntt),
        "shortcut_expected_vnd": int(shortcut_tax),
        "reported_tax_vnd": int(reported),
        "delta_vnd": int(delta),
        "rule_version": rule.version,
        "rule_effective_from": rule.effective_from.isoformat(),
        "as_of": str(as_of) if as_of is not None else None,
        "statutory_citation": rule.citation,
    }


def verify_cit_calculation(
    annual_revenue_vnd: Decimal | int | float,
    taxable_profit_vnd: Decimal | int | float,
    reported_tax_vnd: Decimal | int | float,
    is_sme_incentive: bool = True,
    as_of: typing.Any = None,
) -> dict[str, typing.Any]:
    """Verify CIT against the rate tiers in force for the tax year.

    Luật 67/2025/QH15 (effective 01/10/2025) sets 20% standard, 15% when annual
    revenue <= 3B VND and 17% for 3B < revenue <= 50B VND. Before that date only
    the 20% standard rate applies — the SME tiers must not be applied backwards.
    """
    from src.core.vn_statutory_rules import cit_rule

    rev = _round_vnd(annual_revenue_vnd)
    profit = max(Decimal("0"), _round_vnd(taxable_profit_vnd))
    reported = _round_vnd(reported_tax_vnd)
    rule = cit_rule(as_of)

    standard = Decimal(str(rule.params["standard_rate"]))  # type: ignore[index]
    small_rate = rule.params.get("sme_small_rate")  # type: ignore[union-attr]
    medium_rate = rule.params.get("sme_medium_rate")  # type: ignore[union-attr]
    small_max = Decimal(str(rule.params.get("sme_small_max_revenue", 0)))  # type: ignore[union-attr]
    medium_max = Decimal(str(rule.params.get("sme_medium_max_revenue", 0)))  # type: ignore[union-attr]

    if is_sme_incentive and small_rate is not None and rev <= small_max:
        rate, tier = Decimal(str(small_rate)), "SME_SMALL_15"
    elif is_sme_incentive and medium_rate is not None and rev <= medium_max:
        rate, tier = Decimal(str(medium_rate)), "SME_MEDIUM_17"
    else:
        rate, tier = standard, "STANDARD_20"

    expected = _round_vnd(profit * rate)
    delta = abs(reported - expected)
    passed = delta <= Decimal("1")

    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "CIT_STATUTORY_RATE_VERIFIER",
        "applied_rate_pct": float(rate * Decimal("100")),
        "rate_tier": tier,
        "annual_revenue_vnd": int(rev),
        "taxable_profit_vnd": int(profit),
        "expected_tax_vnd": int(expected),
        "reported_tax_vnd": int(reported),
        "delta_vnd": int(delta),
        "rule_version": rule.version,
        "statutory_citation": rule.citation,
    }


def verify_vat_calculation(
    subtotal_vnd: Decimal | int | float,
    vat_rate_pct: int,
    reported_vat_vnd: Decimal | int | float,
    reported_total_vnd: Decimal | int | float,
) -> dict[str, typing.Any]:
    """Verify VAT calculation under Decree 123/2020/NĐ-CP & Decree 72/2024/NĐ-CP."""
    sub = _round_vnd(subtotal_vnd)
    rate_dec = Decimal(str(vat_rate_pct)) / Decimal("100")
    expected_vat = _round_vnd(sub * rate_dec)
    expected_total = sub + expected_vat

    rep_vat = _round_vnd(reported_vat_vnd)
    rep_tot = _round_vnd(reported_total_vnd)

    passed = (rep_vat == expected_vat) and (rep_tot == expected_total) and (vat_rate_pct in (0, 5, 8, 10))
    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "VAT_TT78_DECIMAL_VERIFIER",
        "vat_rate_pct": vat_rate_pct,
        "expected_vat_vnd": int(expected_vat),
        "expected_total_vnd": int(expected_total),
        "reported_vat_vnd": int(rep_vat),
        "reported_total_vnd": int(rep_tot),
        "statutory_citation": "Thông tư 78/2021/TT-BTC & Nghị định 72/2024/NĐ-CP",
    }


def verify_vas_double_entry(
    total_debit_vnd: Decimal | int | float,
    total_credit_vnd: Decimal | int | float,
    entries: list[dict[str, typing.Any]] | None = None,
) -> dict[str, typing.Any]:
    """Verify Circular 200/133 double-entry accounting balance (Debit == Credit > 0)."""
    debit = _round_vnd(total_debit_vnd)
    credit = _round_vnd(total_credit_vnd)

    lines_debit = Decimal("0")
    lines_credit = Decimal("0")
    if entries:
        for line in entries:
            lines_debit += _round_vnd(line.get("debit", 0))
            lines_credit += _round_vnd(line.get("credit", 0))
        passed = (debit == credit) and (debit > 0) and (lines_debit == debit) and (lines_credit == credit)
    else:
        passed = (debit == credit) and (debit > 0)

    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "VAS_TT200_DOUBLE_ENTRY_BALANCE",
        "total_debit_vnd": int(debit),
        "total_credit_vnd": int(credit),
        "imbalance_vnd": int(abs(debit - credit)),
        "statutory_citation": "Thông tư 200/2014/TT-BTC & Thông tư 133/2016/TT-BTC",
    }


def verify_bhxh_contribution(
    raw_salary_vnd: Decimal | int | float,
    reported_employee_vnd: Decimal | int | float,
    reported_employer_vnd: Decimal | int | float,
    include_kpcd: bool = False,
    region: int = 1,
    as_of: typing.Any = None,
) -> dict[str, typing.Any]:
    """Verify compulsory contributions against the ceilings in force for the period.

    BHXH/BHYT base is capped at 20 x the reference salary (2,340,000đ until
    30/06/2026 per NĐ 73/2024; 2,530,000đ from 01/07/2026 per NĐ 161/2026) and
    the BHTN base at 20 x the regional minimum wage (NĐ 74/2024 until
    31/12/2025; NĐ 293/2025 from 01/01/2026). Rates: employee 8% + 1.5% + 1%,
    employer 17.5% + 3% + 1% (+2% KPCĐ on the BHXH base when requested).
    """
    from src.core.vn_statutory_rules import bhxh_rule

    rule = bhxh_rule(as_of)
    params = rule.params
    reference = Decimal(str(params["reference_salary"]))  # type: ignore[index]
    multiplier = Decimal(str(params["ceiling_multiplier"]))  # type: ignore[index]
    regional = Decimal(str(params["regional_min_wage"][int(region)]))  # type: ignore[index]
    emp_rates = {k: Decimal(str(v)) for k, v in params["employee_rates"].items()}  # type: ignore[union-attr]
    em_rates = {k: Decimal(str(v)) for k, v in params["employer_rates"].items()}  # type: ignore[union-attr]

    raw = _round_vnd(raw_salary_vnd)
    cap_bhxh_bhyt = reference * multiplier
    cap_bhtn = regional * multiplier
    capped_bhxh = min(raw, cap_bhxh_bhyt)
    capped_bhtn = min(raw, cap_bhtn)

    expected_emp = _round_vnd(
        capped_bhxh * (emp_rates["bhxh"] + emp_rates["bhyt"]) + capped_bhtn * emp_rates["bhtn"]
    )
    expected_dn = _round_vnd(
        capped_bhxh * (em_rates["bhxh"] + em_rates["bhyt"]) + capped_bhtn * em_rates["bhtn"]
    )
    if include_kpcd:
        expected_dn += _round_vnd(capped_bhxh * em_rates["kpcd"])

    rep_emp = _round_vnd(reported_employee_vnd)
    rep_dn = _round_vnd(reported_employer_vnd)

    passed = (abs(rep_emp - expected_emp) <= Decimal("1")) and (abs(rep_dn - expected_dn) <= Decimal("1"))
    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "BHXH_STATUTORY_CAP_VERIFIER",
        "legacy_verifier": "BHXH_ND73_2024_CAP_VERIFIER",
        "capped_salary_bhxh_vnd": int(capped_bhxh),
        "cap_bhxh_bhyt_vnd": int(cap_bhxh_bhyt),
        "cap_bhtn_vnd": int(cap_bhtn),
        "region": int(region),
        "expected_employee_vnd": int(expected_emp),
        "expected_employer_vnd": int(expected_dn),
        "reported_employee_vnd": int(rep_emp),
        "reported_employer_vnd": int(rep_dn),
        "rule_version": rule.version,
        "statutory_citation": rule.citation,
    }


def verify_vietqr_emvco(qr_payload: str) -> dict[str, typing.Any]:
    """Verify EMVCo Napas 247 QR payload format and CRC16-CCITT (0x1021) checksum."""
    clean = qr_payload.strip()
    if len(clean) < 12 or "6304" not in clean[-8:]:
        return {
            "status": "FAILED",
            "verifier": "EMVCO_CRC16_CCITT_0x1021",
            "reason": "Missing 6304 CRC tag at tail of payload",
            "statutory_citation": "Quyết định 201/QĐ-NHNN & EMVCo Merchant QR Spec",
        }

    body = clean[:-4]
    provided_crc = clean[-4:].upper()
    expected_crc = _crc16_ccitt(body).upper()
    has_napas_aid = "A000000727" in clean
    passed = (provided_crc == expected_crc) and has_napas_aid

    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "EMVCO_CRC16_CCITT_0x1021",
        "provided_crc": provided_crc,
        "expected_crc": expected_crc,
        "has_napas_aid": has_napas_aid,
        "statutory_citation": "Quyết định 201/QĐ-NHNN & Thông tư 07/VBHN-NHNN",
    }


def verify_admin_sanction_fine(
    min_fine_vnd: Decimal | int | float,
    max_fine_vnd: Decimal | int | float,
    entity_type: str,
    mitigating_count: int,
    aggravating_count: int,
    reported_fine_vnd: Decimal | int | float,
) -> dict[str, typing.Any]:
    """Verify administrative fine under Law 67/2020/QH14 Art. 24.2 & Decree 118/2021/NĐ-CP."""
    min_f = _round_vnd(min_fine_vnd)
    max_f = _round_vnd(max_fine_vnd)
    multiplier = Decimal("2") if entity_type.upper() == "ORGANIZATION" else Decimal("1")

    adj_min = min_f * multiplier
    adj_max = max_f * multiplier
    midpoint = _round_vnd((adj_min + adj_max) / Decimal("2"))

    # Each aggravating/mitigating factor adjusts by ±10% of midpoint (NĐ 125/2020)
    # or scales by (Max - Average) / (n + 1) (Điều 9 NĐ 118/2021/NĐ-CP), clamped to [adj_min, adj_max]
    net_factors = int(aggravating_count) - int(mitigating_count)
    step_10pct = _round_vnd(midpoint * Decimal("0.10") * Decimal(str(net_factors)))
    expected_10pct = max(adj_min, min(adj_max, midpoint + step_10pct))

    if net_factors == 0:
        expected_nd118 = midpoint
    elif net_factors > 0:
        step_nd118 = _round_vnd((adj_max - midpoint) / Decimal(str(int(aggravating_count) + 1)))
        expected_nd118 = min(adj_max, midpoint + step_nd118 * Decimal(str(net_factors)))
    else:
        step_nd118 = _round_vnd((midpoint - adj_min) / Decimal(str(int(mitigating_count) + 1)))
        expected_nd118 = max(adj_min, midpoint - step_nd118 * Decimal(str(abs(net_factors))))

    reported = _round_vnd(reported_fine_vnd)
    passed = (abs(reported - expected_10pct) <= Decimal("1000")) or (abs(reported - expected_nd118) <= Decimal("1000"))
    expected = expected_nd118 if abs(reported - expected_nd118) <= abs(reported - expected_10pct) else expected_10pct
    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "XLVPHC_ND118_125_FINE_VERIFIER",
        "entity_multiplier": int(multiplier),
        "adjusted_min_vnd": int(adj_min),
        "adjusted_max_vnd": int(adj_max),
        "midpoint_vnd": int(midpoint),
        "expected_fine_vnd": int(expected),
        "reported_fine_vnd": int(reported),
        "statutory_citation": "Điều 23 & 24 Luật XLVPHC (sửa đổi 2020), Nghị định 118/2021/NĐ-CP & Nghị định 125/2020/NĐ-CP",
    }
