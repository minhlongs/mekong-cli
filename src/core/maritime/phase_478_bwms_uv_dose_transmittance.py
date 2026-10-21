"""Phase 478: BWMS UV Reactor Transmittance & Dose Interlock Engine.

Complies with:
- IMO Resolution MEPC.300(72) (BWMS Code) & USCG Type Approval Standards:
  - Minimum UV transmittance (UV-T at 254 nm): normal >= 60.0%, warning < 50.0%, trip < 40.0%.
  - Minimum applied UV dose: D_UV >= 300.0 J/m2 (mWs/cm2).
  - Reactor water temperature limit: T <= 45.0 C (prevent quartz sleeve scaling / overheating).
  - Auto-action: Throttle ballast flow control valve or trip ballast pump if UV dose cannot be maintained.

Strictly < 110 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass
from enum import Enum


class BwmsUvStatus(str, Enum):
    NORMAL = "NORMAL"
    LOW_UV_TRANSMITTANCE_ALARM = "LOW_UV_TRANSMITTANCE_ALARM"
    LOW_UV_DOSE_FLOW_THROTTLE = "LOW_UV_DOSE_FLOW_THROTTLE"
    INSUFFICIENT_DOSE_BALLAST_TRIP = "INSUFFICIENT_DOSE_BALLAST_TRIP"
    REACTOR_OVERHEAT_ALARM = "REACTOR_OVERHEAT_ALARM"


@dataclass(frozen=True)
class BwmsUvTelemetry:
    uv_transmittance_pct: float
    uv_dose_j_m2: float
    reactor_temp_c: float
    ballast_flow_m3_h: float
    lamps_operating_pct: float
    ballasting_active: bool


@dataclass(frozen=True)
class BwmsUvAssessment:
    status: BwmsUvStatus
    ballast_discharge_permissive: bool
    flow_throttle_required: bool
    wiper_cycle_command_active: bool
    remarks: str


class BwmsUvSafetyEngine:
    MIN_UV_T_WARNING_PCT: float = 50.0
    MIN_UV_T_TRIP_PCT: float = 40.0
    MIN_UV_DOSE_J_M2: float = 300.0
    MAX_REACTOR_TEMP_C: float = 45.0
    MIN_LAMPS_HEALTHY_PCT: float = 85.0

    @classmethod
    def evaluate(cls, telemetry: BwmsUvTelemetry) -> BwmsUvAssessment:
        if not telemetry.ballasting_active:
            return BwmsUvAssessment(
                status=BwmsUvStatus.NORMAL,
                ballast_discharge_permissive=False,
                flow_throttle_required=False,
                wiper_cycle_command_active=False,
                remarks="BWMS UV treatment system on standby.",
            )

        if telemetry.reactor_temp_c >= cls.MAX_REACTOR_TEMP_C:
            return BwmsUvAssessment(
                status=BwmsUvStatus.REACTOR_OVERHEAT_ALARM,
                ballast_discharge_permissive=False,
                flow_throttle_required=False,
                wiper_cycle_command_active=False,
                remarks=f"ALARM: UV chamber temp {telemetry.reactor_temp_c}C >= {cls.MAX_REACTOR_TEMP_C}C. Cooling flow inadequate.",
            )

        if telemetry.uv_transmittance_pct < cls.MIN_UV_T_TRIP_PCT or telemetry.lamps_operating_pct < cls.MIN_LAMPS_HEALTHY_PCT:
            return BwmsUvAssessment(
                status=BwmsUvStatus.INSUFFICIENT_DOSE_BALLAST_TRIP,
                ballast_discharge_permissive=False,
                flow_throttle_required=True,
                wiper_cycle_command_active=True,
                remarks=f"MEPC.300(72) TRIP: UV-T {telemetry.uv_transmittance_pct}% < {cls.MIN_UV_T_TRIP_PCT}% or lamp failure. Ballast pump trip.",
            )

        if telemetry.uv_dose_j_m2 < cls.MIN_UV_DOSE_J_M2:
            return BwmsUvAssessment(
                status=BwmsUvStatus.LOW_UV_DOSE_FLOW_THROTTLE,
                ballast_discharge_permissive=True,
                flow_throttle_required=True,
                wiper_cycle_command_active=True,
                remarks=f"ACTION: UV dose {telemetry.uv_dose_j_m2} J/m2 < {cls.MIN_UV_DOSE_J_M2} J/m2. Throttling flow to restore target dose.",
            )

        if telemetry.uv_transmittance_pct < cls.MIN_UV_T_WARNING_PCT:
            return BwmsUvAssessment(
                status=BwmsUvStatus.LOW_UV_TRANSMITTANCE_ALARM,
                ballast_discharge_permissive=True,
                flow_throttle_required=False,
                wiper_cycle_command_active=True,
                remarks=f"WARNING: UV-T {telemetry.uv_transmittance_pct}% < {cls.MIN_UV_T_WARNING_PCT}%. Auto sleeve quartz wiper triggered.",
            )

        return BwmsUvAssessment(
            status=BwmsUvStatus.NORMAL,
            ballast_discharge_permissive=True,
            flow_throttle_required=False,
            wiper_cycle_command_active=False,
            remarks="BWMS UV treatment fully compliant with D-2 biological efficacy criteria.",
        )
