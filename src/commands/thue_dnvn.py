"""
Thuế Doanh Nghiệp VN — Tính TNCN lũy tiến, TNDN, GTGT.
Offline, không cần API. Tax rates embedded (2024-2026).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple


# Biểu thuế TNCN lũy tiến (Điều 22, Luật thuế TNCN)
# (thu_nhap_toi_da_thang, thue_suat)
TNCN_BRACKETS: List[Tuple[Decimal, Decimal]] = [
    (Decimal("5_000_000"), Decimal("0.05")),
    (Decimal("10_000_000"), Decimal("0.10")),
    (Decimal("18_000_000"), Decimal("0.15")),
    (Decimal("32_000_000"), Decimal("0.20")),
    (Decimal("52_000_000"), Decimal("0.25")),
    (Decimal("80_000_000"), Decimal("0.30")),
    (Decimal("999_999_999"), Decimal("0.35")),
]

PERSONAL_DEDUCTION = Decimal("11_000_000")  # Giảm trừ bản thân/tháng
DEPENDENT_DEDUCTION = Decimal("4_400_000")  # Giảm trừ mỗi người phụ thuộc/tháng

TNDN_RATE = Decimal("0.20")  # 20% tiêu chuẩn
TNDN_SME_RATE = Decimal("0.17")  # 17% SME ≤ 3 tỷ/năm
TNDN_SME_THRESHOLD = Decimal("3_000_000_000")

DISCLAIMER = "Tra cứu tại thuedientu.gdt.gov.vn để xác nhận. Thuế VN thay đổi theo pháp luật."


@dataclass
class TNCNResult:
    gross_income: Decimal
    personal_deduction: Decimal
    dependent_deduction: Decimal
    taxable_income: Decimal
    tax_amount: Decimal
    net_income: Decimal
    effective_rate: Decimal
    breakdown: List[dict]

    def format_vnd(self, amount: Decimal) -> str:
        return f"{int(amount):,} đ".replace(",", ".")

    def to_summary(self) -> str:
        lines = [
            "=== TÍNH THUẾ TNCN ===",
            f"Thu nhập gộp:      {self.format_vnd(self.gross_income)}/tháng",
            f"Giảm trừ bản thân: {self.format_vnd(self.personal_deduction)}",
            f"Giảm trừ PT:       {self.format_vnd(self.dependent_deduction)}",
            f"Thu nhập tính thuế:{self.format_vnd(self.taxable_income)}",
            "",
            "Chi tiết lũy tiến:",
        ]
        for b in self.breakdown:
            lines.append(f"  Bậc {b['bracket']}: {self.format_vnd(b['amount'])} × {b['rate']} = {self.format_vnd(b['tax'])}")
        lines += [
            "",
            f"THUẾ TNCN PHẢI NỘP: {self.format_vnd(self.tax_amount)}/tháng",
            f"Thuế suất thực tế:  {float(self.effective_rate * 100):.1f}%",
            f"Thu nhập thực lĩnh: {self.format_vnd(self.net_income)}/tháng",
            "",
            f"⚠️  {DISCLAIMER}",
        ]
        return "\n".join(lines)


def calculate_tncn(
    monthly_income: int,
    dependents: int = 0,
) -> TNCNResult:
    """Tính thuế TNCN theo biểu lũy tiến."""
    gross = Decimal(str(monthly_income))
    dep_deduction = DEPENDENT_DEDUCTION * dependents
    taxable = max(Decimal("0"), gross - PERSONAL_DEDUCTION - dep_deduction)

    tax = Decimal("0")
    breakdown = []
    remaining = taxable
    prev_bracket = Decimal("0")

    for i, (bracket_max, rate) in enumerate(TNCN_BRACKETS, 1):
        if remaining <= 0:
            break
        bracket_width = bracket_max - prev_bracket
        amount_in_bracket = min(remaining, bracket_width)
        tax_in_bracket = (amount_in_bracket * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if amount_in_bracket > 0:
            breakdown.append({
                "bracket": i,
                "amount": amount_in_bracket,
                "rate": f"{int(rate * 100)}%",
                "tax": tax_in_bracket,
            })
        tax += tax_in_bracket
        remaining -= amount_in_bracket
        prev_bracket = bracket_max

    effective_rate = (tax / gross).quantize(Decimal("0.0001")) if gross > 0 else Decimal("0")

    return TNCNResult(
        gross_income=gross,
        personal_deduction=PERSONAL_DEDUCTION,
        dependent_deduction=dep_deduction,
        taxable_income=taxable,
        tax_amount=tax,
        net_income=gross - tax,
        effective_rate=effective_rate,
        breakdown=breakdown,
    )


@dataclass
class TNDNResult:
    revenue: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    is_sme: bool

    def format_vnd(self, amount: Decimal) -> str:
        return f"{int(amount):,} đ".replace(",", ".")

    def to_summary(self) -> str:
        rate_note = "(SME ≤ 3 tỷ/năm)" if self.is_sme else "(tiêu chuẩn)"
        return (
            f"=== TÍNH THUẾ TNDN ===\n"
            f"Doanh thu:     {self.format_vnd(self.revenue)}\n"
            f"Thuế suất:     {int(self.tax_rate * 100)}% {rate_note}\n"
            f"THUẾ TNDN:     {self.format_vnd(self.tax_amount)}\n\n"
            f"⚠️  {DISCLAIMER}"
        )


def calculate_tndn(annual_revenue: int) -> TNDNResult:
    """Tính thuế TNDN."""
    revenue = Decimal(str(annual_revenue))
    is_sme = revenue <= TNDN_SME_THRESHOLD
    rate = TNDN_SME_RATE if is_sme else TNDN_RATE
    tax = (revenue * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return TNDNResult(revenue=revenue, tax_rate=rate, tax_amount=tax, is_sme=is_sme)


def calculate_gtgt(amount: int, rate: int = 10) -> dict:
    """Tính thuế GTGT."""
    base = Decimal(str(amount))
    vat_rate = Decimal(str(rate)) / 100
    vat = (base * vat_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    total = base + vat
    return {
        "base_amount": int(base),
        "vat_rate": f"{rate}%",
        "vat_amount": int(vat),
        "total_amount": int(total),
        "disclaimer": DISCLAIMER,
    }


def main(argv=None) -> int:
    """CLI: python3 -m src.commands.thue_dnvn {tncn|tndn|gtgt} ..."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="thue-dnvn", description="Thuế VN: TNCN/TNDN/GTGT")
    sub = parser.add_subparsers(dest="command", required=True)

    p_tncn = sub.add_parser("tncn", help="Thuế TNCN biểu lũy tiến")
    p_tncn.add_argument("--income", type=int, required=True, help="Thu nhập tháng (VND)")
    p_tncn.add_argument("--dependents", type=int, default=0)

    p_tndn = sub.add_parser("tndn", help="Thuế TNDN")
    p_tndn.add_argument("--revenue", type=int, required=True, help="Doanh thu năm (VND)")

    p_gtgt = sub.add_parser("gtgt", help="Thuế GTGT (VAT)")
    p_gtgt.add_argument("--amount", type=int, required=True)
    p_gtgt.add_argument("--rate", type=int, default=10, choices=[0, 5, 8, 10])

    args = parser.parse_args(argv)

    def _run() -> None:
        if args.command == "tncn":
            r = calculate_tncn(args.income, dependents=args.dependents)
            sys.stdout.write(r.to_summary())
        elif args.command == "tndn":
            r = calculate_tndn(args.revenue)
            sys.stdout.write(r.to_summary())
        elif args.command == "gtgt":
            import json as _json
            sys.stdout.write(_json.dumps(calculate_gtgt(args.amount, rate=args.rate), ensure_ascii=False, indent=2))
        sys.stdout.write("\n")

    try:
        from src.core.usage_meter import Stopwatch
        with Stopwatch("thue-dnvn"):
            _run()
    except ImportError:
        _run()
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
