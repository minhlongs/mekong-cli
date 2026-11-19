"""VND rounding and VAT breakdown calculations shared by quotes and drafts."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def _round_vnd(value: Decimal | int | str) -> int:
    """Round a VND monetary value to the nearest integer using Decimal ROUND_HALF_UP."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def compute_vnd_vat_breakdown(subtotal_vnd: Decimal | int | str, vat_rate_pct: int = 8) -> tuple[int, int, int]:
    """Compute (subtotal_vnd, vat_amount_vnd, total_amount_vnd) with Decimal ROUND_HALF_UP."""
    if vat_rate_pct not in (0, 5, 8, 10):
        raise ValueError(f"Unsupported Vietnamese VAT rate '{vat_rate_pct}%' (expected 0, 5, 8, or 10).")
    sub_dec = Decimal(str(subtotal_vnd))
    subtotal_int = _round_vnd(sub_dec)
    vat_int = _round_vnd((Decimal(subtotal_int) * Decimal(vat_rate_pct)) / Decimal(100))
    total_int = subtotal_int + vat_int
    return subtotal_int, vat_int, total_int
