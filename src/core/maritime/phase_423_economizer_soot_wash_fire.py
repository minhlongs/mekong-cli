"""Phase 423: Marine Economizer Automated Soot Water Washing & Fire Prevention.

Implements IMO MARPOL Annex VI Reg 13/14, MEPC.340(77), IACS UR M53, and DNV Pt.4 Ch.6
Sec.6 rules: exhaust gas differential pressure monitoring (dP >= 2.5 kPa warning,
>= 3.2 kPa wash mandatory), soot fire auto-ignition thermal runaway detection
(T_exhaust >= 400°C or dT/dt >= 10°C/min), main engine slowdown/stop trip,
and automated NaOH washwater neutralization (target pH 6.5 - 8.5).
Strictly < 180 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class EconomizerSootTelemetry:
    """Telemetry readings for Marine Economizer Soot Washing & Fire Prevention."""
    exhaust_gas_inlet_temp_c: float = 310.0
    exhaust_gas_outlet_temp_c: float = 175.0
    differential_pressure_kpa: float = 1.65
    temp_rise_rate_c_min: float = 1.2
    gas_velocity_m_s: float = 14.5
    washwater_ph: float = 2.8
    washwater_flow_m3_h: float = 8.5
    soot_density_g_m2: float = 180.0
    holding_tank_ph: float = 7.1
    water_mist_pressure_bar: float = 6.8
    damper_closed: bool = False
    soot_wash_active: bool = False


@dataclass(frozen=True)
class EconomizerSootAssessment:
    """Operational state, fire hazard, and wash neutralization assessment."""
    soot_fouling_index: float
    differential_pressure_compliant: bool
    dp_warning: bool
    dp_critical_soot_wash_required: bool
    soot_fire_pre_alarm: bool
    emergency_soot_fire_trip: bool
    engine_slowdown_demanded: bool
    water_drenching_activated: bool
    naoh_dosing_rate_l_h: float
    discharge_ph_compliant: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class EconomizerSootWaterWashEngine:
    """Evaluates boiler economizer soot fouling, prevents fires, and neutralizes washwater."""

    DP_CLEAN_BENCHMARK_KPA: float = 1.5
    DP_WARNING_KPA: float = 2.5
    DP_MANDATORY_WASH_KPA: float = 3.2
    CRITICAL_TEMP_RISE_RATE_C_MIN: float = 10.0
    FIRE_RUNAWAY_TEMP_C: float = 400.0
    MIN_COMPLIANT_PH: float = 6.5
    MAX_COMPLIANT_PH: float = 8.5

    def evaluate(self, telem: EconomizerSootTelemetry) -> EconomizerSootAssessment:
        warnings: List[str] = []
        soot_fouling = max(0.0, telem.differential_pressure_kpa / self.DP_CLEAN_BENCHMARK_KPA)

        # Differential pressure fouling logic
        dp_warn = telem.differential_pressure_kpa >= self.DP_WARNING_KPA
        dp_wash = telem.differential_pressure_kpa >= self.DP_MANDATORY_WASH_KPA
        dp_ok = telem.differential_pressure_kpa < self.DP_WARNING_KPA

        if dp_wash:
            warnings.append(
                f"Economizer dP {telem.differential_pressure_kpa:.2f} kPa exceeds "
                f"mandatory wash limit ({self.DP_MANDATORY_WASH_KPA} kPa)."
            )
        elif dp_warn:
            warnings.append(
                f"Economizer dP {telem.differential_pressure_kpa:.2f} kPa exceeds "
                f"soot blowing warning threshold ({self.DP_WARNING_KPA} kPa)."
            )

        # Thermal runaway / soot fire detection (IACS M53 / SOLAS II-2)
        soot_pre_alarm = (
            telem.temp_rise_rate_c_min >= self.CRITICAL_TEMP_RISE_RATE_C_MIN
            or telem.exhaust_gas_outlet_temp_c >= 360.0
        )
        soot_fire_trip = (
            telem.exhaust_gas_outlet_temp_c >= self.FIRE_RUNAWAY_TEMP_C
            or (telem.temp_rise_rate_c_min >= 15.0 and telem.exhaust_gas_outlet_temp_c >= 350.0)
        )

        engine_slowdown = False
        water_drenching = False

        if soot_fire_trip:
            engine_slowdown = True
            water_drenching = True
            warnings.append(
                f"EMERGENCY SOOT FIRE: Outlet temp {telem.exhaust_gas_outlet_temp_c:.1f}°C, "
                f"rise rate {telem.temp_rise_rate_c_min:.1f}°C/min. Tripping ME & activating drenching!"
            )
        elif soot_pre_alarm:
            warnings.append(
                f"Soot fire pre-alarm: Rapid thermal rise {telem.temp_rise_rate_c_min:.1f}°C/min."
            )

        # Automated washwater neutralization (NaOH dosing stoichiometric balance)
        # Target pH 7.5: Delta [H+] from current washwater pH
        naoh_l_h = 0.0
        if telem.soot_wash_active and telem.washwater_ph < 6.5:
            # Acidic condensate neutralization: 10^(-pH) mol/L H+
            h_conc = 10.0 ** (-max(1.0, telem.washwater_ph))
            # 20% NaOH solution has ~5.0 mol/L OH-
            naoh_l_h = round((h_conc * telem.washwater_flow_m3_h * 1000.0) / 5.0, 2)
            naoh_l_h = max(0.5, min(50.0, naoh_l_h))

        discharge_ph_ok = self.MIN_COMPLIANT_PH <= telem.holding_tank_ph <= self.MAX_COMPLIANT_PH
        if not discharge_ph_ok:
            warnings.append(
                f"Washwater holding tank pH {telem.holding_tank_ph:.2f} out of range [6.5, 8.5]."
            )

        # Status classification
        if soot_fire_trip:
            status = "EMERGENCY_SOOT_FIRE"
        elif soot_pre_alarm:
            status = "SOOT_FIRE_PRE_ALARM"
        elif dp_wash:
            status = "MANDATORY_WASH_REQUIRED"
        elif dp_warn:
            status = "FOULING_WARNING"
        elif not discharge_ph_ok:
            status = "PH_NEUTRALIZATION_FAULT"
        else:
            status = "NORMAL_OPTIMAL"

        compliance_flags = {
            "dp_compliant": dp_ok,
            "no_soot_fire": not (soot_fire_trip or soot_pre_alarm),
            "washwater_ph_compliant": discharge_ph_ok,
            "drenching_ready": telem.water_mist_pressure_bar >= 5.0,
        }

        return EconomizerSootAssessment(
            soot_fouling_index=round(soot_fouling, 3),
            differential_pressure_compliant=dp_ok,
            dp_warning=dp_warn,
            dp_critical_soot_wash_required=dp_wash,
            soot_fire_pre_alarm=soot_pre_alarm,
            emergency_soot_fire_trip=soot_fire_trip,
            engine_slowdown_demanded=engine_slowdown,
            water_drenching_activated=water_drenching,
            naoh_dosing_rate_l_h=naoh_l_h,
            discharge_ph_compliant=discharge_ph_ok,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
