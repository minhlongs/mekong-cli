"""Phase 425: Bilge Water Vacuum Evaporator & Concentrated Sludge Distillation.

Implements IMO MARPOL Annex I Reg 15 and Resolution MEPC.107(49) guidelines:
sub-atmospheric boiling kinetics via Antoine formulation (P_vac 0.10 - 0.20 bar abs,
T_boil 45 - 60°C utilizing jacket cooling waste heat), mass balance volume
reduction to produce clean distillate (oil content <= 5.0 ppm) and concentrated
sludge (> 60% oil), with VOC demister dP monitoring and optical anti-foaming interlock.
Strictly < 180 LOC, zero mocks.
"""

import math
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BilgeVacuumEvaporatorTelemetry:
    """Telemetry readings for Bilge Water Vacuum Evaporator & Distillation."""
    vacuum_pressure_bar_abs: float = 0.15
    evaporation_chamber_temp_c: float = 54.0
    heating_jacket_inlet_temp_c: float = 82.0
    feed_water_flow_l_h: float = 500.0
    feed_oil_content_pct: float = 3.5
    distillate_oil_ppm: float = 2.1
    distillate_flow_l_h: float = 465.0
    sludge_concentrate_oil_pct: float = 68.0
    demister_dp_mbar: float = 8.5
    foam_detected: bool = False
    anti_foam_dosing_active: bool = False
    vacuum_pump_running: bool = True


@dataclass(frozen=True)
class BilgeVacuumEvaporatorAssessment:
    """Evaporation kinetics, distillate purity, and sludge volume assessment."""
    theoretical_boiling_temp_c: float
    superheat_margin_c: float
    volume_reduction_ratio: float
    distillate_purity_compliant: bool
    sludge_concentration_adequate: bool
    vacuum_optimal: bool
    demister_clear: bool
    anti_foam_demanded: bool
    overboard_discharge_permitted: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class BilgeVacuumEvaporatorEngine:
    """Calculates vacuum distillation equilibria, distillate purity, and sludge recovery."""

    # Antoine coefficients for water (P in mmHg, T in °C): log10(P) = A - (B / (T + C))
    ANTOINE_A: float = 8.07131
    ANTOINE_B: float = 1730.63
    ANTOINE_C: float = 233.426

    MIN_VACUUM_BAR_ABS: float = 0.10
    MAX_VACUUM_BAR_ABS: float = 0.25
    MAX_DISTILLATE_OIL_PPM: float = 5.0  # Conservative marine distillate limit (< 15 ppm MARPOL)
    MIN_SLUDGE_OIL_PCT: float = 60.0
    MAX_DEMISTER_DP_MBAR: float = 20.0

    def calculate_boiling_point_c(self, p_bar_abs: float) -> float:
        """Solves Antoine equation for water boiling point under vacuum."""
        # 1 bar = 750.062 mmHg
        p_mmhg = max(10.0, p_bar_abs * 750.062)
        # T = B / (A - log10(P)) - C
        log_p = math.log10(p_mmhg)
        denom = self.ANTOINE_A - log_p
        if denom <= 0:
            return 100.0
        return (self.ANTOINE_B / denom) - self.ANTOINE_C

    def evaluate(self, telem: BilgeVacuumEvaporatorTelemetry) -> BilgeVacuumEvaporatorAssessment:
        warnings: List[str] = []

        # 1. Vacuum kinetics & boiling point
        t_boil = self.calculate_boiling_point_c(telem.vacuum_pressure_bar_abs)
        superheat = telem.evaporation_chamber_temp_c - t_boil
        vac_ok = self.MIN_VACUUM_BAR_ABS <= telem.vacuum_pressure_bar_abs <= self.MAX_VACUUM_BAR_ABS

        if not vac_ok:
            warnings.append(
                f"Vacuum pressure {telem.vacuum_pressure_bar_abs:.3f} bar abs outside optimal range [0.10, 0.25]."
            )

        if superheat < -2.0:
            warnings.append(
                f"Chamber temperature {telem.evaporation_chamber_temp_c:.1f}°C below boiling point {t_boil:.1f}°C. "
                "Insufficient evaporation."
            )

        # 2. Distillate purity (MARPOL 15 ppm limit, our unit targets <= 5.0 ppm)
        distillate_ok = telem.distillate_oil_ppm <= self.MAX_DISTILLATE_OIL_PPM
        if not distillate_ok:
            warnings.append(
                f"Distillate oil content {telem.distillate_oil_ppm:.2f} ppm exceeds limit ({self.MAX_DISTILLATE_OIL_PPM} ppm)."
            )

        # 3. Sludge concentration efficiency & mass reduction
        sludge_ok = telem.sludge_concentrate_oil_pct >= self.MIN_SLUDGE_OIL_PCT
        vol_reduction = (
            telem.distillate_flow_l_h / max(1.0, telem.feed_water_flow_l_h)
            if telem.feed_water_flow_l_h > 0
            else 0.0
        )

        if not sludge_ok:
            warnings.append(
                f"Concentrated sludge oil {telem.sludge_concentrate_oil_pct:.1f}% below target ({self.MIN_SLUDGE_OIL_PCT}%)."
            )

        # 4. Demister dP & Anti-foam dosing interlock
        demister_ok = telem.demister_dp_mbar <= self.MAX_DEMISTER_DP_MBAR
        if not demister_ok:
            warnings.append(
                f"Demister dP {telem.demister_dp_mbar:.1f} mbar indicates droplet carry-over / fouling."
            )

        anti_foam_needed = telem.foam_detected or (telem.demister_dp_mbar > 15.0)

        # Overboard discharge permission
        discharge_permitted = distillate_ok and vac_ok and not telem.foam_detected

        if not discharge_permitted and distillate_ok:
            warnings.append("Overboard discharge held: System process parameters not in steady state.")

        # Overall Status
        if not distillate_ok:
            status = "CONTAMINATED_DISTILLATE_RECIRCULATE"
        elif telem.foam_detected:
            status = "FOAMING_DOSING_REQUIRED"
        elif not vac_ok:
            status = "VACUUM_LOSS_FAULT"
        elif not demister_ok:
            status = "DEMISTER_CLOGGED_WARNING"
        else:
            status = "OPTIMAL_DISTILLATION"

        compliance_flags = {
            "vacuum_pressure_ok": vac_ok,
            "distillate_purity_ok": distillate_ok,
            "sludge_concentrated_ok": sludge_ok,
            "demister_clear_ok": demister_ok,
            "anti_foam_interlock_ready": not telem.foam_detected or telem.anti_foam_dosing_active,
        }

        return BilgeVacuumEvaporatorAssessment(
            theoretical_boiling_temp_c=round(t_boil, 2),
            superheat_margin_c=round(superheat, 2),
            volume_reduction_ratio=round(vol_reduction, 3),
            distillate_purity_compliant=distillate_ok,
            sludge_concentration_adequate=sludge_ok,
            vacuum_optimal=vac_ok,
            demister_clear=demister_ok,
            anti_foam_demanded=anti_foam_needed,
            overboard_discharge_permitted=discharge_permitted,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
