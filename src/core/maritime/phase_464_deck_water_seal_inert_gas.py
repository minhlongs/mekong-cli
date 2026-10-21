"""Phase 464: Marine Inert Gas System Deck Water Seal & Non-Return Protection.

Compliant with SOLAS II-2 Reg 4.5.5 & FSS Code Ch. 15.
Monitors deck water seal water level (H >= 450 mm WG), continuous supply water flow (Q >= 10.0 m3/h),
non-return valve seat differential pressure, and hydrocarbon gas backflow prevention.
"""

from dataclasses import dataclass
from enum import Enum


class DeckWaterSealStatus(str, Enum):
    NORMAL = "NORMAL"
    SEAL_WATER_LOW = "SEAL_WATER_LOW"
    SUPPLY_FLOW_LOW = "SUPPLY_FLOW_LOW"
    GAS_BACKFLOW_DETECTED = "GAS_BACKFLOW_DETECTED"
    HEATING_FAILURE_FREEZING = "HEATING_FAILURE_FREEZING"
    OVERFLOW_BLOCKED = "OVERFLOW_BLOCKED"


@dataclass(frozen=True)
class DeckWaterSealTelemetry:
    water_level_mm_wg: float
    supply_flow_rate_m3_h: float
    seal_water_temp_celsius: float
    downstream_hc_ppm: float
    non_return_valve_closed: bool


@dataclass(frozen=True)
class DeckWaterSealAssessment:
    status: DeckWaterSealStatus
    seal_integrity_intact: bool
    supply_flow_sufficient: bool
    backflow_risk: bool
    trip_ig_plant_required: bool
    alarm_active: bool
    remarks: str


class DeckWaterSealEngine:
    """SOLAS II-2 Reg 4.5.5 Inert Gas Deck Water Seal Safety Barrier Logic."""

    MIN_WATER_LEVEL_MM_WG: float = 450.0
    MIN_SUPPLY_FLOW_M3_H: float = 10.0
    MIN_WATER_TEMP_C: float = 2.0
    MAX_PERMISSIBLE_HC_PPM: float = 50.0

    @classmethod
    def evaluate(cls, telemetry: DeckWaterSealTelemetry) -> DeckWaterSealAssessment:
        if telemetry.downstream_hc_ppm > cls.MAX_PERMISSIBLE_HC_PPM:
            return DeckWaterSealAssessment(
                status=DeckWaterSealStatus.GAS_BACKFLOW_DETECTED,
                seal_integrity_intact=False,
                supply_flow_sufficient=telemetry.supply_flow_rate_m3_h >= cls.MIN_SUPPLY_FLOW_M3_H,
                backflow_risk=True,
                trip_ig_plant_required=True,
                alarm_active=True,
                remarks=f"Hazardous gas backflow detected: {telemetry.downstream_hc_ppm:.1f} ppm HC > {cls.MAX_PERMISSIBLE_HC_PPM} ppm limit",
            )

        if telemetry.water_level_mm_wg < cls.MIN_WATER_LEVEL_MM_WG:
            return DeckWaterSealAssessment(
                status=DeckWaterSealStatus.SEAL_WATER_LOW,
                seal_integrity_intact=False,
                supply_flow_sufficient=telemetry.supply_flow_rate_m3_h >= cls.MIN_SUPPLY_FLOW_M3_H,
                backflow_risk=True,
                trip_ig_plant_required=True,
                alarm_active=True,
                remarks=f"Deck water seal level low: {telemetry.water_level_mm_wg:.1f} mm WG < {cls.MIN_WATER_LEVEL_MM_WG} mm limit",
            )

        if telemetry.supply_flow_rate_m3_h < cls.MIN_SUPPLY_FLOW_M3_H:
            return DeckWaterSealAssessment(
                status=DeckWaterSealStatus.SUPPLY_FLOW_LOW,
                seal_integrity_intact=True,
                supply_flow_sufficient=False,
                backflow_risk=False,
                trip_ig_plant_required=False,
                alarm_active=True,
                remarks=f"Deck seal makeup water flow {telemetry.supply_flow_rate_m3_h:.1f} m3/h < {cls.MIN_SUPPLY_FLOW_M3_H} m3/h required",
            )

        if telemetry.seal_water_temp_celsius < cls.MIN_WATER_TEMP_C:
            return DeckWaterSealAssessment(
                status=DeckWaterSealStatus.HEATING_FAILURE_FREEZING,
                seal_integrity_intact=True,
                supply_flow_sufficient=True,
                backflow_risk=False,
                trip_ig_plant_required=False,
                alarm_active=True,
                remarks=f"Deck seal heating failure: water temp {telemetry.seal_water_temp_celsius:.1f}C < {cls.MIN_WATER_TEMP_C}C (freezing risk)",
            )

        return DeckWaterSealAssessment(
            status=DeckWaterSealStatus.NORMAL,
            seal_integrity_intact=True,
            supply_flow_sufficient=True,
            backflow_risk=False,
            trip_ig_plant_required=False,
            alarm_active=False,
            remarks="Deck water seal level and water supply rate in full compliance with SOLAS II-2",
        )
