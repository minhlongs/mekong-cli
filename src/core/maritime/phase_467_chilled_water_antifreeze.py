"""Phase 467: Marine Chilled Water Plant Anti-Freeze Low Suction Protection Engine.

Complies with:
- IACS UR M56 & DNV Pt.4 Ch.6 (Piping Systems & Refrigerating Installations)
- ISO 5149 / EN 378 (Refrigerating systems and heat pumps - Safety and environmental requirements)
- Evaporator freeze protection: Freeze stat trip if water supply <= 3.0 deg C (warning <= 4.5 deg C)
- Low suction pressure cutoff: LP trip if suction pressure <= 2.2 bar gauge (R134a/R407C)
- Chilled water delta-T nominal: 5.0 deg C (Supply 7.0 deg C, Return 12.0 deg C)
- Minimum circulation flow interlock: Trip compressor if chilled water flow < 15.0 m3/h

Strictly < 100 LOC, zero mocks, deterministic physical rules.
"""

from dataclasses import dataclass
from enum import Enum


class ChilledWaterStatus(str, Enum):
    NORMAL = "NORMAL"
    LOW_TEMP_WARNING = "LOW_TEMP_WARNING"
    FREEZE_STAT_TRIP = "FREEZE_STAT_TRIP"
    LOW_SUCTION_TRIP = "LOW_SUCTION_TRIP"
    FLOW_INTERLOCK_TRIP = "FLOW_INTERLOCK_TRIP"


@dataclass(frozen=True)
class ChilledWaterTelemetry:
    supply_temp_c: float
    return_temp_c: float
    suction_pressure_bar: float
    circ_flow_m3_h: float
    pump_running: bool


@dataclass(frozen=True)
class ChilledWaterAssessment:
    status: ChilledWaterStatus
    delta_t_c: float
    compressor_permissive: bool
    hot_gas_bypass_active: bool
    remarks: str


class ChilledWaterAntiFreezeEngine:
    FREEZE_TRIP_TEMP_C: float = 3.0
    FREEZE_WARN_TEMP_C: float = 4.5
    MIN_SUCTION_P_BAR: float = 2.2
    MIN_FLOW_M3_H: float = 15.0

    @classmethod
    def evaluate(cls, telemetry: ChilledWaterTelemetry) -> ChilledWaterAssessment:
        delta_t = round(telemetry.return_temp_c - telemetry.supply_temp_c, 2)

        if not telemetry.pump_running or telemetry.circ_flow_m3_h < cls.MIN_FLOW_M3_H:
            return ChilledWaterAssessment(
                status=ChilledWaterStatus.FLOW_INTERLOCK_TRIP,
                delta_t_c=delta_t,
                compressor_permissive=False,
                hot_gas_bypass_active=False,
                remarks=f"Flow trip: flow {telemetry.circ_flow_m3_h} m3/h below min {cls.MIN_FLOW_M3_H} m3/h or pump off.",
            )

        if telemetry.supply_temp_c <= cls.FREEZE_TRIP_TEMP_C:
            return ChilledWaterAssessment(
                status=ChilledWaterStatus.FREEZE_STAT_TRIP,
                delta_t_c=delta_t,
                compressor_permissive=False,
                hot_gas_bypass_active=True,
                remarks=f"Freeze stat trip: supply temp {telemetry.supply_temp_c}C <= {cls.FREEZE_TRIP_TEMP_C}C.",
            )

        if telemetry.suction_pressure_bar <= cls.MIN_SUCTION_P_BAR:
            return ChilledWaterAssessment(
                status=ChilledWaterStatus.LOW_SUCTION_TRIP,
                delta_t_c=delta_t,
                compressor_permissive=False,
                hot_gas_bypass_active=True,
                remarks=f"Low suction trip: suction pressure {telemetry.suction_pressure_bar} bar <= {cls.MIN_SUCTION_P_BAR} bar.",
            )

        if telemetry.supply_temp_c <= cls.FREEZE_WARN_TEMP_C:
            return ChilledWaterAssessment(
                status=ChilledWaterStatus.LOW_TEMP_WARNING,
                delta_t_c=delta_t,
                compressor_permissive=True,
                hot_gas_bypass_active=True,
                remarks=f"Low temp warning: supply temp {telemetry.supply_temp_c}C <= {cls.FREEZE_WARN_TEMP_C}C. Hot gas bypass engaged.",
            )

        return ChilledWaterAssessment(
            status=ChilledWaterStatus.NORMAL,
            delta_t_c=delta_t,
            compressor_permissive=True,
            hot_gas_bypass_active=False,
            remarks="Chilled water loop within normal operating parameters.",
        )
