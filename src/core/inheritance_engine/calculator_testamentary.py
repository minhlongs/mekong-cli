# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Testamentary inheritance division with forced heir protection (Art. 644) under Civil Code 2015."""

from __future__ import annotations

import typing

from .enums import HeirRelationship


def _get_active_forced_heirs(heirs: list[dict[str, typing.Any]]) -> list[dict[str, typing.Any]]:
    """Identify eligible forced heirs under Article 644 BLDS 2015."""
    forced_candidates = [
        h for h in heirs
        if h["relationship"] in (
            HeirRelationship.SPOUSE.value,
            HeirRelationship.BIOLOGICAL_PARENT.value,
            HeirRelationship.ADOPTIVE_PARENT.value,
        ) or (
            h["relationship"] in (HeirRelationship.BIOLOGICAL_CHILD.value, HeirRelationship.ADOPTED_CHILD.value)
            and h["is_minor_or_disabled"]
        )
    ]
    return [
        fh for fh in forced_candidates
        if not fh["has_disclaimed_art620"]
        and not (fh["is_disqualified_art621"] and not fh["is_forgiven_in_will"])
        and fh["is_alive_at_opening"]
    ]


def calculate_testamentary_shares(
    heirs: list[dict[str, typing.Any]],
    net_distributable_estate: float,
    forced_heir_statutory_2_3_share: float,
) -> list[dict[str, typing.Any]]:
    """Allocate estate by will while strictly protecting forced heirs under Article 644 & 659."""
    active_forced_heirs = _get_active_forced_heirs(heirs)
    forced_heir_deficits: dict[str, float] = {}
    total_forced_deficit = 0.0

    for fh in active_forced_heirs:
        given_amount = 0.0
        if fh["testamentary_share_percent"] > 0:
            given_amount = (fh["testamentary_share_percent"] / 100.0) * net_distributable_estate
        elif fh["testamentary_fixed_amount"] > 0:
            given_amount = min(net_distributable_estate, fh["testamentary_fixed_amount"])

        required_amount = forced_heir_statutory_2_3_share
        if given_amount < required_amount:
            deficit = required_amount - given_amount
            forced_heir_deficits[fh["heir_id"]] = deficit
            total_forced_deficit += deficit

    available_for_testamentary = max(0.0, net_distributable_estate - sum(
        max(forced_heir_statutory_2_3_share, (h["testamentary_share_percent"] / 100.0) * net_distributable_estate if h["testamentary_share_percent"] > 0 else h["testamentary_fixed_amount"])
        for h in active_forced_heirs
    ))

    other_beneficiaries = [
        h for h in heirs
        if h["heir_id"] not in [fh["heir_id"] for fh in active_forced_heirs]
        and not h["has_disclaimed_art620"]
        and not (h["is_disqualified_art621"] and not h["is_forgiven_in_will"])
        and (h["testamentary_share_percent"] > 0 or h["testamentary_fixed_amount"] > 0)
    ]

    total_nominal_other = sum(
        (b["testamentary_share_percent"] / 100.0) * net_distributable_estate if b["testamentary_share_percent"] > 0 else b["testamentary_fixed_amount"]
        for b in other_beneficiaries
    )

    allocations: list[dict[str, typing.Any]] = []
    for h in heirs:
        if h["has_disclaimed_art620"]:
            allocations.append({
                "heir_id": h["heir_id"], "full_name": h["full_name"], "relationship": h["relationship"],
                "heir_rank": h["heir_rank"], "is_forced_heir": False, "allocated_amount": 0.0,
                "allocated_percentage": 0.0, "rule_applied": "Điều 620 BLDS 2015 (Đã từ chối nhận di sản)", "status": "DISCLAIMED",
            })
        elif h["is_disqualified_art621"] and not h["is_forgiven_in_will"]:
            allocations.append({
                "heir_id": h["heir_id"], "full_name": h["full_name"], "relationship": h["relationship"],
                "heir_rank": h["heir_rank"], "is_forced_heir": False, "allocated_amount": 0.0,
                "allocated_percentage": 0.0, "rule_applied": "Điều 621 BLDS 2015 (Không có quyền hưởng di sản)", "status": "DISQUALIFIED",
            })
        elif h in active_forced_heirs:
            nominal_given = (h["testamentary_share_percent"] / 100.0) * net_distributable_estate if h["testamentary_share_percent"] > 0 else h["testamentary_fixed_amount"]
            actual_share = max(nominal_given, forced_heir_statutory_2_3_share)
            pct = (actual_share / net_distributable_estate * 100.0) if net_distributable_estate > 0 else 0.0
            rule = "Điều 644 BLDS 2015 (Người thừa kế không phụ thuộc nội dung di chúc - hưởng 2/3 suất theo luật)" if actual_share > nominal_given else "Theo Di chúc (Đã đủ 2/3 suất Đ.644)"
            allocations.append({
                "heir_id": h["heir_id"], "full_name": h["full_name"], "relationship": h["relationship"],
                "heir_rank": h["heir_rank"], "is_forced_heir": True, "forced_minimum_required": forced_heir_statutory_2_3_share,
                "allocated_amount": round(actual_share, 2), "allocated_percentage": round(pct, 2),
                "rule_applied": rule, "status": "FORCED_HEIR_PROTECTED",
            })
        elif h in other_beneficiaries:
            nominal = (h["testamentary_share_percent"] / 100.0) * net_distributable_estate if h["testamentary_share_percent"] > 0 else h["testamentary_fixed_amount"]
            pro_rata_factor = (available_for_testamentary / total_nominal_other if available_for_testamentary < total_nominal_other else 1.0) if total_nominal_other > 0 else 1.0
            actual_share = nominal * pro_rata_factor
            pct = (actual_share / net_distributable_estate * 100.0) if net_distributable_estate > 0 else 0.0
            allocations.append({
                "heir_id": h["heir_id"], "full_name": h["full_name"], "relationship": h["relationship"],
                "heir_rank": h["heir_rank"], "is_forced_heir": False, "allocated_amount": round(actual_share, 2),
                "allocated_percentage": round(pct, 2), "rule_applied": "Điều 659 BLDS 2015 (Phân chia theo di chúc, điều chỉnh bảo đảm suất Đ.644)",
                "status": "TESTAMENTARY_BENEFICIARY",
            })
        else:
            allocations.append({
                "heir_id": h["heir_id"], "full_name": h["full_name"], "relationship": h["relationship"],
                "heir_rank": h["heir_rank"], "is_forced_heir": False, "allocated_amount": 0.0,
                "allocated_percentage": 0.0, "rule_applied": "Không được chỉ định trong di chúc hợp pháp", "status": "OMITTED_IN_WILL",
            })
    return allocations


__all__ = ["calculate_testamentary_shares"]
