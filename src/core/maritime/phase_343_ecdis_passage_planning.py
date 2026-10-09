"""Phase 343: ECDIS Passage Planning & Safety Contour Engine.

Implements IMO Res. A.893(21), SOLAS V/34, and IHO S-57/S-52 standards for
safety depth, safety contour, squat estimation, CATZOC depth allowance,
and narrow channel cross-track limit (XTL) corridor validation.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class PassageLegInput:
    leg_name: str
    planned_speed_knots: float = 10.0
    static_draft_m: float = 8.5
    block_coefficient_cb: float = 0.80
    ukc_policy_m: float = 1.0
    height_of_tide_m: float = 1.5
    catzoc_category: str = "A1"  # "A1", "A2", "B", "C", "U"
    channel_depth_charted_m: float = 11.0
    channel_type: str = "NARROW"  # "NARROW", "APPROACH", "OPEN_SEA"


@dataclass
class PassageLegResult:
    leg_name: str
    squat_m: float
    catzoc_allowance_m: float
    safety_depth_m: float
    safety_contour_m: float
    cross_track_limit_m: float
    look_ahead_minutes: float
    is_safe_transit: bool
    advisories: List[str] = field(default_factory=list)


class EcdisPassagePlanningEngine:
    AVAILABLE_CONTOURS: List[float] = [5.0, 10.0, 15.0, 20.0, 30.0, 50.0]

    @classmethod
    def evaluate(cls, inp: PassageLegInput) -> PassageLegResult:
        advisories: List[str] = []

        # 1. Ship squat calculation: Barrass formula
        v_sq = inp.planned_speed_knots ** 2
        if inp.channel_type == "NARROW":
            # Confined channel squat
            squat = round((inp.block_coefficient_cb * v_sq) / 50.0, 2)
        else:
            # Open water squat
            squat = round((2.0 * inp.block_coefficient_cb * v_sq) / 100.0, 2)

        # 2. CATZOC depth uncertainty allowance per IHO S-57
        d = inp.channel_depth_charted_m
        catzoc = inp.catzoc_category.upper()
        if catzoc == "A1":
            catzoc_err = 0.5 + 0.01 * d
        elif catzoc in ("A2", "B"):
            catzoc_err = 1.0 + 0.02 * d
        elif catzoc == "C":
            catzoc_err = 2.0 + 0.05 * d
        else:  # "U" unassessed
            catzoc_err = 3.0 + 0.10 * d
        catzoc_allowance = round(catzoc_err, 2)

        # 3. Safety depth per IMO Resolution A.893(21)
        # Safety Depth = Draft + Squat + UKC - Tide + CATZOC Allowance
        gross_needed = inp.static_draft_m + squat + inp.ukc_policy_m + catzoc_allowance
        safety_depth = round(gross_needed - inp.height_of_tide_m, 2)

        # 4. Safety contour: round up to next available contour on ENC
        safety_contour = 50.0
        for c in cls.AVAILABLE_CONTOURS:
            if c >= safety_depth:
                safety_contour = c
                break

        # 5. Cross-track limit (XTL) corridor
        if inp.channel_type == "NARROW":
            xtl = 50.0
            look_ahead = 6.0
        elif inp.channel_type == "APPROACH":
            xtl = 100.0
            look_ahead = 10.0
        else:
            xtl = 500.0
            look_ahead = 15.0

        # 6. Under-keel clearance verification
        available_water = inp.channel_depth_charted_m + inp.height_of_tide_m
        is_safe = available_water >= gross_needed

        if not is_safe:
            deficit = round(gross_needed - available_water, 2)
            advisories.append(f"GROUNDING RISK: Available depth {available_water:.2f}m < Required {gross_needed:.2f}m (Deficit {deficit:.2f}m).")
            advisories.append("REDUCE SPEED OR AWAIT HIGH TIDE: Speed reduction directly reduces squat.")
        else:
            effective_ukc = round(available_water - (inp.static_draft_m + squat + catzoc_allowance), 2)
            advisories.append(f"TRANSIT APPROVED: Effective dynamic UKC {effective_ukc:.2f}m satisfies policy.")

        if catzoc in ("C", "U"):
            advisories.append(f"HIGH BATHYMETRIC UNCERTAINTY: CATZOC {catzoc} requires echo sounder continuous logging.")

        return PassageLegResult(
            leg_name=inp.leg_name,
            squat_m=squat,
            catzoc_allowance_m=catzoc_allowance,
            safety_depth_m=safety_depth,
            safety_contour_m=safety_contour,
            cross_track_limit_m=xtl,
            look_ahead_minutes=look_ahead,
            is_safe_transit=is_safe,
            advisories=advisories,
        )
