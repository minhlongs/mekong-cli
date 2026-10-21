"""Master Maritime Safety Auxiliary Systems Coordinator (Phases 467-470).

Aggregates:
- Phase 467: Chilled Water Anti-Freeze & Low Suction Protection
- Phase 468: Incinerator Flue Gas High Temperature & Draft Vacuum Protection
- Phase 469: Deepwell Cargo Pump Stripping & Dry-Running Cavitation Protection
- Phase 470: Fuel Oil Settling Tank Temperature & Quick-Closing Valve Safety

Strictly < 90 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass

from src.core.maritime.phase_467_chilled_water_antifreeze import (
    ChilledWaterAntiFreezeEngine,
    ChilledWaterAssessment,
    ChilledWaterStatus,
    ChilledWaterTelemetry,
)
from src.core.maritime.phase_468_incinerator_flue_protection import (
    IncineratorAssessment,
    IncineratorProtectionEngine,
    IncineratorStatus,
    IncineratorTelemetry,
)
from src.core.maritime.phase_469_deepwell_pump_stripping import (
    DeepwellPumpAssessment,
    DeepwellPumpProtectionEngine,
    DeepwellPumpStatus,
    DeepwellPumpTelemetry,
)
from src.core.maritime.phase_470_settling_tank_safety import (
    SettlingTankAssessment,
    SettlingTankSafetyEngine,
    SettlingTankStatus,
    SettlingTankTelemetry,
)


@dataclass(frozen=True)
class MaritimePhases467to470Telemetry:
    chilled_water: ChilledWaterTelemetry
    incinerator: IncineratorTelemetry
    deepwell_pump: DeepwellPumpTelemetry
    settling_tank: SettlingTankTelemetry


@dataclass(frozen=True)
class MaritimePhases467to470Assessment:
    overall_safe: bool
    chilled_water_res: ChilledWaterAssessment
    incinerator_res: IncineratorAssessment
    deepwell_pump_res: DeepwellPumpAssessment
    settling_tank_res: SettlingTankAssessment
    active_alarms_count: int


class MaritimeSafetyAuxiliaryBatch2Engine:
    @classmethod
    def evaluate(
        cls, telemetry: MaritimePhases467to470Telemetry
    ) -> MaritimePhases467to470Assessment:
        cw_eval = ChilledWaterAntiFreezeEngine.evaluate(telemetry.chilled_water)
        inc_eval = IncineratorProtectionEngine.evaluate(telemetry.incinerator)
        dp_eval = DeepwellPumpProtectionEngine.evaluate(telemetry.deepwell_pump)
        st_eval = SettlingTankSafetyEngine.evaluate(telemetry.settling_tank)

        alarms = 0
        if cw_eval.status != ChilledWaterStatus.NORMAL:
            alarms += 1
        if inc_eval.status != IncineratorStatus.NORMAL:
            alarms += 1
        if dp_eval.status not in (DeepwellPumpStatus.NORMAL_DISCHARGE, DeepwellPumpStatus.STRIPPING_ACTIVE):
            alarms += 1
        if st_eval.status != SettlingTankStatus.NORMAL:
            alarms += 1

        overall_safe = (
            cw_eval.compressor_permissive
            and not inc_eval.emergency_damper_open
            and not dp_eval.auto_stop_permissive
            and not st_eval.quick_closing_valve_tripped
        )

        return MaritimePhases467to470Assessment(
            overall_safe=overall_safe,
            chilled_water_res=cw_eval,
            incinerator_res=inc_eval,
            deepwell_pump_res=dp_eval,
            settling_tank_res=st_eval,
            active_alarms_count=alarms,
        )
