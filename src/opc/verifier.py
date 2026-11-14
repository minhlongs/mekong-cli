"""Deterministic Vietnamese SME two-stage math/confidence verifier and MOIM context compactor."""
from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation
from typing import Any, Final, Sequence

MIN_EXTRACTION_CONFIDENCE: Final[float] = 0.85


class HaltForHumanError(ValueError):
    """Raised when extraction confidence < 0.85 or financial math fails deterministic checks."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code


def verify_confidence_and_math(
    line_items: Sequence[dict[str, Any]],
    declared_total: Decimal | int | str,
    confidence: float = 1.0,
    tax_rate: Decimal = Decimal("0"),
) -> Decimal:
    """Two-stage deterministic verifier: halt for human on NaN/low confidence, negative values, or mismatch."""
    conf = float(confidence)
    if not math.isfinite(conf) or conf < MIN_EXTRACTION_CONFIDENCE or conf > 1.0:
        raise HaltForHumanError("HALT_FOR_HUMAN", f"Invalid or low extraction confidence ({confidence}).")
    try:
        actual_total = Decimal(str(declared_total))
        if not actual_total.is_finite() or actual_total < 0 or tax_rate < 0:
            raise HaltForHumanError("MATH_MISMATCH_REQUIRES_HUMAN", "Negative or non-finite total/tax rejected.")
        computed_sub = Decimal("0")
        for idx, item in enumerate(line_items):
            qty = Decimal(str(item.get("hours", item.get("quantity", 0))))
            rate = Decimal(str(item.get("rate", item.get("unit_price", 0))))
            if not qty.is_finite() or not rate.is_finite() or qty < 0 or rate < 0:
                raise HaltForHumanError("MATH_MISMATCH_REQUIRES_HUMAN", f"Negative/non-finite item at line {idx}.")
            expected_line = qty * rate
            if "subtotal" in item and Decimal(str(item["subtotal"])) != expected_line:
                raise HaltForHumanError("MATH_MISMATCH_REQUIRES_HUMAN", f"Line {idx} mismatch: {qty}*{rate}!={item['subtotal']}.")
            computed_sub += expected_line
    except InvalidOperation as exc:
        raise HaltForHumanError("MATH_MISMATCH_REQUIRES_HUMAN", f"Invalid decimal operand: {exc}") from exc

    expected_total = computed_sub + (computed_sub * tax_rate)
    if expected_total != actual_total:
        raise HaltForHumanError("MATH_MISMATCH_REQUIRES_HUMAN", f"Total {actual_total} != sum {expected_total}.")
    return expected_total


def compact_conversation_preserving_moim(
    turns: Sequence[str], moim_guardrail: str, keep_recent: int = 6,
) -> tuple[str, ...]:
    """Deterministically compact long conversation history while pinning MOIM guardrail and recent turns."""
    pinned = moim_guardrail.strip()
    if not pinned:
        raise ValueError("MOIM guardrail text cannot be empty.")
    recent_n = max(1, int(keep_recent))
    if len(turns) <= recent_n:
        return (pinned, *turns)
    archived = turns[:-recent_n]
    tail = turns[-recent_n:]
    summary = f"[AUTO_COMPACTED turns=1..{len(archived)} count={len(archived)}]"
    return (pinned, summary, *tail)
