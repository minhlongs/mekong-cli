"""Phase 381: Automatic Draft & Tank Sounding Gauging Radar/Bubbler Engine.

Implements IMO Res. MSC.267(85) (2008 IS Code) hydrostatic draft surveying,
quarter-mean trim/heel/deflection, and SOLAS XII tank sounding under 200 lines.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class DraftTankGaugingInput:
    vessel_id: str
    draft_fore_m: float = 10.50
    draft_mid_port_m: float = 10.80
    draft_mid_starboard_m: float = 10.80
    draft_aft_m: float = 11.20
    beam_m: float = 32.20
    tank_height_m: float = 15.00
    sounding_level_m: float = 12.00
    dry_void_ingress_detected: bool = False


@dataclass
class DraftTankGaugingReport:
    vessel_id: str
    quarter_mean_draft_m: float
    trim_m: float
    heel_angle_deg: float
    hull_deflection_m: float
    deflection_type: str
    tank_ullage_m: float
    tank_filling_pct: float
    is_high_level_alarm: bool
    is_overfill_alarm: bool
    is_water_ingress_alarm: bool
    system_status: str
    warnings: List[str] = field(default_factory=list)


class DraftTankSoundingGaugingEngine:
    """Evaluates hydrostatic drafts, vessel trim/heel/deflection, and tank soundings."""

    HIGH_LEVEL_PCT: float = 95.0
    OVERFILL_LEVEL_PCT: float = 98.0

    def evaluate(self, inp: DraftTankGaugingInput) -> DraftTankGaugingReport:
        warnings: List[str] = []

        # 1. Hydrostatic Draft Calculations
        d_mid = (inp.draft_mid_port_m + inp.draft_mid_starboard_m) / 2.0
        # Quarter-mean draft: (dF + 6*dM + dA) / 8
        qm_draft = (inp.draft_fore_m + 6.0 * d_mid + inp.draft_aft_m) / 8.0
        trim = inp.draft_aft_m - inp.draft_fore_m

        # Heel angle from port-starboard midship difference
        delta_list = inp.draft_mid_starboard_m - inp.draft_mid_port_m
        heel_deg = math.degrees(math.atan2(delta_list, max(1.0, inp.beam_m)))
        if abs(heel_deg) > 2.0:
            warnings.append(f"Vessel list angle {abs(heel_deg):.2f}° exceeds 2.0° operational limit.")

        # Hull deflection (Sagging > 0 / Hogging < 0)
        baseline_mid = (inp.draft_fore_m + inp.draft_aft_m) / 2.0
        deflection = d_mid - baseline_mid
        defl_type = "SAGGING" if deflection >= 0 else "HOGGING"
        if abs(deflection) > 0.15:
            warnings.append(
                f"Severe hull deflection ({defl_type}): {abs(deflection):.3f}m exceeding structural threshold."
            )

        # 2. Tank Gauging & Sounding / Ullage
        ullage = max(0.0, inp.tank_height_m - inp.sounding_level_m)
        filling_pct = (inp.sounding_level_m / max(0.1, inp.tank_height_m)) * 100.0

        is_high = filling_pct >= self.HIGH_LEVEL_PCT
        is_overfill = filling_pct >= self.OVERFILL_LEVEL_PCT

        if is_overfill:
            warnings.append(
                f"OVERFILL ALARM: tank level {filling_pct:.1f}% exceeds 98% safe capacity. Terminate bunkering."
            )
        elif is_high:
            warnings.append(
                f"High level alarm: tank level {filling_pct:.1f}% exceeds 95% threshold. Reduce flow rate."
            )

        # 3. SOLAS XII Water Ingress Detection in dry holds
        if inp.dry_void_ingress_detected:
            warnings.append("SOLAS XII WATER INGRESS ALARM: Active water intrusion in dry hold/void.")

        # Determine overall status
        if is_overfill or inp.dry_void_ingress_detected:
            status = "CRITICAL_ALARM"
        elif is_high or abs(heel_deg) > 2.0 or abs(deflection) > 0.15:
            status = "WARNING"
        else:
            status = "OPTIMAL"

        return DraftTankGaugingReport(
            vessel_id=inp.vessel_id,
            quarter_mean_draft_m=round(qm_draft, 3),
            trim_m=round(trim, 3),
            heel_angle_deg=round(heel_deg, 2),
            hull_deflection_m=round(deflection, 3),
            deflection_type=defl_type,
            tank_ullage_m=round(ullage, 3),
            tank_filling_pct=round(filling_pct, 2),
            is_high_level_alarm=is_high,
            is_overfill_alarm=is_overfill,
            is_water_ingress_alarm=inp.dry_void_ingress_detected,
            system_status=status,
            warnings=warnings,
        )
