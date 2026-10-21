"""Coordinator for Maritime Automation Auxiliary Safety Phases 491-494 (Batch 8).

Integrates:
- Phase 491: ME Thrust Bearing Pad Temperature & Oil Wedge Film
- Phase 492: Vacuum Sewage Collecting Tank & Ejector Discharge Control
- Phase 493: Exhaust Gas Scrubbing Washwater Demister & SOx Quench Loop
- Phase 494: Bow Thruster Tunnel Hydraulic Pitch & Overload Power Management

Strictly < 95 LOC.
"""

from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_491_thrust_bearing_pad_temp import (
    ThrustBearingAssessment,
    ThrustBearingPadTempEngine,
    ThrustBearingStatus,
    ThrustBearingTelemetry,
)
from src.core.maritime.phase_492_vacuum_sewage_tank_ejector import (
    VacuumSewageAssessment,
    VacuumSewageStatus,
    VacuumSewageTankEjectorEngine,
    VacuumSewageTelemetry,
)
from src.core.maritime.phase_493_exhaust_scrubber_washwater_demister import (
    ExhaustScrubberWashwaterDemisterEngine,
    ScrubberAssessment,
    ScrubberStatus,
    ScrubberTelemetry,
)
from src.core.maritime.phase_494_bow_thruster_pitch_power import (
    BowThrusterAssessment,
    BowThrusterPitchPowerEngine,
    BowThrusterStatus,
    BowThrusterTelemetry,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch8Telemetry:
    thrust_bearing: ThrustBearingTelemetry
    vacuum_sewage: VacuumSewageTelemetry
    scrubber: ScrubberTelemetry
    bow_thruster: BowThrusterTelemetry


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch8Assessment:
    thrust_bearing: ThrustBearingAssessment
    vacuum_sewage: VacuumSewageAssessment
    scrubber: ScrubberAssessment
    bow_thruster: BowThrusterAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch8Engine:
    """Consolidated Safety Interlock Coordinator for Maritime Batch 8."""

    @classmethod
    def evaluate(cls, telem: MaritimeAuxiliaryBatch8Telemetry) -> MaritimeAuxiliaryBatch8Assessment:
        tb_res = ThrustBearingPadTempEngine.evaluate(telem.thrust_bearing)
        vs_res = VacuumSewageTankEjectorEngine.evaluate(telem.vacuum_sewage)
        sc_res = ExhaustScrubberWashwaterDemisterEngine.evaluate(telem.scrubber)
        bt_res = BowThrusterPitchPowerEngine.evaluate(telem.bow_thruster)

        alarms: List[str] = []
        if tb_res.status not in (ThrustBearingStatus.NORMAL,):
            alarms.append(f"ThrustBearing: {tb_res.status.value}")
        if vs_res.status in (VacuumSewageStatus.VACUUM_LOSS_ALARM, VacuumSewageStatus.HIGH_HIGH_LEVEL_LOCKOUT):
            alarms.append(f"VacuumSewage: {vs_res.status.value}")
        if sc_res.status in (ScrubberStatus.QUENCH_HIGH_TEMP_BYPASS, ScrubberStatus.TURBIDITY_LIMIT_EXCEEDED):
            alarms.append(f"Scrubber: {sc_res.status.value}")
        if bt_res.status in (BowThrusterStatus.HYDRAULIC_LOW_PRESSURE_TRIP, BowThrusterStatus.HEADER_TANK_LOW_LEVEL):
            alarms.append(f"BowThruster: {bt_res.status.value}")

        overall_safe = (
            tb_res.bearing_safe
            and vs_res.system_ready
            and sc_res.emission_compliant
            and bt_res.thruster_available
        )

        return MaritimeAuxiliaryBatch8Assessment(
            thrust_bearing=tb_res,
            vacuum_sewage=vs_res,
            scrubber=sc_res,
            bow_thruster=bt_res,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["All auxiliary batch 8 systems nominal"],
        )
