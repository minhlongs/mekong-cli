"""Maritime Safety Auxiliary Batch 16 Coordinator Engine (Phases 523-526).
Aggregates Torsional BSR Damper, BNWAS Cascade, Paint Locker Deluge, and Accommodation Ladder.
Strictly < 85 LOC, zero mocks, pure deterministic validation.
"""
from dataclasses import dataclass
from typing import List

from src.core.maritime.phase_523_torsional_vibration_bsr_damper import (
    TorsionalBsrAssessment, TorsionalBsrTelemetry, TorsionalVibrationBsrDamperEngine,
)
from src.core.maritime.phase_524_bnwas_watch_alarm_cascade import (
    BnwasAssessment, BnwasTelemetry, BnwasWatchAlarmCascadeEngine,
)
from src.core.maritime.phase_525_paint_locker_vent_waterspray import (
    PaintLockerAssessment, PaintLockerTelemetry, PaintLockerVentWatersprayEngine,
)
from src.core.maritime.phase_526_accommodation_ladder_winch_safety import (
    AccommodationLadderAssessment, AccommodationLadderTelemetry, AccommodationLadderWinchSafetyEngine,
)


@dataclass(frozen=True)
class MaritimeAuxiliaryBatch16Assessment:
    torsional_bsr_assessment: TorsionalBsrAssessment
    bnwas_assessment: BnwasAssessment
    paint_locker_assessment: PaintLockerAssessment
    accommodation_ladder_assessment: AccommodationLadderAssessment
    overall_safe: bool
    active_alarms_count: int
    system_health_summary: List[str]


class MaritimeSafetyAuxiliaryBatch16Engine:
    @classmethod
    def evaluate_batch16(
        cls,
        torsional_bsr: TorsionalBsrTelemetry,
        bnwas: BnwasTelemetry,
        paint_locker: PaintLockerTelemetry,
        accommodation_ladder: AccommodationLadderTelemetry,
    ) -> MaritimeAuxiliaryBatch16Assessment:
        res_bsr = TorsionalVibrationBsrDamperEngine.evaluate(torsional_bsr)
        res_bnwas = BnwasWatchAlarmCascadeEngine.evaluate(bnwas)
        res_paint = PaintLockerVentWatersprayEngine.evaluate(paint_locker)
        res_ladder = AccommodationLadderWinchSafetyEngine.evaluate(accommodation_ladder)

        alarms: List[str] = []
        if res_bsr.alarm_active:
            alarms.append(f"TORSIONAL_BSR: {res_bsr.alarm_code}")
        if res_bnwas.alarm_active:
            alarms.append(f"BNWAS: {res_bnwas.alarm_code}")
        if res_paint.alarm_active:
            alarms.append(f"PAINT_LOCKER: {res_paint.alarm_code}")
        if res_ladder.alarm_active:
            alarms.append(f"ACCOM_LADDER: {res_ladder.alarm_code}")

        overall_safe = (
            not res_bsr.alarm_active
            and not res_bnwas.alarm_active
            and not res_paint.alarm_active
            and not res_ladder.alarm_active
        )

        return MaritimeAuxiliaryBatch16Assessment(
            torsional_bsr_assessment=res_bsr,
            bnwas_assessment=res_bnwas,
            paint_locker_assessment=res_paint,
            accommodation_ladder_assessment=res_ladder,
            overall_safe=overall_safe,
            active_alarms_count=len(alarms),
            system_health_summary=alarms if alarms else ["ALL_SYSTEMS_OPTIMAL"],
        )
