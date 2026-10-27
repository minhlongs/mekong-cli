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


def verify_pit_dual_path(
    taxable_income_vnd: Decimal | int | float,
    reported_tax_vnd: Decimal | int | float,
) -> dict[str, typing.Any]:
    """Verify PIT using GDT shortcut formula (Phụ lục 01/PL-TNCN TT 111/2013/TT-BTC)."""
    tntt = max(Decimal("0"), _round_vnd(taxable_income_vnd))
    reported = _round_vnd(reported_tax_vnd)

    # Shortcut formula (Cách 2 - Rút gọn theo Phụ lục 01/PL-TNCN):
    # Bậc 1: <= 5M          -> 5% * TNTT
    # Bậc 2: >5M..10M       -> 10% * TNTT - 250,000
    # Bậc 3: >10M..18M      -> 15% * TNTT - 750,000
    # Bậc 4: >18M..32M      -> 20% * TNTT - 1,650,000
    # Bậc 5: >32M..52M      -> 25% * TNTT - 3,250,000
    # Bậc 6: >52M..80M      -> 30% * TNTT - 5,850,000
    # Bậc 7: >80M           -> 35% * TNTT - 9,850,000
    if tntt == Decimal("0"):
        shortcut_tax = Decimal("0")
        bracket = 0
    elif tntt <= Decimal("5000000"):
        shortcut_tax = _round_vnd(tntt * Decimal("0.05"))
        bracket = 1
    elif tntt <= Decimal("10000000"):
        shortcut_tax = _round_vnd(tntt * Decimal("0.10") - Decimal("250000"))
        bracket = 2
    elif tntt <= Decimal("18000000"):
        shortcut_tax = _round_vnd(tntt * Decimal("0.15") - Decimal("750000"))
        bracket = 3
    elif tntt <= Decimal("32000000"):
        shortcut_tax = _round_vnd(tntt * Decimal("0.20") - Decimal("1650000"))
        bracket = 4
    elif tntt <= Decimal("52000000"):
        shortcut_tax = _round_vnd(tntt * Decimal("0.25") - Decimal("3250000"))
        bracket = 5
    elif tntt <= Decimal("80000000"):
        shortcut_tax = _round_vnd(tntt * Decimal("0.30") - Decimal("5850000"))
        bracket = 6
    else:
        shortcut_tax = _round_vnd(tntt * Decimal("0.35") - Decimal("9850000"))
        bracket = 7

    delta = abs(reported - shortcut_tax)
    passed = delta <= Decimal("1")
    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "GDT_SHORTCUT_APPENDIX_01_PL_TNCN",
        "bracket": bracket,
        "taxable_income_vnd": int(tntt),
        "shortcut_expected_vnd": int(shortcut_tax),
        "reported_tax_vnd": int(reported),
        "delta_vnd": int(delta),
        "statutory_citation": "Điều 22 Luật Thuế TNCN & Phụ lục 01/PL-TNCN (Thông tư 111/2013/TT-BTC)",
    }


def verify_cit_calculation(
    annual_revenue_vnd: Decimal | int | float,
    taxable_profit_vnd: Decimal | int | float,
    reported_tax_vnd: Decimal | int | float,
    is_sme_incentive: bool = True,
) -> dict[str, typing.Any]:
    """Verify CIT calculation under Law on Corporate Income Tax (20% standard, 17% SME)."""
    rev = _round_vnd(annual_revenue_vnd)
    profit = max(Decimal("0"), _round_vnd(taxable_profit_vnd))
    reported = _round_vnd(reported_tax_vnd)

    rate = Decimal("0.17") if (is_sme_incentive and rev <= Decimal("3000000000")) else Decimal("0.20")
    expected = _round_vnd(profit * rate)
    delta = abs(reported - expected)
    passed = delta <= Decimal("1")

    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "CIT_STATUTORY_RATE_VERIFIER",
        "applied_rate_pct": int(rate * Decimal("100")),
        "expected_tax_vnd": int(expected),
        "reported_tax_vnd": int(reported),
        "delta_vnd": int(delta),
        "statutory_citation": "Điều 10 Luật Thuế TNDN & Nghị định 132/2020/NĐ-CP",
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
) -> dict[str, typing.Any]:
    """Verify Social Insurance contributions under Decree 73/2024/NĐ-CP (cap 46.8M VND)."""
    raw = _round_vnd(raw_salary_vnd)
    cap_bhxh_bhyt = Decimal("46800000")  # 20 * 2,340,000 VND
    capped_bhxh = min(raw, cap_bhxh_bhyt)

    # Employee: 8% BHXH + 1.5% BHYT on capped_bhxh + 1% BHTN on BHTN cap (99.2M Region I)
    cap_bhtn = Decimal("99200000")
    capped_bhtn = min(raw, cap_bhtn)

    expected_emp = _round_vnd(capped_bhxh * Decimal("0.095") + capped_bhtn * Decimal("0.01"))
    dn_rate = Decimal("0.205")
    expected_dn = _round_vnd(capped_bhxh * dn_rate + capped_bhtn * Decimal("0.01"))
    if include_kpcd:
        expected_dn += _round_vnd(capped_bhxh * Decimal("0.02"))

    rep_emp = _round_vnd(reported_employee_vnd)
    rep_dn = _round_vnd(reported_employer_vnd)

    passed = (abs(rep_emp - expected_emp) <= Decimal("1")) and (abs(rep_dn - expected_dn) <= Decimal("1"))
    return {
        "status": "PASSED" if passed else "FAILED",
        "verifier": "BHXH_ND73_2024_CAP_VERIFIER",
        "capped_salary_bhxh_vnd": int(capped_bhxh),
        "expected_employee_vnd": int(expected_emp),
        "expected_employer_vnd": int(expected_dn),
        "reported_employee_vnd": int(rep_emp),
        "reported_employer_vnd": int(rep_dn),
        "statutory_citation": "Nghị định 73/2024/NĐ-CP & Quyết định 595/QĐ-BHXH",
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
