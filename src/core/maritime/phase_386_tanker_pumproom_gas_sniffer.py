"""Phase 386: Tanker Pump Room Atmospheric Hydrocarbon & Bilge Gas Sniffer Engine.

Implements SOLAS II-2 Reg 4.5.10, ISGOTT Ch. 5, and IMO MSC.1/Circ.1370 for continuous
sampling of hydrocarbon (LEL), toxic H2S, oxygen depletion, and bilge flood alarms.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class PumpRoomGasInput:
    """Input telemetry for tanker pump room atmospheric monitoring."""
    hydrocarbon_lel_pct: float = 4.5     # Lower Explosive Limit percentage
    h2s_concentration_ppm: float = 1.0   # Hydrogen Sulfide in parts-per-million
    oxygen_concentration_pct: float = 20.9  # Normal atmospheric ~20.9%
    ventilation_ach: float = 22.0        # Air Changes per Hour (SOLAS min 20)
    ventilation_fan_running: bool = True
    vent_diff_pressure_pa: float = 150.0 # Differential pressure confirmation
    bilge_water_level_m: float = 0.12    # Bilge well water depth
    sampling_point_id: str = "PUMP_ROOM_LOWER_PLATFORM"


@dataclass
class PumpRoomGasResult:
    """Evaluation result for tanker pump room safety and interlocks."""
    atmosphere_status: str  # SAFE, WARNING, CRITICAL_EXPLOSION_HAZARD, TOXIC_HAZARD, ASPHYXIATION_HAZARD
    cargo_pump_trip_required: bool
    ventilation_compliant: bool
    bilge_alarm: bool
    entry_permitted: bool
    warnings: List[str] = field(default_factory=list)


class TankerPumpRoomGasEngine:
    """Evaluates pump room flammable, toxic gases, ventilation, and flood interlocks."""

    LEL_PRE_ALARM_PCT = 10.0
    LEL_CRITICAL_TRIP_PCT = 20.0
    H2S_WARNING_PPM = 5.0
    H2S_EVACUATION_PPM = 10.0
    O2_DEFICIENT_LIMIT_PCT = 19.5
    MIN_VENTILATION_ACH = 20.0
    MIN_VENT_DIFF_PRESSURE_PA = 50.0
    MAX_BILGE_LEVEL_M = 0.30

    def evaluate(self, telemetry: PumpRoomGasInput) -> PumpRoomGasResult:
        warnings: List[str] = []

        # 1. Ventilation compliance check
        vent_compliant = (
            telemetry.ventilation_fan_running
            and telemetry.ventilation_ach >= self.MIN_VENTILATION_ACH
            and telemetry.vent_diff_pressure_pa >= self.MIN_VENT_DIFF_PRESSURE_PA
        )
        if not vent_compliant:
            warnings.append(
                f"VENTILATION INTERLOCK FAIL: ACH {telemetry.ventilation_ach} or "
                f"diff pressure {telemetry.vent_diff_pressure_pa} Pa below SOLAS limits."
            )

        # 2. Bilge High Level Switch
        bilge_alarm = telemetry.bilge_water_level_m > self.MAX_BILGE_LEVEL_M
        if bilge_alarm:
            warnings.append(
                f"BILGE FLOODING ALARM: Water level {telemetry.bilge_water_level_m}m "
                f"exceeds {self.MAX_BILGE_LEVEL_M}m threshold."
            )

        # 3. Gas & Atmosphere Hazard Assessment
        cargo_pump_trip = False
        if telemetry.hydrocarbon_lel_pct >= self.LEL_CRITICAL_TRIP_PCT:
            atmosphere_status = "CRITICAL_EXPLOSION_HAZARD"
            cargo_pump_trip = True
            warnings.append(
                f"SOLAS II-2 CRITICAL GAS ALARM: Hydrocarbon {telemetry.hydrocarbon_lel_pct}% LEL "
                f">= {self.LEL_CRITICAL_TRIP_PCT}% trip threshold. CARGO PUMPS TRIPPED."
            )
        elif telemetry.h2s_concentration_ppm >= self.H2S_EVACUATION_PPM:
            atmosphere_status = "TOXIC_HAZARD"
            warnings.append(
                f"H2S TOXIC EVACUATION ALARM: {telemetry.h2s_concentration_ppm} ppm "
                f">= {self.H2S_EVACUATION_PPM} ppm threshold. IMMEDIATE EVACUATION."
            )
        elif telemetry.oxygen_concentration_pct < self.O2_DEFICIENT_LIMIT_PCT:
            atmosphere_status = "ASPHYXIATION_HAZARD"
            warnings.append(
                f"OXYGEN DEFICIENT: O2 level {telemetry.oxygen_concentration_pct}% "
                f"< {self.O2_DEFICIENT_LIMIT_PCT}% limit."
            )
        elif (
            telemetry.hydrocarbon_lel_pct >= self.LEL_PRE_ALARM_PCT
            or telemetry.h2s_concentration_ppm >= self.H2S_WARNING_PPM
        ):
            atmosphere_status = "WARNING"
            warnings.append(
                f"PRE-ALARM: Elevated gas readings (LEL: {telemetry.hydrocarbon_lel_pct}%, "
                f"H2S: {telemetry.h2s_concentration_ppm} ppm)."
            )
        else:
            atmosphere_status = "SAFE"

        # Interlock: Cargo pump drive cannot operate without ventilation
        if not vent_compliant:
            cargo_pump_trip = True

        # Entry permission: Safe atmosphere AND compliant ventilation AND no bilge flooding
        entry_permitted = (
            atmosphere_status == "SAFE"
            and vent_compliant
            and not bilge_alarm
        )

        return PumpRoomGasResult(
            atmosphere_status=atmosphere_status,
            cargo_pump_trip_required=cargo_pump_trip,
            ventilation_compliant=vent_compliant,
            bilge_alarm=bilge_alarm,
            entry_permitted=entry_permitted,
            warnings=warnings,
        )
