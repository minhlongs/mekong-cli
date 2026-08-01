"""Revenue share payout calculation for marketplace plugin developers."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

# Revenue split: 80% developer / 20% platform
DEVELOPER_SHARE = 0.80
PLATFORM_SHARE = 0.20

# Minimum payout threshold in cents (e.g., $50.00 = 5000 cents)
MINIMUM_PAYOUT_CENTS = 5000


@dataclass(frozen=True)
class PayoutRecord:
    """Single month's payout for one plugin."""
    plugin_id: str
    developer_id: str
    period_start: str  # ISO date
    period_end: str
    gross_revenue_cents: int
    developer_share_cents: int
    platform_share_cents: int
    paid_out: bool = False
    paid_at: Optional[str] = None


def calculate_payout(gross_revenue_cents: int) -> dict:
    """Calculate 80/20 revenue split.

    Args:
        gross_revenue_cents: Total revenue in cents for the period.

    Returns:
        Dict with gross, developer_share, platform_share, all in cents.
    """
    dev = round(gross_revenue_cents * DEVELOPER_SHARE)
    plat = gross_revenue_cents - dev
    return {
        "gross_cents": gross_revenue_cents,
        "developer_share_cents": dev,
        "platform_share_cents": plat,
        "split": f"{int(DEVELOPER_SHARE*100)}/{int(PLATFORM_SHARE*100)}",
    }


def is_payout_eligible(total_pending_cents: int) -> bool:
    """Check if accumulated earnings meet minimum payout threshold."""
    return total_pending_cents >= MINIMUM_PAYOUT_CENTS


def monthly_settlement_report(plugin_id: str, transactions: List[dict]) -> dict:
    """Generate monthly settlement for a plugin.

    Args:
        plugin_id: Plugin identifier
        transactions: List of purchase records with 'amount_cents' each

    Returns:
        Dict with settlement summary including eligible payout flag.
    """
    gross = sum(t.get("amount_cents", 0) for t in transactions)
    split = calculate_payout(gross)
    eligible = is_payout_eligible(split["developer_share_cents"])

    return {
        "plugin_id": plugin_id,
        "period": _current_month(),
        **split,
        "developer_pending_cents": split["developer_share_cents"],
        "eligible_for_payout": eligible,
        "minimum_threshold_cents": MINIMUM_PAYOUT_CENTS,
    }


def _current_month() -> str:
    """Return YYYY-MM for current month."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m")
