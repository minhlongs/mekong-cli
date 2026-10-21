"""Marine Battery Energy Storage System (BESS) & Peak Shaving Safety Engine.

Standards: DNV-RU-SHIP Pt.6 Ch.2 Battery(Power/Safety),
IEC 62619, and IMO MSC.1/Circ.1455.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class BessSafetyTripStage(str, Enum):
    """3-Stage Safety Trip System under DNV-RU-SHIP."""

    STAGE_0_NORMAL = "STAGE_0_NORMAL"
    STAGE_1_ALARM_DERATE = "STAGE_1_ALARM_DERATE"
    STAGE_2_ELECTRICAL_TRIP = "STAGE_2_ELECTRICAL_TRIP"
    STAGE_3_FIRE_DELUGE = "STAGE_3_FIRE_DELUGE"


@dataclass
class BessModuleInput:
    pack_id: str
    soc_pct: float = 75.0  # State of Charge 0-100%
    soh_pct: float = 95.0  # State of Health 0-100%
    c_rate: float = 0.8  # Charge/discharge current rate
    cell_max_temp_c: float = 28.0
    cell_delta_temp_c: float = 1.5
    offgas_h2_ppm: float = 0.0
    offgas_co_ppm: float = 0.0
    is_peak_shaving_mode: bool = False


@dataclass
class BessSafetyReport:
    pack_id: str
    is_safe: bool
    trip_stage: BessSafetyTripStage
    soc_status: str
    soh_status: str
    thermal_status: str
    offgas_status: str
    allowable_c_rate: float
    actions_required: List[str]
    metrics: Dict[str, float]


class MarineBatteryBessEngine:
    """Evaluates marine BESS electrochemical and thermal runaway safety."""

    MIN_SAFE_SOC_PCT: float = 15.0
    MAX_SAFE_SOC_PCT: float = 90.0
    SOH_WARNING_PCT: float = 80.0
    SOH_EOL_PCT: float = 70.0

    MAX_CONTINUOUS_C_RATE: float = 1.0
    MAX_PEAK_SHAVING_C_RATE: float = 2.5

    MAX_CELL_DELTA_TEMP_C: float = 5.0
    ALARM_TEMP_C: float = 45.0
    TRIP_TEMP_C: float = 55.0
    DELUGE_TEMP_C: float = 75.0

    OFFGAS_H2_LIMIT_PPM: float = 50.0
    OFFGAS_CO_LIMIT_PPM: float = 25.0

    def evaluate(self, module: BessModuleInput) -> BessSafetyReport:
        actions: List[str] = []
        is_safe = True
        trip_stage = BessSafetyTripStage.STAGE_0_NORMAL

        # 1. Thermal Runaway Off-Gas & Temperature 3-Stage Protection
        if module.cell_max_temp_c >= self.DELUGE_TEMP_C:
            trip_stage = BessSafetyTripStage.STAGE_3_FIRE_DELUGE
            is_safe = False
            thermal_status = "CRITICAL_THERMAL_RUNAWAY"
            actions.append("EMERGENCY: Activate high-pressure water mist deluge & evacuate battery room")
        elif (
            module.cell_max_temp_c >= self.TRIP_TEMP_C
            or module.offgas_h2_ppm >= self.OFFGAS_H2_LIMIT_PPM
            or module.offgas_co_ppm >= self.OFFGAS_CO_LIMIT_PPM
        ):
            trip_stage = BessSafetyTripStage.STAGE_2_ELECTRICAL_TRIP
            is_safe = False
            thermal_status = "OVERTEMP_TRIP"
            actions.append("TRIP: Open DC main contactors, isolate rack, and start extraction fans")
        elif (
            module.cell_max_temp_c > self.ALARM_TEMP_C
            or module.cell_delta_temp_c > self.MAX_CELL_DELTA_TEMP_C
        ):
            trip_stage = BessSafetyTripStage.STAGE_1_ALARM_DERATE
            thermal_status = "WARNING_DERATE"
            actions.append("ALARM: De-rate charge/discharge power by 50% and inspect liquid cooling loop")
        else:
            thermal_status = "NORMAL"

        # Off-gas assessment
        if (
            module.offgas_h2_ppm >= self.OFFGAS_H2_LIMIT_PPM
            or module.offgas_co_ppm >= self.OFFGAS_CO_LIMIT_PPM
        ):
            offgas_status = "OFFGAS_DETECTED"
        else:
            offgas_status = "CLEAN"

        # 2. SoC limits
        if module.soc_pct < self.MIN_SAFE_SOC_PCT:
            soc_status = "UNDERCHARGED_DEEP_DISCHARGE_RISK"
            actions.append("SoC < 15%: Inhibit discharge to prevent anode copper dissolution")
            if trip_stage == BessSafetyTripStage.STAGE_0_NORMAL:
                trip_stage = BessSafetyTripStage.STAGE_1_ALARM_DERATE
        elif module.soc_pct > self.MAX_SAFE_SOC_PCT:
            soc_status = "OVERCHARGED_LITHIUM_PLATING_RISK"
            actions.append("SoC > 90%: Inhibit charging to prevent cathode breakdown")
            if trip_stage == BessSafetyTripStage.STAGE_0_NORMAL:
                trip_stage = BessSafetyTripStage.STAGE_1_ALARM_DERATE
        else:
            soc_status = "OPTIMAL"

        # 3. SoH degradation
        if module.soh_pct <= self.SOH_EOL_PCT:
            soh_status = "END_OF_LIFE_REPLACE"
            actions.append("SoH <= 70%: Module decommission and recycling required")
            is_safe = False
        elif module.soh_pct < self.SOH_WARNING_PCT:
            soh_status = "DEGRADED_PERFORMANCE"
            actions.append("SoH < 80%: Plan cell balancing and capacity calibration")
        else:
            soh_status = "HEALTHY"

        # 4. Allowable C-rate
        max_allowed_c = (
            self.MAX_PEAK_SHAVING_C_RATE
            if module.is_peak_shaving_mode
            else self.MAX_CONTINUOUS_C_RATE
        )
        if trip_stage == BessSafetyTripStage.STAGE_1_ALARM_DERATE:
            max_allowed_c *= 0.5
        elif trip_stage in (
            BessSafetyTripStage.STAGE_2_ELECTRICAL_TRIP,
            BessSafetyTripStage.STAGE_3_FIRE_DELUGE,
        ):
            max_allowed_c = 0.0

        if module.c_rate > max_allowed_c and max_allowed_c > 0:
            actions.append(f"C-rate {module.c_rate} exceeds limit {max_allowed_c:.1f}C")

        return BessSafetyReport(
            pack_id=module.pack_id,
            is_safe=is_safe,
            trip_stage=trip_stage,
            soc_status=soc_status,
            soh_status=soh_status,
            thermal_status=thermal_status,
            offgas_status=offgas_status,
            allowable_c_rate=max_allowed_c,
            actions_required=actions,
            metrics={
                "soc_pct": module.soc_pct,
                "soh_pct": module.soh_pct,
                "c_rate": module.c_rate,
                "cell_max_temp_c": module.cell_max_temp_c,
                "cell_delta_temp_c": module.cell_delta_temp_c,
                "offgas_h2_ppm": module.offgas_h2_ppm,
                "offgas_co_ppm": module.offgas_co_ppm,
            },
        )


__all__ = [
    "BessSafetyTripStage",
    "BessModuleInput",
    "BessSafetyReport",
    "MarineBatteryBessEngine",
]
