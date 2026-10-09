"""Phase 380: Seachest & Main Seawater Cooling Ingress Protection Engine.

Implements IACS UR M62, anti-marine growth (MGPS), and cooling water intake
safety standards under 200 lines.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class SeachestSuctionType(str, Enum):
    HIGH_SEACHEST = "HIGH_SEACHEST"
    LOW_SEACHEST = "LOW_SEACHEST"


@dataclass
class SeachestCoolingInput:
    vessel_id: str
    active_suction: SeachestSuctionType = SeachestSuctionType.LOW_SEACHEST
    under_keel_clearance_m: float = 6.0
    strainer_inlet_pressure_bar: float = 2.4
    strainer_outlet_pressure_bar: float = 2.2
    seawater_flow_m3_h: float = 800.0
    mgps_anode_current_a: float = 4.0
    seawater_temp_c: float = 25.0
    steam_purge_active: bool = False


@dataclass
class SeachestCoolingReport:
    vessel_id: str
    active_suction: str
    differential_pressure_bar: float
    target_mgps_current_a: float
    is_strainer_clogged: bool
    is_suction_selection_optimal: bool
    is_mgps_effective: bool
    is_ice_protection_active: bool
    system_status: str
    warnings: List[str] = field(default_factory=list)


class SeachestCoolingIngressEngine:
    """Evaluates seachest suction safety, duplex strainer fouling, and MGPS protection."""

    MAX_DIFF_PRESSURE_BAR: float = 0.50
    SHALLOW_UKC_THRESHOLD_M: float = 2.0
    MGPS_COEFFICIENT: float = 0.005  # 5 mA per m3/h
    ICE_TEMP_THRESHOLD_C: float = 2.0

    def evaluate(self, inp: SeachestCoolingInput) -> SeachestCoolingReport:
        warnings: List[str] = []

        # 1. Strainer differential pressure (IACS UR M62)
        diff_p = max(0.0, inp.strainer_inlet_pressure_bar - inp.strainer_outlet_pressure_bar)
        is_clogged = diff_p > self.MAX_DIFF_PRESSURE_BAR
        if is_clogged:
            warnings.append(
                f"Duplex strainer differential pressure {diff_p:.2f} bar exceeds 0.50 bar limit. Switch & clean."
            )

        # 2. Suction selection vs Under-Keel Clearance (UKC)
        is_suction_optimal = True
        if inp.under_keel_clearance_m < self.SHALLOW_UKC_THRESHOLD_M:
            if inp.active_suction == SeachestSuctionType.LOW_SEACHEST:
                is_suction_optimal = False
                warnings.append(
                    f"Low seachest active in shallow water (UKC {inp.under_keel_clearance_m:.1f}m < 2.0m): mud ingestion risk. Switch to High Seachest."
                )

        # 3. MGPS (Marine Growth Prevention System) electrolytic protection
        target_mgps_current = round(inp.seawater_flow_m3_h * self.MGPS_COEFFICIENT, 2)
        is_mgps_ok = inp.mgps_anode_current_a >= (target_mgps_current * 0.90)
        if not is_mgps_ok:
            warnings.append(
                f"MGPS anode current {inp.mgps_anode_current_a:.2f}A below required {target_mgps_current:.2f}A: biofouling risk."
            )

        # 4. Low seawater temperature frazil ice protection
        is_ice_protected = True
        if inp.seawater_temp_c < self.ICE_TEMP_THRESHOLD_C:
            if not inp.steam_purge_active:
                is_ice_protected = False
                warnings.append(
                    f"Seawater temp {inp.seawater_temp_c:.1f}°C < 2.0°C: de-icing steam purge or recirculation required."
                )

        # Determine overall status
        if is_clogged:
            status = "CRITICAL_CLOGGED"
        elif not is_suction_optimal or not is_mgps_ok or not is_ice_protected:
            status = "WARNING"
        else:
            status = "OPTIMAL"

        return SeachestCoolingReport(
            vessel_id=inp.vessel_id,
            active_suction=inp.active_suction.value,
            differential_pressure_bar=round(diff_p, 3),
            target_mgps_current_a=target_mgps_current,
            is_strainer_clogged=is_clogged,
            is_suction_selection_optimal=is_suction_optimal,
            is_mgps_effective=is_mgps_ok,
            is_ice_protection_active=is_ice_protected,
            system_status=status,
            warnings=warnings,
        )
