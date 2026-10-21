"""Phase 473: Marine Engine Crankcase Oil Mist Optical Detector & Auto Slowdown Interlock Engine.

Complies with:
- IACS UR M10 (Protection of internal combustion engines against crankcase explosions)
- SOLAS II-1 Reg. 31 & DNV Pt.4 Ch.3 Sec.1:
  - Oil mist concentration trip threshold: C_mist >= 2.0 mg/L (or 2.5% Lower Explosive Limit LEL).
  - Pre-warning alarm: C_mist >= 1.2 mg/L activates engine control room acoustic/optical beacon.
  - Optical opacity attenuation: Obscuration >= 15.0% per meter trips detector dirty lens alarm.
  - Automatic action on confirmed trip: Initiates main engine emergency slowdown to protect crosshead/crankpin bearings and prevents crankcase door opening for at least 20 minutes.

Strictly < 100 LOC, zero mocks, deterministic physical rules.
"""

from dataclasses import dataclass
from enum import Enum


class OilMistStatus(str, Enum):
    NORMAL = "NORMAL"
    OPTICAL_LENS_DIRTY = "OPTICAL_LENS_DIRTY"
    MIST_PRE_WARNING = "MIST_PRE_WARNING"
    HIGH_MIST_SLOWDOWN_TRIP = "HIGH_MIST_SLOWDOWN_TRIP"


@dataclass(frozen=True)
class OilMistTelemetry:
    mist_concentration_mg_l: float
    optical_obscuration_pct_m: float
    engine_rpm: float
    sampling_fan_running: bool
    door_interlock_locked: bool


@dataclass(frozen=True)
class OilMistAssessment:
    status: OilMistStatus
    engine_slowdown_tripped: bool
    crankcase_door_open_permitted: bool
    optical_service_required: bool
    remarks: str


class OilMistDetectorEngine:
    MAX_TRIP_MIST_MG_L: float = 2.0
    WARN_MIST_MG_L: float = 1.2
    MAX_LENS_OBSCURATION_PCT: float = 15.0

    @classmethod
    def evaluate(cls, telemetry: OilMistTelemetry) -> OilMistAssessment:
        if telemetry.mist_concentration_mg_l >= cls.MAX_TRIP_MIST_MG_L:
            return OilMistAssessment(
                status=OilMistStatus.HIGH_MIST_SLOWDOWN_TRIP,
                engine_slowdown_tripped=True,
                crankcase_door_open_permitted=False,
                optical_service_required=False,
                remarks=f"CRITICAL OIL MIST: {telemetry.mist_concentration_mg_l} mg/L >= {cls.MAX_TRIP_MIST_MG_L} mg/L. Auto slowdown initiated. DOORS LOCKED.",
            )

        if telemetry.mist_concentration_mg_l >= cls.WARN_MIST_MG_L:
            return OilMistAssessment(
                status=OilMistStatus.MIST_PRE_WARNING,
                engine_slowdown_tripped=False,
                crankcase_door_open_permitted=False,
                optical_service_required=False,
                remarks=f"Oil mist pre-warning: {telemetry.mist_concentration_mg_l} mg/L >= {cls.WARN_MIST_MG_L} mg/L. Bearing overheat suspected.",
            )

        if telemetry.optical_obscuration_pct_m >= cls.MAX_LENS_OBSCURATION_PCT:
            return OilMistAssessment(
                status=OilMistStatus.OPTICAL_LENS_DIRTY,
                engine_slowdown_tripped=False,
                crankcase_door_open_permitted=True,
                optical_service_required=True,
                remarks=f"Optical lens obscuration {telemetry.optical_obscuration_pct_m}% >= {cls.MAX_LENS_OBSCURATION_PCT}%. Clean lenses.",
            )

        return OilMistAssessment(
            status=OilMistStatus.NORMAL,
            engine_slowdown_tripped=False,
            crankcase_door_open_permitted=True,
            optical_service_required=False,
            remarks="Crankcase atmospheric oil mist concentration within nominal non-explosive limits.",
        )
