# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Inheritance calculation engine orchestrating Article 658 priority obligations and share allocation."""

from __future__ import annotations

import typing

from .calculator_intestate import calculate_intestate_shares
from .calculator_testamentary import calculate_testamentary_shares
from .enums import HeirRank, SuccessionType, WillStatus


def calculate_statutory_shares_record(estate: dict[str, typing.Any]) -> dict[str, typing.Any]:
    """Execute complete succession allocation under Civil Code 2015."""
    gross_assets = estate["summary"]["total_gross_assets"]
    obligations = estate["obligations"]
    wills = estate["wills"]
    heirs = estate["heirs"]

    # Step 1: Pay obligations according to priority waterfall (Art. 658)
    total_obligations_claimed = sum(o["amount"] for o in obligations)
    obligations_settlement: list[dict[str, typing.Any]] = []
    remaining_funds = gross_assets

    sorted_obligations = sorted(obligations, key=lambda x: x["priority"])
    for ob in sorted_obligations:
        pay_amount = min(remaining_funds, ob["amount"])
        remaining_funds -= pay_amount
        obligations_settlement.append({
            "obligation_id": ob["obligation_id"],
            "creditor_name": ob["creditor_name"],
            "priority": ob["priority"],
            "claimed_amount": ob["amount"],
            "paid_amount": pay_amount,
            "deficit": ob["amount"] - pay_amount,
            "is_fully_paid": pay_amount == ob["amount"],
        })

    total_obligations_paid = sum(o["paid_amount"] for o in obligations_settlement)

    # Step 2: Dedicated worship estate (Art. 645)
    worship_assigned = estate["dedicated_worship_amount"]
    actual_worship_deducted = 0.0
    if worship_assigned > 0:
        if remaining_funds >= worship_assigned:
            actual_worship_deducted = worship_assigned
            remaining_funds -= actual_worship_deducted
        else:
            actual_worship_deducted = remaining_funds
            remaining_funds = 0.0

    net_distributable_estate = remaining_funds

    # Step 3: Check testamentary vs intestate
    valid_will = next((w for w in wills if w["will_status"] == WillStatus.VALID.value and not w["is_revoked"]), None)
    succession_mode = SuccessionType.TESTAMENTARY.value if valid_will else SuccessionType.INTESTATE.value

    # Hypothetical rank 1 share for forced heir calculation (Art. 644)
    rank_1_hypothetical_heirs = [
        h for h in heirs
        if h["heir_rank"] == HeirRank.FIRST_RANK.value
        and not h["has_disclaimed_art620"]
        and not (h["is_disqualified_art621"] and not h["is_forgiven_in_will"])
        and (h["is_alive_at_opening"] or h["is_substitutional_art652"] or h["is_conceived_before_opening"])
    ]
    num_hypothetical_rank1 = len(rank_1_hypothetical_heirs)
    one_statutory_share = (net_distributable_estate / num_hypothetical_rank1) if num_hypothetical_rank1 > 0 else 0.0
    forced_heir_statutory_2_3_share = (2.0 / 3.0) * one_statutory_share

    if succession_mode == SuccessionType.INTESTATE.value:
        allocations = calculate_intestate_shares(heirs, net_distributable_estate)
    else:
        allocations = calculate_testamentary_shares(heirs, net_distributable_estate, forced_heir_statutory_2_3_share)

    return {
        "estate_id": estate["estate_id"],
        "decedent_name": estate["decedent_name"],
        "date_of_death": estate["date_of_death"],
        "succession_mode": succession_mode,
        "gross_assets": gross_assets,
        "total_obligations_claimed": total_obligations_claimed,
        "total_obligations_paid": total_obligations_paid,
        "obligations_settlement": obligations_settlement,
        "dedicated_worship_deducted": actual_worship_deducted,
        "net_distributable_estate": round(net_distributable_estate, 2),
        "one_statutory_share_reference": round(one_statutory_share, 2),
        "forced_heir_2_3_share_reference": round(forced_heir_statutory_2_3_share, 2),
        "allocations": allocations,
    }


__all__ = ["calculate_statutory_shares_record"]
