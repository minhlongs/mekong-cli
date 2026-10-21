"""Phase 471: Marine Tunnel Bow Thruster Hydraulic Pitch & Prime Mover Overload Interlock Engine.

Complies with:
- SOLAS II-1 Reg. 29 & DNV Pt.4 Ch.5 Sec.3 (Thruster and steering systems)
- Classification Society Rules (IACS UR M35 / Bureau Veritas / DNV):
  - Blackout prevention: Thruster motor load limitation with auto pitch reduction on generator overload (> 90% gen capacity).
  - High hydraulic oil temperature trip/alarm: T_oil >= 70.0 deg C (warning at 65.0 deg C).
  - Low header tank level interlock: Level <= 25.0% trips thruster start permissive.
  - Tunnel sea chest grill blockage: Differential pressure dP >= 0.4 bar trips full pitch permissive.

Strictly < 100 LOC, zero mocks, deterministic physical rules.
"""

from dataclasses import dataclass
from enum import Enum


class BowThrusterStatus(str, Enum):
    NORMAL = "NORMAL"
    HIGH_TEMP_WARNING = "HIGH_TEMP_WARNING"
    HIGH_TEMP_TRIP = "HIGH_TEMP_TRIP"
    LOW_HEADER_LEVEL_TRIP = "LOW_HEADER_LEVEL_TRIP"
    GENERATOR_OVERLOAD_PITCH_REDUCTION = "GENERATOR_OVERLOAD_PITCH_REDUCTION"
    SEA_CHEST_GRILL_BLOCKAGE = "SEA_CHEST_GRILL_BLOCKAGE"


@dataclass(frozen=True)
class BowThrusterTelemetry:
    hydraulic_oil_temp_c: float
    header_tank_level_pct: float
    generator_load_pct: float
    commanded_pitch_pct: float
    grill_differential_p_bar: float
    lubrication_running: bool


@dataclass(frozen=True)
class BowThrusterAssessment:
    status: BowThrusterStatus
    allowed_pitch_pct: float
    thruster_run_permissive: bool
    cooling_booster_pump_active: bool
    remarks: str


class BowThrusterInterlockEngine:
    MAX_TRIP_OIL_TEMP_C: float = 70.0
    WARN_OIL_TEMP_C: float = 65.0
    MIN_HEADER_LEVEL_PCT: float = 25.0
    GEN_OVERLOAD_THRESHOLD_PCT: float = 90.0
    MAX_GRILL_DIFF_P_BAR: float = 0.4

    @classmethod
    def evaluate(cls, telemetry: BowThrusterTelemetry) -> BowThrusterAssessment:
        if telemetry.header_tank_level_pct <= cls.MIN_HEADER_LEVEL_PCT:
            return BowThrusterAssessment(
                status=BowThrusterStatus.LOW_HEADER_LEVEL_TRIP,
                allowed_pitch_pct=0.0,
                thruster_run_permissive=False,
                cooling_booster_pump_active=False,
                remarks=f"Header tank level {telemetry.header_tank_level_pct}% <= {cls.MIN_HEADER_LEVEL_PCT}%. Thruster start inhibited.",
            )

        if telemetry.hydraulic_oil_temp_c >= cls.MAX_TRIP_OIL_TEMP_C:
            return BowThrusterAssessment(
                status=BowThrusterStatus.HIGH_TEMP_TRIP,
                allowed_pitch_pct=0.0,
                thruster_run_permissive=False,
                cooling_booster_pump_active=True,
                remarks=f"Hydraulic oil overheat {telemetry.hydraulic_oil_temp_c}C >= {cls.MAX_TRIP_OIL_TEMP_C}C. Thruster tripped.",
            )

        if telemetry.grill_differential_p_bar >= cls.MAX_GRILL_DIFF_P_BAR:
            allowed = min(telemetry.commanded_pitch_pct, 40.0)
            return BowThrusterAssessment(
                status=BowThrusterStatus.SEA_CHEST_GRILL_BLOCKAGE,
                allowed_pitch_pct=allowed,
                thruster_run_permissive=True,
                cooling_booster_pump_active=False,
                remarks=f"Grill differential pressure {telemetry.grill_differential_p_bar} bar >= {cls.MAX_GRILL_DIFF_P_BAR} bar. Pitch limited.",
            )

        if telemetry.generator_load_pct >= cls.GEN_OVERLOAD_THRESHOLD_PCT:
            reduced_pitch = min(telemetry.commanded_pitch_pct, 50.0)
            return BowThrusterAssessment(
                status=BowThrusterStatus.GENERATOR_OVERLOAD_PITCH_REDUCTION,
                allowed_pitch_pct=reduced_pitch,
                thruster_run_permissive=True,
                cooling_booster_pump_active=False,
                remarks=f"Generator load {telemetry.generator_load_pct}% >= {cls.GEN_OVERLOAD_THRESHOLD_PCT}%. Auto pitch reduction active.",
            )

        if telemetry.hydraulic_oil_temp_c >= cls.WARN_OIL_TEMP_C:
            return BowThrusterAssessment(
                status=BowThrusterStatus.HIGH_TEMP_WARNING,
                allowed_pitch_pct=telemetry.commanded_pitch_pct,
                thruster_run_permissive=True,
                cooling_booster_pump_active=True,
                remarks=f"Hydraulic oil warning {telemetry.hydraulic_oil_temp_c}C >= {cls.WARN_OIL_TEMP_C}C. Cooling booster engaged.",
            )

        return BowThrusterAssessment(
            status=BowThrusterStatus.NORMAL,
            allowed_pitch_pct=telemetry.commanded_pitch_pct,
            thruster_run_permissive=True,
            cooling_booster_pump_active=False,
            remarks="Bow thruster hydraulic system and prime mover operating within nominal parameters.",
        )
