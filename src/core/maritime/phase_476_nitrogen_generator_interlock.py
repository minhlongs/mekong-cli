"""Phase 476: Deck Nitrogen Generator Membrane Separation & O2 Interlock Engine.

Complies with:
- SOLAS II-2 Reg. 4.5.5.3 (Inert Gas Systems for Chemical & Gas Carriers):
  - Membrane feed air pressure: P >= 7.0 bar.
  - Membrane feed air temperature: 40.0 C <= T <= 55.0 C.
  - O2 content in delivered nitrogen: nominal <= 1.0% vol, max limit <= 5.0% vol.
  - Auto-action: If O2 > 5.0% vol, trip cargo deck isolation valve and divert nitrogen to vent mast.

Strictly < 110 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass
from enum import Enum


class NitrogenGeneratorStatus(str, Enum):
    NORMAL = "NORMAL"
    LOW_FEED_AIR_PRESSURE_TRIP = "LOW_FEED_AIR_PRESSURE_TRIP"
    ABNORMAL_FEED_TEMPERATURE_ALARM = "ABNORMAL_FEED_TEMPERATURE_ALARM"
    HIGH_O2_VENTING_TRIP = "HIGH_O2_VENTING_TRIP"
    PRE_FILTER_DP_HIGH_WARNING = "PRE_FILTER_DP_HIGH_WARNING"


@dataclass(frozen=True)
class NitrogenGeneratorTelemetry:
    feed_pressure_bar: float
    feed_temperature_c: float
    oxygen_content_pct: float
    filter_dp_bar: float
    plant_running: bool
    deck_demand_active: bool


@dataclass(frozen=True)
class NitrogenGeneratorAssessment:
    status: NitrogenGeneratorStatus
    deck_isolation_valve_open: bool
    atmospheric_vent_valve_open: bool
    heater_control_active: bool
    remarks: str


class NitrogenGeneratorSafetyEngine:
    MIN_FEED_PRESSURE_BAR: float = 7.0
    MIN_FEED_TEMP_C: float = 40.0
    MAX_FEED_TEMP_C: float = 55.0
    MAX_CARGO_O2_PCT: float = 5.0
    MAX_FILTER_DP_BAR: float = 0.35

    @classmethod
    def evaluate(cls, telemetry: NitrogenGeneratorTelemetry) -> NitrogenGeneratorAssessment:
        if not telemetry.plant_running:
            return NitrogenGeneratorAssessment(
                status=NitrogenGeneratorStatus.NORMAL,
                deck_isolation_valve_open=False,
                atmospheric_vent_valve_open=False,
                heater_control_active=False,
                remarks="Nitrogen generator plant on standby.",
            )

        if telemetry.feed_pressure_bar < cls.MIN_FEED_PRESSURE_BAR:
            return NitrogenGeneratorAssessment(
                status=NitrogenGeneratorStatus.LOW_FEED_AIR_PRESSURE_TRIP,
                deck_isolation_valve_open=False,
                atmospheric_vent_valve_open=True,
                heater_control_active=False,
                remarks=f"TRIP: Feed air pressure {telemetry.feed_pressure_bar} bar < {cls.MIN_FEED_PRESSURE_BAR} bar. Separation halted.",
            )

        if telemetry.oxygen_content_pct > cls.MAX_CARGO_O2_PCT:
            return NitrogenGeneratorAssessment(
                status=NitrogenGeneratorStatus.HIGH_O2_VENTING_TRIP,
                deck_isolation_valve_open=False,
                atmospheric_vent_valve_open=True,
                heater_control_active=False,
                remarks=f"SOLAS TRIP: O2 {telemetry.oxygen_content_pct}% > {cls.MAX_CARGO_O2_PCT}%. Deck isolated, nitrogen diverted to vent mast.",
            )

        if telemetry.feed_temperature_c < cls.MIN_FEED_TEMP_C or telemetry.feed_temperature_c > cls.MAX_FEED_TEMP_C:
            return NitrogenGeneratorAssessment(
                status=NitrogenGeneratorStatus.ABNORMAL_FEED_TEMPERATURE_ALARM,
                deck_isolation_valve_open=telemetry.deck_demand_active,
                atmospheric_vent_valve_open=False,
                heater_control_active=telemetry.feed_temperature_c < cls.MIN_FEED_TEMP_C,
                remarks=f"ALARM: Feed temp {telemetry.feed_temperature_c}C outside range [{cls.MIN_FEED_TEMP_C}, {cls.MAX_FEED_TEMP_C}]C.",
            )

        if telemetry.filter_dp_bar > cls.MAX_FILTER_DP_BAR:
            return NitrogenGeneratorAssessment(
                status=NitrogenGeneratorStatus.PRE_FILTER_DP_HIGH_WARNING,
                deck_isolation_valve_open=telemetry.deck_demand_active,
                atmospheric_vent_valve_open=False,
                heater_control_active=False,
                remarks=f"WARNING: Pre-filter DP {telemetry.filter_dp_bar} bar > {cls.MAX_FILTER_DP_BAR} bar. Coalescing element service required.",
            )

        return NitrogenGeneratorAssessment(
            status=NitrogenGeneratorStatus.NORMAL,
            deck_isolation_valve_open=telemetry.deck_demand_active,
            atmospheric_vent_valve_open=False,
            heater_control_active=False,
            remarks="Nitrogen generator producing compliant inert gas (O2 <= 5.0% vol).",
        )
