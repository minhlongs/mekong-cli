"""Phase 414: Marine Bow Visor & Inner Bow Door Hydraulic Latching.

Implements SOLAS II-1 Reg 17-1 / IACS UR S8 standards for Ro-Ro passenger/cargo
ships: hydraulic wedge locking pressures, dual redundant proximity sensors,
pneumatic inflatable seal pressures, and compartment water ingress trips.
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class BowDoorTelemetry:
    """Telemetry readings for Ro-Ro Bow Visor & Inner Bow Door system."""
    hydraulic_pressure_bar: float = 175.0
    sensor_a_locked: bool = True
    sensor_b_locked: bool = True
    inflatable_seal_pressure_bar: float = 4.0
    compartment_water_level_m: float = 0.0
    vessel_speed_knots: float = 18.0
    cleats_engaged_count: int = 12
    cleats_total_count: int = 12


@dataclass(frozen=True)
class BowDoorAssessment:
    """Safety and integrity assessment of Ro-Ro Bow Door and Visor."""
    all_cleats_engaged: bool
    sensors_concordant: bool
    water_ingress_alarm_level: int
    navigation_permissive: bool
    status: str
    warnings: list[str]
    compliance_flags: Dict[str, bool]


class RoRoBowDoorLatchingEngine:
    """Evaluates hydraulic latching, redundant sensors, seals, and ingress."""

    MIN_HYD_PRESSURE_BAR: float = 160.0
    MIN_SEAL_PRESSURE_BAR: float = 3.5
    ALARM_SEAL_PRESSURE_BAR: float = 3.0
    WATER_LEVEL_WARNING_M: float = 0.10
    WATER_LEVEL_EMERGENCY_M: float = 0.50
    SPEED_LOCKOUT_KNOTS: float = 0.50

    def evaluate(self, telemetry: BowDoorTelemetry) -> BowDoorAssessment:
        warnings: list[str] = []

        all_cleats = telemetry.cleats_engaged_count == telemetry.cleats_total_count and telemetry.cleats_total_count > 0
        if not all_cleats:
            warnings.append(
                f"Cleats not fully engaged: {telemetry.cleats_engaged_count}/{telemetry.cleats_total_count} locked."
            )

        if telemetry.hydraulic_pressure_bar < self.MIN_HYD_PRESSURE_BAR:
            warnings.append(
                f"Hydraulic latching pressure {telemetry.hydraulic_pressure_bar} bar below min {self.MIN_HYD_PRESSURE_BAR} bar."
            )

        sensors_agree = telemetry.sensor_a_locked == telemetry.sensor_b_locked
        fully_locked = telemetry.sensor_a_locked and telemetry.sensor_b_locked
        if not sensors_agree:
            warnings.append("Dual sensor discrepancy: Sensor A and Sensor B disagree on door locked status!")
        elif not fully_locked:
            warnings.append("Bow door is NOT fully locked according to dual redundant sensors.")

        if telemetry.inflatable_seal_pressure_bar < self.ALARM_SEAL_PRESSURE_BAR:
            warnings.append(
                f"Inflatable rubber seal pressure critical {telemetry.inflatable_seal_pressure_bar} bar (< {self.ALARM_SEAL_PRESSURE_BAR} bar). Ingress risk!"
            )
        elif telemetry.inflatable_seal_pressure_bar < self.MIN_SEAL_PRESSURE_BAR:
            warnings.append(
                f"Inflatable seal pressure low {telemetry.inflatable_seal_pressure_bar} bar (< {self.MIN_SEAL_PRESSURE_BAR} bar)."
            )

        ingress_level = 0
        if telemetry.compartment_water_level_m >= self.WATER_LEVEL_EMERGENCY_M:
            ingress_level = 2
            warnings.append(
                f"CRITICAL WATER INGRESS: Compartment level {telemetry.compartment_water_level_m} m >= {self.WATER_LEVEL_EMERGENCY_M} m!"
            )
        elif telemetry.compartment_water_level_m >= self.WATER_LEVEL_WARNING_M:
            ingress_level = 1
            warnings.append(
                f"Water ingress warning: Compartment level {telemetry.compartment_water_level_m} m >= {self.WATER_LEVEL_WARNING_M} m."
            )

        # Ship must not get underway if bow door is unsealed or water is ingressing
        nav_permissive = fully_locked and all_cleats and ingress_level == 0 and telemetry.inflatable_seal_pressure_bar >= self.ALARM_SEAL_PRESSURE_BAR
        if not nav_permissive and telemetry.vessel_speed_knots > self.SPEED_LOCKOUT_KNOTS:
            warnings.append(
                f"VESSEL UNDERWAY ({telemetry.vessel_speed_knots} kts) WITH COMPROMISED BOW DOOR INTEGRITY! ESTONIA DISASTER RISK!"
            )

        status = "NORMAL"
        if ingress_level == 2 or (not nav_permissive and telemetry.vessel_speed_knots > self.SPEED_LOCKOUT_KNOTS):
            status = "CRITICAL"
        elif ingress_level == 1 or not nav_permissive:
            status = "WARNING"
        elif warnings:
            status = "ADVISORY"

        compliance_flags = {
            "solas_cleats_secured": all_cleats,
            "dual_sensors_verified": sensors_agree and fully_locked,
            "seal_pressure_intact": telemetry.inflatable_seal_pressure_bar >= self.ALARM_SEAL_PRESSURE_BAR,
            "zero_water_ingress": ingress_level == 0,
            "navigation_permissive": nav_permissive,
        }

        return BowDoorAssessment(
            all_cleats_engaged=all_cleats,
            sensors_concordant=sensors_agree,
            water_ingress_alarm_level=ingress_level,
            navigation_permissive=nav_permissive,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
