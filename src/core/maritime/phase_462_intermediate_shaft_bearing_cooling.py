"""Phase 462: Marine Propulsion Intermediate Shaft Bearing Lube & Cooling.

Compliant with IACS UR M68 & Lloyd's Register Rules Pt. 5 Ch. 2.
Monitors plummer block journal bearing metal temperature (T <= 65 deg C warn, 75 deg C trip),
cooling water flow rate (Q >= 15 L/min), oil ring rotation speed, and lube oil sump water ingress (< 0.10%).
"""

from dataclasses import dataclass
from enum import Enum


class ShaftBearingStatus(str, Enum):
    NORMAL = "NORMAL"
    COOLING_FLOW_LOW = "COOLING_FLOW_LOW"
    OIL_RING_STOPPED = "OIL_RING_STOPPED"
    WATER_CONTAMINATION = "WATER_CONTAMINATION"
    BEARING_OVERHEAT_WARNING = "BEARING_OVERHEAT_WARNING"
    BEARING_OVERHEAT_CRITICAL = "BEARING_OVERHEAT_CRITICAL"


@dataclass(frozen=True)
class ShaftBearingTelemetry:
    bearing_metal_temp_celsius: float
    lube_oil_sump_temp_celsius: float
    cooling_water_flow_l_min: float
    oil_ring_rotating: bool
    oil_water_content_percent: float


@dataclass(frozen=True)
class ShaftBearingAssessment:
    status: ShaftBearingStatus
    temperature_in_spec: bool
    cooling_adequate: bool
    lubrication_active: bool
    safety_alarm: bool
    engine_slowdown_required: bool
    remarks: str


class IntermediateShaftBearingEngine:
    """IACS UR M68 Line Shaft Plummer Block Bearing Monitoring Logic."""

    WARN_TEMP_CELSIUS: float = 65.0
    CRITICAL_TRIP_TEMP_CELSIUS: float = 75.0
    MIN_COOLING_FLOW_L_MIN: float = 15.0
    MAX_WATER_CONTENT_PCT: float = 0.10

    @classmethod
    def evaluate(cls, telemetry: ShaftBearingTelemetry) -> ShaftBearingAssessment:
        if telemetry.bearing_metal_temp_celsius >= cls.CRITICAL_TRIP_TEMP_CELSIUS:
            return ShaftBearingAssessment(
                status=ShaftBearingStatus.BEARING_OVERHEAT_CRITICAL,
                temperature_in_spec=False,
                cooling_adequate=telemetry.cooling_water_flow_l_min >= cls.MIN_COOLING_FLOW_L_MIN,
                lubrication_active=telemetry.oil_ring_rotating,
                safety_alarm=True,
                engine_slowdown_required=True,
                remarks=f"Bearing white metal temp {telemetry.bearing_metal_temp_celsius:.1f}°C exceeds critical 75°C limit: immediate engine slowdown.",
            )

        if not telemetry.oil_ring_rotating:
            return ShaftBearingAssessment(
                status=ShaftBearingStatus.OIL_RING_STOPPED,
                temperature_in_spec=telemetry.bearing_metal_temp_celsius < cls.WARN_TEMP_CELSIUS,
                cooling_adequate=telemetry.cooling_water_flow_l_min >= cls.MIN_COOLING_FLOW_L_MIN,
                lubrication_active=False,
                safety_alarm=True,
                engine_slowdown_required=True,
                remarks="Bearing lube oil pick-up ring stopped rotation: impending boundary friction seizure.",
            )

        if telemetry.bearing_metal_temp_celsius >= cls.WARN_TEMP_CELSIUS:
            return ShaftBearingAssessment(
                status=ShaftBearingStatus.BEARING_OVERHEAT_WARNING,
                temperature_in_spec=False,
                cooling_adequate=telemetry.cooling_water_flow_l_min >= cls.MIN_COOLING_FLOW_L_MIN,
                lubrication_active=telemetry.oil_ring_rotating,
                safety_alarm=True,
                engine_slowdown_required=False,
                remarks=f"Bearing metal temp {telemetry.bearing_metal_temp_celsius:.1f}°C exceeds 65°C warning threshold.",
            )

        if telemetry.cooling_water_flow_l_min < cls.MIN_COOLING_FLOW_L_MIN:
            return ShaftBearingAssessment(
                status=ShaftBearingStatus.COOLING_FLOW_LOW,
                temperature_in_spec=True,
                cooling_adequate=False,
                lubrication_active=telemetry.oil_ring_rotating,
                safety_alarm=True,
                engine_slowdown_required=False,
                remarks=f"Bearing cooling jacket flow {telemetry.cooling_water_flow_l_min:.1f} L/min below 15 L/min design flow.",
            )

        if telemetry.oil_water_content_percent > cls.MAX_WATER_CONTENT_PCT:
            return ShaftBearingAssessment(
                status=ShaftBearingStatus.WATER_CONTAMINATION,
                temperature_in_spec=True,
                cooling_adequate=True,
                lubrication_active=telemetry.oil_ring_rotating,
                safety_alarm=True,
                engine_slowdown_required=False,
                remarks=f"Lube oil water content {telemetry.oil_water_content_percent:.2f}% exceeds 0.10% emulsion limit.",
            )

        return ShaftBearingAssessment(
            status=ShaftBearingStatus.NORMAL,
            temperature_in_spec=True,
            cooling_adequate=True,
            lubrication_active=True,
            safety_alarm=False,
            engine_slowdown_required=False,
            remarks="Line shaft intermediate bearing hydrodynamic film and thermal balance nominal.",
        )
