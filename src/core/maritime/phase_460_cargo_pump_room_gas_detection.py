"""Phase 460: Marine Cargo Pump Room Continuous Hydrocarbon Gas & Toxic Sampling.

Compliant with SOLAS II-2 Reg 4.5.10.1.3 & IACS UR F35.
Monitors lower explosive limit (LEL <= 10%), toxic H2S (<= 5 ppm), pump room bilges level,
and continuous mechanical ventilation pressure differential (DP >= 50 Pa).
"""

from dataclasses import dataclass
from enum import Enum


class PumpRoomGasStatus(str, Enum):
    SAFE = "SAFE"
    VENTILATION_FAILURE = "VENTILATION_FAILURE"
    TOXIC_H2S_ALARM = "TOXIC_H2S_ALARM"
    LEL_PRE_ALARM = "LEL_PRE_ALARM"
    LEL_CRITICAL_TRIP = "LEL_CRITICAL_TRIP"
    BILGE_FLOODING = "BILGE_FLOODING"


@dataclass(frozen=True)
class PumpRoomGasTelemetry:
    hydrocarbon_lel_percent: float
    h2s_toxic_ppm: float
    ventilation_dp_pascals: float
    bilge_high_level_alarm: bool
    sampling_pump_differential_mbar: float


@dataclass(frozen=True)
class PumpRoomGasAssessment:
    status: PumpRoomGasStatus
    ventilation_adequate: bool
    gas_free: bool
    pump_room_isolated: bool
    safety_alarm: bool
    remarks: str


class CargoPumpRoomGasDetectionEngine:
    """SOLAS II-2 Reg 4.5.10.1.3 Continuous Gas Detection & Interlock Logic."""

    MAX_SAFE_LEL_PCT: float = 10.0
    CRITICAL_TRIP_LEL_PCT: float = 20.0  # Automatic trip of cargo pumps at 20% LEL
    MAX_SAFE_H2S_PPM: float = 5.0
    MIN_VENTILATION_DP_PA: float = 50.0  # Minimum negative pressure/differential
    MIN_SAMPLING_FLOW_MBAR: float = 15.0

    @classmethod
    def evaluate(cls, telemetry: PumpRoomGasTelemetry) -> PumpRoomGasAssessment:
        if telemetry.hydrocarbon_lel_percent >= cls.CRITICAL_TRIP_LEL_PCT:
            return PumpRoomGasAssessment(
                status=PumpRoomGasStatus.LEL_CRITICAL_TRIP,
                ventilation_adequate=telemetry.ventilation_dp_pascals >= cls.MIN_VENTILATION_DP_PA,
                gas_free=False,
                pump_room_isolated=True,
                safety_alarm=True,
                remarks=f"Critical hydrocarbon vapor {telemetry.hydrocarbon_lel_percent}% LEL: automatic cargo pump shutdown.",
            )

        if telemetry.hydrocarbon_lel_percent >= cls.MAX_SAFE_LEL_PCT:
            return PumpRoomGasAssessment(
                status=PumpRoomGasStatus.LEL_PRE_ALARM,
                ventilation_adequate=telemetry.ventilation_dp_pascals >= cls.MIN_VENTILATION_DP_PA,
                gas_free=False,
                pump_room_isolated=False,
                safety_alarm=True,
                remarks=f"Hydrocarbon vapor {telemetry.hydrocarbon_lel_percent}% LEL exceeds 10% pre-alarm threshold.",
            )

        if telemetry.h2s_toxic_ppm >= cls.MAX_SAFE_H2S_PPM:
            return PumpRoomGasAssessment(
                status=PumpRoomGasStatus.TOXIC_H2S_ALARM,
                ventilation_adequate=telemetry.ventilation_dp_pascals >= cls.MIN_VENTILATION_DP_PA,
                gas_free=False,
                pump_room_isolated=False,
                safety_alarm=True,
                remarks=f"Toxic H2S concentration {telemetry.h2s_toxic_ppm} ppm exceeds 5 ppm limit.",
            )

        if telemetry.bilge_high_level_alarm:
            return PumpRoomGasAssessment(
                status=PumpRoomGasStatus.BILGE_FLOODING,
                ventilation_adequate=telemetry.ventilation_dp_pascals >= cls.MIN_VENTILATION_DP_PA,
                gas_free=True,
                pump_room_isolated=False,
                safety_alarm=True,
                remarks="Pump room bilge high level switch actuated: potential cargo or sea flooding.",
            )

        if telemetry.ventilation_dp_pascals < cls.MIN_VENTILATION_DP_PA:
            return PumpRoomGasAssessment(
                status=PumpRoomGasStatus.VENTILATION_FAILURE,
                ventilation_adequate=False,
                gas_free=True,
                pump_room_isolated=False,
                safety_alarm=True,
                remarks="Negative pressure extraction ventilation DP below 50 Pa requirement.",
            )

        return PumpRoomGasAssessment(
            status=PumpRoomGasStatus.SAFE,
            ventilation_adequate=True,
            gas_free=True,
            pump_room_isolated=False,
            safety_alarm=False,
            remarks="Cargo pump room atmosphere safe: hydrocarbon < 10% LEL, H2S < 5 ppm, ventilation active.",
        )
