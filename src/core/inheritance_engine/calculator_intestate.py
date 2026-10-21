# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Intestate inheritance division algorithm under Articles 649-655 Civil Code 2015."""

from __future__ import annotations

import typing

from .enums import HeirRank


def calculate_intestate_shares(
    heirs: list[dict[str, typing.Any]],
    net_distributable_estate: float,
) -> list[dict[str, typing.Any]]:
    """Divide estate intestate equally among active eligible heirs in priority ranks (Art. 651 & 652)."""
    allocations: list[dict[str, typing.Any]] = []

    for target_rank in (HeirRank.FIRST_RANK.value, HeirRank.SECOND_RANK.value, HeirRank.THIRD_RANK.value):
        rank_heirs = [
            h for h in heirs
            if h["heir_rank"] == target_rank
            and not h["has_disclaimed_art620"]
            and not (h["is_disqualified_art621"] and not h["is_forgiven_in_will"])
            and (h["is_alive_at_opening"] or h["is_substitutional_art652"] or h["is_conceived_before_opening"])
        ]
        if rank_heirs:
            direct_heirs = [h for h in rank_heirs if not h["is_substitutional_art652"]]
            sub_heirs = [h for h in rank_heirs if h["is_substitutional_art652"]]

            sub_branches: dict[str, list[dict[str, typing.Any]]] = {}
            for sh in sub_heirs:
                sub_key = sh.get("substituting_for_name") or sh["heir_id"]
                sub_branches.setdefault(sub_key, []).append(sh)

            total_branches = len(direct_heirs) + len(sub_branches)
            branch_amount = net_distributable_estate / total_branches if total_branches > 0 else 0.0
            branch_percentage = 100.0 / total_branches if total_branches > 0 else 0.0

            heir_allocations_map: dict[str, dict[str, typing.Any]] = {}
            for dh in direct_heirs:
                heir_allocations_map[dh["heir_id"]] = {
                    "amount": branch_amount,
                    "percentage": branch_percentage,
                    "rule": "Điều 651 BLDS 2015 (Thừa kế theo pháp luật cùng hàng hưởng đều nhau)",
                }

            for sub_key, sh_list in sub_branches.items():
                sh_count = len(sh_list)
                sh_amount = branch_amount / sh_count if sh_count > 0 else 0.0
                sh_percentage = branch_percentage / sh_count if sh_count > 0 else 0.0
                for sh in sh_list:
                    heir_allocations_map[sh["heir_id"]] = {
                        "amount": sh_amount,
                        "percentage": sh_percentage,
                        "rule": f"Điều 652 BLDS 2015 (Thừa kế thế vị hưởng chung 1 suất của {sub_key})",
                    }

            for h in heirs:
                if h["heir_id"] in heir_allocations_map:
                    alloc_info = heir_allocations_map[h["heir_id"]]
                    allocations.append({
                        "heir_id": h["heir_id"],
                        "full_name": h["full_name"],
                        "relationship": h["relationship"],
                        "heir_rank": h["heir_rank"],
                        "is_forced_heir": False,
                        "allocated_amount": alloc_info["amount"],
                        "allocated_percentage": alloc_info["percentage"],
                        "rule_applied": alloc_info["rule"],
                        "status": "ELIGIBLE",
                    })
                else:
                    status_reason = "Đã từ chối (Đ.620)" if h["has_disclaimed_art620"] else (
                        "Không được hưởng (Đ.621)" if h["is_disqualified_art621"] else (
                            f"Hàng sau ({h['heir_rank']}) không được hưởng vì còn hàng trước"
                        )
                    )
                    allocations.append({
                        "heir_id": h["heir_id"],
                        "full_name": h["full_name"],
                        "relationship": h["relationship"],
                        "heir_rank": h["heir_rank"],
                        "is_forced_heir": False,
                        "allocated_amount": 0.0,
                        "allocated_percentage": 0.0,
                        "rule_applied": status_reason,
                        "status": "INELIGIBLE",
                    })
            return allocations

    # If no eligible heirs in rank 1, 2, or 3: Escheat to State (Điều 622)
    allocations.append({
        "heir_id": "STATE_TREASURY",
        "full_name": "Nhà nước Việt Nam (Điều 622 BLDS 2015)",
        "relationship": "STATE",
        "heir_rank": "NONE",
        "is_forced_heir": False,
        "allocated_amount": net_distributable_estate,
        "allocated_percentage": 100.0,
        "rule_applied": "Điều 622 BLDS 2015 (Di sản không có người thừa kế thuộc về Nhà nước)",
        "status": "ESCHEAT",
    })
    return allocations


__all__ = ["calculate_intestate_shares"]
