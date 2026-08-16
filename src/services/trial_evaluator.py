# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Trial evaluator service — billing webhook support.

Provides:
- compute_trial_dates(): returns trial start/end date dict
- evaluate_trial(tenant_id, customer_id): evaluates trial grace window
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

TRIAL_DAYS = 14
GRACE_DAYS = 3


def compute_trial_dates() -> dict:
    """Compute trial start and end dates.

    Returns:
        Dict with trial_started_at (today ISO) and trial_ends_at (today + TRIAL_DAYS, ISO).
    """
    today = date.today()
    return {
        "trial_started_at": today.isoformat(),
        "trial_ends_at": (today + timedelta(days=TRIAL_DAYS)).isoformat(),
    }


def evaluate_trial(tenant_id: str, customer_id: str) -> dict:
    """Evaluate trial grace window after subscription deletion.

    In production this checks whether the trial can be extended into the
    grace period or should be downgraded.  Here we log and return a
    placeholder result so callers can await/spawn it without breaking.

    Args:
        tenant_id: Internal tenant identifier.
        customer_id: Stripe customer ID.

    Returns:
        Dict with evaluation outcome.
    """
    logger.info(
        "Evaluating trial for tenant=%s customer=%s (grace=%dd)",
        tenant_id,
        customer_id,
        GRACE_DAYS,
    )
    return {
        "tenant_id": tenant_id,
        "customer_id": customer_id,
        "action": "grace_window_active",
        "grace_days": GRACE_DAYS,
    }
